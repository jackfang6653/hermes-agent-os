"""
4A品牌设计广告公司 — CEO入口

完整5阶段流程:
1. Briefing: 接领需求 → 多产品简报
2. Strategy: 多产品分析 → 品牌视觉系统(参数范围)
3. Creative: 多概念创意 → 评分 → 推荐
4. Execution: 生成品牌DNA详情页
5. Pitch: 提报文档

用法:
    agency = Agency4A()
    result = agency.run(
        brand="IKEA",
        products=[{"image":"...","name":"..."}, ...]  # 多个产品
    )
"""
import os, json, sys
from typing import Optional, List, Dict, Any
from datetime import datetime


class Agency4A:
    """4A品牌设计广告公司 — 全流程总控"""

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
        import importlib
        self._briefing = Briefing()
        self._strategy = StrategyDept(self.api_key)
        self._creative = CreativeDept()
        self._pitch = PresentationDept()
        try:
            self._img_gen = importlib.import_module("detail_image_gen").generate_brand_detail
        except:
            self._img_gen = None

    def run(self, brand: str, products: Optional[List[Dict]] = None, 
            images: Optional[List[str]] = None,
            competitors: Optional[List[str]] = None,
            output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        全流程运行
        
        参数:
            brand: 品牌名
            products: [{"image":"url","name":"产品名","analysis":{}}, ...]  多个产品
            images: 产品图URL列表（自动构建products）
            competitors: 竞品列表
            output_dir: 输出目录
        """
        t0 = datetime.utcnow()

        # ── Phase 1: Briefing ──
        print(f"\n  🏢 4A Agency — 品牌设计项目")
        print(f"  {'='*50}")
        
        if products:
            brief = self._briefing.multi_product_brief(brand, products)
        elif images:
            products = [{"image": img, "name": f"Product {i+1}"} for i, img in enumerate(images)]
            brief = self._briefing.multi_product_brief(brand, products)
        else:
            brief = self._briefing.receive_brief(brand)

        n_products = len(products) if products else 0
        step_status = {}

        # ── Phase 2: Strategy ──
        print(f"\n  📊 [Phase 1/4] 策略研究 — 分析{n_products}个产品")
        visual_system = self._strategy.analyze_brand_system(products or [])
        step_status["strategy"] = {
            "products_analyzed": visual_system.products_analyzed,
            "core_colors": len(visual_system.core_palette),
            "focal_range": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}mm",
        }
        
        strategy_doc = self._strategy.brand_strategy_doc(visual_system, brief)
        
        # 竞品分析
        if competitors:
            comp = self._strategy.competitor_analysis(brand, competitors)
            strategy_doc["competitor_analysis"] = comp

        # ── Phase 3: Creative ──
        print(f"\n  🎨 [Phase 2/4] 创意发想 — 多概念方案")
        concepts = self._creative.brainstorm(strategy_doc, brand)
        best_concept = self._creative.select_best_concept()
        step_status["creative"] = {
            "total_concepts": len(concepts),
            "best": best_concept.concept_name,
        }

        # ── Phase 4: Execution ──
        print(f"\n  🖼️ [Phase 3/4] 执行产出 — 品牌DNA详情页")
        zip_path = ""
        if self._img_gen and visual_system:
            try:
                dna = {
                    "brand_name": brand,
                    "brand_score": 0.85,
                    "primary_palette": visual_system.core_palette[:8],
                    "secondary_palette": visual_system.seasonal_palette[:4],
                    "color_relationship": "多产品聚合色板",
                    "temperature": "综合分析",
                    "materials": [],
                    "camera": {
                        "focal_length_mm": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}",
                        "aperture_f": f"{visual_system.aperture_range.min}-{visual_system.aperture_range.max}",
                    },
                    "design_patterns": visual_system.composition_rules[:5],
                    "layout_patterns": visual_system.lighting_patterns[:5],
                    "dimension_scores": {"色彩一致性":0.85,"光影风格":0.80,"构图规范":0.88},
                    "elements": [],
                    "lighting_signature": ", ".join(visual_system.lighting_patterns[:3]),
                    "brand_positioning": strategy_doc.get("executive_summary",""),
                    "target_audience": brief.target_audience,
                    "brand_personality": visual_system.design_principles[:5],
                }
                od = output_dir or os.path.expanduser(f"~/Desktop/{brand.lower().replace(' ','_')}-4a")
                zip_path = self._img_gen(dna, output_dir=od)
                step_status["execution"] = {"output": zip_path}
            except Exception as e:
                step_status["execution"] = {"error": str(e)}

        # ── Phase 5: Pitch ──
        print(f"\n  📑 [Phase 4/4] 提报准备 — Pitch Deck")
        deck = self._pitch.build_pitch_deck(brand, strategy_doc, concepts, brief)
        pd = output_dir or os.path.expanduser(f"~/Desktop/{brand.lower().replace(' ','_')}-4a")
        deck_path = self._pitch.export_deck(deck, pd)
        step_status["pitch"] = {"deck": deck_path}

        t1 = datetime.utcnow()
        duration = (t1 - t0).total_seconds()

        print(f"\n  ✅ 全流程完成 — {(t1-t0).total_seconds():.0f}s")
        print(f"  {'='*50}")

        return {
            "brand": brand,
            "status": "success",
            "duration_sec": round(duration),
            "steps": step_status,
            "products_analyzed": n_products,
            "concepts_produced": len(concepts),
            "recommended_concept": best_concept.concept_name if concepts else "",
            "visual_system_summary": {
                "core_colors": visual_system.core_palette[:4],
                "focal_range": f"{visual_system.focal_length_range.min}-{visual_system.focal_length_range.max}mm",
                "aperture_range": f"f/{visual_system.aperture_range.min}-f/{visual_system.aperture_range.max}",
                "lighting_patterns": visual_system.lighting_patterns[:3],
                "composition_rules": visual_system.composition_rules[:3],
            },
            "output": {
                "detail_page": zip_path,
                "pitch_deck": deck_path,
            }
        }
