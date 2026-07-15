"""
Module C: Style Engine — 风格库 + ACR指纹 + 视觉DNA存储 + Prompt生成

核心能力:
- 风格库: 存储每个模块的ACR指纹 + 视觉DNA (ModuleACRFingerprint)
- 全局约束: BaseTemperatureK / MaxContrastOffset(15) / MaxSaturationOffset(10)
- Positive Prompt 生成: 锁定直方图/色调/光照/色板
- Negative Prompt 生成: 反向约束防止风格漂移
- 支持 JSON 持久化 / 版本管理 / 增量更新

依赖: acr_analyzer (ModuleACRAnalysis), json, typing
"""

import os
import re
import json
import copy
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from .acr_analyzer import (
    ModuleACRAnalysis,
    HistogramBaseInfo,
    ACRBasicAdjust,
    ToneCurveKeyPoints,
    VisualDNA,
    TextParams,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════


@dataclass
class GlobalConstraint:
    """全局风格约束 — 保证整个页面一致性"""
    # 色温基准
    base_temperature_k: int = 4800
    # 对比度最大偏移 (任意两模块之间)
    max_contrast_offset: int = 15
    # 饱和度最大偏移
    max_saturation_offset: int = 10
    # 曝光最大偏移 (EV)
    max_exposure_offset: float = 0.5
    # 色温最大偏移 (K)
    max_temperature_offset: int = 500
    # 色调最大偏移
    max_tint_offset: int = 10
    # 全局 Gamma
    gamma_value: float = 2.2
    # 禁止独立色偏 (任意单模块不得偏离全局基准超过阈值)
    no_independent_color_cast: bool = True
    # 禁止曝光漂移
    no_exposure_drift: bool = True
    # 统一字体系统
    unified_font_system: str = ""
    # 统一间距规范
    unified_spacing_spec: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleACRFingerprint:
    """单个模块的ACR指纹 — 用于锁定风格"""
    module_id: str = ""
    module_type: str = ""

    # 核心 ACR 参数 (从 ModuleACRAnalysis 提取)
    histogram: Dict[str, Any] = field(default_factory=dict)
    acr_params: Dict[str, Any] = field(default_factory=dict)
    tone_curve: Dict[str, Any] = field(default_factory=dict)
    visual_dna: Dict[str, Any] = field(default_factory=dict)
    text_params: Optional[Dict[str, Any]] = None

    # 指纹哈希 (快速对比)
    fingerprint_hash: str = ""

    # 版本追踪
    version: str = "V1.0"
    updated_at: str = ""
    deviation_history: List[float] = field(default_factory=list)  # 历次偏差值

    @staticmethod
    def from_analysis(analysis: ModuleACRAnalysis) -> "ModuleACRFingerprint":
        """从 ModuleACRAnalysis 创建指纹"""
        fp = ModuleACRFingerprint(
            module_id=analysis.module_id,
            module_type=analysis.module_type,
            histogram=analysis.histogram.to_dict() if hasattr(analysis.histogram, 'to_dict') else asdict(analysis.histogram),
            acr_params=analysis.acr_basic.to_dict() if hasattr(analysis.acr_basic, 'to_dict') else asdict(analysis.acr_basic),
            tone_curve=analysis.tone_curve.to_dict() if hasattr(analysis.tone_curve, 'to_dict') else asdict(analysis.tone_curve),
            visual_dna=analysis.visual_dna.to_dict() if hasattr(analysis.visual_dna, 'to_dict') else asdict(analysis.visual_dna),
            text_params=asdict(analysis.text_params) if analysis.text_params else None,
            updated_at=datetime.now().isoformat(),
        )
        fp.fingerprint_hash = fp._compute_hash()
        return fp

    def _compute_hash(self) -> str:
        """计算指纹哈希"""
        import hashlib
        data = json.dumps({
            "histogram": self.histogram,
            "acr_params": self.acr_params,
            "tone_curve": self.tone_curve,
            "visual_dna": self.visual_dna,
        }, sort_keys=True, default=str)
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StyleLibrary:
    """
    完整风格库 — 基准页面的所有模块指纹 + 全局约束
    对应文档中的统一JSON格式: PageBenchmarkID / GlobalConstraint / ModuleLibrary
    """
    page_benchmark_id: str = ""
    url: str = ""
    brand: str = ""

    # 全局约束
    global_constraint: GlobalConstraint = field(default_factory=GlobalConstraint)

    # 模块指纹库
    module_library: List[ModuleACRFingerprint] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    updated_at: str = ""
    version: str = "V1.0"
    total_modules: int = 0

    def to_benchmark_json(self) -> Dict[str, Any]:
        """输出文档指定的统一JSON格式"""
        return {
            "PageBenchmarkID": self.page_benchmark_id,
            "GlobalGlobalConstraint": self.global_constraint.to_dict(),
            "ModuleLibrary": [
                {
                    "ModuleID": fp.module_id,
                    "ModuleType": fp.module_type,
                    "FilePath": "",  # 由上游填充
                    "BoundingBox": [],  # 由上游填充
                    "HistogramFingerprint": {
                        "LuminanceBias": fp.histogram.get("luminance_distribution_bias", ""),
                        "RGBPeak": fp.histogram.get("rgb_peak", {}),
                        "ClipShadow": fp.histogram.get("shadow_clipping", False),
                        "ClipHighlight": fp.histogram.get("highlight_clipping", False),
                        "Gamma": fp.histogram.get("gamma_value", 2.2),
                    },
                    "ACRParams": {
                        "Exposure": fp.acr_params.get("exposure", 0),
                        "Contrast": fp.acr_params.get("contrast", 0),
                        "Highlights": fp.acr_params.get("highlights", 0),
                        "Shadows": fp.acr_params.get("shadows", 0),
                        "Whites": fp.acr_params.get("whites", 0),
                        "Blacks": fp.acr_params.get("blacks", 0),
                        "Temperature_K": fp.acr_params.get("temperature_k", 5500),
                        "Tint": fp.acr_params.get("tint", 0),
                    },
                    "VisualDNA": {
                        "ShotType": fp.visual_dna.get("shot_type", ""),
                        "LightMode": fp.visual_dna.get("light_mode", ""),
                        "MainColorHex": fp.visual_dna.get("main_color_hex", ""),
                        "AuxColorHex": fp.visual_dna.get("aux_color_hex", ""),
                        "AccentColorHex": fp.visual_dna.get("accent_color_hex", ""),
                    },
                    "TextParams": fp.text_params or {},
                    "LastGenerateDeviation": fp.deviation_history[-1] if fp.deviation_history else 0.0,
                    "Version": fp.version,
                }
                for fp in self.module_library
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_benchmark_json(), ensure_ascii=False, indent=indent)

    def save(self, filepath: str) -> None:
        """保存风格库到JSON文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_benchmark_json(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(filepath: str) -> "StyleLibrary":
        """从JSON文件加载风格库"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StyleLibrary.from_benchmark_json(data)

    @staticmethod
    def from_benchmark_json(data: Dict[str, Any]) -> "StyleLibrary":
        """从统一JSON格式反序列化"""
        lib = StyleLibrary(
            page_benchmark_id=data.get("PageBenchmarkID", ""),
        )

        # 全局约束
        gc = data.get("GlobalGlobalConstraint", {})
        lib.global_constraint = GlobalConstraint(
            base_temperature_k=gc.get("BaseTemperatureK", 4800),
            max_contrast_offset=gc.get("MaxContrastOffset", 15),
            max_saturation_offset=gc.get("MaxSaturationOffset", 10),
        )

        # 模块库
        for mod_data in data.get("ModuleLibrary", []):
            hf = mod_data.get("HistogramFingerprint", {})
            acr = mod_data.get("ACRParams", {})
            vd = mod_data.get("VisualDNA", {})

            fp = ModuleACRFingerprint(
                module_id=mod_data.get("ModuleID", ""),
                module_type=mod_data.get("ModuleType", ""),
                histogram={
                    "luminance_distribution_bias": hf.get("LuminanceBias", ""),
                    "rgb_peak": hf.get("RGBPeak", {}),
                    "shadow_clipping": hf.get("ClipShadow", False),
                    "highlight_clipping": hf.get("ClipHighlight", False),
                    "gamma_value": hf.get("Gamma", 2.2),
                },
                acr_params=acr,
                tone_curve={},
                visual_dna=vd,
                text_params=mod_data.get("TextParams"),
                version=mod_data.get("Version", "V1.0"),
                deviation_history=[mod_data.get("LastGenerateDeviation", 0.0)],
            )
            lib.module_library.append(fp)

        lib.total_modules = len(lib.module_library)
        lib.updated_at = datetime.now().isoformat()
        return lib


@dataclass
class PromptResult:
    """Prompt生成结果"""
    module_id: str = ""
    positive_prompt: str = ""
    negative_prompt: str = ""
    global_positive: str = ""
    global_negative: str = ""


# ═══════════════════════════════════════════════════════════════
# Prompt Generator — Positive/Negative Prompt
# ═══════════════════════════════════════════════════════════════

class PromptGenerator:
    """
    文生图Prompt生成器 — 基于ACR指纹锁定风格

    策略:
    - Positive: 锁定直方图分布、RGB通道、色调曲线、白平衡色温色调、
      光照方向、构图框架、色板比例、分层层次
    - Negative: 防止直方图偏移、高光过曝、死黑阴影、RGB偏色、
      白平衡不一致、随机曝光、对比度/饱和度错配、光源方向混乱、
      页面风格碎片化、色调曲线失真、额外裁剪区域、不规范字体文字颜色、
      混乱排版间距
    """

    def __init__(self, global_constraint: Optional[GlobalConstraint] = None):
        self.global_constraint = global_constraint or GlobalConstraint()

    def generate_positive_prompt(
        self, fingerprint: ModuleACRFingerprint
    ) -> str:
        """
        为单个模块生成 Positive Prompt。
        锁定: 直方图/色调/光照/色板/构图
        """
        h = fingerprint.histogram
        acr = fingerprint.acr_params
        vd = fingerprint.visual_dna
        gc = self.global_constraint

        parts = []

        # 模块类型提示
        parts.append(
            f"Generate a product detail page {fingerprint.module_type} module."
        )

        # ACR 直方图锁定
        lum_bias = h.get("luminance_distribution_bias", "MidtoneMain")
        shadow_ratio = h.get("shadow_pixel_ratio", 0)
        midtone_ratio = h.get("midtone_pixel_ratio", 0)
        highlight_ratio = h.get("highlight_pixel_ratio", 0)

        parts.append(
            f"Luminance histogram: {lum_bias} distribution with "
            f"shadow {shadow_ratio:.0%}, midtone {midtone_ratio:.0%}, "
            f"highlight {highlight_ratio:.0%}."
        )

        # RGB通道锁定
        rgb = h.get("rgb_peak", {})
        if rgb:
            parts.append(
                f"RGB channel peaks: Red={rgb.get('R', 128)}, "
                f"Green={rgb.get('G', 128)}, Blue={rgb.get('B', 128)}, "
                f"channels overlapping {h.get('rgb_overlap_ratio', 0.75):.0%}."
            )

        # 裁剪状态
        if h.get("shadow_clipping"):
            parts.append("Shadow clipping present — maintain deep blacks.")
        if h.get("highlight_clipping"):
            parts.append("Highlight clipping present — maintain bright whites.")

        if not h.get("shadow_clipping") and not h.get("highlight_clipping"):
            parts.append(
                "No shadow or highlight clipping — "
                "preserve full tonal range without loss."
            )

        # Gamma
        gamma = h.get("gamma_value", 2.2)
        parts.append(f"Gamma={gamma}.")

        # ACR 参数锁定
        acr_lines = []
        for key, label in [
            ("exposure", "Exposure"), ("contrast", "Contrast"),
            ("highlights", "Highlights"), ("shadows", "Shadows"),
            ("whites", "Whites"), ("blacks", "Blacks"),
            ("texture", "Texture"), ("clarity", "Clarity"),
            ("dehaze", "Dehaze"), ("vibrance", "Vibrance"),
            ("saturation", "Saturation"),
        ]:
            val = acr.get(key, 0)
            if val != 0:
                acr_lines.append(f"{label}={val:+d}" if isinstance(val, int) else f"{label}={val:+.1f}")

        # 色温色调
        temp_k = acr.get("temperature_k", gc.base_temperature_k)
        tint = acr.get("tint", 0)
        acr_lines.append(f"WhiteBalance={temp_k}K Tint={tint:+d}")

        if acr_lines:
            parts.append("ACR parameters: " + ", ".join(acr_lines) + ".")

        # 色调曲线锚点 (如果有)
        tc = fingerprint.tone_curve
        if tc:
            curve_parts = []
            for key in ["black_point", "shadow_point", "midtone_point", "highlight_point", "white_point"]:
                pt = tc.get(key)
                if pt and isinstance(pt, (list, tuple)) and len(pt) == 2:
                    curve_parts.append(f"{key}=({pt[0]:.2f},{pt[1]:.2f})")
            if curve_parts:
                parts.append("Tone curve anchors: " + ", ".join(curve_parts) + ".")

        # 视觉DNA锁定
        parts.append("Visual DNA constraints:")

        shot = vd.get("shot_type", "")
        comp = vd.get("composition_type", "")
        angle = vd.get("camera_angle", "")
        perspective = vd.get("perspective", "")
        if shot:
            parts.append(f"Shot type: {shot}.")
        if comp:
            parts.append(f"Composition: {comp}.")
        if angle:
            parts.append(f"Camera angle: {angle}.")
        if perspective:
            parts.append(f"Perspective: {perspective}.")

        # 光照
        light_mode = vd.get("light_mode", "")
        key_dir = vd.get("key_light_direction", "")
        fill_ratio = vd.get("fill_light_ratio", 0.3)

        parts.append(
            f"Lighting: {light_mode}, key light from {key_dir}, "
            f"fill ratio {fill_ratio:.1f}."
        )

        # 色板
        main_color = vd.get("main_color_hex", "")
        aux_color = vd.get("aux_color_hex", "")
        accent_color = vd.get("accent_color_hex", "")

        color_parts = []
        if main_color:
            color_parts.append(f"primary {main_color} at {vd.get('main_color_area_ratio', 0.5):.0%}")
        if aux_color:
            color_parts.append(f"secondary {aux_color} at {vd.get('aux_color_area_ratio', 0.3):.0%}")
        if accent_color:
            color_parts.append(f"accent {accent_color} at {vd.get('accent_color_area_ratio', 0.2):.0%}")

        if color_parts:
            parts.append("Color palette: " + ", ".join(color_parts) + ".")

        # 分层
        dof = vd.get("depth_of_field", "Medium")
        blur = vd.get("background_blur_strength", 0.0)
        parts.append(f"Depth of field: {dof}, background blur {blur:.1f}.")

        # 全局约束
        parts.append(
            f"Global constraints: base white balance {gc.base_temperature_k}K, "
            f"contrast deviation ≤{gc.max_contrast_offset}, "
            f"saturation deviation ≤{gc.max_saturation_offset}."
        )

        # 文字排版 (如果是TextCopyBlock)
        tp = fingerprint.text_params
        if tp:
            parts.append(
                f"Typography: {tp.get('font_family', 'sans-serif')} "
                f"{tp.get('font_weight', 400)}, "
                f"{tp.get('font_size', 14)}px, "
                f"line height {tp.get('line_height', 1.5)}, "
                f"color {tp.get('text_color_hex', '#333333')}, "
                f"alignment {tp.get('alignment', 'left')}."
            )

        return " ".join(parts)

    def generate_negative_prompt(
        self, fingerprint: Optional[ModuleACRFingerprint] = None
    ) -> str:
        """
        生成 Negative Prompt — 反向约束防止风格漂移。

        如果提供 fingerprint，会针对性约束该模块的关键参数。
        """
        neg_parts = [
            # 直方图/曝光
            "histogram offset", "highlight blowout", "dead black shadow",
            "overexposed whites", "underexposed blacks",
            "clipped shadows", "clipped highlights",

            # RGB通道
            "RGB channel color skew", "chromatic aberration",
            "color fringing", "channel misalignment",

            # 白平衡
            "inconsistent white balance among modules",
            "color cast", "yellow tint", "blue tint",
            "green tint", "magenta tint",

            # 曝光/对比/饱和
            "random exposure value", "exposure drift",
            "mismatched contrast", "mismatched saturation",
            "oversaturated", "desaturated",
            "excessive contrast", "flat contrast",

            # 光照
            "disordered light source direction",
            "multiple conflicting shadows",
            "harsh lighting", "flat lighting",

            # 风格
            "fragmented page style", "style inconsistency",
            "tone curve distortion", "gamma shift",

            # 画面
            "extra clipping area", "cropped subject",
            "missing content", "watermark", "logo",

            # 文字 (如果适用)
            "out-of-spec font", "wrong text color",
            "messy typesetting spacing",
            "inconsistent font size", "wrong alignment",

            # 通用质量
            "low resolution", "blurry", "noisy",
            "compression artifacts", "JPEG artifacts",
            "AI artifacts", "distorted proportions",
        ]

        # 如果提供了指纹，加入针对性约束
        if fingerprint:
            acr = fingerprint.acr_params

            # 色温锁定
            temp_k = acr.get("temperature_k", 5500)
            if temp_k < 4000:
                neg_parts.append("warm lighting")
            elif temp_k > 6500:
                neg_parts.append("warm yellow lighting")

            # 饱和度锁定
            sat = acr.get("saturation", 0)
            if sat > 0:
                neg_parts.append("desaturated")
            elif sat < 0:
                neg_parts.append("oversaturated")

            # 对比度锁定
            contrast = acr.get("contrast", 0)
            if contrast > 10:
                neg_parts.append("flat low-contrast")
            elif contrast < -10:
                neg_parts.append("high contrast")

        return ", ".join(neg_parts)

    def generate_global_prompt(
        self,
        library: StyleLibrary,
    ) -> PromptResult:
        """
        生成全局页面级 Positive + Negative Prompt。

        遍历所有模块指纹，合成统一的生成约束。
        """
        parts = []

        parts.append(
            "Generate a complete product detail page with consistent "
            f"visual style across all {library.total_modules} modules."
        )
        parts.append("The whole page follows a unified aesthetic system:")

        gc = library.global_constraint

        # 全局色温
        parts.append(
            f"Global white balance baseline: {gc.base_temperature_k}K."
        )

        # 全局容差
        parts.append(
            f"Between any two modules, contrast deviation must not exceed "
            f"{gc.max_contrast_offset}, saturation deviation must not exceed "
            f"{gc.max_saturation_offset}, exposure deviation within "
            f"{gc.max_exposure_offset} EV."
        )

        # 全局 Gamma
        parts.append(f"Global gamma: {gc.gamma_value}.")

        # 禁止项
        if gc.no_independent_color_cast:
            parts.append(
                "No independent color cast of single block — "
                "every module must use the unified white balance."
            )
        if gc.no_exposure_drift:
            parts.append("No independent exposure drift per module.")

        # 统一字体 (如果有)
        if gc.unified_font_system:
            parts.append(
                f"All text areas adopt unified brand font system: "
                f"{gc.unified_font_system}."
            )

        # 整合各模块的特定约束
        module_descs = []
        for fp in library.module_library:
            desc = (
                f"{fp.module_id} ({fp.module_type}): "
                f"ACR contrast={fp.acr_params.get('contrast', 0)}, "
                f"saturation={fp.acr_params.get('saturation', 0)}, "
                f"exposure={fp.acr_params.get('exposure', 0)}, "
                f"temp={fp.acr_params.get('temperature_k', 5500)}K"
            )
            module_descs.append(desc)

        if module_descs:
            parts.append("Per-module ACR baselines: " + "; ".join(module_descs) + ".")

        global_positive = " ".join(parts)
        global_negative = self.generate_negative_prompt()

        return PromptResult(
            positive_prompt=global_positive,
            negative_prompt=global_negative,
            global_positive=global_positive,
            global_negative=global_negative,
        )

    def generate_module_prompt(
        self, fingerprint: ModuleACRFingerprint
    ) -> PromptResult:
        """为单个模块生成 Positive + Negative Prompt"""
        positive = self.generate_positive_prompt(fingerprint)
        negative = self.generate_negative_prompt(fingerprint)
        return PromptResult(
            module_id=fingerprint.module_id,
            positive_prompt=positive,
            negative_prompt=negative,
        )

    def generate_all_module_prompts(
        self, library: StyleLibrary
    ) -> Tuple[PromptResult, List[PromptResult]]:
        """
        生成所有模块的 prompt: 全局 + 各模块。

        Returns:
            (global_prompt, [module_prompt_1, module_prompt_2, ...])
        """
        global_prompt = self.generate_global_prompt(library)
        module_prompts = [
            self.generate_module_prompt(fp)
            for fp in library.module_library
        ]
        return (global_prompt, module_prompts)


# ═══════════════════════════════════════════════════════════════
# Style Library Manager
# ═══════════════════════════════════════════════════════════════

class StyleLibraryManager:
    """
    风格库管理器 — 创建、更新、查询、版本管理
    """

    def __init__(self, storage_dir: str = "./style_library"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_library(
        self,
        page_benchmark_id: str,
        url: str = "",
        brand: str = "",
        global_constraint: Optional[GlobalConstraint] = None,
    ) -> StyleLibrary:
        """创建新的风格库"""
        return StyleLibrary(
            page_benchmark_id=page_benchmark_id,
            url=url,
            brand=brand,
            global_constraint=global_constraint or GlobalConstraint(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    def add_module_fingerprint(
        self,
        library: StyleLibrary,
        analysis: ModuleACRAnalysis,
    ) -> ModuleACRFingerprint:
        """
        添加/更新模块指纹到风格库。

        如果 module_id 已存在 → 更新并版本号+1
        如果 module_id 不存在 → 新增
        """
        fingerprint = ModuleACRFingerprint.from_analysis(analysis)

        # 查找是否已存在
        existing_idx = None
        for i, fp in enumerate(library.module_library):
            if fp.module_id == fingerprint.module_id:
                existing_idx = i
                break

        if existing_idx is not None:
            # 更新
            old = library.module_library[existing_idx]
            fingerprint.deviation_history = old.deviation_history + [0.0]
            # 版本号递增
            ver_match = re.match(r"V(\d+)\.(\d+)", old.version)
            if ver_match:
                major, minor = int(ver_match.group(1)), int(ver_match.group(2))
                fingerprint.version = f"V{major}.{minor + 1}"
            library.module_library[existing_idx] = fingerprint
        else:
            library.module_library.append(fingerprint)

        library.total_modules = len(library.module_library)
        library.updated_at = datetime.now().isoformat()
        return fingerprint

    def get_fingerprint(
        self, library: StyleLibrary, module_id: str
    ) -> Optional[ModuleACRFingerprint]:
        """按 ModuleID 查询指纹"""
        for fp in library.module_library:
            if fp.module_id == module_id:
                return fp
        return None

    def get_module_ids_by_type(
        self, library: StyleLibrary, module_type: str
    ) -> List[str]:
        """按模块类型获取 ModuleID 列表"""
        return [
            fp.module_id for fp in library.module_library
            if fp.module_type == module_type
        ]

    def save_library(self, library: StyleLibrary, version_tag: str = "") -> str:
        """
        保存风格库到文件 (带版本归档)。

        Args:
            library: 风格库对象
            version_tag: 版本标签 (留空则使用 library.version)

        Returns:
            保存文件路径
        """
        tag = version_tag or library.version
        filename = f"{library.page_benchmark_id}_{tag}.json"
        filepath = self.storage_dir / filename
        library.save(str(filepath))
        return str(filepath)

    def load_library(self, filepath: str) -> StyleLibrary:
        """从文件加载风格库"""
        return StyleLibrary.load(filepath)

    def list_libraries(self) -> List[Dict[str, str]]:
        """列出所有已保存的风格库文件"""
        files = []
        for f in self.storage_dir.glob("*.json"):
            files.append({
                "filename": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        return sorted(files, key=lambda x: x["modified"], reverse=True)

    def export_module_acr_templates(
        self, library: StyleLibrary
    ) -> Dict[str, Dict[str, Any]]:
        """
        导出所有模块的ACR参数模板 (可直接用于图像生成工具)。
        返回 {module_id: {acr_params, visual_dna, ...}}
        """
        templates = {}
        for fp in library.module_library:
            templates[fp.module_id] = {
                "module_type": fp.module_type,
                "acr_params": fp.acr_params,
                "visual_dna": fp.visual_dna,
                "histogram": fp.histogram,
                "text_params": fp.text_params,
                "version": fp.version,
            }
        return templates


# ═══════════════════════════════════════════════════════════════
# 单函数快速入口
# ═══════════════════════════════════════════════════════════════

def create_style_library(
    benchmark_id: str,
    url: str = "",
    brand: str = "",
) -> Tuple[StyleLibrary, StyleLibraryManager]:
    """快速创建风格库"""
    manager = StyleLibraryManager()
    library = manager.create_library(
        page_benchmark_id=benchmark_id,
        url=url,
        brand=brand,
    )
    return (library, manager)


def generate_prompts_for_library(
    library: StyleLibrary,
) -> Tuple[PromptResult, List[PromptResult]]:
    """为风格库中所有模块生成prompts"""
    generator = PromptGenerator(library.global_constraint)
    return generator.generate_all_module_prompts(library)
