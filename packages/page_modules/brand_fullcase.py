"""
终极版块 — 品牌全案溯源系统

基于文档: AI品牌全案｜调研-分析-定调-设计 完整溯源体系

4大调研模块:
  M1: 市场行业趋势分析 — 定大环境
  M2: 目标用户洞察分析 — 定审美适配
  M3: 产品基因深度分析 — 定内核基调
  M4: TOP10竞品全维度对标 — 定差异化定位

因果溯源模块: 每一项定调 → 调研依据 → Why逻辑

7套交付物:
  1. 市场行业趋势分析报告
  2. 目标用户审美洞察报告
  3. 品牌产品视觉基因分析报告
  4. TOP10竞品对标分析报告
  5. 品牌视觉调性定调说明书
  6. 全链路设计溯源手册
  7. 品牌视觉规范库
"""
import os
import json
import requests
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime


# ── 精确匹配文档的4段 Prompt ────────────────────────

PROMPT_MARKET = """Conduct in-depth industry market environment analysis for the product category. Summarize current industry mainstream aesthetic trends, price-band visual differentiation rules, consumer upgrading preferences, popular color trends, layout and scene style iteration directions. Summarize market homogenization pain points and user aesthetic fatigue problems, extract blank market opportunities and visual differentiation tracks. Record all trend bases that support brand tone formulation."""

PROMPT_USER = """Analyze core target user group portrait and visual aesthetic psychology. Summarize users' preference for texture, color atmosphere, space sense, layout density and scene style. Extract user's visual recognition standard of high-end, comfort, luxury and minimalism. Clarify which visual styles can stimulate user trust and purchase desire, and take user aesthetic cognition as the core basis for brand tone and page design."""

PROMPT_PRODUCT = """Sort out the core visual gene of the brand's own products. Analyze product material texture, hard and soft attributes, price positioning, core selling points and inherent emotional temperament. Deduce the matching light and shadow tone, color temperature, contrast range, decorative collocation logic, font temperament and layout atmosphere that fit the product attributes. Ensure all visual designs are consistent with product positioning and avoid style mismatch."""

PROMPT_COMPETITOR = """Complete full-dimensional benchmarking analysis of TOP10 competing products in the same category. Comprehensively compare competitor brand tone, color system, page layout paradigm, product scene collocation, light and shadow histogram tone, font hierarchy, blank rhythm and scene atmosphere. Summarize the common design rules and homogeneous shortcomings of mainstream competitors. Extract market visual blank areas and differentiation opportunities. Form clear brand differentiation positioning basis, clarify what styles to follow, what shortcomings to avoid, and what unique tonality to establish."""

PROMPT_TRACEABILITY = """For every final brand tone decision and visual design specification, output complete traceable causal logic: 
1. Which market trend supports this tonality; 
2. Which user aesthetic demand matches this design; 
3. Which product gene determines this collocation; 
4. Which competitor's shortcoming makes this differentiation necessary; 
5. Explain why this color, light and shadow, layout, ornament, font and atmosphere is the best solution for the current brand positioning. 
Form a standardized "Research Basis — Design Decision — Why Logic" comparison table for all brand visual rules."""

PROMPT_DELIVER = """Output standardized full-case brand research and design deliverables: market trend analysis report, user aesthetic insight report, product visual gene report, TOP10 competitor benchmarking report, brand final tone positioning specification, full-link design traceability manual, brand unified visual standard library. All outputs must have clear research basis and complete reasoning chain, no empty subjective definition."""


# ── 数据模型 ──────────────────────────────────────────

@dataclass
class ModuleResult:
    """单个调研模块结果"""
    module_id: int
    name: str
    raw_output: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_s: float = 0.0


@dataclass
class FullCaseResult:
    """品牌全案完整结果"""
    brand: str = ""
    category: str = ""
    
    # 4调研模块
    market: ModuleResult = field(default_factory=lambda: ModuleResult(1, "市场行业趋势分析"))
    user: ModuleResult = field(default_factory=lambda: ModuleResult(2, "目标用户洞察分析"))
    product: ModuleResult = field(default_factory=lambda: ModuleResult(3, "产品基因分析"))
    competitor: ModuleResult = field(default_factory=lambda: ModuleResult(4, "TOP10竞品对标"))
    
    # 因果溯源
    traceability: ModuleResult = field(default_factory=lambda: ModuleResult(5, "因果溯源"))
    
    # 7交付物
    deliverables: Dict[str, str] = field(default_factory=dict)
    zip_path: str = ""
    
    generated_at: str = ""


class BrandFullCase:
    """品牌全案溯源系统 — 终极版块"""

    MODULES = [
        (1, "市场行业趋势分析", PROMPT_MARKET, "market"),
        (2, "目标用户审美洞察", PROMPT_USER, "user"),
        (3, "产品视觉基因分析", PROMPT_PRODUCT, "product"),
        (4, "TOP10竞品对标分析", PROMPT_COMPETITOR, "competitor"),
    ]

    def __init__(self, api_key: Optional[str] = None,
                 output_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "..", "..", "output", "brand-fullcase")
        os.makedirs(self.output_dir, exist_ok=True)
        self.results: Dict[str, ModuleResult] = {}

    def _call_gpt(self, prompt: str, context: str = "",
                  image_url: Optional[str] = None) -> Tuple[str, Dict]:
        """调用GPT-4o"""
        messages = [{"role": "user", "content": []}]
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\nReference data:\n{context[:3000]}"
        messages[0]["content"].append({"type": "text", "text": full_prompt})
        if image_url:
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": image_url, "detail": "high"}
            })
        
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.3,
            },
            timeout=120
        )
        if resp.status_code != 200:
            return "", {"error": f"API {resp.status_code}"}
        
        text = resp.json()["choices"][0]["message"]["content"]
        structured = {}
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            structured = json.loads(text[start:end])
        except:
            pass
        return text, structured

    def run_full_research(self, brand: str, category: str,
                          product_description: str = "",
                          image_url: Optional[str] = None,
                          competitor_urls: Optional[List[str]] = None) -> FullCaseResult:
        """执行完整的4模块调研 + 溯源 + 交付"""
        result = FullCaseResult(brand=brand, category=category)
        accumulated = []

        print(f"\n  🏛️  品牌全案溯源启动: {brand} ({category})")
        print()

        # ── 4调研模块 (串行，每个依赖前一个结果) ──
        for mid, name, prompt, key in self.MODULES:
            print(f"  📊 调研模块{mid}: {name}...", end=" ")
            t0 = time.time()
            
            ctx = "\n\n".join(accumulated[-2:]) if accumulated else ""
            raw, struct = self._call_gpt(prompt, ctx, image_url)
            
            module_result = ModuleResult(mid, name, raw, struct,
                                         duration_s=time.time()-t0)
            self.results[key] = module_result
            setattr(result, key, module_result)
            
            accumulated.append(f"[{name}]\n{raw[:1000]}")
            status = "✅" if raw else "❌"
            print(f"{status} ({module_result.duration_s:.1f}s)")

        # ── 因果溯源模块 ──
        print("  🔗 因果溯源模块...", end=" ")
        t0 = time.time()
        all_research = "\n\n".join([f"[{n}]\n{self.results[k].raw_output[:1500]}"
                                    for _, n, _, k in self.MODULES])
        raw, struct = self._call_gpt(PROMPT_TRACEABILITY, all_research)
        result.traceability = ModuleResult(5, "因果溯源", raw, struct,
                                           duration_s=time.time()-t0)
        print(f"{'✅' if raw else '❌'} ({result.traceability.duration_s:.1f}s)")

        # ── 7交付物生成 ──
        print("  📦 生成7套交付物...", end=" ")
        t0 = time.time()
        full_context = "\n\n".join([
            f"[Market]\n{result.market.raw_output[:1500]}",
            f"[User]\n{result.user.raw_output[:1500]}",
            f"[Product]\n{result.product.raw_output[:1500]}",
            f"[Competitor]\n{result.competitor.raw_output[:1500]}",
            f"[Traceability]\n{result.traceability.raw_output[:1500]}",
        ])
        raw, struct = self._call_gpt(PROMPT_DELIVER, full_context)
        
        # 生成7份独立文档
        docs = self._split_deliverables(raw, struct, brand)
        result.deliverables = docs
        result.zip_path = self._package_deliverables(docs, brand)
        
        dur = time.time()-t0
        print(f"✅ ({dur:.1f}s)")
        print(f"  📍 ZIP: {result.zip_path}")

        result.generated_at = datetime.utcnow().isoformat()
        return result

    def _split_deliverables(self, raw: str, struct: Dict,
                            brand: str) -> Dict[str, str]:
        """从GPT输出中拆分出7份独立文档"""
        docs = {}
        
        # 从结构化数据提取
        if struct:
            for i in range(1, 8):
                key = f"deliverable_{i}"
                val = struct.get(key, struct.get(f"doc_{i}", struct.get(f"report_{i}", "")))
                if isinstance(val, str) and val:
                    docs[f"deliverable_{i}"] = val

        # 如结构化提取不足，从raw text按标题拆分
        if len(docs) < 7:
            sections = raw.split("## ")
            for i, sec in enumerate(sections):
                if i > 0 and i <= 7:
                    docs.setdefault(f"deliverable_{i}", sec.strip())

        # 补齐到7份
        titles = [
            "市场行业趋势分析报告",
            "目标用户审美洞察报告",
            "品牌产品视觉基因分析报告",
            "TOP10竞品对标分析报告",
            "品牌视觉调性定调说明书",
            "全链路设计溯源手册",
            "品牌视觉规范库",
        ]
        full_raw = raw
        for i, title in enumerate(titles, 1):
            key = f"deliverable_{i}"
            if key not in docs or not docs[key]:
                docs[key] = f"# {title}\n\n{full_raw[:2000]}\n\n(内容由AI生成)"

        return docs

    def _package_deliverables(self, docs: Dict[str, str], brand: str) -> str:
        """打包7份交付物为ZIP"""
        import zipfile
        import io
        
        session = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_path = os.path.join(self.output_dir, f"{brand}_{session}")
        os.makedirs(dir_path, exist_ok=True)

        titles = [
            "01_市场行业趋势分析报告",
            "02_目标用户审美洞察报告",
            "03_品牌产品视觉基因分析报告",
            "04_TOP10竞品对标分析报告",
            "05_品牌视觉调性定调说明书",
            "06_全链路设计溯源手册",
            "07_品牌视觉规范库",
        ]

        zip_path = os.path.join(self.output_dir, f"{brand}_品牌全案_{session}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (key, title) in enumerate(zip(
                [f"deliverable_{i+1}" for i in range(7)], titles)):
                content = docs.get(key, f"# {title}\n\n(待生成)")
                fname = f"{title}.md"
                filepath = os.path.join(dir_path, fname)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                zf.write(filepath, fname)

            # 写summary
            summary = {
                "brand": brand,
                "deliverables": titles,
                "generated_at": datetime.utcnow().isoformat(),
            }
            zf.writestr("summary.json", json.dumps(summary, ensure_ascii=False, indent=2))

        return zip_path

    @staticmethod
    def generate_master_prompt() -> str:
        """生成终极一键总控Prompt"""
        return """Complete brand full-case research and visual tone positioning closed-loop analysis. Conduct market trend research, target user aesthetic psychology insight, brand product gene sorting, and in-depth benchmarking of top 10 competitors in the same category. Summarize industry mainstream styles, homogenization pain points and market blank opportunities. Determine the brand's exclusive visual tonality, color system, light and shadow tone, layout grid, scene collocation and font system based on research data. For each design rule and tone decision, output complete traceable "research basis + design purpose + market value" logic, form a complete brand visual specification system and design traceability manual, realize all brand design decisions are data-driven and logically explainable."""
