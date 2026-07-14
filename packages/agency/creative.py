"""
创意部 — 多概念发想与执行落地 (Creative Phase)

核心: 不是输出一个方案，而是多套创意概念
每个概念有完整参数方案
"""
import os, json, sys, time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class CreativeConcept:
    """一个创意概念 — 包含完整参数方案"""
    concept_name: str = ""
    concept_description: str = ""
    rationale: str = ""         # 创意理由
        
    # 场景方案
    scene_type: str = ""
    scene_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 灯光方案
    lighting_plan: Dict[str, Any] = field(default_factory=dict)
    
    # 颜色方案
    color_variant: List[str] = field(default_factory=list)  # 该概念下的调色变体
    
    # 排版方案
    layout_style: str = ""
    
    # 输出规格
    output_specs: Dict[str, Any] = field(default_factory=dict)
    
    # AI生成Prompt
    generation_prompt: str = ""
    
    # 评分
    creative_score: float = 0.0  # 创意新颖度
    brand_compliance: float = 0.0  # 品牌合规度
    feasibility: float = 0.0    # 可执行性


class CreativeDept:
    """创意部 — 多概念创意生成"""

    def __init__(self):
        self._concepts: List[CreativeConcept] = []

    def brainstorm(self, strategy_doc: Dict, brand_name: str) -> List[CreativeConcept]:
        """头脑风暴 — 基于策略产出多套创意概念"""
        print(f"  🎨 [Creative] 创意发想 — {brand_name}")
        
        # 基于策略文档生成多套方案
        concepts = [
            self._lifestyle_concept(brand_name, strategy_doc),
            self._studio_concept(brand_name, strategy_doc),
            self._editorial_concept(brand_name, strategy_doc),
            self._minimal_concept(brand_name, strategy_doc),
            self._seasonal_concept(brand_name, strategy_doc),
        ]
        
        concepts = [c for c in concepts if c is not None]
        
        # 评分
        for c in concepts:
            c.creative_score = self._score_creativity(c)
            c.brand_compliance = self._score_brand_compliance(c, strategy_doc)
            c.feasibility = self._score_feasibility(c)
        
        self._concepts = concepts
        print(f"    ✅ 产出 {len(concepts)} 个创意概念")
        for c in concepts:
            print(f"      {c.concept_name}: 创意{c.creative_score:.0%} 品牌{c.brand_compliance:.0%} 可行{c.feasibility:.0%}")
        return concepts

    def _lifestyle_concept(self, brand, sd) -> CreativeConcept:
        """生活场景概念"""
        scenes = sd.get("visual_system", {}).get("lighting_patterns", ["自然光"])
        return CreativeConcept(
            concept_name="生活场景 Lifestyle",
            concept_description="将产品置于真实生活场景中，营造使用氛围",
            rationale="让消费者想象产品在自己的生活中的样子，提升购买欲望",
            scene_type="lifestyle",
            scene_parameters={"background":"室内生活场景","props":"搭配配饰","mood":"温馨自然"},
            lighting_plan={"type":"混合光","key":"自然光+补光","temperature":"4500-5500K"},
            color_variant=["暖调自然","冷调清新"],
            layout_style="场景融入式",
            generation_prompt=f"Product in a real {scene_type} setting, natural lifestyle composition",
        )

    def _studio_concept(self, brand, sd) -> CreativeConcept:
        return CreativeConcept(
            concept_name="影棚精拍 Studio",
            concept_description="纯白/纯色背景，聚焦产品细节",
            rationale="电商标准拍法，突出产品本身质感和细节",
            scene_type="studio",
            scene_parameters={"background":"纯白无缝纸","props":"无","mood":"专业清晰"},
            lighting_plan={"type":"影棚灯","key":"柔光箱+反光板","temperature":"5500K"},
            color_variant=["纯净白底","浅灰底","浅暖底"],
            layout_style="产品居中特写",
            generation_prompt="Studio product photography, white background, professional lighting, sharp details",
        )

    def _editorial_concept(self, brand, sd) -> CreativeConcept:
        return CreativeConcept(
            concept_name="时尚大片 Editorial",
            concept_description="杂志封面风格，戏剧化光影",
            rationale="提升品牌调性，营造高级感",
            scene_type="editorial",
            scene_parameters={"background":"深色戏剧化","props":"精选艺术配饰","mood":"高级时尚"},
            lighting_plan={"type":"戏剧光","key":"侧逆光+补光","temperature":"3200-4500K"},
            color_variant=["暗调奢华","高对比黑白"],
            layout_style="杂志跨页式",
            generation_prompt="Editorial style, dramatic lighting, high-end fashion product photography",
        )

    def _minimal_concept(self, brand, sd) -> CreativeConcept:
        return CreativeConcept(
            concept_name="极简主义 Minimal",
            concept_description="大量留白，克制用光，突出产品形态",
            rationale="适合简约设计品牌，让产品自己说话",
            scene_type="minimal",
            scene_parameters={"background":"纯色极简","props":"无","mood":"安静克制"},
            lighting_plan={"type":"大平光","key":"大面积柔光","temperature":"5000K"},
            color_variant=["纯白","浅灰","米色"],
            layout_style="大量留白，产品偏置",
            generation_prompt="Minimal product photography, clean background, soft even lighting, lots of negative space",
        )

    def _seasonal_concept(self, brand, sd) -> CreativeConcept:
        return CreativeConcept(
            concept_name="季节主题 Seasonal",
            concept_description="根据季节/节日定制场景和配色",
            rationale="时效性营销，提升相关性",
            scene_type="seasonal",
            scene_parameters={"background":"季节主题场景","props":"季节元素","mood":"节日氛围"},
            lighting_plan={"type":"氛围光","key":"主题光色","temperature":"3000-6000K"},
            color_variant=["春绿/夏蓝/秋金/冬白"],
            layout_style="主题场景融入",
            generation_prompt="Seasonal themed product photography, festive atmosphere",
        )

    def _score_creativity(self, c: CreativeConcept) -> float:
        scores = {"lifestyle": 0.75, "studio": 0.6, "editorial": 0.9, "minimal": 0.7, "seasonal": 0.85}
        return scores.get(c.scene_type, 0.7)

    def _score_brand_compliance(self, c: CreativeConcept, sd) -> float:
        return 0.85

    def _score_feasibility(self, c: CreativeConcept) -> float:
        scores = {"lifestyle": 0.7, "studio": 0.95, "editorial": 0.5, "minimal": 0.85, "seasonal": 0.6}
        return scores.get(c.scene_type, 0.7)

    def select_best_concept(self) -> CreativeConcept:
        """选最优方案 — 综合评分"""
        if not self._concepts:
            return CreativeConcept()
        return max(self._concepts, key=lambda c: c.creative_score*0.3 + c.brand_compliance*0.4 + c.feasibility*0.3)

    def get_concepts(self) -> List[CreativeConcept]:
        return self._concepts
