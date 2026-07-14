"""
品牌DNA五道质量门禁系统

Gate 1 (Reconnaissance):      侦察门 — 5项阻止性标准
Gate 2 (Token Extraction):    令牌提取门 — >=0.85 阈值
Gate 3 (Asset Extraction):    资产提取门 — >=0.60 + logo必需
Gate 4 (Synthesis & Interpretation): 合成解释门 — >=0.80
Gate 5 (Visual Replication):  视觉复现门 — 3层(pixel/structural/traceability) >=0.83 avg

流程：
  Input → Gate1 → Gate2 → Gate3 → Gate4 → Gate5 → Approved Output

任何一门未通过则停止并返回失败原因。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Callable
from enum import Enum
from datetime import datetime
import json


# ═══════════════════════════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════════════════════════

class GateStatus(Enum):
    """门禁状态"""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"

class Severity(Enum):
    """问题严重程度"""
    BLOCKER = "blocker"       # 阻止通过
    CRITICAL = "critical"     # 严重影响
    WARNING = "warning"       # 警告
    INFO = "info"             # 信息

@dataclass
class GateResult:
    """单门结果"""
    gate_number: int
    gate_name: str
    status: GateStatus = GateStatus.PENDING
    score: float = 0.0
    threshold: float = 0.0
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evaluated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_number": self.gate_number,
            "gate_name": self.gate_name,
            "status": self.status.value,
            "score": self.score,
            "threshold": self.threshold,
            "passed": self.passed,
            "details": self.details,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "evaluated_at": self.evaluated_at,
        }

@dataclass
class QualityPipelineResult:
    """完整门禁管线结果"""
    brand_name: str
    overall_passed: bool
    results: Dict[int, GateResult] = field(default_factory=dict)
    total_score: float = 0.0
    failed_at_gate: Optional[int] = None
    execution_time_seconds: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "overall_passed": self.overall_passed,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "total_score": self.total_score,
            "failed_at_gate": self.failed_at_gate,
            "execution_time_seconds": self.execution_time_seconds,
            "summary": self.summary,
        }


# ═══════════════════════════════════════════════════════════════
# Gate 1: Reconnaissance (侦察门)
# ═══════════════════════════════════════════════════════════════

class ReconnaissanceGate:
    """
    Gate 1 — 侦察门

    5项阻止性标准 (blocking criteria)，任何一项不通过即 BLOCK：
    1. 品牌识别: 必须能够唯一识别品牌名称
    2. 页面获取: 至少成功抓取1个页面
    3. 资源可访问: CSS/JS/字体资源可访问性 >=80%
    4. DOM完整性: DOM结构可用性 >=90%
    5. 反爬检测: 无严重反爬阻断
    """

    GATE_NUMBER = 1
    GATE_NAME = "Reconnaissance"
    THRESHOLD = 0.85

    BLOCKING_CRITERIA = [
        {
            "id": "brand_identification",
            "name": "品牌识别",
            "description": "必须能够唯一识别品牌名称",
            "check": "brand_name_identified",
        },
        {
            "id": "page_access",
            "name": "页面获取",
            "description": "至少成功抓取1个页面",
            "check": "pages_captured",
        },
        {
            "id": "resource_accessibility",
            "name": "资源可访问",
            "description": "CSS/JS/字体资源可访问性 >=80%",
            "check": "resource_ratio",
        },
        {
            "id": "dom_integrity",
            "name": "DOM完整性",
            "description": "DOM结构可用性 >=90%",
            "check": "dom_score",
        },
        {
            "id": "anti_scraping",
            "name": "反爬检测",
            "description": "无严重反爬阻断",
            "check": "blocked",
        },
    ]

    def evaluate(self, recon_data: Dict[str, Any]) -> GateResult:
        """
        评估侦察结果

        Args:
            recon_data: {
                "brand_name": str | None,
                "pages_captured": int,
                "resources_total": int,
                "resources_accessible": int,
                "dom_elements_found": int,
                "dom_elements_expected": int,
                "anti_scraping_blocked": bool,
            }
        """
        result = GateResult(
            gate_number=self.GATE_NUMBER,
            gate_name=self.GATE_NAME,
            threshold=self.THRESHOLD,
            evaluated_at=datetime.now().isoformat(),
        )

        checks_passed = 0
        total_checks = len(self.BLOCKING_CRITERIA)

        # 1. 品牌识别
        brand_ok = bool(recon_data.get("brand_name"))
        result.details["brand_identification"] = {
            "passed": brand_ok,
            "value": recon_data.get("brand_name", ""),
        }
        if not brand_ok:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "brand_identification",
                "message": "无法识别品牌名称 — 品牌识别失败",
            })
        else:
            checks_passed += 1

        # 2. 页面获取
        pages = recon_data.get("pages_captured", 0)
        pages_ok = pages >= 1
        result.details["page_access"] = {
            "passed": pages_ok,
            "value": pages,
        }
        if not pages_ok:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "page_access",
                "message": f"仅获取到 {pages} 个页面，需要至少 1 个",
            })
        else:
            checks_passed += 1

        # 3. 资源可访问性
        res_total = recon_data.get("resources_total", 0)
        res_accessible = recon_data.get("resources_accessible", 0)
        res_ratio = (res_accessible / res_total) if res_total > 0 else 0
        res_ok = res_ratio >= 0.80
        result.details["resource_accessibility"] = {
            "passed": res_ok,
            "ratio": round(res_ratio, 4),
            "accessible": res_accessible,
            "total": res_total,
        }
        if not res_ok:
            result.issues.append({
                "severity": Severity.CRITICAL.value if res_ratio >= 0.60 else Severity.BLOCKER.value,
                "criterion": "resource_accessibility",
                "message": f"资源可访问率 {res_ratio:.1%}，需要 >= 80%",
            })
        else:
            checks_passed += 1

        # 4. DOM完整性
        dom_found = recon_data.get("dom_elements_found", 0)
        dom_expected = recon_data.get("dom_elements_expected", 1)
        dom_score = (dom_found / dom_expected) if dom_expected > 0 else 0
        dom_ok = dom_score >= 0.90
        result.details["dom_integrity"] = {
            "passed": dom_ok,
            "score": round(dom_score, 4),
            "found": dom_found,
            "expected": dom_expected,
        }
        if not dom_ok:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "dom_integrity",
                "message": f"DOM完整性 {dom_score:.1%}，需要 >= 90%",
            })
        else:
            checks_passed += 1

        # 5. 反爬检测
        blocked = recon_data.get("anti_scraping_blocked", False)
        anti_ok = not blocked
        result.details["anti_scraping"] = {
            "passed": anti_ok,
            "blocked": blocked,
        }
        if not anti_ok:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "anti_scraping",
                "message": "检测到反爬阻断 — 无法继续提取",
            })
        else:
            checks_passed += 1

        result.score = checks_passed / total_checks
        result.passed = result.score >= self.THRESHOLD
        result.status = GateStatus.PASSED if result.passed else GateStatus.FAILED

        if not result.passed:
            result.recommendations.append("检查目标网站的可访问性和反爬策略")
            result.recommendations.append("确认品牌身份后再重新开始侦察")

        return result


# ═══════════════════════════════════════════════════════════════
# Gate 2: Token Extraction (令牌提取门)
# ═══════════════════════════════════════════════════════════════

class TokenExtractionGate:
    """
    Gate 2 — 令牌提取门

    评估设计令牌提取的完整性和准确性：
    - 颜色令牌提取覆盖率 >=85%
    - 字体令牌提取覆盖率 >=85%
    - 间距令牌提取覆盖率 >=85%
    - 每个令牌的提取置信度 >=85%
    - W3C DTCG路径映射正确率 >=90%
    """

    GATE_NUMBER = 2
    GATE_NAME = "Token Extraction"
    THRESHOLD = 0.85

    REQUIRED_CATEGORIES = [
        "color",
        "typography",
        "spacing",
        "layout",
        "shape",
    ]

    def evaluate(self, token_data: Dict[str, Any]) -> GateResult:
        """
        评估令牌提取结果

        Args:
            token_data: {
                "tokens": [...],
                "category_coverage": {"color": 0.95, "typography": 0.90, ...},
                "avg_confidence": 0.92,
                "dtcg_mapping_accuracy": 0.88,
            }
        """
        result = GateResult(
            gate_number=self.GATE_NUMBER,
            gate_name=self.GATE_NAME,
            threshold=self.THRESHOLD,
            evaluated_at=datetime.now().isoformat(),
        )

        sub_scores = []

        # 1. 分类覆盖率
        coverage = token_data.get("category_coverage", {})
        for cat in self.REQUIRED_CATEGORIES:
            cat_cov = coverage.get(cat, 0.0)
            cat_ok = cat_cov >= self.THRESHOLD
            result.details[f"coverage_{cat}"] = {
                "passed": cat_ok,
                "value": round(cat_cov, 4),
            }
            sub_scores.append(cat_cov)
            if not cat_ok:
                result.issues.append({
                    "severity": Severity.CRITICAL.value,
                    "criterion": f"coverage_{cat}",
                    "message": f"{cat} 令牌覆盖率 {cat_cov:.1%}，需要 >= {self.THRESHOLD:.0%}",
                })

        # 2. 平均置信度
        avg_conf = token_data.get("avg_confidence", 0.0)
        conf_ok = avg_conf >= self.THRESHOLD
        result.details["avg_confidence"] = {
            "passed": conf_ok,
            "value": round(avg_conf, 4),
        }
        sub_scores.append(avg_conf)
        if not conf_ok:
            result.issues.append({
                "severity": Severity.CRITICAL.value,
                "criterion": "avg_confidence",
                "message": f"令牌平均置信度 {avg_conf:.1%}，需要 >= {self.THRESHOLD:.0%}",
            })

        # 3. DTCG映射准确率
        dtcg_acc = token_data.get("dtcg_mapping_accuracy", 0.0)
        dtcg_ok = dtcg_acc >= 0.90
        result.details["dtcg_mapping"] = {
            "passed": dtcg_ok,
            "value": round(dtcg_acc, 4),
        }
        sub_scores.append(dtcg_acc)
        if not dtcg_ok:
            result.issues.append({
                "severity": Severity.WARNING.value,
                "criterion": "dtcg_mapping",
                "message": f"DTCG路径映射准确率 {dtcg_acc:.1%}，需要 >= 90%",
            })

        # 4. Token count check
        token_count = len(token_data.get("tokens", []))
        result.details["token_count"] = token_count
        if token_count < 10:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "token_count",
                "message": f"仅提取到 {token_count} 个令牌 (< 10)，数据不足",
            })
            sub_scores.append(0.0)
        else:
            sub_scores.append(1.0)

        result.score = sum(sub_scores) / len(sub_scores)
        result.passed = result.score >= self.THRESHOLD
        result.status = GateStatus.PASSED if result.passed else GateStatus.FAILED

        if not result.passed:
            result.recommendations.append("重新运行CSS解析，检查样式表加载完整性")
            result.recommendations.append("手动补充缺失的设计令牌类别")

        return result


# ═══════════════════════════════════════════════════════════════
# Gate 3: Asset Extraction (资产提取门)
# ═══════════════════════════════════════════════════════════════

class AssetExtractionGate:
    """
    Gate 3 — 资产提取门

    阈值: >=0.60
    Logo提取为必选项
    评估:
    - Logo检测与提取
    - 图片资产元数据提取
    - 图标资产识别
    - 字体文件检测
    - Favicon提取
    """

    GATE_NUMBER = 3
    GATE_NAME = "Asset Extraction"
    THRESHOLD = 0.60

    LOGO_REQUIRED = True

    def evaluate(self, asset_data: Dict[str, Any]) -> GateResult:
        """
        评估资产提取结果

        Args:
            asset_data: {
                "logo": {"found": True, "url": "...", "format": "svg"},
                "images": [...],
                "icons": [...],
                "fonts": [...],
                "favicon": {"found": True},
            }
        """
        result = GateResult(
            gate_number=self.GATE_NUMBER,
            gate_name=self.GATE_NAME,
            threshold=self.THRESHOLD,
            evaluated_at=datetime.now().isoformat(),
        )

        sub_scores = []

        # 1. Logo (BLOCKING)
        logo = asset_data.get("logo", {})
        logo_found = logo.get("found", False)
        result.details["logo"] = {
            "passed": logo_found,
            "found": logo_found,
            "url": logo.get("url", ""),
            "format": logo.get("format", ""),
        }
        if self.LOGO_REQUIRED and not logo_found:
            result.issues.append({
                "severity": Severity.BLOCKER.value,
                "criterion": "logo_required",
                "message": "未检测到品牌Logo — 这是必选项",
            })
            sub_scores.append(0.0)
        else:
            sub_scores.append(1.0 if logo_found else 0.5)

        # 2. 图片提取率
        images = asset_data.get("images", [])
        image_types = set(img.get("type", "") for img in images if img.get("type"))
        image_coverage = len(image_types) / max(len({"hero", "product", "lifestyle", "detail", "icon", "bg"}), 1)
        result.details["images"] = {
            "count": len(images),
            "types_found": list(image_types),
            "coverage": round(image_coverage, 4),
        }
        sub_scores.append(min(image_coverage, 1.0))

        # 3. 图标提取
        icons = asset_data.get("icons", [])
        icon_score = min(len(icons) / 5, 1.0) if icons else 0.3  # at least partial credit
        result.details["icons"] = {
            "count": len(icons),
            "score": round(icon_score, 4),
        }
        sub_scores.append(icon_score)

        # 4. 字体检测
        fonts = asset_data.get("fonts", [])
        font_score = 1.0 if fonts else 0.0
        result.details["fonts"] = {
            "count": len(fonts),
            "families": [f.get("family", "") for f in fonts[:5]],
        }
        sub_scores.append(font_score)

        # 5. Favicon
        favicon = asset_data.get("favicon", {})
        fav_found = favicon.get("found", False)
        result.details["favicon"] = {
            "found": fav_found,
        }
        sub_scores.append(0.2 if fav_found else 0.0)

        result.score = sum(sub_scores) / len(sub_scores)
        result.passed = result.score >= self.THRESHOLD

        # If logo not found, force fail even if score passes threshold
        if self.LOGO_REQUIRED and not logo_found:
            result.passed = False
            result.status = GateStatus.FAILED
        else:
            result.status = GateStatus.PASSED if result.passed else GateStatus.FAILED

        if not result.passed:
            if not logo_found:
                result.recommendations.append("手动提供Logo URL或从页面header中提取")
            result.recommendations.append("增加页面抓取范围以获取更多资产")

        return result


# ═══════════════════════════════════════════════════════════════
# Gate 4: Synthesis & Interpretation (合成解释门)
# ═══════════════════════════════════════════════════════════════

class SynthesisGate:
    """
    Gate 4 — 合成与解释门

    阈值: >=0.80
    评估AI对品牌DNA的深层理解和综合解释能力:
    - 设计系统一致性评分
    - 品牌风格准确度
    - WHY追溯完整性
    - ACR (Artistic Content Resonance) 得分
    - 设计原则推导准确度
    """

    GATE_NUMBER = 4
    GATE_NAME = "Synthesis & Interpretation"
    THRESHOLD = 0.80

    def evaluate(self, synthesis_data: Dict[str, Any]) -> GateResult:
        """
        评估合成解释结果

        Args:
            synthesis_data: {
                "design_system_consistency": 0.88,
                "style_accuracy": 0.85,
                "why_trace_completeness": 0.90,
                "acr_score": 0.82,
                "principle_derivation_accuracy": 0.87,
            }
        """
        result = GateResult(
            gate_number=self.GATE_NUMBER,
            gate_name=self.GATE_NAME,
            threshold=self.THRESHOLD,
            evaluated_at=datetime.now().isoformat(),
        )

        metrics = [
            ("design_system_consistency", "设计系统一致性", 0.85),
            ("style_accuracy", "品牌风格准确度", 0.80),
            ("why_trace_completeness", "WHY追溯完整性", 0.80),
            ("acr_score", "ACR艺术内容共振", 0.75),
            ("principle_derivation_accuracy", "设计原则推导", 0.80),
        ]

        sub_scores = []
        for key, name, sub_threshold in metrics:
            value = synthesis_data.get(key, 0.0)
            sub_ok = value >= sub_threshold
            result.details[key] = {
                "passed": sub_ok,
                "value": round(value, 4),
                "sub_threshold": sub_threshold,
            }
            sub_scores.append(value)
            if not sub_ok:
                severity = Severity.CRITICAL if value < sub_threshold - 0.10 else Severity.WARNING
                result.issues.append({
                    "severity": severity.value,
                    "criterion": key,
                    "message": f"{name}: {value:.1%} < {sub_threshold:.0%}",
                })

        result.score = sum(sub_scores) / len(sub_scores)
        result.passed = result.score >= self.THRESHOLD
        result.status = GateStatus.PASSED if result.passed else GateStatus.FAILED

        if not result.passed:
            result.recommendations.append("增加参考页面以提升设计一致性评分")
            result.recommendations.append("加强AI对品牌美学和设计哲学的深度分析")

        return result


# ═══════════════════════════════════════════════════════════════
# Gate 5: Visual Replication (视觉复现门)
# ═══════════════════════════════════════════════════════════════

class VisualReplicationGate:
    """
    Gate 5 — 视觉复现门

    阈值: >=0.83 (三层平均)
    三层评估:
    1. Pixel-level accuracy (像素级准确度)
    2. Structural fidelity (结构保真度)
    3. Traceability (溯源可验证性)
    """

    GATE_NUMBER = 5
    GATE_NAME = "Visual Replication"
    THRESHOLD = 0.83

    def evaluate(self, replication_data: Dict[str, Any]) -> GateResult:
        """
        评估视觉复现结果

        Args:
            replication_data: {
                "pixel_accuracy": 0.85,
                "structural_fidelity": 0.90,
                "traceability": 0.80,
                "generated_output": "path/to/output",
                "reference_url": "...",
            }
        """
        result = GateResult(
            gate_number=self.GATE_NUMBER,
            gate_name=self.GATE_NAME,
            threshold=self.THRESHOLD,
            evaluated_at=datetime.now().isoformat(),
        )

        layers = [
            ("pixel_accuracy", "像素级准确度", 0.80, Severity.CRITICAL),
            ("structural_fidelity", "结构保真度", 0.85, Severity.CRITICAL),
            ("traceability", "溯源可验证性", 0.80, Severity.WARNING),
        ]

        layer_scores = []
        for key, name, layer_threshold, severity in layers:
            value = replication_data.get(key, 0.0)
            layer_ok = value >= layer_threshold
            result.details[key] = {
                "passed": layer_ok,
                "value": round(value, 4),
                "layer_threshold": layer_threshold,
            }
            layer_scores.append(value)
            if not layer_ok:
                result.issues.append({
                    "severity": severity.value,
                    "criterion": key,
                    "message": f"{name}: {value:.1%} < {layer_threshold:.0%}",
                })

        # 三层加权平均
        weights = [0.35, 0.40, 0.25]  # structural fidelity most important
        result.score = sum(s * w for s, w in zip(layer_scores, weights))
        result.details["weighted_average"] = round(result.score, 4)

        result.passed = result.score >= self.THRESHOLD
        result.status = GateStatus.PASSED if result.passed else GateStatus.FAILED

        if not result.passed:
            result.recommendations.append("调整生成的视觉输出以提高像素级准确度")
            result.recommendations.append("检查结构保真度，确保布局与源站一致")
            result.recommendations.append("完善溯源链路，确保每个设计决策可追溯到原始参数")

        return result


# ═══════════════════════════════════════════════════════════════
# 完整门禁管线
# ═══════════════════════════════════════════════════════════════

class QualityGatePipeline:
    """五道质量门禁管线 — 顺序执行，任一失败即停止"""

    def __init__(self, db: Optional[Any] = None):
        """
        Args:
            db: DNADatabase instance for persisting results
        """
        self.db = db
        self.gates = {
            1: ReconnaissanceGate(),
            2: TokenExtractionGate(),
            3: AssetExtractionGate(),
            4: SynthesisGate(),
            5: VisualReplicationGate(),
        }

    def evaluate(self, brand_name: str, gate_data: Dict[int, Dict[str, Any]],
                 stop_on_failure: bool = True) -> QualityPipelineResult:
        """
        执行完整门禁管线

        Args:
            brand_name: 品牌名称
            gate_data: {1: {...}, 2: {...}, 3: {...}, 4: {...}, 5: {...}}
            stop_on_failure: 是否在第一次失败时停止

        Returns:
            QualityPipelineResult
        """
        start_time = datetime.now()
        pipeline_result = QualityPipelineResult(brand_name=brand_name, overall_passed=True)

        for gate_number in range(1, 6):
            gate = self.gates[gate_number]
            data = gate_data.get(gate_number, {})

            result = gate.evaluate(data)
            pipeline_result.results[gate_number] = result

            if self.db:
                self._persist_gate_result(brand_name, result)

            if not result.passed:
                pipeline_result.overall_passed = False
                pipeline_result.failed_at_gate = gate_number
                if stop_on_failure:
                    # Mark remaining as skipped
                    for gn in range(gate_number + 1, 6):
                        skipped = GateResult(
                            gate_number=gn,
                            gate_name=self.gates[gn].GATE_NAME,
                            status=GateStatus.SKIPPED,
                            evaluated_at=datetime.now().isoformat(),
                        )
                        pipeline_result.results[gn] = skipped
                    break

        # Calculate total score (average of completed gates)
        completed = [r.score for r in pipeline_result.results.values()
                     if r.status != GateStatus.SKIPPED]
        pipeline_result.total_score = sum(completed) / len(completed) if completed else 0.0
        pipeline_result.execution_time_seconds = (datetime.now() - start_time).total_seconds()

        # Build summary
        if pipeline_result.overall_passed:
            pipeline_result.summary = f"✅ {brand_name}: 通过全部5道质量门禁 (avg={pipeline_result.total_score:.2%})"
        else:
            failed_gate = pipeline_result.failed_at_gate
            gate_name = self.gates[failed_gate].GATE_NAME if failed_gate else "Unknown"
            pipeline_result.summary = f"❌ {brand_name}: 未通过 Gate {failed_gate} ({gate_name})"

        return pipeline_result

    def _persist_gate_result(self, brand_name: str, result: GateResult):
        """将门禁结果持久化到数据库"""
        if not self.db:
            return
        try:
            self.db.record_gate_result(
                brand_id=brand_name,
                gate_number=result.gate_number,
                score=result.score,
                threshold=result.threshold,
                blocking_criteria=[
                    i["criterion"] for i in result.issues
                    if i["severity"] == Severity.BLOCKER.value
                ],
                details=result.details,
            )
        except Exception:
            pass  # Don't let persistence failure block the pipeline

    def get_gate_by_number(self, gate_number: int):
        """获取指定门禁实例"""
        return self.gates.get(gate_number)


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def evaluate_brand_quality(brand_name: str, gate_data: Dict[int, Dict[str, Any]],
                           db: Optional[Any] = None) -> QualityPipelineResult:
    """一键评估品牌质量门禁"""
    pipeline = QualityGatePipeline(db)
    return pipeline.evaluate(brand_name, gate_data)

def gate_data_template() -> Dict[int, Dict[str, Any]]:
    """返回标准门禁数据模板"""
    return {
        1: {  # Reconnaissance
            "brand_name": "",
            "pages_captured": 0,
            "resources_total": 0,
            "resources_accessible": 0,
            "dom_elements_found": 0,
            "dom_elements_expected": 0,
            "anti_scraping_blocked": False,
        },
        2: {  # Token Extraction
            "tokens": [],
            "category_coverage": {"color": 0.0, "typography": 0.0, "spacing": 0.0, "layout": 0.0, "shape": 0.0},
            "avg_confidence": 0.0,
            "dtcg_mapping_accuracy": 0.0,
        },
        3: {  # Asset Extraction
            "logo": {"found": False, "url": "", "format": ""},
            "images": [],
            "icons": [],
            "fonts": [],
            "favicon": {"found": False},
        },
        4: {  # Synthesis
            "design_system_consistency": 0.0,
            "style_accuracy": 0.0,
            "why_trace_completeness": 0.0,
            "acr_score": 0.0,
            "principle_derivation_accuracy": 0.0,
        },
        5: {  # Visual Replication
            "pixel_accuracy": 0.0,
            "structural_fidelity": 0.0,
            "traceability": 0.0,
            "generated_output": "",
            "reference_url": "",
        },
    }
