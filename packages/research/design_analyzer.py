"""
设计模式分析器 — 理解设计语言和视觉语法

核心能力：
1. 从产品图/页面中提取设计模式
2. 分析视觉层级和信息架构
3. 理解版式设计的 WHY
4. 识别设计工具和参数
5. 推断设计工作流
"""
import os, json, requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DesignElement:
    """设计元素分析"""
    type: str                            # image/text/button/space/divider
    purpose: str                         # 作用
    size_ratio: float = 0                # 占页面比例
    visual_weight: float = 0             # 视觉权重 0-1
    position: str = ""                   # 位置描述
    hierarchy_level: int = 0             # 层级 1=最重要


@dataclass
class VisualGrammar:
    """视觉语法分析结果"""
    elements: List[DesignElement] = field(default_factory=list)
    reading_pattern: str = ""            # Z型/F型/自由
    whitespace_ratio: float = 0          # 留白比例
    rhythm: str = ""                     # 节奏感
    balance: str = ""                    # 平衡方式
    emphasis_technique: str = ""         # 强调手法
    motion_guidance: List[str] = field(default_factory=list)  # 视线引导


@dataclass
class ToolInference:
    """设计工具推断"""
    design_tool: str = ""                # Figma/Sketch/XD/PS
    renderer: str = ""                   # 渲染器
    plugin_detected: List[str] = field(default_factory=list)
    parameters_estimated: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0


class DesignAnalyzer:
    """设计模式分析器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def analyze_design(self, image_url: str) -> Dict[str, Any]:
        """分析一张产品图的设计模式"""
        if not self.api_key:
            raise ValueError("需要 OPENAI_API_KEY")

        prompt = """你是一位4A设计总监和视觉分析师。分析这张产品图片的设计语言。

输出JSON分析：

1. visual_grammar: {
    "elements": [
        {"type":"元素类型","purpose":"作用","size_ratio":0.3,"visual_weight":0.8,"position":"位置","hierarchy_level":1}
    ],
    "reading_pattern": "视线阅读模式 Z型/F型/自由",
    "whitespace_ratio": 留白比例0-1,
    "rhythm": "节奏感描述",
    "balance": "平衡方式",
    "emphasis_technique": "强调手法",
    "motion_guidance": ["视线引导路径"]
   }

2. layout_rationale: "为什么这样排版——解释设计决策背后的逻辑"

3. tool_inference: {
    "design_tool": "推测的设计工具",
    "renderer": "推测的渲染器",
    "plugin_detected": ["插件"],
    "parameters_estimated": {"关键参数"},
    "confidence": 置信度
   }

4. design_principles_applied: ["应用了哪些设计原则"]

5. visual_hierarchy_analysis: "视觉层级分析——用户第一眼看到什么，第二眼看到什么"

6. brand_consistency: "品牌一致性分析——这个设计如何体现品牌调性"

重点：不仅描述"是什么"，更要解释"为什么这样设计"和"达到了什么效果"。"""
        
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
            return json.loads(text[start:end])
        except:
            return {"raw": text}

    def infer_tools(self, image_url: str) -> ToolInference:
        """专门分析设计工具和参数"""
        result = self.analyze_design(image_url)
        ti = result.get("tool_inference", {})
        return ToolInference(
            design_tool=ti.get("design_tool", ""),
            renderer=ti.get("renderer", ""),
            plugin_detected=ti.get("plugin_detected", []),
            parameters_estimated=ti.get("parameters_estimated", {}),
            confidence=ti.get("confidence", 0),
        )
