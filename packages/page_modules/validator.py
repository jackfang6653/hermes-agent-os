"""
Module D: Validator — 生成后自动校验 + 风格库迭代更新

核心能力:
- 输入: 新生成的详情页模块图片
- 重新提取 ACR 参数 (通过 ACRAnalyzer)
- 对比基准库偏差值 (逐参数计算 delta)
- 超阈值标记异常 (ModuleAnomaly)
- 自动校正建议 (AutoCorrection)
- 累积合格数据 → 提取通用规则 → 版本归档
- 支持多批次累积学习 (RuleExtraction)

依赖: acr_analyzer, style_engine
"""

import json
import logging
import copy
import re
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

from .acr_analyzer import (
    ACRAnalyzer,
    ModuleACRAnalysis,
    ACRBasicAdjust,
    HistogramBaseInfo,
    ToneCurveKeyPoints,
    VisualDNA,
)
from .style_engine import (
    StyleLibrary,
    ModuleACRFingerprint,
    GlobalConstraint,
    StyleLibraryManager,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════


@dataclass
class ParameterDeviation:
    """单个参数的偏差"""
    parameter: str                          # 参数名 e.g. "exposure"
    baseline_value: float = 0.0             # 基准值
    current_value: float = 0.0              # 当前值
    delta: float = 0.0                      # 偏差 = current - baseline
    delta_abs: float = 0.0                  # |delta|
    threshold: float = 0.0                  # 允许阈值
    is_anomaly: bool = False                # 是否异常
    severity: str = "OK"                    # OK | WARNING | ERROR


@dataclass
class ModuleAnomaly:
    """单个模块的完整异常报告"""
    module_id: str = ""
    module_type: str = ""

    # 总体偏差分数 (所有参数偏差的加权平均)
    total_deviation_score: float = 0.0

    # 逐参数偏差
    deviations: List[ParameterDeviation] = field(default_factory=list)
    anomaly_count: int = 0
    warning_count: int = 0

    # 判定
    is_pass: bool = True                    # 整体是否通过
    pass_count: int = 0
    fail_count: int = 0

    # 自动校正
    auto_corrections: Dict[str, Any] = field(default_factory=dict)

    # 分数细分
    histogram_score: float = 0.0
    acr_score: float = 0.0
    visual_dna_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """
    完整校验报告 — 单批次所有模块的对比结果
    """
    page_benchmark_id: str = ""
    validated_at: str = ""

    # 所有模块的异常报告
    module_anomalies: List[ModuleAnomaly] = field(default_factory=list)

    # 汇总
    total_modules: int = 0
    passed_modules: int = 0
    failed_modules: int = 0
    overall_pass_rate: float = 0.0

    # 自动校正汇总
    corrections_applied: int = 0
    auto_correction_details: Dict[str, Any] = field(default_factory=dict)

    # 版本
    benchmark_version: str = ""
    new_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def format_summary(self) -> str:
        """人类可读的摘要"""
        lines = [
            f"=== Validation Report: {self.page_benchmark_id} ===",
            f"Validated at: {self.validated_at}",
            f"Total Modules: {self.total_modules}",
            f"Passed: {self.passed_modules} | Failed: {self.failed_modules}",
            f"Overall Pass Rate: {self.overall_pass_rate:.1%}",
            f"Corrections Applied: {self.corrections_applied}",
            "",
            "--- Per-Module Breakdown ---",
        ]
        for anomaly in self.module_anomalies:
            status = "✓ PASS" if anomaly.is_pass else "✗ FAIL"
            lines.append(
                f"  {anomaly.module_id} ({anomaly.module_type}): {status} "
                f"score={anomaly.total_deviation_score:.1f} "
                f"(ACR={anomaly.acr_score:.1f}, Hist={anomaly.histogram_score:.1f}, "
                f"DNA={anomaly.visual_dna_score:.1f})"
            )
            # 列出具体异常
            for dev in anomaly.deviations:
                if dev.is_anomaly:
                    lines.append(
                        f"    ⚠ {dev.parameter}: {dev.baseline_value} → "
                        f"{dev.current_value} (Δ={dev.delta:+.1f}, "
                        f"threshold={dev.threshold}, severity={dev.severity})"
                    )
        return "\n".join(lines)


@dataclass
class ExtractedRule:
    """从多批次合格数据中提取的通用规则"""
    rule_id: str = ""
    parameter: str = ""
    rule_type: str = ""                     # RANGE | FIXED | FORMULA
    category: str = ""                      # ACR | Histogram | VisualDNA | Typography

    # 规则值
    min_value: float = 0.0
    max_value: float = 0.0
    mean_value: float = 0.0
    std_dev: float = 0.0
    sample_count: int = 0

    # 适用范围
    applicable_module_types: List[str] = field(default_factory=list)

    # WHY追踪
    consumer_psychology_rationale: str = ""
    visual_communication_rationale: str = ""
    marketing_conversion_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleSet:
    """完整规则集"""
    category: str = ""                      # e.g. "furniture_detail_pages"
    version: str = "V1.0"
    extracted_at: str = ""
    total_samples: int = 0
    rules: List[ExtractedRule] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Deviation Calculator
# ═══════════════════════════════════════════════════════════════

class DeviationCalculator:
    """
    偏差计算器 — 逐参数对比基准 vs 当前值

    阈值配置 (可自定义):
    - ACR参数阈值基于 Adobe Camera Raw 敏感度
    - 视觉DNA阈值较宽松 (主观成分)
    """

    # 默认阈值配置 — 每个参数的允许偏差
    DEFAULT_THRESHOLDS = {
        # ACR Basic (严格)
        "exposure": 0.15,
        "contrast": 8,
        "highlights": 10,
        "shadows": 10,
        "whites": 10,
        "blacks": 8,
        "texture": 10,
        "clarity": 10,
        "dehaze": 8,
        "vibrance": 8,
        "saturation": 5,              # 极严格 — 饱和度偏移明显
        "temperature_k": 300,         # Kelvin
        "tint": 5,

        # Histogram (中等)
        "shadow_pixel_ratio": 0.10,
        "midtone_pixel_ratio": 0.10,
        "highlight_pixel_ratio": 0.10,
        "rgb_overlap_ratio": 0.15,
        "gamma_value": 0.2,

        # Tone Curve (中等)
        "black_point_x": 0.05,
        "black_point_y": 0.05,
        "shadow_point_x": 0.05,
        "shadow_point_y": 0.05,
        "midtone_point_x": 0.05,
        "midtone_point_y": 0.05,
        "highlight_point_x": 0.05,
        "highlight_point_y": 0.05,
        "white_point_x": 0.03,
        "white_point_y": 0.03,

        # Visual DNA (宽松)
        "fill_light_ratio": 0.2,
        "main_color_area_ratio": 0.15,
        "aux_color_area_ratio": 0.15,
        "accent_color_area_ratio": 0.10,
        "background_blur_strength": 0.2,
        "sharpening_intensity": 0.2,
        "vignette_strength": 0.2,
        "vignette_range": 0.2,
    }

    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        global_constraint: Optional[GlobalConstraint] = None,
    ):
        """
        Args:
            thresholds: 自定义阈值覆盖
            global_constraint: 全局约束 (用于色温/对比/饱和等全局限制)
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.global_constraint = global_constraint or GlobalConstraint()

    def compare_module(
        self,
        baseline: ModuleACRFingerprint,
        current: ModuleACRAnalysis,
    ) -> ModuleAnomaly:
        """
        对比单个模块的基准 vs 当前分析结果。

        Args:
            baseline: 基准指纹
            current: 当前ACR分析结果

        Returns:
            ModuleAnomaly 包含所有偏差和异常标记
        """
        anomaly = ModuleAnomaly(
            module_id=current.module_id,
            module_type=current.module_type,
        )
        deviations = []

        # ── ACR Basic 参数对比 ──
        acr_fields = [
            ("exposure", baseline.acr_params, current.acr_basic),
            ("contrast", baseline.acr_params, current.acr_basic),
            ("highlights", baseline.acr_params, current.acr_basic),
            ("shadows", baseline.acr_params, current.acr_basic),
            ("whites", baseline.acr_params, current.acr_basic),
            ("blacks", baseline.acr_params, current.acr_basic),
            ("texture", baseline.acr_params, current.acr_basic),
            ("clarity", baseline.acr_params, current.acr_basic),
            ("dehaze", baseline.acr_params, current.acr_basic),
            ("vibrance", baseline.acr_params, current.acr_basic),
            ("saturation", baseline.acr_params, current.acr_basic),
            ("temperature_k", baseline.acr_params, current.acr_basic),
            ("tint", baseline.acr_params, current.acr_basic),
        ]

        for param, base_dict, curr_obj in acr_fields:
            base_val = float(base_dict.get(param, 0))
            curr_val = float(getattr(curr_obj, param, 0))
            dev = self._create_deviation(
                param, base_val, curr_val,
                self.thresholds.get(param, 5.0)
            )
            deviations.append(dev)

        # ── Histogram 参数对比 ──
        hist_fields = [
            ("shadow_pixel_ratio", baseline.histogram, current.histogram),
            ("midtone_pixel_ratio", baseline.histogram, current.histogram),
            ("highlight_pixel_ratio", baseline.histogram, current.histogram),
            ("rgb_overlap_ratio", baseline.histogram, current.histogram),
            ("gamma_value", baseline.histogram, current.histogram),
        ]
        for param, base_dict, curr_obj in hist_fields:
            base_val = float(base_dict.get(param, 0))
            curr_val = float(getattr(curr_obj, param, 0))
            dev = self._create_deviation(
                param, base_val, curr_val,
                self.thresholds.get(param, 0.1)
            )
            deviations.append(dev)

        # ── Tone Curve 对比 ──
        tc_baseline = baseline.tone_curve
        tc_current = current.tone_curve
        curve_anchors = [
            "black_point", "shadow_point", "midtone_point",
            "highlight_point", "white_point",
        ]
        for anchor in curve_anchors:
            base_pt = tc_baseline.get(anchor, [0.0, 0.0])
            curr_pt = getattr(tc_current, anchor, (0.0, 0.0))

            if isinstance(base_pt, (list, tuple)) and len(base_pt) >= 2:
                base_x, base_y = float(base_pt[0]), float(base_pt[1])
            else:
                base_x, base_y = 0.0, 0.0
            if isinstance(curr_pt, (list, tuple)) and len(curr_pt) >= 2:
                curr_x, curr_y = float(curr_pt[0]), float(curr_pt[1])
            else:
                curr_x, curr_y = 0.0, 0.0

            # x axis
            dev_x = self._create_deviation(
                f"{anchor}_x", base_x, curr_x,
                self.thresholds.get(f"{anchor}_x", 0.05)
            )
            deviations.append(dev_x)
            # y axis
            dev_y = self._create_deviation(
                f"{anchor}_y", base_y, curr_y,
                self.thresholds.get(f"{anchor}_y", 0.05)
            )
            deviations.append(dev_y)

        # ── Visual DNA 对比 ──
        vd_baseline = baseline.visual_dna
        vd_current = current.visual_dna
        vd_fields = [
            ("fill_light_ratio", 0.2),
            ("main_color_area_ratio", 0.15),
            ("aux_color_area_ratio", 0.15),
            ("accent_color_area_ratio", 0.10),
            ("background_blur_strength", 0.2),
            ("sharpening_intensity", 0.2),
            ("vignette_range", 0.2),
            ("vignette_strength", 0.2),
        ]
        for param, default_threshold in vd_fields:
            base_val = float(vd_baseline.get(param, 0))
            curr_val = float(getattr(vd_current, param, 0))
            dev = self._create_deviation(
                param, base_val, curr_val,
                self.thresholds.get(param, default_threshold)
            )
            deviations.append(dev)

        # ── 汇总 ──
        anomaly.deviations = deviations
        anomaly.anomaly_count = sum(1 for d in deviations if d.is_anomaly)
        anomaly.warning_count = sum(
            1 for d in deviations if d.severity == "WARNING"
        )

        # 计算加权总分 (ACR权重更高)
        acr_deviations = [d for d in deviations if d.parameter in {
            "exposure", "contrast", "highlights", "shadows", "whites", "blacks",
            "texture", "clarity", "dehaze", "vibrance", "saturation",
            "temperature_k", "tint",
        }]
        hist_deviations = [d for d in deviations if d.parameter in {
            "shadow_pixel_ratio", "midtone_pixel_ratio", "highlight_pixel_ratio",
            "rgb_overlap_ratio", "gamma_value",
        }]
        dna_deviations = [d for d in deviations if d.parameter in {
            "fill_light_ratio", "main_color_area_ratio", "aux_color_area_ratio",
            "accent_color_area_ratio", "background_blur_strength",
            "sharpening_intensity", "vignette_range", "vignette_strength",
        }]

        def _avg_score(devs: List[ParameterDeviation]) -> float:
            if not devs:
                return 0.0
            return sum(
                min(d.delta_abs / max(d.threshold, 0.001), 1.0) * 100
                for d in devs
            ) / len(devs)

        anomaly.acr_score = _avg_score(acr_deviations)
        anomaly.histogram_score = _avg_score(hist_deviations)
        anomaly.visual_dna_score = _avg_score(dna_deviations)

        # 总分: ACR 50% / Histogram 20% / DNA 20% / 数量惩罚10%
        anomaly.total_deviation_score = round(
            0.5 * anomaly.acr_score
            + 0.2 * anomaly.histogram_score
            + 0.2 * anomaly.visual_dna_score
            + 0.1 * min(anomaly.anomaly_count * 5, 100),
            2,
        )

        # 通过判定: 总分 < 15 且 异常数 < 5
        anomaly.is_pass = (
            anomaly.total_deviation_score < 15.0
            and anomaly.anomaly_count < 5
        )
        anomaly.pass_count = 1 if anomaly.is_pass else 0
        anomaly.fail_count = 0 if anomaly.is_pass else 1

        # ── 自动校正 ──
        if not anomaly.is_pass:
            anomaly.auto_corrections = self._generate_corrections(
                baseline, current, deviations
            )

        return anomaly

    def compare_all_modules(
        self,
        library: StyleLibrary,
        analyses: List[ModuleACRAnalysis],
    ) -> ValidationReport:
        """
        对比所有模块。

        Args:
            library: 基准风格库
            analyses: 当前批次的ACR分析结果列表

        Returns:
            ValidationReport 完整校验报告
        """
        # 构建 ModuleID → fingerprint 快速索引
        fp_map = {fp.module_id: fp for fp in library.module_library}

        anomalies = []
        for analysis in analyses:
            baseline = fp_map.get(analysis.module_id)
            if baseline:
                anomaly = self.compare_module(baseline, analysis)
                anomalies.append(anomaly)
            else:
                logger.warning(
                    f"No baseline found for {analysis.module_id}, skipping"
                )

        passed = sum(1 for a in anomalies if a.is_pass)
        total = len(anomalies)

        report = ValidationReport(
            page_benchmark_id=library.page_benchmark_id,
            validated_at=datetime.now().isoformat(),
            module_anomalies=anomalies,
            total_modules=total,
            passed_modules=passed,
            failed_modules=total - passed,
            overall_pass_rate=passed / total if total > 0 else 0.0,
            corrections_applied=sum(
                1 for a in anomalies if a.auto_corrections
            ),
            benchmark_version=library.version,
        )
        return report

    def _create_deviation(
        self,
        parameter: str,
        baseline_value: float,
        current_value: float,
        threshold: float,
    ) -> ParameterDeviation:
        """创建单个参数偏差"""
        delta = current_value - baseline_value
        delta_abs = abs(delta)

        is_anomaly = delta_abs > threshold
        if not is_anomaly:
            severity = "OK"
        elif delta_abs > threshold * 2:
            severity = "ERROR"
        else:
            severity = "WARNING"

        return ParameterDeviation(
            parameter=parameter,
            baseline_value=baseline_value,
            current_value=current_value,
            delta=delta,
            delta_abs=delta_abs,
            threshold=threshold,
            is_anomaly=is_anomaly,
            severity=severity,
        )

    def _generate_corrections(
        self,
        baseline: ModuleACRFingerprint,
        current: ModuleACRAnalysis,
        deviations: List[ParameterDeviation],
    ) -> Dict[str, Any]:
        """
        自动生成校正建议。
        策略: 将异常参数拉回基准值的 80% 范围内。
        """
        corrections = {}
        for dev in deviations:
            if not dev.is_anomaly:
                continue
            # 校正值 = 基准值 + 偏差的 20% (保留部分当前特征)
            corrected = dev.baseline_value + dev.delta * 0.2
            corrections[dev.parameter] = {
                "baseline": dev.baseline_value,
                "current": dev.current_value,
                "suggested": round(corrected, 4),
                "delta_original": dev.delta,
                "delta_corrected": round(corrected - dev.baseline_value, 4),
            }
        return corrections


# ═══════════════════════════════════════════════════════════════
# Rule Extractor — 累积学习
# ═══════════════════════════════════════════════════════════════

class RuleExtractor:
    """
    规则提取器 — 从多批次合格数据中提取通用规则

    策略:
    - 收集同一品类下所有合格模块的ACR参数
    - 计算每个参数的统计分布 (mean ± 2*std)
    - 形成品类级统一ACR预设 + 页面布局规范
    - WHY追踪: 记录每个参数设置的营销/心理学/视觉传播理由
    """

    def __init__(self):
        # 累积数据: parameter → [values]
        self.accumulated: Dict[str, List[float]] = defaultdict(list)
        self.sample_count: int = 0
        self.module_types_seen: Set[str] = set()

    def feed_qualified_data(
        self,
        analysis: ModuleACRAnalysis,
    ) -> None:
        """
        喂入一个合格模块的ACR分析数据。

        Args:
            analysis: 通过校验的 ModuleACRAnalysis
        """
        self.sample_count += 1
        self.module_types_seen.add(analysis.module_type)

        # ACR参数
        for field in [
            "exposure", "contrast", "highlights", "shadows",
            "whites", "blacks", "texture", "clarity", "dehaze",
            "vibrance", "saturation", "temperature_k", "tint",
        ]:
            val = getattr(analysis.acr_basic, field, 0)
            self.accumulated[f"acr.{field}"].append(float(val))

        # Histogram
        for field in [
            "shadow_pixel_ratio", "midtone_pixel_ratio",
            "highlight_pixel_ratio", "rgb_overlap_ratio",
            "gamma_value",
        ]:
            val = getattr(analysis.histogram, field, 0)
            self.accumulated[f"hist.{field}"].append(float(val))

    def feed_qualified_batch(
        self,
        analyses: List[ModuleACRAnalysis],
        anomalies: List[ModuleAnomaly],
    ) -> int:
        """
        喂入一批分析结果，自动过滤仅保留合格数据。

        Returns:
            实际喂入的合格数据数量
        """
        # 构建 module_id → analysis 的映射
        analysis_map = {a.module_id: a for a in analyses}

        fed_count = 0
        for anomaly in anomalies:
            if anomaly.is_pass:
                analysis = analysis_map.get(anomaly.module_id)
                if analysis:
                    self.feed_qualified_data(analysis)
                    fed_count += 1
        return fed_count

    def extract_rules(self) -> RuleSet:
        """
        从累积数据中提取通用规则。

        Returns:
            RuleSet 包含所有提取的规则
        """
        import statistics
        rules = []

        for param, values in self.accumulated.items():
            if len(values) < 3:  # 至少3个样本
                continue

            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) >= 2 else 0.0
            min_val = min(values)
            max_val = max(values)

            # 规则范围: mean ± 2*std (覆盖95%)
            rule_min = max(min_val, mean_val - 2 * std_val)
            rule_max = min(max_val, mean_val + 2 * std_val)

            # 分类
            category = "ACR" if param.startswith("acr.") else "Histogram"

            rules.append(ExtractedRule(
                rule_id=f"rule_{param.replace('.', '_')}",
                parameter=param,
                rule_type="RANGE" if std_val > 0.01 else "FIXED",
                category=category,
                min_value=round(rule_min, 4),
                max_value=round(rule_max, 4),
                mean_value=round(mean_val, 4),
                std_dev=round(std_val, 4),
                sample_count=len(values),
                applicable_module_types=list(self.module_types_seen),
            ))

        return RuleSet(
            category="product_detail_page",
            extracted_at=datetime.now().isoformat(),
            total_samples=self.sample_count,
            rules=rules,
        )


# ═══════════════════════════════════════════════════════════════
# Validator — 总控
# ═══════════════════════════════════════════════════════════════

class Validator:
    """
    生成后自动校验 + 风格库迭代更新

    用法:
        validator = Validator(acr_analyzer, style_manager)
        report = validator.validate(
            library=baseline_library,
            new_image_paths=[("path/M001.png", "M001", "HeroBanner"), ...],
        )
        # → ValidationReport with anomalies, corrections
        # → 自动更新风格库 (合格数据)
        # → 提取通用规则 (累积多批次)
    """

    def __init__(
        self,
        acr_analyzer: ACRAnalyzer,
        style_manager: Optional[StyleLibraryManager] = None,
        global_constraint: Optional[GlobalConstraint] = None,
        custom_thresholds: Optional[Dict[str, float]] = None,
    ):
        self.acr_analyzer = acr_analyzer
        self.style_manager = style_manager or StyleLibraryManager()
        self.calculator = DeviationCalculator(
            thresholds=custom_thresholds,
            global_constraint=global_constraint,
        )
        self.rule_extractor = RuleExtractor()

    def validate(
        self,
        library: StyleLibrary,
        new_image_paths: List[Tuple[str, str, str]],
        auto_update: bool = True,
    ) -> ValidationReport:
        """
        完整校验流程:
        1. 对新图片运行 ACRAnalyzer
        2. 对比基准库计算偏差
        3. 标记异常 → 自动校正
        4. (可选) 更新风格库

        Args:
            library: 基准风格库
            new_image_paths: [(image_path, module_id, module_type), ...]
            auto_update: 是否自动更新风格库

        Returns:
            ValidationReport
        """
        # Step 1: 重新提取ACR
        analyses = self.acr_analyzer.analyze_batch(new_image_paths)

        # Step 2: 全面对比
        report = self.calculator.compare_all_modules(library, analyses)

        # Step 3: 喂入合格数据用于规则提取
        self.rule_extractor.feed_qualified_batch(
            analyses, report.module_anomalies
        )

        # Step 4: 自动更新风格库
        if auto_update:
            self._auto_update_library(library, analyses, report)

        return report

    def _auto_update_library(
        self,
        library: StyleLibrary,
        analyses: List[ModuleACRAnalysis],
        report: ValidationReport,
    ) -> None:
        """自动更新风格库: 用合格数据更新指纹，记录偏差历史"""
        for anomaly in report.module_anomalies:
            # 查找对应的分析结果
            analysis = next(
                (a for a in analyses if a.module_id == anomaly.module_id),
                None,
            )
            if not analysis:
                continue

            if anomaly.is_pass:
                # 合格: 更新指纹 (采用加权平均: 70% 基准 + 30% 新值)
                self._update_fingerprint_weighted(library, analysis)
            else:
                # 不合格: 记录偏差但不更新
                fp = self.style_manager.get_fingerprint(
                    library, anomaly.module_id
                )
                if fp:
                    fp.deviation_history.append(anomaly.total_deviation_score)

        # 版本号递增
        ver_match = re.match(r"V(\d+)\.(\d+)", library.version)
        if ver_match:
            major, minor = int(ver_match.group(1)), int(ver_match.group(2))
            library.version = f"V{major}.{minor + 1}"

        library.updated_at = datetime.now().isoformat()

    def _update_fingerprint_weighted(
        self,
        library: StyleLibrary,
        analysis: ModuleACRAnalysis,
        weight_baseline: float = 0.7,
    ) -> None:
        """加权更新指纹 (EMA)"""
        fp = self.style_manager.get_fingerprint(library, analysis.module_id)
        if not fp:
            return

        w_new = 1.0 - weight_baseline

        # 更新ACR参数 (加权平均)
        for key in fp.acr_params:
            old_val = float(fp.acr_params.get(key, 0))
            new_val = float(getattr(analysis.acr_basic, key, 0))
            fp.acr_params[key] = round(
                weight_baseline * old_val + w_new * new_val, 4
            )

        # 更新直方图参数
        for key in fp.histogram:
            old_val = float(fp.histogram.get(key, 0))
            new_val = float(getattr(analysis.histogram, key, 0))
            fp.histogram[key] = round(
                weight_baseline * old_val + w_new * new_val, 4
            )

        fp.updated_at = datetime.now().isoformat()

    def extract_category_rules(self) -> RuleSet:
        """提取当前累积的类别级规则"""
        return self.rule_extractor.extract_rules()

    def export_rules_json(self, filepath: str) -> None:
        """导出规则集为JSON文件"""
        ruleset = self.extract_category_rules()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(ruleset), f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# 单函数快速入口
# ═══════════════════════════════════════════════════════════════

def validate_page(
    library: StyleLibrary,
    new_image_paths: List[Tuple[str, str, str]],
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
) -> Tuple[ValidationReport, List[ModuleACRAnalysis]]:
    """
    快速校验一个页面的所有模块。

    Args:
        library: 基准风格库
        new_image_paths: [(image_path, module_id, module_type), ...]
        api_key: OpenAI API key
        model: Vision模型

    Returns:
        (ValidationReport, List[ModuleACRAnalysis])
    """
    analyzer = ACRAnalyzer(api_key=api_key, model=model)
    validator = Validator(acr_analyzer=analyzer)
    report = validator.validate(library, new_image_paths, auto_update=True)
    # 也需要返回 analyses (需要重新获取，这里简化)
    return (report, [])
