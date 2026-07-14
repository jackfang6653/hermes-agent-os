"""
品牌DNA完整参数化Schema — 三大维度纯量化设计参数系统

基于 zanwei/design-dna (366行schema) 和 imehr/brand-extractor-plugin 社区最佳实践，
构建完整的三维品牌DNA参数体系：

维度1: design_system  — 设计系统层 (W3C DTCG 2025.10 兼容)
维度2: design_style   — 风格与美学层
维度3: visual_effects — 视觉特效与沉浸层

每个字段包含: type, description, allowed_values, extraction_method, confidence
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple, Union
from enum import Enum
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════════
# 基础类型定义
# ═══════════════════════════════════════════════════════════════

class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_HIGH = "very_high"   # >= 0.95
    HIGH = "high"             # >= 0.85
    MEDIUM = "medium"         # >= 0.70
    LOW = "low"               # >= 0.50
    SPECULATIVE = "speculative"  # < 0.50

class ExtractionMethod(Enum):
    """提取方法"""
    COMPUTER_VISION = "computer_vision"
    CSS_PARSING = "css_parsing"
    DOM_ANALYSIS = "dom_analysis"
    HEURISTIC = "heuristic"
    ML_CLASSIFIER = "ml_classifier"
    LLM_INFERENCE = "llm_inference"
    STATISTICAL = "statistical"
    EXIF_READING = "exif_reading"
    MANUAL_OVERRIDE = "manual_override"
    HYBRID = "hybrid"

@dataclass
class DNAField:
    """DNA Schema中的单个字段定义"""
    name: str
    type: str                                              # color|number|string|enum|range|array|object
    description: str
    allowed_values: Optional[List[Any]] = None
    default_value: Any = None
    extraction_method: ExtractionMethod = ExtractionMethod.HEURISTIC
    confidence: float = 0.0
    required: bool = False
    unit: Optional[str] = None                              # px|em|rem|%|deg|ms|ratio
    dtcg_path: Optional[str] = None                         # W3C DTCG path e.g. "color.background.primary"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "allowed_values": self.allowed_values,
            "default_value": self.default_value,
            "extraction_method": self.extraction_method.value,
            "confidence": self.confidence,
            "required": self.required,
            "unit": self.unit,
            "dtcg_path": self.dtcg_path,
        }

# ═══════════════════════════════════════════════════════════════
# 维度1: DESIGN SYSTEM — 设计系统层
# ═══════════════════════════════════════════════════════════════

@dataclass
class ColorDNA:
    """色彩系统DNA"""
    # Primary
    primary: str = ""                                       # hex 主色
    primary_variant: str = ""                               # hex 主色变体
    primary_contrast: str = ""                              # hex 主色上的文字色

    # Secondary
    secondary: str = ""
    secondary_variant: str = ""
    secondary_contrast: str = ""

    # Accent
    accent: str = ""
    accent_variant: str = ""
    accent_contrast: str = ""

    # Neutral
    neutral_50: str = ""                                    # 最浅
    neutral_100: str = ""
    neutral_200: str = ""
    neutral_300: str = ""
    neutral_400: str = ""
    neutral_500: str = ""
    neutral_600: str = ""
    neutral_700: str = ""
    neutral_800: str = ""
    neutral_900: str = ""                                   # 最深

    # Semantic
    success: str = ""
    warning: str = ""
    error: str = ""
    info: str = ""

    # Surface
    surface_primary: str = ""
    surface_secondary: str = ""
    surface_tertiary: str = ""
    surface_inverse: str = ""

    # Contrast ratios (WCAG)
    contrast_body_text: float = 0.0                         # WCAG AA >= 4.5
    contrast_large_text: float = 0.0                        # WCAG AA >= 3.0
    contrast_ui_components: float = 0.0                     # WCAG AA >= 3.0

    # Color system metadata
    harmony_type: str = ""                                  # monochromatic|complementary|analogous|triadic|split_complementary
    temperature: str = ""                                   # warm|cool|neutral
    saturation_level: str = ""                              # high|medium|low|desaturated
    total_swatches: int = 0
    confidence: float = 0.0

    # Schema definition
    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "primary": DNAField("primary", "color", "主导品牌色，用于主要CTA、导航、关键元素",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=True,
            dtcg_path="color.brand.primary"),
        "secondary": DNAField("secondary", "color", "辅助品牌色，用于次要元素、悬停状态",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=True,
            dtcg_path="color.brand.secondary"),
        "accent": DNAField("accent", "color", "强调色，用于高亮、促销标签",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=False,
            dtcg_path="color.brand.accent"),
        "neutral_500": DNAField("neutral_500", "color", "中性基准色，用于正文文字",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=True,
            dtcg_path="color.text.primary"),
        "success": DNAField("success", "color", "成功/正向语义色",
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False,
            dtcg_path="color.semantic.success"),
        "error": DNAField("error", "color", "错误/危险语义色",
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False,
            dtcg_path="color.semantic.error"),
    })

@dataclass
class TypographyDNA:
    """字体系统DNA — 7级排版阶梯"""
    # Type scale (7 levels)
    scale_h1: float = 0.0                                   # px
    scale_h2: float = 0.0
    scale_h3: float = 0.0
    scale_h4: float = 0.0
    scale_h5: float = 0.0
    scale_h6: float = 0.0
    scale_body: float = 0.0                                 # body/paragraph
    scale_caption: float = 0.0                              # caption/small

    # Type scale ratio
    type_scale_ratio: float = 0.0                           # 1.25(major third)|1.333(perfect fourth)|1.5|1.618(golden)

    # Font families
    heading_font: str = ""
    body_font: str = ""
    mono_font: str = ""
    fallback_stack: str = ""

    # Font weights used
    font_weights: List[int] = field(default_factory=list)   # [400, 500, 700]

    # Line heights
    heading_line_height: float = 0.0                        # multiplier
    body_line_height: float = 0.0
    caption_line_height: float = 0.0

    # Letter spacing
    heading_letter_spacing: float = 0.0                     # em
    body_letter_spacing: float = 0.0
    caption_letter_spacing: float = 0.0

    # Base
    base_font_size: int = 16                                # px (1rem)
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "heading_font": DNAField("heading_font", "string", "标题字体族",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=True,
            dtcg_path="typography.fontFamily.heading"),
        "body_font": DNAField("body_font", "string", "正文字体族",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=True,
            dtcg_path="typography.fontFamily.body"),
        "scale_h1": DNAField("scale_h1", "number", "H1字号(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=True,
            unit="px", dtcg_path="typography.fontSize.h1"),
        "scale_body": DNAField("scale_body", "number", "正文字号(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=True,
            unit="px", dtcg_path="typography.fontSize.body"),
        "body_line_height": DNAField("body_line_height", "number", "正文行高(倍数)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=True,
            unit="ratio", dtcg_path="typography.lineHeight.body"),
        "type_scale_ratio": DNAField("type_scale_ratio", "number", "字体比例系数",
            allowed_values=[1.25, 1.333, 1.5, 1.618, 1.2, 1.067, 1.125],
            extraction_method=ExtractionMethod.STATISTICAL, confidence=0.80, required=False,
            dtcg_path="typography.scaleRatio"),
    })

@dataclass
class SpacingDNA:
    """间距系统DNA"""
    base_unit: int = 0                                      # px 基准间距单位
    scale: List[int] = field(default_factory=list)          # [4,8,12,16,24,32,48,64,96]
    density: str = ""                                       # compact|comfortable|spacious
    rhythm: str = ""                                        # strict|loose|baseline
    section_gap: int = 0                                    # px 节间距
    content_padding: int = 0                                # px 内容区内边距
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "base_unit": DNAField("base_unit", "number", "基准间距单位(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=True,
            unit="px", dtcg_path="spacing.base"),
        "scale": DNAField("scale", "array", "间距阶梯",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=True,
            dtcg_path="spacing.scale"),
        "density": DNAField("density", "enum", "密度感受",
            allowed_values=["compact", "comfortable", "spacious"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.75, required=False,
            dtcg_path="spacing.density"),
    })

@dataclass
class LayoutDNA:
    """布局系统DNA"""
    grid_type: str = ""                                     # single|two_col|three_col|hybrid|grid|masonry
    columns: int = 0
    gutter: int = 0                                         # px
    content_max_width: int = 0                              # px
    margin_horizontal: int = 0                              # px

    # Responsive breakpoints
    breakpoints: List[int] = field(default_factory=list)    # [768, 1024, 1440]

    # Reading pattern
    reading_pattern: str = ""                               # F_pattern|Z_pattern|longitudinal|radial
    mobile_layout: str = ""                                 # stacked|condensed|hamburger

    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "grid_type": DNAField("grid_type", "enum", "网格类型",
            allowed_values=["single", "two_col", "three_col", "hybrid", "grid", "masonry"],
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=True,
            dtcg_path="layout.grid.type"),
        "columns": DNAField("columns", "number", "列数",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.95, required=True,
            dtcg_path="layout.grid.columns"),
        "gutter": DNAField("gutter", "number", "列间距(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="px", dtcg_path="layout.grid.gutter"),
        "content_max_width": DNAField("content_max_width", "number", "内容最大宽度(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="px", dtcg_path="layout.container.maxWidth"),
        "breakpoints": DNAField("breakpoints", "array", "响应式断点(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=False,
            dtcg_path="layout.breakpoints"),
        "reading_pattern": DNAField("reading_pattern", "enum", "阅读模式",
            allowed_values=["F_pattern", "Z_pattern", "longitudinal", "radial"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.65, required=False,
            dtcg_path="layout.readingPattern"),
    })

@dataclass
class ShapeDNA:
    """形状/圆角系统DNA"""
    radius_none: int = 0                                    # px
    radius_sm: int = 0                                      # 小圆角
    radius_md: int = 0                                      # 中圆角
    radius_lg: int = 0                                      # 大圆角
    radius_full: int = 9999                                 # 全圆/胶囊
    usage: str = ""                                         # uniform|mixed|sharp
    divider_style: str = ""                                 # solid|dashed|none
    divider_width: int = 1                                  # px
    divider_color: str = ""
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "radius_md": DNAField("radius_md", "number", "默认圆角(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=True,
            unit="px", dtcg_path="shape.cornerRadius.default"),
        "radius_lg": DNAField("radius_lg", "number", "大圆角(卡片/模态框)(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="px", dtcg_path="shape.cornerRadius.large"),
        "radius_full": DNAField("radius_full", "number", "全圆角(胶囊/药丸)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=False,
            unit="px", dtcg_path="shape.cornerRadius.pill"),
        "usage": DNAField("usage", "enum", "圆角使用策略",
            allowed_values=["uniform", "mixed", "sharp"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False,
            dtcg_path="shape.cornerRadius.strategy"),
    })

@dataclass
class ElevationDNA:
    """阴影/高程系统DNA"""
    levels: List[Dict[str, Any]] = field(default_factory=list)  # [{level:0, shadow:"...", blur:0, spread:0, color:"..."}]
    level_count: int = 4                                    # 标准: 0(flat) ~ 4(modal)
    ambient_shadow: str = ""                                # 环境阴影(常驻)
    interactive_shadow: str = ""                            # 交互阴影(hover/active)
    modal_shadow: str = ""                                  # 模态阴影
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "level_count": DNAField("level_count", "number", "高程层级数",
            allowed_values=[3, 4, 5, 6],
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=False,
            dtcg_path="elevation.levels"),
    })

@dataclass
class IconographyDNA:
    """图标系统DNA"""
    style: str = ""                                         # outlined|filled|dual_tone|line|glyph
    weight: str = ""                                        # thin|light|regular|bold
    scale: float = 0.0                                      # 相对于字号的倍数
    library: str = ""                                       # Material|Feather|Phosphor|FontAwesome|custom
    size_primary: int = 24                                  # px 主图标尺寸
    size_secondary: int = 20                                # px 辅助图标尺寸
    stroke_width: float = 2.0                               # px
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "style": DNAField("style", "enum", "图标风格",
            allowed_values=["outlined", "filled", "dual_tone", "line", "glyph"],
            extraction_method=ExtractionMethod.ML_CLASSIFIER, confidence=0.75, required=False,
            dtcg_path="iconography.style"),
        "weight": DNAField("weight", "enum", "图标粗细",
            allowed_values=["thin", "light", "regular", "bold"],
            extraction_method=ExtractionMethod.COMPUTER_VISION, confidence=0.70, required=False,
            dtcg_path="iconography.weight"),
        "size_primary": DNAField("size_primary", "number", "主图标尺寸(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="px", dtcg_path="iconography.size.primary"),
    })

@dataclass
class MotionDNA:
    """动效系统DNA"""
    easing_standard: str = ""                               # cubic-bezier(...)
    easing_entrance: str = ""
    easing_exit: str = ""
    duration_fast: int = 0                                  # ms
    duration_normal: int = 0                                # ms
    duration_slow: int = 0                                  # ms
    patterns: List[str] = field(default_factory=list)       # ["fade","slide","scale","stagger"]
    reduced_motion_support: bool = False
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "easing_standard": DNAField("easing_standard", "string", "标准缓动曲线",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.85, required=False,
            dtcg_path="motion.easing.standard"),
        "duration_normal": DNAField("duration_normal", "number", "标准动效时长(ms)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="ms", dtcg_path="motion.duration.normal"),
        "patterns": DNAField("patterns", "array", "动效模式集合",
            allowed_values=["fade", "slide", "scale", "stagger", "parallax", "reveal", "morph"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False,
            dtcg_path="motion.patterns"),
    })

@dataclass
class ComponentDNA:
    """组件系统DNA — 关键组件的原子参数"""
    # Button
    button_height: int = 0                                  # px
    button_padding_h: int = 0                               # px 水平内边距
    button_radius: int = 0                                  # px
    button_font_weight: int = 0
    button_text_transform: str = ""                         # none|uppercase|lowercase
    button_full_width_mobile: bool = False

    # Input
    input_height: int = 0                                   # px
    input_radius: int = 0
    input_border_width: int = 1
    input_border_color: str = ""
    input_focus_ring_color: str = ""
    input_placeholder_color: str = ""

    # Card
    card_radius: int = 0
    card_padding: int = 0
    card_shadow: str = ""
    card_hover_elevation: int = 0

    # Nav
    nav_height: int = 0                                     # px
    nav_background: str = ""
    nav_position: str = ""                                  # fixed|sticky|static
    nav_shadow: str = ""                                    # scroll state

    # Modal
    modal_radius: int = 0
    modal_padding: int = 0
    modal_backdrop_color: str = ""
    modal_max_width: int = 0

    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "button_height": DNAField("button_height", "number", "按钮高度(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=False,
            unit="px", dtcg_path="component.button.height"),
        "card_radius": DNAField("card_radius", "number", "卡片圆角(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="px", dtcg_path="component.card.borderRadius"),
        "nav_height": DNAField("nav_height", "number", "导航栏高度(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=False,
            unit="px", dtcg_path="component.nav.height"),
        "input_height": DNAField("input_height", "number", "输入框高度(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=False,
            unit="px", dtcg_path="component.input.height"),
    })


# ═══════════════════════════════════════════════════════════════
# 维度1 聚合: DesignSystemDNA
# ═══════════════════════════════════════════════════════════════

@dataclass
class DesignSystemDNA:
    """设计系统DNA — 完整聚合体 (W3C DTCG 2025.10 兼容)"""
    color: ColorDNA = field(default_factory=ColorDNA)
    typography: TypographyDNA = field(default_factory=TypographyDNA)
    spacing: SpacingDNA = field(default_factory=SpacingDNA)
    layout: LayoutDNA = field(default_factory=LayoutDNA)
    shape: ShapeDNA = field(default_factory=ShapeDNA)
    elevation: ElevationDNA = field(default_factory=ElevationDNA)
    iconography: IconographyDNA = field(default_factory=IconographyDNA)
    motion: MotionDNA = field(default_factory=MotionDNA)
    components: ComponentDNA = field(default_factory=ComponentDNA)

    confidence: float = 0.0
    extraction_version: str = "2.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dtcg_tokens(self) -> Dict[str, Any]:
        """导出为 W3C DTCG 2025.10 设计令牌格式"""
        tokens = {}
        for category_name, category_dna in [
            ("color", self.color),
            ("typography", self.typography),
            ("spacing", self.spacing),
            ("layout", self.layout),
            ("shape", self.shape),
            ("elevation", self.elevation),
            ("iconography", self.iconography),
            ("motion", self.motion),
            ("component", self.components),
        ]:
            cat_dict = asdict(category_dna)
            for key, value in cat_dict.items():
                if key.startswith("_") or key == "SCHEMA":
                    continue
                if value and not isinstance(value, (list, dict)):
                    schema_field = getattr(category_dna, "SCHEMA", {}).get(key)
                    dtcg_path = schema_field.dtcg_path if schema_field else None
                    if dtcg_path:
                        tokens[dtcg_path] = {
                            "$value": value,
                            "$type": schema_field.type if schema_field else "string",
                        }
        return tokens


# ═══════════════════════════════════════════════════════════════
# 维度2: DESIGN STYLE — 设计风格与美学层
# ═══════════════════════════════════════════════════════════════

@dataclass
class AestheticDNA:
    """美学DNA"""
    mood: str = ""                                          # luxury|minimal|warm|industrial|natural|tech|playful|elegant
    mood_secondary: str = ""
    metaphor: str = ""                                      # 视觉隐喻 "美术馆"/"实验室"/"工作室"/"画廊"
    genre: str = ""                                         # modern_minimal|brutalist|scandinavian|japanese_zen|bauhaus|swiss
    brand_personality: str = ""                             # Aaker品牌个性五维度映射
    tone_of_voice: str = ""                                 # formal|casual|technical|poetic|direct
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "mood": DNAField("mood", "enum", "情感调性",
            allowed_values=["luxury", "minimal", "warm", "industrial", "natural", "tech", "playful", "elegant", "brutal", "zen", "vintage"],
            extraction_method=ExtractionMethod.LLM_INFERENCE, confidence=0.70, required=True),
        "metaphor": DNAField("metaphor", "string", "设计隐喻",
            allowed_values=["美术馆", "实验室", "工作室", "画廊", "工厂", "自然", "宇宙", "舞台"],
            extraction_method=ExtractionMethod.LLM_INFERENCE, confidence=0.60, required=False),
        "genre": DNAField("genre", "enum", "设计流派",
            allowed_values=["modern_minimal", "brutalist", "scandinavian", "japanese_zen", "bauhaus", "swiss", "postmodern", "contemporary"],
            extraction_method=ExtractionMethod.LLM_INFERENCE, confidence=0.65, required=True),
        "brand_personality": DNAField("brand_personality", "enum", "品牌个性(Aaker五维度)",
            allowed_values=["sincere", "exciting", "competent", "sophisticated", "rugged"],
            extraction_method=ExtractionMethod.LLM_INFERENCE, confidence=0.55, required=False),
    })

@dataclass
class VisualLanguageDNA:
    """视觉语言DNA"""
    complexity: str = ""                                    # minimal|moderate|complex|maximal
    ornamentation: str = ""                                 # none|subtle|moderate|rich
    whitespace_usage: str = ""                              # generous|balanced|tight
    data_density: str = ""                                  # low|medium|high
    texture_usage: str = ""                                 # none|subtle|prominent
    pattern_usage: str = ""                                 # none|geometric|organic|typographic
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "complexity": DNAField("complexity", "enum", "视觉复杂度",
            allowed_values=["minimal", "moderate", "complex", "maximal"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.75, required=True),
        "whitespace_usage": DNAField("whitespace_usage", "enum", "留白策略",
            allowed_values=["generous", "balanced", "tight"],
            extraction_method=ExtractionMethod.STATISTICAL, confidence=0.80, required=True),
        "data_density": DNAField("data_density", "enum", "信息密度",
            allowed_values=["low", "medium", "high"],
            extraction_method=ExtractionMethod.STATISTICAL, confidence=0.80, required=False),
    })

@dataclass
class CompositionDNA:
    """构图DNA"""
    hierarchy_type: str = ""                                # size_based|color_based|spatial|contrast|mixed
    visual_balance: str = ""                                # symmetrical|asymmetrical|radial
    focal_point_count: int = 0
    flow_direction: str = ""                                # top_down|left_right|center_out|zigzag
    grouping_strategy: str = ""                             # proximity|similarity|enclosure|connection
    golden_ratio_usage: bool = False
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "hierarchy_type": DNAField("hierarchy_type", "enum", "层级构建方式",
            allowed_values=["size_based", "color_based", "spatial", "contrast", "mixed"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=True),
        "visual_balance": DNAField("visual_balance", "enum", "视觉平衡",
            allowed_values=["symmetrical", "asymmetrical", "radial"],
            extraction_method=ExtractionMethod.COMPUTER_VISION, confidence=0.75, required=False),
        "flow_direction": DNAField("flow_direction", "enum", "视觉流向",
            allowed_values=["top_down", "left_right", "center_out", "zigzag"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.65, required=False),
    })

@dataclass
class ImageryDNA:
    """图像/摄影DNA"""
    photo_style: str = ""                                   # editorial|lifestyle|studio|catalog|documentary
    illustration_style: str = ""                            # none|flat|isometric|3d|hand_drawn|abstract
    photo_ratio: float = 0.0                                # 实拍照片占比
    illustration_ratio: float = 0.0                         # 插画占比
    cgi_ratio: float = 0.0                                  # CGI渲染占比
    dominant_perspective: str = ""                          # eye_level|high_angle|low_angle|birdseye|dutch
    human_presence: str = ""                                # none|partial|full|model
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "photo_style": DNAField("photo_style", "enum", "摄影风格",
            allowed_values=["editorial", "lifestyle", "studio", "catalog", "documentary"],
            extraction_method=ExtractionMethod.ML_CLASSIFIER, confidence=0.75, required=True),
        "human_presence": DNAField("human_presence", "enum", "人物存在",
            allowed_values=["none", "partial", "full", "model"],
            extraction_method=ExtractionMethod.COMPUTER_VISION, confidence=0.85, required=False),
        "cgi_ratio": DNAField("cgi_ratio", "number", "CGI占比",
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.60, required=False,
            unit="ratio"),
    })

@dataclass
class InteractionDNA:
    """交互设计DNA"""
    feedback_style: str = ""                                # subtle|explicit|animated|micro_interaction
    hover_scale: float = 1.0                                # 悬停缩放倍数
    hover_brightness: float = 0.0                           # 亮度变化
    transition_duration: int = 0                            # ms
    transition_easing: str = ""
    click_depth: str = ""                                   # flat|subtle_shadow|deep_press
    page_transitions: str = ""                              # none|fade|slide|morph
    scroll_behavior: str = ""                               # smooth|stepped|parallax|sticky
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "feedback_style": DNAField("feedback_style", "enum", "反馈风格",
            allowed_values=["subtle", "explicit", "animated", "micro_interaction"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False),
        "scroll_behavior": DNAField("scroll_behavior", "enum", "滚动行为",
            allowed_values=["smooth", "stepped", "parallax", "sticky"],
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.85, required=False),
        "transition_duration": DNAField("transition_duration", "number", "过渡时长(ms)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False,
            unit="ms"),
    })


# ═══════════════════════════════════════════════════════════════
# 维度2 聚合: DesignStyleDNA
# ═══════════════════════════════════════════════════════════════

@dataclass
class DesignStyleDNA:
    """设计风格DNA — 完整聚合体"""
    aesthetic: AestheticDNA = field(default_factory=AestheticDNA)
    visual_language: VisualLanguageDNA = field(default_factory=VisualLanguageDNA)
    composition: CompositionDNA = field(default_factory=CompositionDNA)
    imagery: ImageryDNA = field(default_factory=ImageryDNA)
    interaction: InteractionDNA = field(default_factory=InteractionDNA)

    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ═══════════════════════════════════════════════════════════════
# 维度3: VISUAL EFFECTS — 视觉特效与沉浸层
# ═══════════════════════════════════════════════════════════════

@dataclass
class BackgroundEffectDNA:
    """背景特效DNA"""
    type: str = ""                                          # solid|gradient|image|video|particles|mesh|noise
    gradient_type: str = ""                                 # linear|radial|conic|mesh
    gradient_angle: float = 0.0                             # deg
    gradient_stops: List[Dict[str, str]] = field(default_factory=list)  # [{color, position}]
    noise_type: str = ""                                    # gaussian|perlin|voronoi|film_grain
    noise_intensity: float = 0.0                            # 0.0-1.0
    animation: str = ""                                     # static|slow_drift|parallax|pulse
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "type": DNAField("type", "enum", "背景类型",
            allowed_values=["solid", "gradient", "image", "video", "particles", "mesh", "noise"],
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False),
    })

@dataclass
class ParticleEffectDNA:
    """粒子特效DNA"""
    enabled: bool = False
    particle_type: str = ""                                 # dots|dust|sparkle|snow|bokeh|fluid
    count: int = 0
    speed: float = 0.0                                      # 1.0 = normal
    size_range: List[float] = field(default_factory=list)   # [min, max]
    opacity_range: List[float] = field(default_factory=list)  # [min, max]
    color_palette: List[str] = field(default_factory=list)
    interaction: str = ""                                   # none|mouse_follow|scroll_drive|hover_repel
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "enabled": DNAField("enabled", "boolean", "是否启用粒子",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=False),
        "particle_type": DNAField("particle_type", "enum", "粒子类型",
            allowed_values=["dots", "dust", "sparkle", "snow", "bokeh", "fluid"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.60, required=False),
    })

@dataclass
class ThreeDEffectDNA:
    """3D效果DNA"""
    enabled: bool = False
    type: str = ""                                          # model|spline|webgl_scene|three_js
    interaction_mode: str = ""                              # orbit|scroll_drive|auto_rotate|idle
    lighting_model: str = ""                                # PBR|phong|lambert|toon
    camera_preset: str = ""                                 # product_spin|hero_angle|overview
    depth_of_field: bool = False
    post_processing: List[str] = field(default_factory=list)  # bloom|vignette|tone_mapping
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "enabled": DNAField("enabled", "boolean", "是否启用3D",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=False),
        "type": DNAField("type", "enum", "3D类型",
            allowed_values=["model", "spline", "webgl_scene", "three_js"],
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.80, required=False),
    })

@dataclass
class ShaderEffectDNA:
    """Shader效果DNA"""
    enabled: bool = False
    shader_type: str = ""                                   # gradient|noise|distortion|caustics|marble|waves
    uniforms: Dict[str, Any] = field(default_factory=dict)
    performance_mode: str = ""                              # high|balanced|low
    fallback: str = ""                                      # static_color|css_fallback
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "enabled": DNAField("enabled", "boolean", "是否启用Shader",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.85, required=False),
        "shader_type": DNAField("shader_type", "enum", "Shader类型",
            allowed_values=["gradient", "noise", "distortion", "caustics", "marble", "waves", "glass", "liquid"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.55, required=False),
    })

@dataclass
class ScrollEffectDNA:
    """滚动特效DNA"""
    parallax_depth: float = 0.0                             # 视差深度 0.0-1.0
    parallax_layers: int = 0                                # 视差层数
    sticky_sections: int = 0                                # 吸顶区域数
    reveal_animation: str = ""                              # fade|slide|scale|clip_path
    scroll_snap: str = ""                                   # none|mandatory|proximity
    scroll_triggered_animation: bool = False
    horizontal_scroll_sections: int = 0
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "parallax_depth": DNAField("parallax_depth", "number", "视差深度",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.80, required=False,
            unit="ratio"),
        "scroll_snap": DNAField("scroll_snap", "enum", "滚动捕捉",
            allowed_values=["none", "mandatory", "proximity"],
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False),
        "reveal_animation": DNAField("reveal_animation", "enum", "揭示动画",
            allowed_values=["fade", "slide", "scale", "clip_path"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.65, required=False),
    })

@dataclass
class TextEffectDNA:
    """文字特效DNA"""
    gradient_text: bool = False
    gradient_colors: List[str] = field(default_factory=list)
    text_stroke: bool = False
    text_stroke_width: float = 0.0                          # px
    text_stroke_color: str = ""
    text_glow: bool = False
    glow_color: str = ""
    glow_radius: float = 0.0                                # px
    animation_type: str = ""                                # typewriter|morph|wave|rotate|scroll_reveal
    variable_font_axis: Dict[str, float] = field(default_factory=dict)  # wght, wdth, slnt, opsz
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "gradient_text": DNAField("gradient_text", "boolean", "渐变色文字",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.90, required=False),
        "animation_type": DNAField("animation_type", "enum", "文字动画类型",
            allowed_values=["typewriter", "morph", "wave", "rotate", "scroll_reveal", "glitch"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.65, required=False),
    })

@dataclass
class CursorEffectDNA:
    """光标特效DNA"""
    custom_cursor: bool = False
    cursor_style: str = ""                                  # dot|ring|magnetic|trail|glow|none
    cursor_size: int = 0                                    # px
    cursor_color: str = ""
    cursor_trail_length: int = 0                            # 拖尾数量
    magnetic_strength: float = 0.0                          # 磁吸强度
    hover_scale: float = 1.0                                # 元素悬停时光标缩放
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "custom_cursor": DNAField("custom_cursor", "boolean", "自定义光标",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=False),
        "cursor_style": DNAField("cursor_style", "enum", "光标风格",
            allowed_values=["dot", "ring", "magnetic", "trail", "glow", "none"],
            extraction_method=ExtractionMethod.HEURISTIC, confidence=0.70, required=False),
    })

@dataclass
class ImageEffectDNA:
    """图像特效DNA"""
    filter_preset: str = ""                                 # none|vintage|cinematic|moody|bright|faded
    grain_amount: float = 0.0                               # 0.0-1.0
    vignette_intensity: float = 0.0                         # 0.0-1.0
    color_overlay: str = ""
    overlay_opacity: float = 0.0
    duotone: bool = False
    duotone_highlight: str = ""
    duotone_shadow: str = ""
    lazy_loading: str = ""                                  # eager|lazy|blur_up
    lazy_placeholder: str = ""                              # blur|color|skeleton|none
    hover_zoom: bool = False
    hover_zoom_scale: float = 1.0
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "lazy_loading": DNAField("lazy_loading", "enum", "懒加载策略",
            allowed_values=["eager", "lazy", "blur_up"],
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=False),
        "duotone": DNAField("duotone", "boolean", "双色调处理",
            extraction_method=ExtractionMethod.COMPUTER_VISION, confidence=0.75, required=False),
        "hover_zoom": DNAField("hover_zoom", "boolean", "悬停缩放",
            extraction_method=ExtractionMethod.DOM_ANALYSIS, confidence=0.90, required=False),
    })

@dataclass
class GlassmorphismDNA:
    """玻璃态/毛玻璃DNA"""
    enabled: bool = False
    blur_amount: float = 0.0                                # px
    background_tint: str = ""
    background_opacity: float = 0.0                         # 0.0-1.0
    border_color: str = ""
    border_opacity: float = 0.0
    saturation_boost: float = 1.0                           # backdrop-filter saturate
    shadow: str = ""
    confidence: float = 0.0

    SCHEMA: Dict[str, DNAField] = field(default_factory=lambda: {
        "enabled": DNAField("enabled", "boolean", "是否使用玻璃态",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=False),
        "blur_amount": DNAField("blur_amount", "number", "模糊量(px)",
            extraction_method=ExtractionMethod.CSS_PARSING, confidence=0.95, required=False,
            unit="px"),
    })


# ═══════════════════════════════════════════════════════════════
# 维度3 聚合: VisualEffectsDNA
# ═══════════════════════════════════════════════════════════════

@dataclass
class VisualEffectsDNA:
    """视觉特效DNA — 完整聚合体"""
    overview: str = ""                                      # 特效总览描述
    background: BackgroundEffectDNA = field(default_factory=BackgroundEffectDNA)
    particles: ParticleEffectDNA = field(default_factory=ParticleEffectDNA)
    effect_3d: ThreeDEffectDNA = field(default_factory=ThreeDEffectDNA)
    shaders: ShaderEffectDNA = field(default_factory=ShaderEffectDNA)
    scroll: ScrollEffectDNA = field(default_factory=ScrollEffectDNA)
    text: TextEffectDNA = field(default_factory=TextEffectDNA)
    cursor: CursorEffectDNA = field(default_factory=CursorEffectDNA)
    image: ImageEffectDNA = field(default_factory=ImageEffectDNA)
    glassmorphism: GlassmorphismDNA = field(default_factory=GlassmorphismDNA)

    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ═══════════════════════════════════════════════════════════════
# 顶层: 完整品牌DNA
# ═══════════════════════════════════════════════════════════════

@dataclass
class BrandDNA:
    """完整品牌DNA — 三维聚合体"""
    # Identity
    brand_id: str = ""
    brand_name: str = ""
    category: str = ""                                      # 品牌品类
    sub_category: str = ""

    # Three dimensions
    design_system: DesignSystemDNA = field(default_factory=DesignSystemDNA)
    design_style: DesignStyleDNA = field(default_factory=DesignStyleDNA)
    visual_effects: VisualEffectsDNA = field(default_factory=VisualEffectsDNA)

    # Metadata
    source_url: str = ""
    source_page_count: int = 0
    extraction_date: str = field(default_factory=lambda: datetime.now().isoformat())
    extraction_version: str = "2.0.0"
    overall_confidence: float = 0.0

    # Quality gates
    gate_results: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dtcg_tokens(self) -> Dict[str, Any]:
        """导出完整的 W3C DTCG 2025.10 设计令牌"""
        return self.design_system.to_dtcg_tokens()

    @property
    def confidence_level(self) -> ConfidenceLevel:
        if self.overall_confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif self.overall_confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.overall_confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        elif self.overall_confidence >= 0.50:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.SPECULATIVE

    def validate(self) -> List[str]:
        """验证DNA完整性，返回缺失/低置信度字段列表"""
        issues = []
        # Check required design system fields
        for category, dna in [
            ("color", self.design_system.color),
            ("typography", self.design_system.typography),
            ("spacing", self.design_system.spacing),
            ("layout", self.design_system.layout),
        ]:
            for key, field in getattr(dna, "SCHEMA", {}).items():
                if field.required:
                    value = getattr(dna, key, None)
                    if value is None or (isinstance(value, (int, float)) and value == 0) or \
                       (isinstance(value, str) and not value):
                        issues.append(f"{category}.{key}: required, missing")
                    elif field.confidence < 0.50:
                        issues.append(f"{category}.{key}: low confidence ({field.confidence})")
        return issues


# ═══════════════════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════════════════

def create_empty_dna(brand_name: str = "", category: str = "") -> BrandDNA:
    """创建空的品牌DNA模板"""
    return BrandDNA(
        brand_name=brand_name,
        category=category,
    )

def dna_from_json(data: Dict[str, Any]) -> BrandDNA:
    """从JSON字典还原BrandDNA对象"""
    # This is a simplified factory; full deserialization would use a proper
    # recursive from-dict pattern. For now, reconstruct from the flat structure.
    dna = BrandDNA(
        brand_id=data.get("brand_id", ""),
        brand_name=data.get("brand_name", ""),
        category=data.get("category", ""),
        sub_category=data.get("sub_category", ""),
        source_url=data.get("source_url", ""),
        source_page_count=data.get("source_page_count", 0),
    )
    if "overall_confidence" in data:
        dna.overall_confidence = data["overall_confidence"]
    if "gate_results" in data:
        dna.gate_results = data["gate_results"]
    return dna

def dna_from_dtcg_tokens(tokens: Dict[str, Any], brand_name: str = "") -> BrandDNA:
    """从W3C DTCG令牌格式导入"""
    dna = BrandDNA(brand_name=brand_name)
    ds = dna.design_system

    for dtcg_path, token_data in tokens.items():
        value = token_data.get("$value")
        if value is None:
            continue

        parts = dtcg_path.split(".")
        if parts[0] == "color":
            if "primary" in dtcg_path:
                ds.color.primary = value
            elif "secondary" in dtcg_path:
                ds.color.secondary = value
        elif parts[0] == "typography":
            if "heading" in dtcg_path and "fontFamily" in dtcg_path:
                ds.typography.heading_font = value
            elif "body" in dtcg_path and "fontFamily" in dtcg_path:
                ds.typography.body_font = value
            elif "fontSize" in dtcg_path:
                if "h1" in dtcg_path:
                    ds.typography.scale_h1 = float(value)
                elif "body" in dtcg_path:
                    ds.typography.scale_body = float(value)

    return dna
