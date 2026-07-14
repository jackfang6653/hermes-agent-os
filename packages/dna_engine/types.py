"""
品牌DNA逆向工程 — 核心类型定义
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# ── 相机参数 ───────────────────────────────────────────

@dataclass
class CameraInference:
    """从图像反推的相机参数"""
    focal_length_mm: Optional[float] = None      # 35mm等效焦距
    aperture_f: Optional[float] = None            # 光圈 f/x.x
    shutter_speed: Optional[str] = None           # 快门速度 "1/125"
    iso: Optional[int] = None                     # ISO
    camera_model: Optional[str] = None            # 推测机身型号
    lens_model: Optional[str] = None              # 推测镜头型号
    has_exif: bool = False                        # 是否有EXIF数据
    confidence: float = 0.0                       # 置信度 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class LightingInference:
    """灯光分析结果"""
    light_count: Optional[int] = None             # 灯光数量
    light_types: List[str] = field(default_factory=list)  # softbox/umbrella/beauty dish/ring...
    key_light_position: Optional[str] = None      # 主光位置 "45度左上"
    fill_light_ratio: Optional[float] = None      # 填充比
    backlight: bool = False                       # 是否有背光
    color_temperature_k: Optional[int] = None     # 色温
    light_modifiers: List[str] = field(default_factory=list) # 光效附件
    natural_light: bool = False                   # 是否自然光
    studio: bool = False                          # 是否影棚
    confidence: float = 0.0

@dataclass
class ColorGradingInference:
    """后期色彩分析"""
    color_temperature_shift: Optional[float] = None  # 色温偏移
    tint_shift: Optional[float] = None               # 色调偏移
    contrast: Optional[float] = None                  # 对比度 -1~1
    highlights: Optional[float] = None                # 高光
    shadows: Optional[float] = None                   # 阴影
    whites: Optional[float] = None                    # 白色
    blacks: Optional[float] = None                    # 黑色
    texture: Optional[float] = None                   # 纹理
    clarity: Optional[float] = None                   # 清晰度
    vibrance: Optional[float] = None                  # 自然饱和度
    saturation: Optional[float] = None                # 饱和度
    tone_curve: Optional[List[float]] = None          # 色调曲线点
    hsl_adjustments: Dict[str, Dict[str, float]] = field(default_factory=dict)  # HSL各通道调整
    color_grading_lut: Optional[str] = None           # 推测LUT
    dominant_color_tone: Optional[str] = None         # 主色调 "暖调/冷调/中性"
    confidence: float = 0.0

@dataclass
class CompositionAnalysis:
    """构图分析"""
    rule_of_thirds: bool = False
    golden_ratio: bool = False
    symmetry: bool = False
    leading_lines: bool = False
    negative_space: float = 0.0           # 留白比例
    product_position: str = "center"       # 产品位置
    aspect_ratio: str = "4:3"            # 宽高比
    crop_info: Optional[str] = None       # 裁剪信息

@dataclass
class SoftwareInference:
    """推断使用的软件工具"""
    renderer: Optional[str] = None        # Cycles/Octane/Redshift/V-Ray
    modeling_software: Optional[str] = None  # Blender/C4D/3DS Max
    post_software: Optional[str] = None   # Lightroom/Capture One/Photoshop
    is_cgi: bool = False                  # 是否CGI渲染
    confidence: float = 0.0

# ── 完整分析结果 ───────────────────────────────────────

@dataclass
class ImageAnalysisResult:
    """对一张产品图的完整逆向分析"""
    image_url: str
    camera: CameraInference = field(default_factory=CameraInference)
    lighting: LightingInference = field(default_factory=LightingInference)
    color_grading: ColorGradingInference = field(default_factory=ColorGradingInference)
    composition: CompositionAnalysis = field(default_factory=CompositionAnalysis)
    software: SoftwareInference = field(default_factory=SoftwareInference)
    materials_detected: List[str] = field(default_factory=list)
    style_keywords: List[str] = field(default_factory=list)
    brand_match: Optional[str] = None
    raw_analysis: str = ""

# ── 品牌DNA条目 ───────────────────────────────────────

@dataclass
class BrandDNAEntry:
    """品牌DNA的一个维度条目"""
    brand: str
    dimension: str                           # camera/lighting/color/composition/software/material
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source_url: str = ""
    embedding: Optional[List[float]] = None  # 向量嵌入
    created_at: str = ""
    updated_at: str = ""

@dataclass
class SceneReplaceRequest:
    """场景替换请求"""
    product_image_url: str
    target_scene: str                        # studio/living_room/outdoor/etc
    preserve_camera: bool = True             # 保持原相机参数
    preserve_lighting: bool = True           # 保持原灯光
    preserve_product_pose: bool = True       # 保持产品姿态
    output_style: Optional[str] = None       # 输出风格
