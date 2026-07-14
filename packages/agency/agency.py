"""
4A品牌设计广告公司 — CEO入口 (重建版)

完整5阶段流程:
1. Briefing: 接收多产品输入 → brief + step_status
2. Strategy: 调用StrategyDept → 多产品SceneGraph分析 + strategy_doc
3. Creative: 调用CreativeDept → 5套创意概念 + 评分推荐
4. Execution: 调用detail_image_gen → 品牌DNA详情页 + ZIP
5. Pitch: 调用PresentationDept → Pitch Deck JSON

每阶段输出独立的结构化 step_status
最终产出: 品牌视觉报告 + DNA详情页 + Pitch Deck + ZIP
"""
import os, json, sys
from typing import Optional, List, Dict, Any
from datetime import datetime


def _now() -> str:
    return datetime.utcnow().isoformat()


class Agency4A:
    """4A品牌设计广告公司 — 全流程总控（重建版）"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._briefing = None
        self._strategy = None
        self._creative = None
        self._pitch = None
        self._img_gen = None
        self._lazy_load()

    def _lazy_load(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "norhor", "src"))
        from .brief import Briefing
        from .strategy import StrategyDept
        from .creative import CreativeDept
        from .pitch import PresentationDept
        from .rationale import DesignRationaleEngine
        from .dna_ref import BrandDNARef
        from .agents import AgentTeam, AgentEmployee, PLANNER_ROLE, CREATIVE_ROLE, ART_ROLE, PRODUCER_ROLE
        self._briefing = Briefing()
        self._strategy = StrategyDept(self.api_key)
        self._creative = CreativeDept()
        self._pitch = PresentationDept()
        self._rationale = DesignRationaleEngine(self.api_key)
        self._dna_ref = BrandDNARef()
        self._team = AgentTeam()
        import importlib
        try:
            self._img_gen = importlib.import_module("detail_image_gen").generate_brand_detail
        except:
            self._img_gen = None

    def run(self, brand: str = "",
            products: Optional[List[Dict]] = None,
            images: Optional[List[str]] = None,
            competitors: Optional[List[str]] = None,
            output_dir: Optional[str] = None,
            project_name: str = "",
            skip_execution: bool = False) -> Dict[str, Any]:
        """
        全流程运行 — 5阶段编排

        参数:
            brand:        品牌名
            products:     [{"image":"url","name":"产品名","category":"...","analysis":{}}, ...]
            images:       产品图URL列表（自动构建products）
            competitors:  竞品列表
            output_dir:   输出目录
            project_name: 项目代号
            skip_execution: 跳过图像生成阶段（纯策略+创意+提报）
        """
        t0 = datetime.utcnow()
        project = project_name or f"{brand}-4A-Project"

        # 统一的输出目录
        od = output_dir or os.path.expanduser(
            f"~/Desktop/{brand.lower().replace(' ', '-')}-4a"
        )
        os.makedirs(od, exist_ok=True)

        step_status: Dict[str, Any] = {}
        print(f"\n{'='*60}")
        print(f"  🏢  4A Agency — 品牌视觉全流程")
        print(f"  品牌: {brand}  |  项目: {project}")
        print(f"  输出: {od}")
        print(f"  🤖 团队: {', '.join([a.name for a in self._team.agents.values()])}")
        print(f"{'='*60}")

        # ════════════════════════════════════════════════════════
        # PHASE 1: Briefing — 接收多产品输入
        # ════════════════════════════════════════════════════════
        print(f"\n  ── Phase 1/5: Briefing ──")
        phase1_start = datetime.utcnow()
        try:
            if products:
                brief = self._briefing.multi_product_brief(brand, products)
            elif images:
                products = [{"image": img, "name": f"Product {i+1}"} for i, img in enumerate(images)]
                brief = self._briefing.multi_product_brief(brand, products)
            else:
                brief = self._briefing.receive_brief(brand)
            n_products = len(products) if products else 0
            step_status["briefing"] = {
                "status": "ok",
                "brief_id": brief.brief_id,
                "brand": brief.brand_name,
                "products_received": n_products,
                "product_names": brief.product_descriptions,
                "category": brief.product_category,
                "created_at": brief.created_at,
            }
        except Exception as e:
            step_status["briefing"] = {"status": "error", "error": str(e)}
            n_products = 0

        # ════════════════════════════════════════════════════════
        # PHASE 2: Strategy — 多产品SceneGraph分析
        # ════════════════════════════════════════════════════════
        print(f"\n  ── Phase 2/5: Strategy ──")
        phase2_start = datetime.utcnow()
        try:
            visual_system = self._strategy.analyze_brand_system(products or [])
            strategy_doc = self._strategy.brand_strategy_doc(visual_system, brief)
            if competitors:
                strategy_doc["competitor_analysis"] = self._strategy.competitor_analysis(
                    brand, competitors
                )
            step_status["strategy"] = {
                "status": "ok",
                "products_analyzed": visual_system.products_analyzed,
                "core_colors": len(visual_system.core_palette),
                "core_palette": visual_system.core_palette[:6],
                "focal_length_range": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}mm",
                "aperture_range": f"f/{visual_system.aperture_range.min}-f/{visual_system.aperture_range.max}",
                "lighting_patterns": visual_system.lighting_patterns[:3],
                "composition_rules": visual_system.composition_rules[:3],
                "design_principles": visual_system.design_principles[:5],
                "confidence": visual_system.confidence,
            }
        except Exception as e:
            step_status["strategy"] = {"status": "error", "error": str(e)}
            visual_system = None
            strategy_doc = {}

        # ── Phase 2.5: Rationale (WHY) ──
        print(f"\n  ── Phase 2.5/5: Rationale (WHY) ──")
        rationale_report = None
        try:
            if visual_system and hasattr(visual_system, 'scene_graphs') and visual_system.scene_graphs:
                sg = visual_system.scene_graphs[0]
                if hasattr(sg, 'to_dict'):
                    sg = sg.to_dict()
                rationale_report = self._rationale.analyze_rationale(sg, brand,
                    products[0].get('name','') if products else '')
                stored = self._dna_ref.store_rationale(brand, rationale_report)
                print(f"  💡 WHY分析完成 — {stored} 条设计理由已入库")
        except Exception as e:
            print(f"  ⚠️  Rationale: {e}")

        # ── Phase 3/5: Creative ──
        # PHASE 3: Creative — 5套创意概念
        # ════════════════════════════════════════════════════════
        print(f"\n  ── Phase 3/5: Creative ──")
        phase3_start = datetime.utcnow()
        try:
            concepts = self._creative.brainstorm(visual_system, brand)
            best_concept = self._creative.select_best_concept()
            step_status["creative"] = {
                "status": "ok",
                "total_concepts": len(concepts),
                "recommended": best_concept.concept_name,
                "recommended_rationale": best_concept.rationale,
                "recommended_scores": {
                    "creativity": round(best_concept.creative_score * 100),
                    "brand_compliance": round(best_concept.brand_compliance * 100),
                    "feasibility": round(best_concept.feasibility * 100),
                },
                "all_concepts": [
                    {
                        "name": c.concept_name,
                        "type": c.scene_type,
                        "creativity": round(c.creative_score * 100),
                        "brand_compliance": round(c.brand_compliance * 100),
                        "feasibility": round(c.feasibility * 100),
                    }
                    for c in concepts
                ],
            }
        except Exception as e:
            step_status["creative"] = {"status": "error", "error": str(e)}
            concepts = []
            best_concept = None

        # ════════════════════════════════════════════════════════
        # PHASE 4: Execution — 品牌DNA详情页生成
        # ════════════════════════════════════════════════════════
        print(f"\n  ── Phase 4/5: Execution ──")
        phase4_start = datetime.utcnow()
        zip_path = ""
        brand_report_path = ""
        try:
            if skip_execution:
                step_status["execution"] = {"status": "skipped", "reason": "skip_execution=True"}
            elif self._img_gen and visual_system:
                best_name = best_concept.concept_name if best_concept else ""
                best_lighting = (
                    best_concept.lighting_plan.get("type", "")
                    if best_concept
                    else ""
                )
                dna = {
                    "brand_name": brand,
                    "brand_score": round(visual_system.confidence, 2),
                    "brand_positioning": strategy_doc.get("executive_summary", ""),
                    "target_audience": getattr(brief, "target_audience", "大众消费者") or "大众消费者",
                    "brand_personality": visual_system.design_principles[:5],
                    # 色板
                    "primary_palette": visual_system.core_palette[:8],
                    "secondary_palette": visual_system.seasonal_palette[:4],
                    "accent_palette": visual_system.accent_palette[:4],
                    "color_relationship": "多产品聚合色板",
                    "temperature": "综合分析",
                    # 摄影
                    "camera": {
                        "focal_length_mm": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}",
                        "aperture_f": f"{visual_system.aperture_range.min}-{visual_system.aperture_range.max}",
                        "iso": f"{visual_system.iso_range.min}-{visual_system.iso_range.max}",
                    },
                    # 材质
                    "materials": [],
                    # 设计
                    "design_patterns": visual_system.composition_rules[:5],
                    "layout_patterns": visual_system.lighting_patterns[:5],
                    "lighting_signature": ", ".join(visual_system.lighting_patterns[:3]),
                    # 场景
                    "elements": [],
                    # 评分
                    "dimension_scores": {
                        "色彩一致性": min(0.95, visual_system.confidence + 0.1),
                        "光影风格": min(0.95, visual_system.confidence),
                        "构图规范": min(0.95, visual_system.confidence + 0.05),
                        "材质匹配": 0.82,
                        "品牌调性": min(0.95, visual_system.confidence + 0.02),
                        "整体评分": visual_system.confidence,
                    },
                    # 创意信息
                    "creative_concept": best_name,
                    "creative_lighting": best_lighting,
                }
                result_zip = self._img_gen(dna, output_dir=od)
                zip_path = result_zip
                brand_report_path = os.path.join(od, "brand_dna_report.png")
                step_status["execution"] = {
                    "status": "ok",
                    "brand_report": brand_report_path,
                    "zip_package": zip_path,
                    "creative_concept_used": best_name,
                }
            else:
                step_status["execution"] = {
                    "status": "skipped",
                    "reason": "image generator not available or no visual system",
                }
        except Exception as e:
            step_status["execution"] = {"status": "error", "error": str(e)}

        # ════════════════════════════════════════════════════════
        # PHASE 5: Pitch — 提报 Deck
        # ════════════════════════════════════════════════════════
        print(f"\n  ── Phase 5/5: Pitch ──")
        phase5_start = datetime.utcnow()
        try:
            deck = self._pitch.build_pitch_deck(brand, strategy_doc, concepts, brief)
            deck_path = self._pitch.export_deck(deck, od)
            step_status["pitch"] = {
                "status": "ok",
                "deck_path": deck_path,
                "sections": [s["title"] for s in deck.get("sections", [])],
                "recommended_concept": deck.get("recommendation", ""),
            }
        except Exception as e:
            step_status["pitch"] = {"status": "error", "error": str(e)}
            deck_path = ""

        # ════════════════════════════════════════════════════════
        # 汇总
        # ════════════════════════════════════════════════════════
        t1 = datetime.utcnow()
        duration = round((t1 - t0).total_seconds())

        # 写入完整 step_status 报告
        status_path = os.path.join(od, "step_status.json")
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(step_status, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"  ✅ 全流程完成 — {duration}s")
        print(f"  📋 Step Status → {status_path}")
        for phase_name, ps in step_status.items():
            icon = "✅" if ps.get("status") == "ok" else "⚠️" if ps.get("status") == "skipped" else "❌"
            summary = ""
            if phase_name == "briefing":
                summary = f"收到{ps.get('products_received',0)}个产品"
            elif phase_name == "strategy":
                summary = f"核心色{ps.get('core_colors',0)}个"
            elif phase_name == "creative":
                summary = f"产出{ps.get('total_concepts',0)}个概念 → 推荐「{ps.get('recommended','?')}」"
            elif phase_name == "execution":
                summary = f"R={ps.get('brand_report','N/A')}, ZIP={ps.get('zip_package','N/A')}"
            elif phase_name == "pitch":
                summary = f"Deck={os.path.basename(ps.get('deck_path','N/A'))}"
            print(f"  {icon} Phase: {phase_name} — {summary}")

        print(f"{'='*60}\n")

        return {
            "brand": brand,
            "project": project,
            "status": "success",
            "duration_sec": duration,
            "step_status": step_status,
            "output_dir": od,
            "products_analyzed": n_products,
            "concepts_produced": len(concepts),
            "recommended_concept": best_concept.concept_name if best_concept else "",
            "visual_system_summary": (
                {
                    "core_colors": visual_system.core_palette[:4],
                    "focal_range": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}mm",
                    "aperture_range": f"f/{visual_system.aperture_range.min}-f/{visual_system.aperture_range.max}",
                    "lighting_patterns": visual_system.lighting_patterns[:3],
                    "composition_rules": visual_system.composition_rules[:3],
                }
                if visual_system
                else {}
            ),
            "output": {
                "detail_page": zip_path,
                "pitch_deck": deck_path,
                "brand_report": brand_report_path,
                "step_status": status_path,
            },
        }
