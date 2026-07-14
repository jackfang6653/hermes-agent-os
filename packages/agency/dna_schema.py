"""
Full Parametric DNA Schema — quantifies every atomic element of a brand product detail page

Covers: page module layout, typography, color system, image/lens/layering,
lighting, shadow, interaction/animation, grid/margin, and deep WHY tracing.
Output: strict JSON dict (no ambiguous description). Each parameter is numeric or label.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════════
# 1. PAGE MODULE LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class PageModule:
    """Atomic page module — fixed position, size, hierarchy"""
    id: str                               # e.g. "mod_01_hero"
    module_type: str                       # hero|gallery|info|desc|specs|reviews|cta|nav|footer
    name: str = ""
    
    # Absolute layout (px from viewport top-left)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    z_index: int = 0                      # visual stacking order
    
    # Box model (px)
    margin_top: int = 0
    margin_bottom: int = 0
    margin_left: int = 0
    margin_right: int = 0
    padding_top: int = 0
    padding_bottom: int = 0
    padding_left: int = 0
    padding_right: int = 0
    
    # Hierarchy
    visual_weight: float = 0.0            # 0.0-1.0 — how much visual attention this module gets
    hierarchy_level: int = 1              # 1=primary hero, 5=footer
    reading_order: int = 0                # visual flow sequence
    
    # Background
    bg_color: str = ""                    # hex
    bg_image: str = ""
    bg_gradient: str = ""
    
    # Border
    border_width: int = 0
    border_color: str = ""
    border_radius: int = 0

@dataclass
class PageLayout:
    """Full page grid and flow"""
    grid_type: str = ""                   # single|two_col|three_col|hybrid|grid
    columns: int = 0
    gutter: int = 0                       # px between columns
    content_max_width: int = 0            # px
    margin_auto: bool = False
    
    # Visual flow
    reading_pattern: str = ""             # F_pattern|Z_pattern|longitudinal|radial
    visual_hierarchy_count: int = 4       # distinct hierarchy levels
    
    # Responsive
    breakpoints: List[str] = field(default_factory=list)  # ["768px","1024px","1440px"]
    
    # White space
    section_gap: int = 0                  # px between major sections
    whitespace_ratio: float = 0.0         # 0.0-1.0 — proportion of empty space

# ═══════════════════════════════════════════════════════════════
# 2. TYPOGRAPHY LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class TextElement:
    """Single atomic text element"""
    id: str
    content: str = ""
    
    # Font
    font_family: str = ""                 # "PingFang SC, sans-serif"
    font_size: int = 0                    # px
    font_weight: int = 400                # 100-900
    font_style: str = "normal"            # normal|italic
    text_transform: str = "none"          # none|uppercase|lowercase|capitalize
    
    # Spacing
    line_height: float = 1.5             # multiplier
    letter_spacing: float = 0.0           # em
    paragraph_spacing: int = 0            # px
    word_spacing: float = 0.0             # em
    
    # Color
    color: str = ""                       # hex
    color_opacity: float = 1.0            # 0.0-1.0
    
    # Effect
    text_decoration: str = "none"         # none|underline|line-through
    text_shadow: str = ""                 # "2px 2px 4px rgba(0,0,0,0.3)"
    
    # Position
    align: str = "left"                   # left|center|right|justify
    module_id: str = ""                   # belongs to which module
    order_in_module: int = 0

@dataclass
class TypographySystem:
    """Full typography system extracted from page"""
    text_elements: List[TextElement] = field(default_factory=list)
    
    # Hierarchy summary
    heading_sizes: Dict[str, int] = field(default_factory=dict)      # {"h1":32,"h2":24,"h3":18}
    body_size: int = 0
    caption_size: int = 0
    price_size: int = 0
    
    # Font usage
    font_families: List[str] = field(default_factory=list)
    primary_font: str = ""
    secondary_font: str = ""
    
    # System
    type_scale_ratio: float = 0.0        # e.g. 1.25 for major third
    base_size: int = 0                   # root font-size px
    line_height_system: float = 0.0

# ═══════════════════════════════════════════════════════════════
# 3. COLOR SYSTEM LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ColorSwatch:
    """Single color with metadata"""
    hex: str = ""
    role: str = ""                       # primary|secondary|accent|bg|text|border
    usage_count: int = 0                 # how many elements use this color
    coverage_ratio: float = 0.0          # 0.0-1.0 — proportion of page area
    contrast_ratio_with_bg: float = 0.0  # WCAG contrast ratio

@dataclass 
class ColorSystem:
    """Complete color system"""
    swatches: List[ColorSwatch] = field(default_factory=list)
    
    # Semantic colors
    primary: str = ""
    secondary: str = ""
    accent: str = ""
    background: str = ""
    text_primary: str = ""
    text_secondary: str = ""
    border: str = ""
    
    # Proportions
    primary_ratio: float = 0.0           # 0.0-1.0
    secondary_ratio: float = 0.0
    accent_ratio: float = 0.0
    neutral_ratio: float = 0.0
    
    # Relationships
    harmony_type: str = ""               # monochromatic|complementary|analogous|triadic
    temperature: str = ""                # warm|cool|neutral
    
    # Psychology mapping
    psychology_tags: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════
# 4. IMAGE / PHOTOGRAPHY LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ImageElement:
    """Single image with full capture parameters"""
    id: str
    url: str = ""
    image_type: str = ""                 # hero|product|lifestyle|detail|spec|model
    
    # Shooting
    focal_length: int = 0                # 35mm eq mm
    aperture: float = 0.0                # f/value
    iso: int = 0
    shutter: str = ""
    camera_model: str = ""
    lens_model: str = ""
    
    # Composition
    composition_type: str = ""           # centered|rule_of_thirds|golden_ratio|symmetry|leading_lines
    camera_angle: str = ""               # eye_level|high_angle|low_angle|birdseye|dutch
    perspective: str = ""                # front|three_quarter|profile|top_down
    
    # Layering
    foreground: str = ""
    midground: str = ""
    background: str = ""
    depth_of_field: str = ""             # shallow|medium|deep
    subject_isolation: bool = False
    
    # Dimensions
    width: int = 0
    height: int = 0
    aspect_ratio: str = ""               # "1:1","4:3","3:2","16:9"
    resolution_dpi: int = 72
    
    # Placement
    module_id: str = ""
    position_in_module: int = 0
    z_index: int = 0

@dataclass
class ImageSystem:
    """Complete image system"""
    images: List[ImageElement] = field(default_factory=list)
    total_count: int = 0
    
    # Image mix
    hero_count: int = 0
    product_count: int = 0
    lifestyle_count: int = 0
    detail_count: int = 0
    spec_count: int = 0
    
    # Common patterns
    common_focal_lengths: List[int] = field(default_factory=list)
    common_apertures: List[float] = field(default_factory=list)
    common_compositions: List[str] = field(default_factory=list)
    common_angles: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════
# 5. LIGHTING / SHADOW LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class LightSource:
    """Single light source in the scene"""
    id: str
    light_type: str = ""                 # key|fill|rim|background|ambient
    hardware: str = ""                   # softbox|beauty_dish|umbrella|ring|natural
    
    # Position (3D coordinates cm, camera at 0,0,-400)
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    
    # Intensity
    intensity_lumens: int = 0
    intensity_percent: float = 0.0       # 0.0-1.0 relative to key light
    ev_adjustment: float = 0.0           # stops
    
    # Color
    temperature_k: int = 5500
    color_hex: str = "#FFFFFF"
    
    # Modifier
    modifier: str = ""                   # grid|barn_door|gel|diffuser
    grid_angle: int = 0
    diffusion_strength: float = 1.0      # 0.0-1.0
    
    # Shadow
    shadow_hardness: float = 0.5         # 0.0=diffuse 1.0=hard
    shadow_length: float = 0.0           # cm from subject
    shadow_density: float = 0.5          # 0.0-1.0

@dataclass
class LightingSystem:
    """Complete lighting setup"""
    lights: List[LightSource] = field(default_factory=list)
    light_count: int = 0
    setup_type: str = ""                 # three_point|single|Rembrandt|butterfly|loop|split
    key_to_fill_ratio: float = 0.0       # intensity ratio

# ═══════════════════════════════════════════════════════════════
# 6. INTERACTION / ANIMATION LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class InteractionRule:
    """Interactive behavior on an element"""
    element_id: str = ""
    event: str = ""                      # hover|click|scroll|load|viewport_enter
    action: str = ""                     # color_change|scale|slide|fade|reveal
    duration_ms: int = 300
    delay_ms: int = 0
    easing: str = "ease-out"
    transform_from: str = ""
    transform_to: str = ""
    color_from: str = ""
    color_to: str = ""

# ═══════════════════════════════════════════════════════════════
# 7. DEEP WHY TRACE LAYER
# ═══════════════════════════════════════════════════════════════

@dataclass
class WhyTrace:
    """Multi-angle WHY analysis for one design decision"""
    parameter: str = ""                  # e.g. "font_size_h1=32px"
    value: str = ""                      # current value
    
    # Five-angle WHY
    consumer_psychology: str = ""        # How this affects user perception/emotion
    social_cognition: str = ""           # Cultural/social meaning
    product_positioning: str = ""        # How this supports product strategy
    visual_communication: str = ""       # Visual hierarchy/information priority
    marketing_conversion: str = ""       # How this drives conversion
    
    # Alternatives
    alternative_values: str = ""         # what other options exist
    why_this_over_alternatives: str = ""
    
    # Source
    evidence_source: str = ""            # industry_study|a_b_test|brand_guideline|best_practice

# ═══════════════════════════════════════════════════════════════
# 8. FULL PAGE DNA
# ═══════════════════════════════════════════════════════════════

@dataclass
class FullPageDNA:
    """Complete parametric DNA of one product detail page"""
    url: str = ""
    brand: str = ""
    product_name: str = ""
    product_category: str = ""
    extracted_at: str = ""
    
    # Layers
    layout: PageLayout = field(default_factory=PageLayout)
    modules: List[PageModule] = field(default_factory=list)
    typography: TypographySystem = field(default_factory=TypographySystem)
    colors: ColorSystem = field(default_factory=ColorSystem)
    images: ImageSystem = field(default_factory=ImageSystem)
    lighting: LightingSystem = field(default_factory=LightingSystem)
    interactions: List[InteractionRule] = field(default_factory=list)
    
    # WHY traces (one per key parameter)
    why_traces: List[WhyTrace] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    extraction_version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict"""
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))
    
    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

# ═══════════════════════════════════════════════════════════════
# 9. AGGREGATION: category → brand
# ═══════════════════════════════════════════════════════════════

@dataclass
class CategoryDNASummary:
    """Statistical summary of multiple pages in same category"""
    category: str = ""
    sample_count: int = 0
    
    # Typography ranges
    heading_size_range: List[int] = field(default_factory=list)  # [min, max, median]
    body_size_range: List[int] = field(default_factory=list)
    
    # Color frequency
    common_colors: Dict[str, float] = field(default_factory=dict)  # hex→frequency
    
    # Layout patterns
    common_grids: Dict[str, int] = field(default_factory=dict)
    common_reading_patterns: Dict[str, int] = field(default_factory=dict)
    
    # Photography patterns
    common_focal_lengths: Dict[int, int] = field(default_factory=dict)
    common_compositions: Dict[str, int] = field(default_factory=dict)
    common_angles: Dict[str, int] = field(default_factory=dict)
    
    # Lighting patterns
    common_lighting_setups: Dict[str, int] = field(default_factory=dict)
    
    # Design rules extracted
    design_rules: List[str] = field(default_factory=list)

@dataclass 
class BrandVISystem:
    """Brand-level VI system from multi-category aggregation"""
    brand: str = ""
    categories_analyzed: List[str] = field(default_factory=list)
    total_pages_analyzed: int = 0
    
    # VI core
    brand_colors: Dict[str, str] = field(default_factory=dict)  # role→hex
    brand_typography: Dict[str, Any] = field(default_factory=dict)
    brand_photography_rules: List[str] = field(default_factory=list)
    brand_layout_system: str = ""
    
    # Cross-category consistency
    consistency_score: float = 0.0       # 0.0-1.0
    
    # Rules usable by AI designers
    design_tokens: Dict[str, Any] = field(default_factory=dict)
