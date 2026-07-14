"""
策略部 — 市场调研与品牌视觉系统分析 (Strategy Phase)

核心能力升级: 不是分析一个产品的参数
而是分析品牌多个产品 → 提取参数范围和系统

产出:
- 品牌视觉参数范围 (不是固定值)
- 竞品对标分析
- 消费者洞察
- 策略文档
"""
import json, os, sys, time, requests
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParameterRange:
    """参数范围 — 品牌实际的视觉参数分布"""
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0
    median: float = 0.0
    samples: int = 0
    common_values: List[Any] = field(default_factory=list)

    def to_dict(self):
        return {"min": self.min, "max": self.max, "avg": self.avg,
                "samples": self.samples, "common": self.common_values[:3]}


@dataclass
class BrandVisualSystem:
    """品牌视觉系统 — 多产品分析结果"""
    brand: str = ""
    
    # 色板范围 (多个产品的色板聚合)
    core_palette: List[str] = field(default_factory=list)       # 跨产品共同色
    seasonal_palette: List[str] = field(default_factory=list)    # 系列特有色
    accent_palette: List[str] = field(default_factory=list)
    
    # 摄影参数范围
    focal_length_range: ParameterRange = field(default_factory=ParameterRange)
    aperture_range: ParameterRange = field(default_factory=ParameterRange)
    iso_range: ParameterRange = field(default_factory=ParameterRange)
    
    # 灯光系统(多产品归纳)
    lighting_patterns: List[str] = field(default_factory=list)
    common_lighting_setups: List[Dict] = field(default_factory=list)
    
    # 材质系统
    material_system: Dict[str, List[Dict]] = field(default_factory=dict)  # type->[variations]
    
    # 构图规律
    composition_rules: List[str] = field(default_factory=list)
    
    # 设计语言
    design_principles: List[str] = field(default_factory=list)
    
    # 分析方法
    products_analyzed: int = 0
    image_count: int = 0
    confidence: float = 0.0


class StrategyDept:
    """策略部 — 多产品品牌视觉系统分析"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def analyze_brand_system(self, products: List[Dict]) -> BrandVisualSystem:
        """分析品牌多个产品 → 提取完整视觉系统"""
        if not products:
            return BrandVisualSystem()

        brand = products[0].get("brand", "unknown")
        print(f"  📊 [Strategy] 分析品牌视觉系统: {brand}")
        print(f"    产品样本数: {len(products)}")

        # 如果没有API key，用启发式聚合
        if not self.api_key:
            return self._heuristic_aggregate(products, brand)

        # 用GPT分析全部产品 → 提取系统
        return self._gpt_analyze_system(products, brand)

    def _gpt_analyze_system(self, products: List[Dict], brand: str) -> BrandVisualSystem:
        """用GPT-4o分析多个产品的视觉系统"""
        # 准备产品数据摘要
        product_summaries = []
        for p in products[:10]:
            img = p.get("image", p.get("image_url", ""))
            name = p.get("name", p.get("product_name", "?"))
            analysis = p.get("analysis", p.get("scene_graph", {}))
            product_summaries.append(f"产品: {name}\n图片: {img[:80]}\n分析: {json.dumps(analysis, ensure_ascii=False)[:500]}")

        prompt = f"""你是一位4A策略总监。分析以下品牌 "{brand}" 的 {len(products)} 个产品的视觉系统。

目标是**提取品牌视觉系统的参数范围**，而不是单点参数。

产品数据:
{chr(10).join(product_summaries)}

输出JSON:
{{
    "core_palette": ["跨产品共同出现的核心色"],
    "seasonal_palette": ["系列特有的辅助色"],
    "accent_palette": ["点缀色"],
    "focal_length": {{"min":最短,"max":最长,"avg":平均,"common":["最常用"]}},
    "aperture": {{"min":最小,"max":最大,"avg":平均}},
    "iso": {{"min":最低,"max":最高}},
    "lighting_patterns": ["多产品归纳的灯光模式"],
    "common_setups": [{{"type":"常用灯光类型","description":"描述"}}],
    "composition_rules": ["构图规律"],
    "design_principles": ["设计原则"],
    "material_types": {{"材质类型1":["变体1","变体2"],"材质类型2":[...]}},
    "visual_consistency": "品牌视觉一致性分析",
    "key_insight": "核心策略洞察"
}}"""
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model":"gpt-4o","messages":[{"role":"user","content":prompt}],
                      "max_tokens":4096,"temperature":0.2,"response_format":{"type":"json_object"}},
                timeout=120
            )
            if resp.status_code == 200:
                data = json.loads(resp.json()["choices"][0]["message"]["content"])
                return self._dict_to_system(data, brand, len(products))
        except Exception as e:
            print(f"    ⚠️  GPT分析失败: {e}")

        return self._heuristic_aggregate(products, brand)

    def _dict_to_system(self, d: dict, brand: str, n: int) -> BrandVisualSystem:
        def pr(k, dflt=None):
            v = d.get(k, {})
            if isinstance(v, dict):
                return ParameterRange(
                    min=v.get("min",0), max=v.get("max",0), avg=v.get("avg",0),
                    common_values=v.get("common",v.get("common_values",[])),
                    samples=n
                )
            return ParameterRange(samples=n)
        return BrandVisualSystem(
            brand=brand, products_analyzed=n,
            core_palette=d.get("core_palette",[]),
            seasonal_palette=d.get("seasonal_palette",[]),
            accent_palette=d.get("accent_palette",[]),
            focal_length_range=pr("focal_length"),
            aperture_range=pr("aperture"),
            iso_range=pr("iso"),
            lighting_patterns=d.get("lighting_patterns",[]),
            common_lighting_setups=d.get("common_setups",[]),
            composition_rules=d.get("composition_rules",[]),
            design_principles=d.get("design_principles",[]),
            image_count=n,
            confidence=0.8,
        )

    def _heuristic_aggregate(self, products: List[Dict], brand: str) -> BrandVisualSystem:
        """无API key时的启发式聚合"""
        all_palettes = []
        all_fl = []; all_ap = []; all_iso = []
        lighting = set(); compositions = set(); principles = set()
        materials = {}

        for p in products:
            a = p.get("analysis", p.get("scene_graph", {}))
            # 色板
            for k in ["primary_palette","colors","palette"]:
                c = a.get(k, [])
                if isinstance(c, list):
                    all_palettes.extend(c)
            # 相机
            cam = a.get("camera", {})
            if cam.get("focal_length_mm"): all_fl.append(cam["focal_length_mm"])
            if cam.get("aperture_f"): all_ap.append(cam["aperture_f"])
            if cam.get("iso"): all_iso.append(cam["iso"])
            # 灯光
            ls = a.get("lighting_signature","")
            if ls: lighting.add(ls)
            for l in a.get("lights",[]):
                if isinstance(l, dict): lighting.add(l.get("modifier","") or l.get("type",""))
            # 构图
            comp = a.get("composition",{})
            if isinstance(comp, dict):
                for v in comp.values():
                    if isinstance(v, str) and len(v) > 5: compositions.add(v)

        def rng(vals):
            if not vals: return ParameterRange()
            return ParameterRange(min=min(vals), max=max(vals), avg=sum(vals)/len(vals),
                                  median=sorted(vals)[len(vals)//2], samples=len(vals))

        # 聚核色板
        from collections import Counter
        core = [c for c, _ in Counter(all_palettes).most_common(8) if isinstance(c, str) and c.startswith("#")]

        return BrandVisualSystem(
            brand=brand, products_analyzed=len(products), image_count=sum(1 for p in products if p.get("image")),
            core_palette=core[:6], seasonal_palette=core[6:10],
            focal_length_range=rng(all_fl), aperture_range=rng(all_ap), iso_range=rng(all_iso),
            lighting_patterns=list(lighting)[:5],
            composition_rules=list(compositions)[:5],
            design_principles=list(principles)[:5],
            confidence=0.5,
        )

    def competitor_analysis(self, brand: str, competitors: List[str]) -> Dict:
        """竞品对标分析"""
        return {
            "brand": brand,
            "competitors": competitors,
            "analysis": "竞品视觉系统对比分析",
            "positioning_gap": "品牌定位差异点",
            "opportunity": "视觉差异化机会",
        }

    def brand_strategy_doc(self, system: BrandVisualSystem, brief) -> Dict:
        """产出自策略文档"""
        return {
            "brand": system.brand,
            "executive_summary": f"基于{system.products_analyzed}个产品的视觉系统分析",
            "visual_system": {
                "core_palette": system.core_palette,
                "focal_length": f"{system.focal_length_range.min}-{system.focal_length_range.max}mm",
                "aperture": f"f/{system.aperture_range.min}-f/{system.aperture_range.max}",
                "lighting_patterns": system.lighting_patterns,
            },
            "design_direction": system.design_principles,
            "recommendation": "建议产出方案",
        }
