"""
Module B: ACR Analyzer — GPT-4o Vision 驱动的 ACR 直方图 + 参数解析

核心能力:
- 输入单张裁切模块图片URL/路径
- 调用 GPT-4o Vision 分析 ACR 参数:
  1. 亮度直方图分布 (Shadow/Midtone/Highlight 像素比例)
  2. RGB 三通道主峰偏移位置 + 重叠度
  3. Shadow/Highlight 裁剪状态
  4. ACR Basic 全部参数: Exposure/Contrast/Highlights/Shadows/Whites/Blacks/
     Texture/Clarity/Dehaze/Vibrance/Saturation/Temperature_K/Tint
  5. Tone Curve 5个锚点: Black/Shadow/Midtone/Highlight/White Point
- 强制输出标准化JSON，禁止空值填充(未知字段标记null)
- 同时输出视觉DNA维度: 构图/光比/分层/色板/锐度/暗角

依赖: openai, Pillow
"""

import os
import re
import json
import base64
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class HistogramBaseInfo:
    """直方图基础信息"""
    luminance_distribution_bias: str = ""
    shadow_pixel_ratio: float = 0.0
    midtone_pixel_ratio: float = 0.0
    highlight_pixel_ratio: float = 0.0
    rgb_peak: Dict[str, int] = field(default_factory=lambda: {"R": 0, "G": 0, "B": 0})
    rgb_overlap_ratio: float = 0.0
    shadow_clipping: bool = False
    highlight_clipping: bool = False
    gamma_value: float = 2.2


@dataclass
class ACRBasicAdjust:
    """ACR Basic 面板全部参数"""
    exposure: float = 0.0
    contrast: int = 0
    highlights: int = 0
    shadows: int = 0
    whites: int = 0
    blacks: int = 0
    texture: int = 0
    clarity: int = 0
    dehaze: int = 0
    vibrance: int = 0
    saturation: int = 0
    temperature_k: int = 5500
    tint: int = 0


@dataclass
class ToneCurveKeyPoints:
    """Tone Curve 5个锚点 (x,y 归一化 0.0-1.0)"""
    black_point: Tuple[float, float] = (0.0, 0.0)
    shadow_point: Tuple[float, float] = (0.25, 0.25)
    midtone_point: Tuple[float, float] = (0.5, 0.5)
    highlight_point: Tuple[float, float] = (0.75, 0.75)
    white_point: Tuple[float, float] = (1.0, 1.0)


@dataclass
class VisualDNA:
    """视觉DNA — 构图/光照/色板/分层"""
    shot_type: str = ""
    composition_type: str = ""
    camera_angle: str = ""
    perspective: str = ""
    light_mode: str = ""
    key_light_direction: str = ""
    fill_light_ratio: float = 0.0
    light_temperature_k: int = 5500
    main_color_hex: str = ""
    aux_color_hex: str = ""
    accent_color_hex: str = ""
    main_color_area_ratio: float = 0.0
    aux_color_area_ratio: float = 0.0
    accent_color_area_ratio: float = 0.0
    color_temperature: str = ""
    foreground_content: str = ""
    midground_content: str = ""
    background_content: str = ""
    depth_of_field: str = ""
    background_blur_strength: float = 0.0
    sharpening_intensity: float = 0.0
    vignette_range: float = 0.0
    vignette_strength: float = 0.0
    style_tags: List[str] = field(default_factory=list)


@dataclass
class TextParams:
    """文字排版参数"""
    copy_content: str = ""
    font_family: str = ""
    font_weight: int = 400
    font_size: int = 0
    line_height: float = 1.5
    paragraph_spacing: int = 0
    letter_spacing: float = 0.0
    text_color_hex: str = ""
    alignment: str = ""
    grid_margin: int = 0
    grid_padding: int = 0


@dataclass
class ModuleACRAnalysis:
    """单个模块的完整ACR分析结果"""
    module_id: str = ""
    module_type: str = ""
    image_url: str = ""
    analyzed_at: str = ""
    histogram: HistogramBaseInfo = field(default_factory=HistogramBaseInfo)
    acr_basic: ACRBasicAdjust = field(default_factory=ACRBasicAdjust)
    tone_curve: ToneCurveKeyPoints = field(default_factory=ToneCurveKeyPoints)
    visual_dna: VisualDNA = field(default_factory=VisualDNA)
    text_params: Optional[TextParams] = None
    analysis_duration_ms: int = 0
    model_used: str = ""
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ═══════════════════════════════════════════════════════════════
# ACR Analysis Prompt Templates
# ═══════════════════════════════════════════════════════════════

ACR_ANALYSIS_SYSTEM_PROMPT = """You are an expert Adobe Camera Raw histogram analyst and visual parameter extraction engine. 
Your sole purpose is to examine product detail page module images and output precise, structured JSON data.

CRITICAL RULES:
1. Only output valid JSON — no markdown, no explanatory text, no code fences.
2. Every numeric field must have a real value from your analysis — do NOT skip or omit fields.
3. If a parameter truly cannot be determined from the image, set it to null, NEVER guess or fill with defaults.
4. Follow the exact JSON schema provided.
5. For histogram analysis, estimate pixel distribution from visual inspection of the image.
6. For ACR parameters, estimate what Adobe Camera Raw settings would produce this look."""

ACR_ANALYSIS_USER_PROMPT = """Analyze this product detail page module image. 

Complete these analyses:

1. HISTOGRAM BASE INFO:
   - Overall luminance pixel distribution tendency: Shadow, Midtone, or Highlight?
   - Estimate the percentage ratio: Shadow_Pixel_Ratio, Midtone_Pixel_Ratio, Highlight_Pixel_Ratio (sum to ~100%)
   - RGB three-channel independent histogram: peak position (0-255) for Red, Green, Blue channels
   - Estimate the overlap degree of the three channels (0.0-1.0)
   - Shadow Clipping: true if black pixels are cut off at the left edge
   - Highlight Clipping: true if white pixels are blown out at the right edge
   - Gamma value: default 2.2 unless visibly different

2. ACR BASIC ADJUST PARAMETERS (within Adobe Camera Raw official ranges):
   - Exposure: -5.0 to +5.0
   - Contrast: -100 to +100
   - Highlights: -100 to +100
   - Shadows: -100 to +100
   - Whites: -100 to +100
   - Blacks: -100 to +100
   - Texture: -100 to +100
   - Clarity: -100 to +100
   - Dehaze: -100 to +100
   - Vibrance: -100 to +100
   - Saturation: -100 to +100
   - Temperature_K: 2000 to 50000 (Kelvin)
   - Tint: -150 to +150

3. TONE CURVE KEY POINTS (5 anchor points, x,y normalized 0.0-1.0):
   - Black Point, Shadow Point, Midtone Point, Highlight Point, White Point

4. VISUAL DNA:
   - Shot type: MediumShot / CloseUp / WideShot / Macro / TopDown
   - Composition: Centered / RuleOfThirds / GoldenRatio / Symmetry / LeadingLines
   - Camera angle: EyeLevel / HighAngle / LowAngle / Birdseye / Dutch
   - Perspective: Front / ThreeQuarter / Profile / TopDown
   - Lighting: SoftFrontKeyLight / Rembrandt / Split / Butterfly / Loop / SingleHardLight / DiffusedAmbient
   - Key light direction: TopLeft / TopRight / Front / Side / Back
   - Fill light ratio (0.0-1.0)
   - Light temperature in Kelvin
   - Main/Aux/Accent color HEX codes and area ratios (0.0-1.0, sum to ~1.0)
   - Foreground/Midground/Background content descriptions
   - Depth of field: Shallow / Medium / Deep
   - Sharpening intensity (0.0-1.0), Vignette range (0.0-1.0), Vignette strength (0.0-1.0)
   - Style tags: [minimalist, luxury, industrial, natural, warm, cool, etc.]

5. TEXT PARAMS (if the module contains visible text):
   - Extract visible text content
   - Font family, weight, size (px), line height, letter spacing (em)
   - Text color HEX, alignment, grid margin/padding (px)

Return ONLY this JSON structure (replace values, no extra text):
{
  "Histogram_BaseInfo": {
    "Luminance_Distribution_Bias": "MidtoneMain",
    "Shadow_Pixel_Ratio": 0.15,
    "Midtone_Pixel_Ratio": 0.60,
    "Highlight_Pixel_Ratio": 0.25,
    "RGB_Peak": {"R": 128, "G": 140, "B": 120},
    "RGB_Overlap_Ratio": 0.75,
    "Shadow_Clipping": false,
    "Highlight_Clipping": false,
    "Gamma_Value": 2.2
  },
  "ACR_Basic_Adjust": {
    "Exposure": 0.0,
    "Contrast": 0,
    "Highlights": 0,
    "Shadows": 0,
    "Whites": 0,
    "Blacks": 0,
    "Texture": 0,
    "Clarity": 0,
    "Dehaze": 0,
    "Vibrance": 0,
    "Saturation": 0,
    "Temperature_K": 5500,
    "Tint": 0
  },
  "Tone_Curve_Key_Points": {
    "Black_Point": [0.0, 0.0],
    "Shadow_Point": [0.25, 0.25],
    "Midtone_Point": [0.5, 0.5],
    "Highlight_Point": [0.75, 0.75],
    "White_Point": [1.0, 1.0]
  },
  "Visual_DNA": {
    "Shot_Type": "MediumShot",
    "Composition_Type": "Centered",
    "Camera_Angle": "EyeLevel",
    "Perspective": "Front",
    "Light_Mode": "SoftFrontKeyLight",
    "Key_Light_Direction": "TopLeft",
    "Fill_Light_Ratio": 0.3,
    "Light_Temperature_K": 5500,
    "Main_Color_Hex": "#FFFFFF",
    "Aux_Color_Hex": "#CCCCCC",
    "Accent_Color_Hex": "#333333",
    "Main_Color_Area_Ratio": 0.5,
    "Aux_Color_Area_Ratio": 0.3,
    "Accent_Color_Area_Ratio": 0.2,
    "Color_Temperature": "Neutral",
    "Foreground_Content": "",
    "Midground_Content": "",
    "Background_Content": "",
    "Depth_Of_Field": "Medium",
    "Background_Blur_Strength": 0.0,
    "Sharpening_Intensity": 0.0,
    "Vignette_Range": 0.0,
    "Vignette_Strength": 0.0,
    "Style_Tags": []
  },
  "Text_Params": null
}"""


# ═══════════════════════════════════════════════════════════════
# ACR Analyzer Engine
# ═══════════════════════════════════════════════════════════════

class ACRAnalyzer:
    """ACR参数分析器 — 调用 GPT-4o Vision 分析模块图像"""

    SUPPORTED_MODELS = [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
        "gpt-4-vision-preview", "gpt-4o-2024-08-06",
        "claude-3-5-sonnet", "claude-3-opus",
        "gemini-1.5-pro", "gemini-2.0-flash-exp",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key, "timeout": self.timeout}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def analyze(
        self,
        image_path: str,
        module_id: str = "",
        module_type: str = "",
    ) -> ModuleACRAnalysis:
        start_time = datetime.now()
        result = ModuleACRAnalysis(
            module_id=module_id, module_type=module_type,
            image_url=image_path, analyzed_at=datetime.now().isoformat(),
            model_used=self.model,
        )
        if not self.api_key:
            result.errors.append("No API key configured. Set OPENAI_API_KEY or pass api_key.")
            return result
        try:
            image_b64 = self._encode_image(image_path)
            raw_response = self._call_vision_api(image_b64)
            parsed = self._parse_response(raw_response)
            self._populate_result(result, parsed)
        except Exception as e:
            logger.exception(f"ACR analysis failed for {image_path}")
            result.errors.append(str(e))
        result.analysis_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result

    def analyze_batch(
        self, images: List[Tuple[str, str, str]]
    ) -> List[ModuleACRAnalysis]:
        results = []
        for path, mid, mtype in images:
            results.append(self.analyze(path, module_id=mid, module_type=mtype))
        return results

    def _encode_image(self, image_path: str) -> str:
        import requests as req
        if image_path.startswith(("http://", "https://")):
            resp = req.get(image_path, timeout=30)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/png")
            b64 = base64.b64encode(resp.content).decode("utf-8")
        else:
            with open(image_path, "rb") as f:
                content = f.read()
            ext = Path(image_path).suffix.lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
            content_type = mime_map.get(ext, "image/png")
            b64 = base64.b64encode(content).decode("utf-8")
        return f"data:{content_type};base64,{b64}"

    def _call_vision_api(self, image_b64: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ACR_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": ACR_ANALYSIS_USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_b64, "detail": "high"}},
                ]},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or "{}"

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        brace_match = re.search(r"\{[\s\S]*\}", raw)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        logger.error(f"Failed to parse JSON from response: {raw[:500]}...")
        return {}

    def _populate_result(self, result: ModuleACRAnalysis, data: Dict[str, Any]) -> None:
        hist = data.get("Histogram_BaseInfo", {})
        if hist:
            rgb_peak = hist.get("RGB_Peak", {})
            result.histogram = HistogramBaseInfo(
                luminance_distribution_bias=hist.get("Luminance_Distribution_Bias", ""),
                shadow_pixel_ratio=float(hist.get("Shadow_Pixel_Ratio", 0)),
                midtone_pixel_ratio=float(hist.get("Midtone_Pixel_Ratio", 0)),
                highlight_pixel_ratio=float(hist.get("Highlight_Pixel_Ratio", 0)),
                rgb_peak={"R": int(rgb_peak.get("R", 0)), "G": int(rgb_peak.get("G", 0)), "B": int(rgb_peak.get("B", 0))},
                rgb_overlap_ratio=float(hist.get("RGB_Overlap_Ratio", 0)),
                shadow_clipping=bool(hist.get("Shadow_Clipping", False)),
                highlight_clipping=bool(hist.get("Highlight_Clipping", False)),
                gamma_value=float(hist.get("Gamma_Value", 2.2)),
            )
        acr = data.get("ACR_Basic_Adjust", {})
        if acr:
            result.acr_basic = ACRBasicAdjust(
                exposure=float(acr.get("Exposure", 0)), contrast=int(acr.get("Contrast", 0)),
                highlights=int(acr.get("Highlights", 0)), shadows=int(acr.get("Shadows", 0)),
                whites=int(acr.get("Whites", 0)), blacks=int(acr.get("Blacks", 0)),
                texture=int(acr.get("Texture", 0)), clarity=int(acr.get("Clarity", 0)),
                dehaze=int(acr.get("Dehaze", 0)), vibrance=int(acr.get("Vibrance", 0)),
                saturation=int(acr.get("Saturation", 0)),
                temperature_k=int(acr.get("Temperature_K", 5500)), tint=int(acr.get("Tint", 0)),
            )
        tc = data.get("Tone_Curve_Key_Points", {})
        if tc:
            def _pt(k): v = tc.get(k, [0.0, 0.0]); return (float(v[0]), float(v[1])) if isinstance(v, (list, tuple)) and len(v) >= 2 else (0.0, 0.0)
            result.tone_curve = ToneCurveKeyPoints(
                black_point=_pt("Black_Point"), shadow_point=_pt("Shadow_Point"),
                midtone_point=_pt("Midtone_Point"), highlight_point=_pt("Highlight_Point"),
                white_point=_pt("White_Point"),
            )
        vd = data.get("Visual_DNA", {})
        if vd:
            result.visual_dna = VisualDNA(
                shot_type=vd.get("Shot_Type", ""), composition_type=vd.get("Composition_Type", ""),
                camera_angle=vd.get("Camera_Angle", ""), perspective=vd.get("Perspective", ""),
                light_mode=vd.get("Light_Mode", ""), key_light_direction=vd.get("Key_Light_Direction", ""),
                fill_light_ratio=float(vd.get("Fill_Light_Ratio", 0)),
                light_temperature_k=int(vd.get("Light_Temperature_K", 5500)),
                main_color_hex=vd.get("Main_Color_Hex", ""), aux_color_hex=vd.get("Aux_Color_Hex", ""),
                accent_color_hex=vd.get("Accent_Color_Hex", ""),
                main_color_area_ratio=float(vd.get("Main_Color_Area_Ratio", 0)),
                aux_color_area_ratio=float(vd.get("Aux_Color_Area_Ratio", 0)),
                accent_color_area_ratio=float(vd.get("Accent_Color_Area_Ratio", 0)),
                color_temperature=vd.get("Color_Temperature", ""),
                foreground_content=vd.get("Foreground_Content", ""),
                midground_content=vd.get("Midground_Content", ""),
                background_content=vd.get("Background_Content", ""),
                depth_of_field=vd.get("Depth_Of_Field", ""),
                background_blur_strength=float(vd.get("Background_Blur_Strength", 0)),
                sharpening_intensity=float(vd.get("Sharpening_Intensity", 0)),
                vignette_range=float(vd.get("Vignette_Range", 0)),
                vignette_strength=float(vd.get("Vignette_Strength", 0)),
                style_tags=vd.get("Style_Tags", []),
            )
        tp = data.get("Text_Params")
        if tp is not None:
            result.text_params = TextParams(
                copy_content=tp.get("Copy_Content", ""), font_family=tp.get("Font_Family", ""),
                font_weight=int(tp.get("Font_Weight", 400)), font_size=int(tp.get("Font_Size", 0)),
                line_height=float(tp.get("Line_Height", 1.5)),
                paragraph_spacing=int(tp.get("Paragraph_Spacing", 0)),
                letter_spacing=float(tp.get("Letter_Spacing", 0)),
                text_color_hex=tp.get("Text_Color_Hex", ""), alignment=tp.get("Alignment", ""),
                grid_margin=int(tp.get("Grid_Margin", 0)), grid_padding=int(tp.get("Grid_Padding", 0)),
            )
        result.confidence = float(data.get("Confidence", 0.0))


def analyze_module_image(
    image_path: str,
    module_id: str = "",
    module_type: str = "",
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
) -> ModuleACRAnalysis:
    """快速分析单张模块图片的ACR参数"""
    analyzer = ACRAnalyzer(api_key=api_key, model=model)
    return analyzer.analyze(image_path, module_id=module_id, module_type=module_type)
