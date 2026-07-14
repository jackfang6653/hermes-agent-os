"""
场景图核心类型 — 完整参数化数字孪生

每个元素有唯一ID，包含完整参数：
- 3D包围盒（尺寸/结构/位置）
- PBR材质（albedo/roughness/metallic/normal/subsurface）
- 透视关系（相对相机距离/角度/相互比例）
- 灯光系统（每盏灯的类型/位置/强度/色温/衰减）
- 摄影参数（机身/镜头/焦距/光圈/ISO/快门）
- 后期参数（色温偏移/HSL/色调曲线/清晰度）
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# ═══════════════════════════════════════════════════════
# 1. PBR 材质系统
# ═══════════════════════════════════════════════════════

@dataclass
class PBRMaterial:
    """完整PBR材质参数 — 可直接输入渲染引擎"""
    id: str = ""
    name: str = ""
    type: str = "unknown"          # fabric/wood/metal/leather/stone/glass/plastic
    
    # PBR核心通道
    albedo: str = "#808080"        # 基础色 hex
    albedo_map: Optional[str] = None  # 纹理贴图URL
    roughness: float = 0.5         # 粗糙度 0-1
    roughness_map: Optional[str] = None
    metallic: float = 0.0          # 金属度 0-1
    metallic_map: Optional[str] = None
    normal_strength: float = 0.5   # 法线强度
    normal_map: Optional[str] = None
    
    # 高级PBR
    subsurface: float = 0.0        # 次表面散射 0-1
    subsurface_color: str = "#ffffff"
    clearcoat: float = 0.0         # 清漆层 0-1
    clearcoat_roughness: float = 0.0
    anisotropy: float = 0.0        # 各项异性 0-1
    sheen: float = 0.0             # 绒毛光泽 0-1
    sheen_tint: float = 0.5
    
    # 位移
    displacement: float = 0.0      # 置换强度
    displacement_map: Optional[str] = None
    
    # 透明度
    opacity: float = 1.0
    ior: float = 1.5               # 折射率
    transmission: float = 0.0      # 透射 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}

# ═══════════════════════════════════════════════════════
# 2. 灯光系统
# ═══════════════════════════════════════════════════════

@dataclass
class Light:
    """完整灯光参数 — 可直接输入渲染引擎"""
    id: str
    type: str = "area"             # area/point/spot/directional/hdri
    shape: str = "rectangle"       # rectangle/disc/sphere/tube
    
    # 位置与方向
    position_3d: Tuple[float, float, float] = (0, 0, 0)  # xyz
    rotation: Tuple[float, float, float] = (0, 0, 0)      # 欧拉角
    target: Optional[Tuple[float, float, float]] = None    # 目标点
    
    # 强度与颜色
    intensity: float = 1000        # 流明/瓦特
    color: str = "#ffffff"
    temperature: int = 5500        # 色温K
    exposure: float = 0.0          # 曝光补偿EV
    
    # 尺寸与衰减
    size: Tuple[float, float] = (60, 90)  # cm
    falloff_type: str = "inverse_square"
    distance_max: float = 1000     # 最大衰减距离cm
    
    # 光效附件
    modifier: Optional[str] = None # softbox/beauty_dish/umbrella/grid/barndoor
    grid_angle: Optional[float] = None  # 蜂巢角度
    diffusion: float = 1.0         # 柔光程度 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

# ═══════════════════════════════════════════════════════
# 3. 摄影系统
# ═══════════════════════════════════════════════════════

@dataclass
class CameraSystem:
    """完整摄影参数 — 可直接输入渲染相机"""
    # 机身
    camera_model: Optional[str] = None
    sensor_size: str = "full_frame"  # full_frame/aps_c/medium_format
    sensor_width_mm: float = 36
    sensor_height_mm: float = 24
    
    # 镜头
    lens_model: Optional[str] = None
    focal_length_mm: float = 85     # 35mm等效
    aperture_f: float = 2.8
    aperture_blades: int = 9        # 光圈叶片数（影响焦外形状）
    
    # 曝光
    shutter_speed: str = "1/125"
    iso: int = 100
    
    # 相机位置
    position_3d: Tuple[float, float, float] = (0, 80, -400)  # xyz cm
    target: Tuple[float, float, float] = (0, 0, 0)
    distance_to_subject_cm: float = 400
    
    # 光学
    focus_distance_cm: float = 400
    dof_style: str = "natural"      # natural/tilt_shift/macro
    lens_distortion: float = 0.0    # 镜头畸变 -1~1
    
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

# ═══════════════════════════════════════════════════════
# 4. 场景元素
# ═══════════════════════════════════════════════════════

@dataclass
class SceneElement:
    """场景中的单个元素 — 有完整参数化描述"""
    id: str                           # 唯一ID e.g. "product_01", "floor_01", "wall_01"
    type: str                         # product/floor/wall/prop/decoration/light_fixture
    label: str = ""                   # 人类可读标签
    
    # 3D包围盒 (厘米)
    bbox_center: Tuple[float, float, float] = (0, 0, 0)
    bbox_size: Tuple[float, float, float] = (100, 100, 100)  # w/h/d cm
    
    # 变换
    rotation: Tuple[float, float, float] = (0, 0, 0)  # 欧拉角
    scale: Tuple[float, float, float] = (1, 1, 1)
    
    # 材质
    material: PBRMaterial = field(default_factory=PBRMaterial)
    material_layers: List[PBRMaterial] = field(default_factory=list)  # 多层材质
    
    # 透视关系
    distance_to_camera_cm: float = 0
    angle_to_camera_deg: float = 0     # 相对相机角度
    relative_scale_to_frame: float = 0  # 占画面比例 0-1
    occlusion_relation: str = ""       # 遮挡关系 "in_front_of:wall_01"
    
    # 父子关系
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # 可见性与光照
    visible: bool = True
    shadow_casting: bool = True
    receives_lighting: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = {"id": self.id, "type": self.type, "label": self.label,
             "bbox_center": self.bbox_center, "bbox_size": self.bbox_size,
             "rotation": self.rotation, "scale": self.scale,
             "material": self.material.to_dict(),
             "distance_to_camera_cm": self.distance_to_camera_cm,
             "angle_to_camera_deg": self.angle_to_camera_deg,
             "relative_scale_to_frame": self.relative_scale_to_frame,
             "parent_id": self.parent_id, "visible": self.visible}
        if self.material_layers:
            d["material_layers"] = [m.to_dict() for m in self.material_layers]
        return d

# ═══════════════════════════════════════════════════════
# 5. 后期处理
# ═══════════════════════════════════════════════════════

@dataclass
class PostProcessing:
    """完整后期参数 — Lightroom/Capture One 完全可复刻"""
    # 基本
    exposure: float = 0.0
    contrast: float = 0
    highlights: float = 0
    shadows: float = 0
    whites: float = 0
    blacks: float = 0
    
    # 质感
    texture: float = 0
    clarity: float = 0
    dehaze: float = 0
    vibrance: float = 0
    saturation: float = 0
    
    # 色调
    color_temperature: float = 0     # -100~100
    tint: float = 0                  # -100~100
    
    # 色调曲线 (RGB各通道)
    tone_curve_rgb: List[Tuple[float, float]] = field(default_factory=lambda: [(0,0), (64,64), (128,128), (192,192), (255,255)])
    tone_curve_red: Optional[List[Tuple[float, float]]] = None
    tone_curve_green: Optional[List[Tuple[float, float]]] = None
    tone_curve_blue: Optional[List[Tuple[float, float]]] = None
    
    # HSL
    hsl_hue: Dict[str, int] = field(default_factory=dict)       # red/orange/yellow/green/...
    hsl_saturation: Dict[str, int] = field(default_factory=dict)
    hsl_luminance: Dict[str, int] = field(default_factory=dict)
    
    # 颜色分级
    shadow_tone: str = "#000000"
    midtone_tone: str = "#000000"
    highlight_tone: str = "#000000"
    shadow_balance: float = 0
    
    # 校准
    calibration: Dict[str, float] = field(default_factory=dict)
    
    # 锐化/降噪
    sharpening: float = 0
    sharpening_radius: float = 1.0
    noise_reduction: float = 0
    color_noise_reduction: float = 0
    
    # LUT
    lut_path: Optional[str] = None
    lut_strength: float = 1.0
    
    # 裁切
    crop_aspect: Optional[str] = None
    crop_rotation: float = 0
    vignette: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != 0
                and v != [(0,0),(64,64),(128,128),(192,192),(255,255)]}

# ═══════════════════════════════════════════════════════
# 6. 完整场景图
# ═══════════════════════════════════════════════════════

@dataclass
class SceneGraph:
    """完整场景图 — 产品摄影的数字孪生"""
    scene_id: str = ""
    scene_type: str = "product_photography"
    brand: str = ""
    
    # 核心组件
    elements: List[SceneElement] = field(default_factory=list)
    camera: CameraSystem = field(default_factory=CameraSystem)
    lights: List[Light] = field(default_factory=list)
    post_processing: PostProcessing = field(default_factory=PostProcessing)
    
    # 环境
    environment_hdri: Optional[str] = None  # HDR环境贴图
    environment_rotation: float = 0
    background_color: str = "#f5f0e8"
    
    # 元数据
    source_image_url: str = ""
    confidence: float = 0.0
    extracted_by: str = "dna_engine_v1"
    
    def get_element(self, eid: str) -> Optional[SceneElement]:
        for e in self.elements:
            if e.id == eid:
                return e
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_type": self.scene_type,
            "brand": self.brand,
            "elements": [e.to_dict() for e in self.elements],
            "camera": self.camera.to_dict(),
            "lights": [l.to_dict() for l in self.lights],
            "post_processing": self.post_processing.to_dict(),
            "environment_hdri": self.environment_hdri,
            "background_color": self.background_color,
            "source_image_url": self.source_image_url,
            "confidence": self.confidence,
        }
    
    def to_json(self, indent=2) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
