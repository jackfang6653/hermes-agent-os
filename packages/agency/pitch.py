"""
提报系统 — 专业提案准备 (Presentation Phase)

产出: 策略文档 + 创意方案 + 执行排期
"""
import json, os
from typing import Optional, List, Dict, Any
from datetime import datetime


class PresentationDept:
    """提报部 — 制作提案文件"""

    def build_pitch_deck(self, brand: str, strategy_doc: Dict, concepts: List,
                         brief) -> Dict[str, Any]:
        """制作完整提报文档"""
        print(f"  📑 [Pitch] 制作提报文档 — {brand}")

        # 选择最优概念
        best = max(concepts, key=lambda c: c.creative_score*0.3 + c.brand_compliance*0.4 + c.feasibility*0.3) if concepts else None

        deck = {
            "brand": brand,
            "pitch_date": datetime.utcnow().isoformat(),
            "sections": [
                {
                    "title": "1. 策略洞察 Strategy",
                    "content": {
                        "executive_summary": strategy_doc.get("executive_summary",""),
                        "visual_system": strategy_doc.get("visual_system",{}),
                        "key_insight": strategy_doc.get("key_insight",""),
                    }
                },
                {
                    "title": "2. 创意概念 Creative",
                    "content": {
                        "total_concepts": len(concepts),
                        "recommended": {
                            "name": best.concept_name if best else "",
                            "rationale": best.rationale if best else "",
                            "scores": {
                                "creativity": round(best.creative_score*100) if best else 0,
                                "brand_compliance": round(best.brand_compliance*100) if best else 0,
                                "feasibility": round(best.feasibility*100) if best else 0,
                            }
                        } if best else {},
                        "all_concepts": [
                            {"name": c.concept_name, "type": c.scene_type,
                             "score": round(c.creative_score*100)}
                            for c in concepts
                        ],
                    }
                },
                {
                    "title": "3. 执行方案 Execution",
                    "content": {
                        "photography_plan": "详见各概念灯光方案",
                        "post_production": "专业调色+精修",
                        "deliverables": ["长图详情页","分图模块","品牌DNA报告","ZIP包"],
                    }
                },
                {
                    "title": "4. 排期与预算 Timeline & Budget",
                    "content": {
                        "estimated_timeline": "5-8个工作日",
                        "phases": ["研究(1d)","创意(1d)","拍摄/生成(2d)","后期(1d)","提报(1d)"],
                    }
                },
            ],
            "recommendation": best.concept_name if best else "",
        }
        return deck

    def export_deck(self, deck: Dict, output_dir: str) -> str:
        """导出提报文档为JSON+摘要"""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "pitch_deck.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
        
        # 摘要
        print(f"\n  📋 提报摘要")
        print(f"  {'='*40}")
        best = deck.get("sections",[{}])[1].get("content",{}).get("recommended",{})
        if best:
            print(f"  推荐方案: {best.get('name','')}")
            print(f"  创意理由: {best.get('rationale','')[:60]}")
        print(f"  产出物: {deck.get('sections',[{}])[2].get('content',{}).get('deliverables',[])}")
        print(f"  排期: {deck.get('sections',[{}])[3].get('content',{}).get('estimated_timeline','')}")
        
        print(f"\n  ✅ Pitch Deck: {path}")
        return path
