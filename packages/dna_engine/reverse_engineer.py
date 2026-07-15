"""
品牌DNA逆向工程引擎

核心功能：给定一张产品图，通过GPT-4o Vision反推：
1. 相机参数（机身、镜头、焦距、光圈、ISO）
2. 灯光方案（灯数、位置、附件、色温）
3. 后期调色（色温偏移、HSL、色调曲线、LUT）
4. 构图规则
5. 使用软件
6. 材质识别

输出：结构化的 ImageAnalysisResult
"""
import os
import json
import base64
import time
import requests
from typing import Optional
from .types import *

def _call_vision_api(image_url: str, prompt: str, api_key: Optional[str] = None) -> str:
    """调用GPT-4o Vision分析图像"""
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("需要 OPENAI_API_KEY。请设置环境变量或在调用时传入 api_key 参数。")

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}
                ]
            }],
            "max_tokens": 4096,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        },
        timeout=60
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Vision API error {resp.status_code}: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"]


class ReverseEngineer:
    """品牌视觉逆向分析引擎"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def analyze(self, image_url: str) -> ImageAnalysisResult:
        """对一张产品图执行全维度逆向分析"""
        raw = self._full_analysis(image_url)
        data = self._parse_json(raw)
        return ImageAnalysisResult(
            image_url=image_url,
            camera=self._parse_camera(data.get("camera", {})),
            lighting=self._parse_lighting(data.get("lighting", {})),
            color_grading=self._parse_color(data.get("color_grading", {})),
            composition=self._parse_composition(data.get("composition", {})),
            software=self._parse_software(data.get("software", {})),
            materials_detected=data.get("materials", []),
            style_keywords=data.get("style_keywords", []),
            brand_match=data.get("brand_match"),
            raw_analysis=raw,
        )

    def _full_analysis(self, image_url: str) -> str:
        prompt = """你是一位顶尖产品摄影师和数字影像分析师。请对这张产品图片进行**专业级逆向分析**，输出JSON。

分析维度：

1. **camera（相机参数）**:
   - focal_length_mm: 等效全画幅焦距(估算)
   - aperture_f: 光圈值(根据景深/焦外虚化推测)
   - shutter_speed: 快门速度(根据动态模糊推测)
   - iso: ISO值(根据噪点推测)
   - camera_model: 推测机身品牌/型号
   - lens_model: 推测镜头型号
   - has_exif: 是否有EXIF特征
   - confidence: 置信度0-1

2. **lighting（灯光方案）**:
   - light_count: 灯数
   - light_types: 灯类型数组 [softbox,beauty_dish,umbrella,ring,etc]
   - key_light_position: 主光位置描述
   - fill_light_ratio: 填充比(0-1)
   - backlight: 是否有背光
   - color_temperature_k: 色温
   - light_modifiers: 光效附件
   - natural_light: 是否自然光
   - studio: 是否影棚
   - confidence: 置信度0-1

3. **color_grading（后期调色）**:
   - color_temperature_shift: 色温偏移(-100~100)
   - tint_shift: 色调偏移(-100~100)
   - contrast: 对比度(-1~1)
   - highlights/shadows/whites/blacks: 各通道调整(-100~100)
   - texture/clarity/vibrance/saturation: 质感调整(-100~100)
   - tone_curve: 色调曲线近似点[0,0.25,0.5,0.75,1]对应输出
   - hsl_adjustments: HSL各通道{hue,saturation,luminance}调整
   - dominant_color_tone: 主色调 warm/cool/neutral
   - confidence: 置信度0-1

4. **composition（构图）**:
   - rule_of_thirds: 是否三分法
   - golden_ratio: 是否黄金比例
   - symmetry: 是否对称
   - leading_lines: 是否有引导线
   - negative_space: 留白比例0-1
   - product_position: 产品位置
   - aspect_ratio: 画面比例

5. **software（软件推断）**:
   - renderer: 渲染器(Cycles/Octane/Redshift/V-Ray/natural)
   - modeling_software: 建模软件
   - post_software: 后期软件
   - is_cgi: 是否CGI渲染
   - confidence: 置信度0-1

6. **materials**: 识别到的材质数组
7. **style_keywords**: 风格关键词数组
8. **brand_match**: 匹配的品牌风格描述

注意：所有数值必须有理有据。如果没有足够证据，返回null而不是猜测。"""
        return _call_vision_api(image_url, prompt, self.api_key)

    def _parse_json(self, text: str) -> dict:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except:
            return {}

    def _parse_camera(self, d: dict) -> CameraInference:
        return CameraInference(
            focal_length_mm=d.get("focal_length_mm"),
            aperture_f=d.get("aperture_f"),
            shutter_speed=d.get("shutter_speed"),
            iso=d.get("iso"),
            camera_model=d.get("camera_model"),
            lens_model=d.get("lens_model"),
            has_exif=d.get("has_exif", False),
            confidence=d.get("confidence", 0),
        )

    def _parse_lighting(self, d: dict) -> LightingInference:
        return LightingInference(
            light_count=d.get("light_count"),
            light_types=d.get("light_types", []),
            key_light_position=d.get("key_light_position"),
            fill_light_ratio=d.get("fill_light_ratio"),
            backlight=d.get("backlight", False),
            color_temperature_k=d.get("color_temperature_k"),
            light_modifiers=d.get("light_modifiers", []),
            natural_light=d.get("natural_light", False),
            studio=d.get("studio", False),
            confidence=d.get("confidence", 0),
        )

    def _parse_color(self, d: dict) -> ColorGradingInference:
        return ColorGradingInference(
            color_temperature_shift=d.get("color_temperature_shift"),
            tint_shift=d.get("tint_shift"),
            contrast=d.get("contrast"),
            highlights=d.get("highlights"),
            shadows=d.get("shadows"),
            whites=d.get("whites"),
            blacks=d.get("blacks"),
            texture=d.get("texture"),
            clarity=d.get("clarity"),
            vibrance=d.get("vibrance"),
            saturation=d.get("saturation"),
            tone_curve=d.get("tone_curve"),
            hsl_adjustments=d.get("hsl_adjustments", {}),
            dominant_color_tone=d.get("dominant_color_tone"),
            color_grading_lut=d.get("color_grading_lut"),
            confidence=d.get("confidence", 0),
        )

    def _parse_composition(self, d: dict) -> CompositionAnalysis:
        return CompositionAnalysis(
            rule_of_thirds=d.get("rule_of_thirds", False),
            golden_ratio=d.get("golden_ratio", False),
            symmetry=d.get("symmetry", False),
            leading_lines=d.get("leading_lines", False),
            negative_space=d.get("negative_space", 0),
            product_position=d.get("product_position", "center"),
            aspect_ratio=d.get("aspect_ratio", "4:3"),
            crop_info=d.get("crop_info"),
        )

    def _parse_software(self, d: dict) -> SoftwareInference:
        return SoftwareInference(
            renderer=d.get("renderer"),
            modeling_software=d.get("modeling_software"),
            post_software=d.get("post_software"),
            is_cgi=d.get("is_cgi", False),
            confidence=d.get("confidence", 0),
        )
