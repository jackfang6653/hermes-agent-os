"""
色彩系统分析器 — 理解品牌色彩语言

核心能力：
1. 提取完整色板 + 明暗关系
2. 分析色彩搭配逻辑（为什么这样搭）
3. 理解色彩心理学效果
4. 分析场景配饰的色彩摆放逻辑
5. 推断色彩系统规则
"""
import os
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ColorSystem:
    """完整色彩系统"""
    brand: str = ""
    
    # 主色系
    primary_palette: List[str] = field(default_factory=list)
    secondary_palette: List[str] = field(default_factory=list)
    accent_palette: List[str] = field(default_factory=list)
    neutral_palette: List[str] = field(default_factory=list)
    
    # 明暗关系
    light_values: List[str] = field(default_factory=list)    # 亮部色
    mid_values: List[str] = field(default_factory=list)       # 中间色
    dark_values: List[str] = field(default_factory=list)      # 暗部色
    
    # 场景配色
    scene_primary: List[str] = field(default_factory=list)    # 场景主色
    scene_accent: List[str] = field(default_factory=list)     # 场景点缀色
    prop_colors: List[str] = field(default_factory=list)      # 配饰色
    
    # 色彩关系
    color_relationship: str = ""    # 互补/类似/三角/分裂互补
    temperature: str = ""           # 暖调/冷调/中性
    saturation_curve: str = ""      # 饱和度曲线
    contrast_strategy: str = ""     # 对比策略
    
    # 心理学
    psychological_effect: str = ""  # 心理效果
    cultural_meaning: str = ""      # 文化含义
    target_emotion: str = ""        # 目标情感


@dataclass
class ColorRule:
    """可执行的色彩规则"""
    rule_type: str                   # gradient/contrast/complementary/analogous
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class ColorSystemAnalyzer:
    """色彩系统分析器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def analyze(self, image_url: str) -> ColorSystem:
        """从产品图分析完整色彩系统"""
        if not self.api_key:
            raise ValueError("需要 OPENAI_API_KEY")

        prompt = """你是一位顶级色彩学家和品牌视觉策略师。分析这张产品图片的色彩系统。

输出JSON：
{
    "color_system": {
        "primary_palette": ["#hex", "#hex"],
        "secondary_palette": ["#hex"],
        "accent_palette": ["#hex"],
        "neutral_palette": ["#hex"],
        "light_values": ["#hex"],
        "mid_values": ["#hex"],
        "dark_values": ["#hex"],
        "scene_primary": ["场景主色"],
        "scene_accent": ["场景点缀色"],
        "prop_colors": ["配饰颜色"],
        "color_relationship": "互补/类似/三角/分裂互补/矩形",
        "temperature": "暖调/冷调/中性",
        "saturation_curve": "饱和度分布描述",
        "contrast_strategy": "对比策略"
    },
    "psychology": {
        "psychological_effect": "这个配色对消费者产生的心理效果",
        "cultural_meaning": "文化含义",
        "target_emotion": "目标情感"
    },
    "placement_rationale": "场景中的配饰为什么摆放在这个位置？色彩逻辑是什么？",
    "lighting_impact": "灯光如何影响色彩呈现？",
    "extractable_rules": [
        {"rule_type": "gradient/contrast/complementary", "parameters": {"描述": "参数"}, "confidence": 0.9}
    ]
}

重点分析：
1. 主色/辅色/点缀色的关系
2. 明暗过渡逻辑
3. 场景配饰的色彩摆放为什么这样安排
4. 灯光对色彩的影响
5. 提取可执行的色彩规则（可直接用于生成）"""

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}
                ]}],
                "max_tokens": 4096,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            },
            timeout=120
        )
        if resp.status_code != 200:
            raise RuntimeError(f"GPT error {resp.status_code}")
        text = resp.json()["choices"][0]["message"]["content"]
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
        except:
            return ColorSystem()

        cs = data.get("color_system", {})
        ps = data.get("psychology", {})
        return ColorSystem(
            primary_palette=cs.get("primary_palette", []),
            secondary_palette=cs.get("secondary_palette", []),
            accent_palette=cs.get("accent_palette", []),
            neutral_palette=cs.get("neutral_palette", []),
            light_values=cs.get("light_values", []),
            mid_values=cs.get("mid_values", []),
            dark_values=cs.get("dark_values", []),
            scene_primary=cs.get("scene_primary", []),
            scene_accent=cs.get("scene_accent", []),
            prop_colors=cs.get("prop_colors", []),
            color_relationship=cs.get("color_relationship", ""),
            temperature=cs.get("temperature", ""),
            saturation_curve=cs.get("saturation_curve", ""),
            contrast_strategy=cs.get("contrast_strategy", ""),
            psychological_effect=ps.get("psychological_effect", ""),
            cultural_meaning=ps.get("cultural_meaning", ""),
            target_emotion=ps.get("target_emotion", ""),
        )
