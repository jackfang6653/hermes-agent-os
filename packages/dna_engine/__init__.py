"""
品牌DNA引擎 — 完整的品牌DNA参数数据库系统

模块:
- dna_schema:     三维品牌DNA Schema (design_system / design_style / visual_effects)
- dna_database:   品牌DNA数据库 (SQLite + W3C DTCG 2025.10)
- quality_gates:  五道质量门禁系统 (Recon → Token → Asset → Synthesis → Visual)
- scene_graph:    场景图建模 (PBR材质/灯光/相机/空间关系)
- scene_parser:   场景图解析器
- scene_renderer: 场景图渲染器
- brand_db:       旧版品牌数据库 (v1)
- pipeline:       DNA流水线
"""

# ── 新模块 (v2) ──────────────────────────────────────────

from .dna_schema import (
    # 基础类型
    ConfidenceLevel,
    ExtractionMethod,
    DNAField,

    # 维度1: 设计系统
    ColorDNA,
    TypographyDNA,
    SpacingDNA,
    LayoutDNA,
    ShapeDNA,
    ElevationDNA,
    IconographyDNA,
    MotionDNA,
    ComponentDNA,
    DesignSystemDNA,

    # 维度2: 设计风格
    AestheticDNA,
    VisualLanguageDNA,
    CompositionDNA,
    ImageryDNA,
    InteractionDNA,
    DesignStyleDNA,

    # 维度3: 视觉特效
    BackgroundEffectDNA,
    ParticleEffectDNA,
    ThreeDEffectDNA,
    ShaderEffectDNA,
    ScrollEffectDNA,
    TextEffectDNA,
    CursorEffectDNA,
    ImageEffectDNA,
    GlassmorphismDNA,
    VisualEffectsDNA,

    # 顶层
    BrandDNA,

    # 工厂函数
    create_empty_dna,
    dna_from_json,
    dna_from_dtcg_tokens,
)

from .dna_database import (
    DNADatabase,
    create_database,
    migrate_from_v1,
    DTCG_VERSION,
    QUALITY_GATE_THRESHOLDS,
    QUALITY_GATE_NAMES,
)

from .quality_gates import (
    GateStatus,
    Severity,
    GateResult,
    QualityPipelineResult,
    ReconnaissanceGate,
    TokenExtractionGate,
    AssetExtractionGate,
    SynthesisGate,
    VisualReplicationGate,
    QualityGatePipeline,
    evaluate_brand_quality,
    gate_data_template,
)

# ── 旧模块 (v1) — 保持向后兼容 ─────────────────────────

from .scene_graph import SceneGraph, SceneElement, PBRMaterial, Light, CameraSystem, PostProcessing
from .scene_parser import SceneParser
from .scene_renderer import SceneRenderer
from .brand_db import BrandDatabase
from .pipeline import DNAPipeline

# ── 版本信息 ────────────────────────────────────────────

__version__ = "2.0.0"
__all__ = [
    # DNA Schema
    "BrandDNA",
    "DesignSystemDNA",
    "DesignStyleDNA",
    "VisualEffectsDNA",
    "ColorDNA",
    "TypographyDNA",
    "SpacingDNA",
    "LayoutDNA",
    "ShapeDNA",
    "ElevationDNA",
    "IconographyDNA",
    "MotionDNA",
    "ComponentDNA",
    "AestheticDNA",
    "VisualLanguageDNA",
    "CompositionDNA",
    "ImageryDNA",
    "InteractionDNA",
    "BackgroundEffectDNA",
    "ParticleEffectDNA",
    "ThreeDEffectDNA",
    "ShaderEffectDNA",
    "ScrollEffectDNA",
    "TextEffectDNA",
    "CursorEffectDNA",
    "ImageEffectDNA",
    "GlassmorphismDNA",
    "DNAField",
    "ConfidenceLevel",
    "ExtractionMethod",
    "create_empty_dna",
    "dna_from_json",
    "dna_from_dtcg_tokens",

    # Database
    "DNADatabase",
    "create_database",
    "migrate_from_v1",
    "DTCG_VERSION",
    "QUALITY_GATE_THRESHOLDS",
    "QUALITY_GATE_NAMES",

    # Quality Gates
    "GateStatus",
    "Severity",
    "GateResult",
    "QualityPipelineResult",
    "ReconnaissanceGate",
    "TokenExtractionGate",
    "AssetExtractionGate",
    "SynthesisGate",
    "VisualReplicationGate",
    "QualityGatePipeline",
    "evaluate_brand_quality",
    "gate_data_template",

    # Legacy (v1)
    "SceneGraph",
    "SceneElement",
    "PBRMaterial",
    "Light",
    "CameraSystem",
    "PostProcessing",
    "SceneParser",
    "SceneRenderer",
    "BrandDatabase",
    "DNAPipeline",
]
