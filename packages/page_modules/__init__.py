"""
packages/page_modules/ — 爬虫分块 + ACR直方图分析 + 风格锁定 + 校验迭代

五模块系统 (A-E):

  A. page_crawler  — 爬虫抓取详情页，识别功能模块区域，输出 mapping JSON
  B. acr_analyzer  — GPT-4o Vision ACR直方图 + 参数解析，强制 JSON 输出
  C. style_engine  — 风格库 + ACR指纹 + 全局约束 + Positive/Negative Prompt生成
  D. validator     — 生成后自动校验 + 偏差对比 + 异常标记 + 自动校正 + 规则提取
  E. pipeline      — 全流程编排 (A→B→C→D) with concurrent.futures + 缓存 + 错误隔离

统一 JSON 输出格式 (PageBenchmarkID / GlobalConstraint / ModuleLibrary)
"""

# ── Module A: Crawl ──
from .page_crawler import (
    PageCrawler,
    CrawlResult,
    ModuleRegion,
    crawl_page,
    MODULE_TYPES,
)

# ── Module B: ACR Analyze ──
from .acr_analyzer import (
    ACRAnalyzer,
    ModuleACRAnalysis,
    HistogramBaseInfo,
    ACRBasicAdjust,
    ToneCurveKeyPoints,
    VisualDNA,
    TextParams,
    analyze_module_image,
)

# ── Module C: Style Engine ──
from .style_engine import (
    StyleLibrary,
    StyleLibraryManager,
    ModuleACRFingerprint,
    GlobalConstraint,
    PromptGenerator,
    PromptResult,
    create_style_library,
    generate_prompts_for_library,
)

# ── Module D: Validator ──
from .validator import (
    Validator,
    ValidationReport,
    DeviationCalculator,
    ModuleAnomaly,
    ParameterDeviation,
    RuleExtractor,
    RuleSet,
    ExtractedRule,
    validate_page,
)

# ── Module E: Pipeline ──
from .pipeline import (
    PageModulesPipeline,
    PipelineResult,
    StageResult,
    PipelineCache,
    run_pipeline,
    run_crawl_only,
    run_analyze_only,
    run_style_only,
    run_validate_only,
)

__all__ = [
    # A: Crawl
    "PageCrawler", "CrawlResult", "ModuleRegion", "crawl_page", "MODULE_TYPES",
    # B: ACR Analyze
    "ACRAnalyzer", "ModuleACRAnalysis", "HistogramBaseInfo", "ACRBasicAdjust",
    "ToneCurveKeyPoints", "VisualDNA", "TextParams", "analyze_module_image",
    # C: Style Engine
    "StyleLibrary", "StyleLibraryManager", "ModuleACRFingerprint",
    "GlobalConstraint", "PromptGenerator", "PromptResult",
    "create_style_library", "generate_prompts_for_library",
    # D: Validator
    "Validator", "ValidationReport", "DeviationCalculator", "ModuleAnomaly",
    "ParameterDeviation", "RuleExtractor", "RuleSet", "ExtractedRule", "validate_page",
    # E: Pipeline
    "PageModulesPipeline", "PipelineResult", "StageResult", "PipelineCache",
    "run_pipeline", "run_crawl_only", "run_analyze_only", "run_style_only", "run_validate_only",
]
