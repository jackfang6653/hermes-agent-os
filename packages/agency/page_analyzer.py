"""
页面全方位分析器 PageAnalyzer — 提取产品详情页每个元素的参数

核心能力:
- 接收产品详情页URL，截图后用Vision模型分析
- 提取页面结构(板块划分)、文案、字体/字号/颜色、排版位置/间距
- 提取图片数量/类型/构图、色彩关系
- 输出结构化的 PageDesignDNA

用法:
    analyzer = PageAnalyzer()
    dna = analyzer.analyze("https://www.muji.com.cn/...")
    # → PageDesignDNA with all sections, typography, colors, images, layout

输出结构:
    PageDesignDNA:
        sections[] → PageSection (id/type/content/font/size/color/position/spacing)
        typography → Typography (primary/secondary fonts, sizes, weights)
        colors     → ColorPalette (primary/secondary/accent/background/text, harmony)
        images     → ImageInfo (count, types, composition, angles)
        layout     → LayoutInfo (grid, columns, width, flow)
"""

import os
import json
import base64
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from io import BytesIO

# ── Data Structures ──────────────────────────────────────────


@dataclass
class PageSection:
    """单个页面板块的完整参数"""

    id: str = ""                # e.g. "s1-hero"
    type: str = ""              # hero / product_gallery / description / specs / cta / reviews / nav / footer
    content: str = ""           # 该板块的文案内容摘要

    # 排版参数
    font: str = ""              # 字体族 e.g. "PingFang SC"
    size: str = ""              # 字号 e.g. "14px / 24px / 32px"
    color: str = ""             # 文字颜色 e.g. "#333333"
    weight: str = ""            # 字重 e.g. "400 / 700"
    line_height: str = ""       # 行高 e.g. "1.6"

    # 位置/间距参数
    position: str = ""          # 描述 e.g. "顶部全宽 / 居中 / 左对齐"
    spacing: str = ""           # 间距 e.g. "上下padding 40px, 左右margin 20px"
    alignment: str = ""         # 对齐 e.g. "center / left / right"

    # 背景
    background: str = ""        # 背景色/图 e.g. "#FAFAFA / image"

    # 图片
    image_count: int = 0
    image_types: List[str] = field(default_factory=list)  # product / lifestyle / detail / icon / banner

    # 元数据
    confidence: float = 0.0     # 分析置信度


@dataclass
class Typography:
    """页面排版系统"""

    primary_font: str = ""        # 主字体
    secondary_font: str = ""      # 辅字体
    heading_font: str = ""        # 标题字体
    heading_sizes: List[str] = field(default_factory=list)   # ["32px H1", "24px H2", "18px H3"]
    body_size: str = ""           # 正文大小
    caption_size: str = ""        # 辅助文字大小
    line_height: str = ""         # 行高
    weight_usage: str = ""        # 字重使用规律 e.g. "标题Bold 700, 正文Regular 400"


@dataclass
class ColorPalette:
    """页面色彩体系"""

    primary: str = ""             # 主色
    secondary: str = ""           # 辅色
    accent: str = ""              # 强调色
    background: str = ""          # 背景色
    surface: str = ""             # 卡片/区块底色
    text_primary: str = ""        # 主文字色
    text_secondary: str = ""      # 辅文字色
    text_placeholder: str = ""    # 占位/禁用文字色
    border: str = ""              # 边框色
    all_colors: List[str] = field(default_factory=list)  # 完整色板
    color_harmony: str = ""       # 色彩关系描述 e.g. "单色调 / 互补色 / 类似色"


@dataclass
class ImageInfo:
    """页面图片系统"""

    total_count: int = 0
    hero_images: int = 0          # 首屏大图
    product_images: int = 0       # 产品图
    lifestyle_images: int = 0     # 场景/生活方式图
    detail_images: int = 0        # 细节特写
    icon_count: int = 0           # 图标
    composition_styles: List[str] = field(default_factory=list)   # ["白底product shot", "lifestyle场景"]
    dominant_angles: List[str] = field(default_factory=list)      # ["平视45°", "俯拍", "特写"]
    image_ratio: str = ""         # 图片比例 e.g. "1:1 / 4:3 / 16:9 mixed"


@dataclass
class LayoutInfo:
    """页面布局系统"""

    grid_type: str = ""           # "单栏 / 两栏 / 三栏 / 混合"
    column_count: int = 0
    content_max_width: str = ""   # e.g. "1200px"
    reading_flow: str = ""        # 阅读流 e.g. "F-pattern / Z-pattern / 纵向流"
    section_count: int = 0        # 板块总数
    vertical_rhythm: str = ""     # 纵向节奏 e.g. "大块留白+紧凑信息交替"


@dataclass
class PageDesignDNA:
    """完整页面设计DNA — 包含所有元素的参数化描述"""

    url: str = ""
    title: str = ""
    brand: str = ""
    analyzed_at: str = ""

    sections: List[PageSection] = field(default_factory=list)
    typography: Typography = field(default_factory=Typography)
    colors: ColorPalette = field(default_factory=ColorPalette)
    images: ImageInfo = field(default_factory=ImageInfo)
    layout: LayoutInfo = field(default_factory=LayoutInfo)

    overall_style: str = ""       # 整体风格描述
    design_language: str = ""     # 设计语言 e.g. "极简 / 日式 / 北欧 / 科技感"
    summary: str = ""             # 一句话总结

    # JSON 序列化
    def to_dict(self) -> dict:
        """转为可序列化的字典 (处理dataclass嵌套和List[dataclass])"""
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)

    # Markdown 报告
    def to_markdown(self) -> str:
        """生成人类可读的Markdown分析报告"""
        lines = [
            "# 页面设计DNA分析报告",
            "",
            f"**URL**: {self.url}",
            f"**标题**: {self.title}",
            f"**品牌**: {self.brand}",
            f"**分析时间**: {self.analyzed_at}",
            "",
            "## 整体风格",
            "",
            f"- **设计语言**: {self.design_language}",
            f"- **风格描述**: {self.overall_style}",
            f"- **总结**: {self.summary}",
            "",
        ]

        # 排版
        t = self.typography
        lines += [
            "## 排版系统",
            "",
            "| 参数 | 值 |",
            "|------|-----|",
            f"| 主字体 | {t.primary_font} |",
            f"| 辅字体 | {t.secondary_font} |",
            f"| 标题字体 | {t.heading_font} |",
            f"| 标题字号 | {', '.join(t.heading_sizes) if t.heading_sizes else '-'} |",
            f"| 正文字号 | {t.body_size} |",
            f"| 辅助字号 | {t.caption_size} |",
            f"| 行高 | {t.line_height} |",
            f"| 字重规律 | {t.weight_usage} |",
            "",
        ]

        # 色彩
        c = self.colors
        lines += [
            "## 色彩体系",
            "",
            "| 角色 | 色值 |",
            "|------|------|",
            f"| 主色 | {c.primary} |",
            f"| 辅色 | {c.secondary} |",
            f"| 强调色 | {c.accent} |",
            f"| 背景色 | {c.background} |",
            f"| 区块底色 | {c.surface} |",
            f"| 主文字 | {c.text_primary} |",
            f"| 辅文字 | {c.text_secondary} |",
            f"| 边框色 | {c.border} |",
            "",
            f"**色彩关系**: {c.color_harmony}",
            f"**完整色板**: {', '.join(c.all_colors) if c.all_colors else '-'}",
            "",
        ]

        # 图片
        img = self.images
        lines += [
            "## 图片系统",
            "",
            "| 指标 | 值 |",
            "|------|-----|",
            f"| 图片总数 | {img.total_count} |",
            f"| Hero大图 | {img.hero_images} |",
            f"| 产品图 | {img.product_images} |",
            f"| 场景图 | {img.lifestyle_images} |",
            f"| 细节特写 | {img.detail_images} |",
            f"| 图标 | {img.icon_count} |",
            f"| 图片比例 | {img.image_ratio} |",
            f"| 构图类型 | {', '.join(img.composition_styles) if img.composition_styles else '-'} |",
            f"| 拍摄角度 | {', '.join(img.dominant_angles) if img.dominant_angles else '-'} |",
            "",
        ]

        # 布局
        l = self.layout
        lines += [
            "## 布局系统",
            "",
            "| 参数 | 值 |",
            "|------|-----|",
            f"| 网格类型 | {l.grid_type} |",
            f"| 列数 | {l.column_count} |",
            f"| 内容最大宽度 | {l.content_max_width} |",
            f"| 阅读流 | {l.reading_flow} |",
            f"| 板块总数 | {l.section_count} |",
            f"| 纵向节奏 | {l.vertical_rhythm} |",
            "",
        ]

        # 逐板块详情
        lines.append("## 板块详情")
        lines.append("")
        for i, sec in enumerate(self.sections):
            lines += [
                f"### {i+1}. {sec.type} `{sec.id}`",
                "",
                "| 参数 | 值 |",
                "|------|-----|",
                f"| 文案 | {sec.content[:80]}{'...' if len(sec.content) > 80 else ''} |",
                f"| 字体 | {sec.font} |",
                f"| 字号 | {sec.size} |",
                f"| 颜色 | {sec.color} |",
                f"| 字重 | {sec.weight} |",
                f"| 行高 | {sec.line_height} |",
                f"| 位置 | {sec.position} |",
                f"| 间距 | {sec.spacing} |",
                f"| 对齐 | {sec.alignment} |",
                f"| 背景 | {sec.background} |",
                f"| 图片数 | {sec.image_count} ({', '.join(sec.image_types) if sec.image_types else 'none'}) |",
                f"| 置信度 | {sec.confidence:.0%} |",
                "",
            ]

        return "\n".join(lines)


# ── Serialization helper ─────────────────────────────────────

def _dataclass_to_dict(obj) -> Any:
    """递归转换dataclass为纯dict (处理嵌套dataclass和list)"""
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    elif hasattr(obj, '__dataclass_fields__'):
        return {k: _dataclass_to_dict(v) for k, v in asdict(obj).items()}
    else:
        return obj


# ── Engine ───────────────────────────────────────────────────

_VISION_ANALYSIS_PROMPT = """你是一位资深网页设计分析师。请仔细分析这张产品详情页截图，提取**每个板块**的设计参数。

请按以下JSON格式输出（严格按照字段名，不要遗漏）:

```json
{
    "title": "页面标题",
    "brand": "品牌名",
    "overall_style": "整体风格描述(50字以内)",
    "design_language": "设计语言(如: 极简日式 / 北欧自然 / 科技质感)",
    "summary": "一句话总结页面设计特点",

    "sections": [
        {
            "id": "s1-hero",
            "type": "板块类型(hero/product_gallery/description/specs/cta/reviews/features/breadcrumb/nav/footer)",
            "content": "该板块文案内容(不要截断，完整提取)",
            "font": "字体族(如PingFang SC/Noto Sans SC)",
            "size": "字号(如14px)",
            "color": "文字色值(hex，如#333333)",
            "weight": "字重(如400)",
            "line_height": "行高(如1.6)",
            "position": "位置描述(如顶部全宽/居中偏左/右侧1/3)",
            "spacing": "间距描述(如padding:40px 20px; margin-bottom:60px)",
            "alignment": "对齐方式(left/center/right/justify)",
            "background": "背景(色值如#FAFAFA 或 图片描述)",
            "image_count": 0,
            "image_types": ["product", "lifestyle"],
            "confidence": 0.0
        }
    ],

    "typography": {
        "primary_font": "主字体",
        "secondary_font": "辅字体(无则留空)",
        "heading_font": "标题字体",
        "heading_sizes": ["32px H1", "24px H2"],
        "body_size": "正文字号(如14px)",
        "caption_size": "辅助文字大小(如12px)",
        "line_height": "正文行高(如1.6)",
        "weight_usage": "字重规律(如: 标题700 Bold, 正文400 Regular)"
    },

    "colors": {
        "primary": "主色hex",
        "secondary": "辅色hex",
        "accent": "强调色hex",
        "background": "页面背景色hex",
        "surface": "卡片/区块底色hex",
        "text_primary": "主文字色hex",
        "text_secondary": "辅文字色hex",
        "text_placeholder": "占位文字色hex",
        "border": "边框色hex",
        "all_colors": ["#主色", "#辅色", "#强调色"],
        "color_harmony": "色彩关系(如: 单色调/类似色/互补色)"
    },

    "images": {
        "total_count": 0,
        "hero_images": 0,
        "product_images": 0,
        "lifestyle_images": 0,
        "detail_images": 0,
        "icon_count": 0,
        "composition_styles": ["白底产品图", "场景叙事"],
        "dominant_angles": ["平视45°", "俯拍"],
        "image_ratio": "图片比例(如1:1/4:3 mixed)"
    },

    "layout": {
        "grid_type": "网格类型(单栏/两栏/三栏/混合)",
        "column_count": 0,
        "content_max_width": "内容区最大宽度(如1200px)",
        "reading_flow": "阅读流(如F-pattern/Z-pattern/纵向流)",
        "section_count": 0,
        "vertical_rhythm": "纵向节奏(如大留白+紧凑信息交替)"
    }
}
```

**严格要求:**
1. 每个板块的 content 只提取文案，不要加任何解释
2. 颜色必须输出 hex 值 (#RRGGBB)
3. section 按从上到下顺序排列，id 以 s1- s2- s3- 开头
4. 如果某个参数无法判断，填 "unknown" 或 0，不要留空
5. 所有字段都必须出现，不要省略任何字段
6. 只输出JSON，不要有任何其他文字"""


class PageAnalyzer:
    """页面全方位分析器 — 提取产品详情页每个元素的参数

    用法:
        analyzer = PageAnalyzer(api_key="sk-...")  # 或用环境变量 OPENAI_API_KEY
        dna = analyzer.analyze_from_url("https://muji.com.cn/product/123")
        print(dna.to_markdown())

        # 或者从已有截图分析
        dna = analyzer.analyze_from_image("screenshot.png")
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "gpt-4o",
                 base_url: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API key (默认读环境变量 OPENAI_API_KEY)
            model: Vision模型名 (默认 gpt-4o)
            base_url: API base URL (可选，用于代理或Azure)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # ── 主入口 ────────────────────────────────────────────

    def analyze_from_url(self, url: str) -> PageDesignDNA:
        """从URL分析页面 (需要浏览器工具配合截图)

        NOTE: 此方法需要外部提供截图。在实际使用中，由 Hermes Agent
        的 browser_vision 工具完成截图后，将图片路径传入 analyze_from_image()。
        或由调用方自行完成页面截图。

        如果直接调用，会尝试用 web_extract 获取页面文本作为补充分析。

        Args:
            url: 产品详情页URL

        Returns:
            PageDesignDNA: 完整的设计DNA
        """
        dna = PageDesignDNA(
            url=url,
            analyzed_at=datetime.utcnow().isoformat(),
        )

        # 尝试获取页面文本作为补充
        try:
            import requests
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code == 200:
                dna.title = self._extract_title(resp.text)
        except Exception:
            pass

        # 如果没有API key，返回启发式分析
        if not self.api_key:
            return self._heuristic_analysis(dna)

        return dna

    def analyze_from_image(self, image_path: str, url: str = "",
                           context: Optional[Dict] = None) -> PageDesignDNA:
        """从截图分析页面 — 核心分析入口

        Args:
            image_path: 截图文件路径
            url: 页面URL (可选，用于记录)
            context: 额外上下文 (如页面文本提取结果)

        Returns:
            PageDesignDNA: 完整的设计DNA
        """
        dna = PageDesignDNA(
            url=url,
            analyzed_at=datetime.utcnow().isoformat(),
        )

        if not self.api_key:
            return self._heuristic_analysis(dna)

        # 读取图片并编码为 base64
        try:
            image_b64 = self._encode_image(image_path)
        except FileNotFoundError:
            return self._heuristic_analysis(dna)

        # 构建 Vision API 请求
        result = self._call_vision_api(image_b64, context)

        if result:
            dna = self._parse_vision_result(result, url)
        else:
            dna = self._heuristic_analysis(dna)

        return dna

    def analyze_from_base64(self, image_b64: str, url: str = "",
                            context: Optional[Dict] = None) -> PageDesignDNA:
        """从base64编码的图片直接分析

        Args:
            image_b64: base64编码的图片数据
            url: 页面URL
            context: 额外上下文

        Returns:
            PageDesignDNA
        """
        dna = PageDesignDNA(
            url=url,
            analyzed_at=datetime.utcnow().isoformat(),
        )

        if not self.api_key:
            return self._heuristic_analysis(dna)

        result = self._call_vision_api(image_b64, context)

        if result:
            dna = self._parse_vision_result(result, url)
        else:
            dna = self._heuristic_analysis(dna)

        return dna

    def analyze_from_images(self, image_paths: List[str], url: str = "",
                            context: Optional[Dict] = None) -> PageDesignDNA:
        """从多张截图分析 (用于长页面，分段截图)

        对每张截图分别分析，然后合并结果。

        Args:
            image_paths: 截图文件路径列表 (从上到下)
            url: 页面URL
            context: 额外上下文

        Returns:
            PageDesignDNA: 合并后的完整设计DNA
        """
        if not image_paths:
            return PageDesignDNA(url=url)

        # 先分析第一张获取全局信息 (typography/colors/layout)
        primary = self.analyze_from_image(image_paths[0], url=url, context=context)

        if len(image_paths) == 1:
            return primary

        # 分析剩余图片获取更多 sections
        all_sections = list(primary.sections)
        for i, img_path in enumerate(image_paths[1:], start=1):
            partial = self.analyze_from_image(img_path, url=url, context=context)
            # 合并 sections，去重
            existing_ids = {s.id for s in all_sections}
            for sec in partial.sections:
                if sec.id not in existing_ids:
                    all_sections.append(sec)

        # 重新编号
        for i, sec in enumerate(all_sections):
            parts = sec.id.split("-", 1)
            sec.id = f"s{i+1}-{parts[1]}" if len(parts) > 1 else f"s{i+1}"

        primary.sections = all_sections
        primary.layout.section_count = len(all_sections)
        primary.images.total_count = sum(s.image_count for s in all_sections)
        primary.analyzed_at = datetime.utcnow().isoformat()

        return primary

    # ── Internal: Vision API ───────────────────────────────

    def _encode_image(self, image_path: str) -> str:
        """读取图片文件并转为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_vision_api(self, image_b64: str,
                         context: Optional[Dict] = None) -> Optional[dict]:
        """调用 GPT-4o Vision API 分析截图"""
        import requests

        prompt = _VISION_ANALYSIS_PROMPT
        if context:
            prompt += f"\n\n补充上下文:\n{json.dumps(context, ensure_ascii=False)}"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.1,  # 低温度保证一致性
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            return self._extract_json(content)

        except Exception as e:
            print(f"[PageAnalyzer] Vision API call failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        """从 LLM 回复中提取 JSON (处理 markdown code block)"""
        # 尝试提取 ```json ... ``` 块
        import re
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到第一个 { 和最后一个 }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass
        return None

    # ── Internal: Parse ─────────────────────────────────────

    def _parse_vision_result(self, result: dict, url: str) -> PageDesignDNA:
        """将Vision API返回的JSON解析为 PageDesignDNA"""
        dna = PageDesignDNA(
            url=url,
            title=result.get("title", ""),
            brand=result.get("brand", ""),
            analyzed_at=datetime.utcnow().isoformat(),
            overall_style=result.get("overall_style", ""),
            design_language=result.get("design_language", ""),
            summary=result.get("summary", ""),
        )

        # 解析 sections
        for sec_data in result.get("sections", []):
            section = PageSection(
                id=sec_data.get("id", ""),
                type=sec_data.get("type", "unknown"),
                content=sec_data.get("content", ""),
                font=sec_data.get("font", "unknown"),
                size=sec_data.get("size", "unknown"),
                color=sec_data.get("color", "unknown"),
                weight=sec_data.get("weight", "unknown"),
                line_height=sec_data.get("line_height", "unknown"),
                position=sec_data.get("position", "unknown"),
                spacing=sec_data.get("spacing", "unknown"),
                alignment=sec_data.get("alignment", "unknown"),
                background=sec_data.get("background", "unknown"),
                image_count=sec_data.get("image_count", 0),
                image_types=sec_data.get("image_types", []),
                confidence=sec_data.get("confidence", 0.0),
            )
            dna.sections.append(section)

        # 解析 typography
        typo = result.get("typography", {})
        dna.typography = Typography(
            primary_font=typo.get("primary_font", ""),
            secondary_font=typo.get("secondary_font", ""),
            heading_font=typo.get("heading_font", ""),
            heading_sizes=typo.get("heading_sizes", []),
            body_size=typo.get("body_size", ""),
            caption_size=typo.get("caption_size", ""),
            line_height=typo.get("line_height", ""),
            weight_usage=typo.get("weight_usage", ""),
        )

        # 解析 colors
        col = result.get("colors", {})
        dna.colors = ColorPalette(
            primary=col.get("primary", ""),
            secondary=col.get("secondary", ""),
            accent=col.get("accent", ""),
            background=col.get("background", ""),
            surface=col.get("surface", ""),
            text_primary=col.get("text_primary", ""),
            text_secondary=col.get("text_secondary", ""),
            text_placeholder=col.get("text_placeholder", ""),
            border=col.get("border", ""),
            all_colors=col.get("all_colors", []),
            color_harmony=col.get("color_harmony", ""),
        )

        # 解析 images
        img = result.get("images", {})
        dna.images = ImageInfo(
            total_count=img.get("total_count", 0),
            hero_images=img.get("hero_images", 0),
            product_images=img.get("product_images", 0),
            lifestyle_images=img.get("lifestyle_images", 0),
            detail_images=img.get("detail_images", 0),
            icon_count=img.get("icon_count", 0),
            composition_styles=img.get("composition_styles", []),
            dominant_angles=img.get("dominant_angles", []),
            image_ratio=img.get("image_ratio", ""),
        )

        # 解析 layout
        lay = result.get("layout", {})
        dna.layout = LayoutInfo(
            grid_type=lay.get("grid_type", ""),
            column_count=lay.get("column_count", 0),
            content_max_width=lay.get("content_max_width", ""),
            reading_flow=lay.get("reading_flow", ""),
            section_count=lay.get("section_count", len(dna.sections)),
            vertical_rhythm=lay.get("vertical_rhythm", ""),
        )

        return dna

    # ── Internal: Heuristic fallback ────────────────────────

    def _heuristic_analysis(self, dna: PageDesignDNA) -> PageDesignDNA:
        """无API时的启发式分析 (基于URL和页面文本推断)"""
        dna.design_language = "无法确定 (需要Vision API)"
        dna.overall_style = "需要提供截图或配置OPENAI_API_KEY后重新分析"
        dna.summary = "启发式分析 — 无视觉数据"

        # 尝试从URL推断品牌
        from urllib.parse import urlparse
        if dna.url:
            domain = urlparse(dna.url).netloc
            if "muji" in domain:
                dna.brand = "MUJI"
                dna.design_language = "日式极简 (基于URL推断)"
            elif "ikea" in domain:
                dna.brand = "IKEA"
            elif "apple" in domain:
                dna.brand = "Apple"

        return dna

    def _extract_title(self, html: str) -> str:
        """从HTML提取title"""
        import re
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""


# ── Convenience function ─────────────────────────────────────

def analyze_page(image_path: str, url: str = "",
                 api_key: Optional[str] = None) -> PageDesignDNA:
    """快捷函数 — 一步分析页面截图

    Args:
        image_path: 页面截图路径
        url: 页面URL
        api_key: OpenAI API key

    Returns:
        PageDesignDNA
    """
    analyzer = PageAnalyzer(api_key=api_key)
    return analyzer.analyze_from_image(image_path, url=url)


# ── Integration with BrandDNARef ─────────────────────────────

def extract_brand_rules(dna: PageDesignDNA) -> Dict[str, List[Dict]]:
    """从PageDesignDNA中提取品牌设计规则，可存入BrandDNARef

    将页面分析结果转换为与 BrandDNARef.store_rationale() 兼容的格式。
    """
    rules = {
        "color": [],
        "typography": [],
        "composition": [],
        "material": [],
    }

    # 色彩规则
    if dna.colors.primary:
        rules["color"].append({
            "parameter": "primary_color",
            "value": dna.colors.primary,
            "why": "品牌主色，用于关键CTA和品牌标识",
            "brand_strategy_link": f"{dna.brand}品牌识别核心",
            "confidence": 0.85,
        })
    if dna.colors.color_harmony:
        rules["color"].append({
            "parameter": "color_harmony",
            "value": dna.colors.color_harmony,
            "why": "色彩搭配策略",
            "brand_strategy_link": f"{dna.brand}设计语言: {dna.design_language}",
            "confidence": 0.80,
        })

    # 排版规则
    if dna.typography.primary_font:
        rules["typography"].append({
            "parameter": "primary_font",
            "value": dna.typography.primary_font,
            "why": f"主字体选择，传达{dna.design_language}调性",
            "brand_strategy_link": f"{dna.brand}品牌字体规范",
            "confidence": 0.85,
        })
    if dna.typography.body_size:
        rules["typography"].append({
            "parameter": "body_font_size",
            "value": dna.typography.body_size,
            "why": "正文可读性基准",
            "confidence": 0.80,
        })

    # 构图规则
    if dna.images.composition_styles:
        rules["composition"].append({
            "parameter": "image_composition",
            "value": ", ".join(dna.images.composition_styles),
            "why": "产品图片构图风格",
            "brand_strategy_link": f"{dna.brand}视觉规范",
            "confidence": 0.80,
        })
    if dna.layout.grid_type:
        rules["composition"].append({
            "parameter": "layout_grid",
            "value": dna.layout.grid_type,
            "why": "页面网格系统",
            "confidence": 0.80,
        })

    return {k: v for k, v in rules.items() if v}


def compare_dna(dna_a: PageDesignDNA, dna_b: PageDesignDNA) -> Dict[str, Any]:
    """比较两个PageDesignDNA，找出差异

    用于竞品分析：对比两个品牌/产品详情页的设计差异。
    """
    diff = {
        "url_a": dna_a.url,
        "url_b": dna_b.url,
        "brand_a": dna_a.brand,
        "brand_b": dna_b.brand,
        "differences": [],
    }

    # 色彩差异
    if dna_a.colors.primary != dna_b.colors.primary:
        diff["differences"].append({
            "category": "colors",
            "parameter": "primary_color",
            "a": dna_a.colors.primary,
            "b": dna_b.colors.primary,
        })

    # 排版差异
    if dna_a.typography.primary_font != dna_b.typography.primary_font:
        diff["differences"].append({
            "category": "typography",
            "parameter": "primary_font",
            "a": dna_a.typography.primary_font,
            "b": dna_b.typography.primary_font,
        })

    # 布局差异
    if dna_a.layout.grid_type != dna_b.layout.grid_type:
        diff["differences"].append({
            "category": "layout",
            "parameter": "grid_type",
            "a": dna_a.layout.grid_type,
            "b": dna_b.layout.grid_type,
        })

    # 图片差异
    if dna_a.images.total_count != dna_b.images.total_count:
        diff["differences"].append({
            "category": "images",
            "parameter": "total_count",
            "a": dna_a.images.total_count,
            "b": dna_b.images.total_count,
        })

    # 板块差异
    diff["section_count_diff"] = len(dna_a.sections) - len(dna_b.sections)

    return diff
