"""
设计理由引擎 — 对每个参数追问 WHY

核心能力: 不仅提取参数, 更理解每个设计决策背后的品牌逻辑

输入: SceneGraph / 分析结果
输出: 每个参数对应的设计理由 + 品牌策略关联

这是4A公司真正的价值: 知道"为什么"这样设计
"""
import os
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DesignRationaleItem:
    """一个设计决策的理由"""
    parameter: str = ""           # 参数名 e.g. "focal_length"
    value: str = ""               # 参数值 e.g. "85mm"
    why: str = ""                 # 为什么选这个值
    brand_strategy_link: str = "" # 关联的品牌策略
    psychological_effect: str = "" # 心理效果
    alternative_options: List[str] = field(default_factory=list)  # 其他选项及效果
    confidence: float = 0.0


@dataclass
class DesignRationaleReport:
    """完整设计理由报告"""
    brand: str = ""
    product: str = ""
    
    camera_rationale: List[DesignRationaleItem] = field(default_factory=list)
    lighting_rationale: List[DesignRationaleItem] = field(default_factory=list)
    color_rationale: List[DesignRationaleItem] = field(default_factory=list)
    composition_rationale: List[DesignRationaleItem] = field(default_factory=list)
    material_rationale: List[DesignRationaleItem] = field(default_factory=list)
    
    brand_dna_summary: str = ""    # 品牌DNA总结
    design_philosophy: str = ""    # 设计哲学
    key_takeaways: List[str] = field(default_factory=list)  # 关键启示


class DesignRationaleEngine:
    """设计理由引擎 — 追问WHY"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def analyze_rationale(self, scene_graph: dict, brand: str = "", product: str = "") -> DesignRationaleReport:
        """从场景图分析每个设计决策的理由"""
        if not self.api_key:
            return self._heuristic_rationale(scene_graph, brand, product)

        prompt = f"""你是一位4A创意总监和品牌策略师。分析以下产品场景图，对**每个设计参数**追问 WHY。

品牌: {brand}
产品: {product}

场景图数据:
{json.dumps(scene_graph, ensure_ascii=False, indent=2)[:4000]}

请输出JSON，对每个设计维度分析设计理由:

{{
    "camera_rationale": [
        {{
            "parameter": "focal_length",
            "value": "85mm",
            "why": "85mm压缩透视效果使产品在画面中比例恰当，背景虚化自然，突出产品主体",
            "brand_strategy_link": "中长焦镜头营造的压缩感传递专业品质感，符合高端品牌定位",
            "psychological_effect": "压缩透视让产品更有分量感，增强信任和品质认知",
            "alternative_options": "50mm更自然但背景干扰多，135mm更压缩但需要更大拍摄空间"
        }}
    ],
    "lighting_rationale": [...],
    "color_rationale": [...],
    "composition_rationale": [...],
    "material_rationale": [...],
    "brand_dna_summary": "该品牌的核心视觉DNA是...",
    "design_philosophy": "设计哲学是...",
    "key_takeaways": ["启示1", "启示2"]
}}

**重点**: 对每个参数, 必须解释 WHY 选这个值, 而不是只描述值。
"""
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model":"gpt-4o","messages":[{"role":"user","content":prompt}],
                      "max_tokens":4096,"temperature":0.3,"response_format":{"type":"json_object"}},
                timeout=120
            )
            if resp.status_code == 200:
                data = json.loads(resp.json()["choices"][0]["message"]["content"])
                return self._dict_to_report(data, brand, product)
        except Exception as e:
            print(f"  ⚠️  Rationale分析失败: {e}")

        return self._heuristic_rationale(scene_graph, brand, product)

    def _dict_to_report(self, d: dict, brand: str, product: str) -> DesignRationaleReport:
        def items(key):
            return [DesignRationaleItem(**i) for i in d.get(key, []) if isinstance(i, dict)]
        return DesignRationaleReport(
            brand=brand, product=product,
            camera_rationale=items("camera_rationale"),
            lighting_rationale=items("lighting_rationale"),
            color_rationale=items("color_rationale"),
            composition_rationale=items("composition_rationale"),
            material_rationale=items("material_rationale"),
            brand_dna_summary=d.get("brand_dna_summary",""),
            design_philosophy=d.get("design_philosophy",""),
            key_takeaways=d.get("key_takeaways",[]),
        )

    def _heuristic_rationale(self, sg: dict, brand: str, product: str) -> DesignRationaleReport:
        """无API时启发式WHY分析"""
        items = []
        cam = sg.get("camera",{})
        if cam.get("focal_length_mm"):
            items.append(DesignRationaleItem(
                parameter="focal_length", value=f"{cam['focal_length_mm']}mm",
                why="中长焦压缩透视突出产品主体，虚化背景干扰",
                brand_strategy_link="专业产品摄影标准选择",
                psychological_effect="压缩感增强产品分量感",
            ))
        if cam.get("aperture_f"):
            items.append(DesignRationaleItem(
                parameter="aperture", value=f"f/{cam['aperture_f']}",
                why=f"f/{cam['aperture_f']}控制景深，{('浅景深虚化背景' if cam['aperture_f']<4 else '全清晰展示细节')}",
                brand_strategy_link="景深控制引导视觉焦点",
                psychological_effect="引导观看者关注产品关键部位",
            ))
        return DesignRationaleReport(
            brand=brand, product=product,
            camera_rationale=items,
            brand_dna_summary=f"{brand}的设计DNA分析",
            key_takeaways=["参数服务于品牌策略"],
        )
