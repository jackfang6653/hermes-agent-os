"""
Hermes OS — 合并核心类型 (Unified Types)

来源: dna_engine/types, dna_engine/scene_graph, page_modules/acr_analyzer,
      research/brand_researcher, research/color_system, knowledge/brand_knowledge
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

# ═══════════════════════════════════════════════════════
# 1. PBR 材质
# ═══════════════════════════════════════════════════════

@dataclass
class PBRMaterial:
    id: str = ""
    name: str = ""
    type: str = "unknown"
    albedo: str = "#808080"
    roughness: float = 0.5
    metallic: float = 0.0
    normal_strength: float = 0.5
    subsurface: float = 0.0
    clearcoat: float = 0.0
    anisotropy: float = 0.0
    sheen: float = 0.0
    opacity: float = 1.0
    ior: float = 1.5
    transmission: float = 0.0
    displacement: float = 0.0

# ═══════════════════════════════════════════════════════
# 2. 灯光
# ═══════════════════════════════════════════════════════

@dataclass
class Light:
    id: str
    type: str = "area"
    shape: str = "rectangle"
    position_3d: Tuple[float, float, float] = (0, 0, 0)
    target: Optional[Tuple[float, float, float]] = None
    intensity: float = 1000
    color: str = "#ffffff"
    temperature: int = 5500
    exposure: float = 0.0
    size: Tuple[float, float] = (60, 90)
    modifier: Optional[str] = None
    diffusion: float = 1.0

# ═══════════════════════════════════════════════════════
# 3. 相机
# ═══════════════════════════════════════════════════════

@dataclass
class CameraSystem:
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    sensor_size: str = "full_frame"
    focal_length_mm: float = 85
    aperture_f: float = 2.8
    shutter_speed: str = "1/125"
    iso: int = 100
    position_3d: Tuple[float, float, float] = (0, 80, -400)
    distance_to_subject_cm: float = 400

# ═══════════════════════════════════════════════════════
# 4. 场景元素
# ═══════════════════════════════════════════════════════

@dataclass
class SceneElement:
    id: str
    type: str = "product"
    label: str = ""
    bbox_center: Tuple[float, float, float] = (0, 0, 0)
    bbox_size: Tuple[float, float, float] = (100, 100, 100)
    material: PBRMaterial = field(default_factory=PBRMaterial)
    distance_to_camera_cm: float = 0
    angle_to_camera_deg: float = 0
    relative_scale_to_frame: float = 0

@dataclass
class SceneGraph:
    scene_id: str = ""
    elements: List[SceneElement] = field(default_factory=list)
    camera: CameraSystem = field(default_factory=CameraSystem)
    lights: List[Light] = field(default_factory=list)
    background_color: str = "#f5f0e8"
    source_image_url: str = ""

# ═══════════════════════════════════════════════════════
# 5. ACR 直方图
# ═══════════════════════════════════════════════════════

@dataclass
class ACRParams:
    exposure: Optional[float] = None
    contrast: Optional[float] = None
    highlights: Optional[float] = None
    shadows: Optional[float] = None
    whites: Optional[float] = None
    blacks: Optional[float] = None
    texture: Optional[float] = None
    clarity: Optional[float] = None
    dehaze: Optional[float] = None
    vibrance: Optional[float] = None
    saturation: Optional[float] = None
    temperature_k: Optional[int] = None
    tint: Optional[float] = None

@dataclass
class HistogramInfo:
    luminance_bias: str = ""       # Shadow/Midtone/Highlight
    shadow_clipping: bool = False
    highlight_clipping: bool = False
    gamma: float = 2.2
    rgb_peak_offset: Dict[str, float] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════
# 6. 品牌设计分析
# ═══════════════════════════════════════════════════════

@dataclass
class DesignRationale:
    layout_purpose: str = ""
    psychological_effect: str = ""
    target_audience: str = ""
    brand_positioning: str = ""
    design_principles: List[str] = field(default_factory=list)

@dataclass
class BrandDesignReport:
    brand_name: str = ""
    layout_analysis: str = ""
    design_rationale: DesignRationale = field(default_factory=DesignRationale)
    primary_palette: List[str] = field(default_factory=list)
    secondary_palette: List[str] = field(default_factory=list)
    color_psychology: str = ""
    typography: Dict[str, Any] = field(default_factory=dict)
    scene_composition: str = ""
    tools_detected: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════
# 7. 品牌档案
# ═══════════════════════════════════════════════════════

@dataclass
class BrandProfile:
    brand_name: str
    category: str = ""
    brand_positioning: str = ""
    target_audience: str = ""
    primary_palette: List[str] = field(default_factory=list)
    accent_palette: List[str] = field(default_factory=list)
    color_psychology: str = ""
    layout_patterns: List[str] = field(default_factory=list)
    lighting_signature: str = ""
    research_count: int = 0
    confidence: float = 0.0

# ═══════════════════════════════════════════════════════
# 8. 质量门禁
# ═══════════════════════════════════════════════════════

@dataclass
class QualityGateResult:
    gate_name: str
    passed: bool = False
    score: float = 0.0
    threshold: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════
# 9. 模型健康
# ═══════════════════════════════════════════════════════

@dataclass
class ModelHealth:
    name: str
    provider: str
    status: str = "unknown"
    latency_ms: float = 0
    error_count: int = 0
    success_count: int = 0
    last_error: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

# ═══════════════════════════════════════════════════════
# 10. 4A案例
# ═══════════════════════════════════════════════════════

@dataclass
class AgencyCase:
    agency: str = ""
    brand: str = ""
    project_name: str = ""
    design_rationale: str = ""
    strategic_thinking: str = ""
    consumer_insight: str = ""
    differentiation: str = ""
    color_palette: List[str] = field(default_factory=list)
    layout_patterns: List[str] = field(default_factory=list)
    extracted_at: str = ""
    confidence: float = 0.0
