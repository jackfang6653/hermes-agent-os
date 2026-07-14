"""
6 项 AI 设计研究模块 — 精确实现文档提示词

模块 1: 全元素参数拆解 — Visual Element Quantitative Analyzer
模块 2: 设计原理溯源 WHY — Design Principle Traceability Researcher
模块 3: 品类规则自动归纳 — Category Design Rule Inducer
模块 4: 品牌调性沉淀 — Brand Visual Tone Researcher
模块 5: AI 自主学习迭代 — Self-Learning Iteration Engine
模块 6: 标准化最终产出 — Standardized Deliverables Generator
"""
import os, json, requests, time
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# ── 严格匹配文档的 6 段 Prompt ───────────────────────

PROMPT_MODULE_1 = """You are a visual element quantitative analyzer. Traverse every element in the image and detail page without omission: main product, decorative ornaments, background, texture, light shadow, text, font, spacing, blank area. Quantify position, proportion, size ratio, color HEX, material texture, layer hierarchy, spacing distance, alignment, text size/line spacing/paragraph spacing. Bind ACR histogram and full tonal parameters. Output structured parameter table and element dependency relationship."""

PROMPT_MODULE_2 = """You are a design principle traceability researcher. For every element layout, proportion, color matching, material collocation, decoration placement, font style, spacing setting in the picture, independently analyze the complete "why" design logic. Analyze from product attribute, visual balance, consumer psychology, scene atmosphere, brand tone, e-commerce conversion six dimensions. Explain the rationality of hard and soft material collocation, color echo, proportion restriction, visual focus guidance and hierarchical design. Extract reusable design rules for each design decision."""

PROMPT_MODULE_3 = """You are a category design rule inducer. Collect multiple homogeneous product page cases, eliminate accidental individual design, summarize fixed general rules of the category. Induce unified standards for ornament collocation, color matching range, layout grid, proportion specification, font matching system, picture tone and histogram baseline. Classify mandatory fixed rules and optional variable rules, output complete category design specification manual."""

PROMPT_MODULE_4 = """You are a brand visual tone researcher. Aggregate all category design rules of the same brand, extract brand exclusive visual DNA: brand consistent color system, light and shadow tone preference, composition habit, material matching tendency, font tone, layout style, scene atmosphere positioning. Summarize brand high-end/household/minimalist/luxury style orientation, target user portrait and brand visual differentiation characteristics, form brand visual system research report."""

PROMPT_MODULE_5 = """Automatically compare new image cases with existing category rules and brand database. If consistent, strengthen rule learning; if new reasonable design appears, expand rule library and add new branch; if design is unreasonable, mark abnormal records. Automatically integrate samples, optimize rule framework, update version iteration log, realize continuous self-optimization of design knowledge base."""

PROMPT_MODULE_6 = """According to the research process, output standardized complete deliverables including: 1.Element parameter disassembled data sheet 2.Design cause traceability analysis report 3.Category unified design specification manual 4.Brand tone research & visual system report 5.ACR histogram tone preset library 6.Knowledge base iteration version log. Output all content with Markdown directory + structured JSON data."""


@dataclass
class ResearchResult:
    """一次研究的结果"""
    module_id: int
    module_name: str
    raw_output: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_s: float = 0.0


class ResearchModule:
    """单个AI研究模块 — 执行GPT调用+解析结果"""

    def __init__(self, module_id: int, name: str, prompt: str, api_key: str):
        self.module_id = module_id
        self.name = name
        self.prompt = prompt
        self.api_key = api_key

    def run(self, image_url: Optional[str] = None, context: Optional[str] = None) -> ResearchResult:
        """执行一次GPT调用"""
        t0 = time.time()
        try:
            messages = [{"role": "user", "content": []}]
            
            # 系统指令
            system_content = self.prompt
            if context:
                system_content += f"\n\nAdditional context: {context}"
            messages[0]["content"].append({"type": "text", "text": system_content})
            
            # 如果提供图片URL，附加图片
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
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"} if self.module_id in (1, 6) else None,
                },
                timeout=120
            )
            if resp.status_code != 200:
                return ResearchResult(self.module_id, self.name, error=f"API error {resp.status_code}",
                                      duration_s=time.time()-t0)
            
            text = resp.json()["choices"][0]["message"]["content"]
            structured = {}
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                structured = json.loads(text[start:end])
            except:
                pass
            
            return ResearchResult(self.module_id, self.name, raw_output=text,
                                  structured_data=structured, duration_s=time.time()-t0)
        except Exception as e:
            return ResearchResult(self.module_id, self.name, error=str(e), duration_s=time.time()-t0)


class ResearchEngine:
    """6 项研究引擎 — 按序执行全部模块"""
    
    MODULES = [
        (1, "全元素参数拆解", PROMPT_MODULE_1),
        (2, "设计原理溯源 WHY", PROMPT_MODULE_2),
        (3, "品类规则自动归纳", PROMPT_MODULE_3),
        (4, "品牌调性沉淀研究", PROMPT_MODULE_4),
        (5, "AI自主学习迭代", PROMPT_MODULE_5),
        (6, "标准化最终产出", PROMPT_MODULE_6),
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.results: Dict[int, ResearchResult] = {}

    def run_all(self, image_url: Optional[str] = None, context: Optional[str] = None) -> Dict[int, ResearchResult]:
        """顺序执行全部6个模块（模块依赖前置结果）"""
        accumulated_context = context or ""
        
        for mid, name, prompt in self.MODULES:
            print(f"  📦 模块{mid}: {name}...", end=" ")
            t0 = time.time()
            
            if mid == 3 and self.results.get(2):
                # 模块3依赖模块2的设计规则
                accumulated_context += f"\n\n[Previous analysis results]: {self.results[2].raw_output[:2000]}"
            elif mid == 4 and self.results.get(3):
                accumulated_context += f"\n\n[Category rules]: {self.results[3].raw_output[:2000]}"
            elif mid == 5:
                cat_rules = self.results.get(3)
                brand_dna = self.results.get(4)
                ctx = ""
                if cat_rules: ctx += f"[Category rules]: {cat_rules.raw_output[:1500]}\n"
                if brand_dna: ctx += f"[Brand DNA]: {brand_dna.raw_output[:1500]}"
                accumulated_context += f"\n\n{ctx}"
            
            module = ResearchModule(mid, name, prompt, self.api_key)
            result = module.run(image_url, accumulated_context if mid > 1 else context)
            self.results[mid] = result
            
            dur = time.time() - t0
            status = "✅" if not result.error else "❌"
            print(f"{status} ({dur:.1f}s)")
            if result.error:
                print(f"    错误: {result.error}")

        return self.results

    def get_deliverable(self, module_id: int) -> Optional[ResearchResult]:
        return self.results.get(module_id)

    def all_passed(self) -> bool:
        return len(self.results) == 6 and all(not r.error for r in self.results.values())

    @staticmethod
    def generate_master_prompt() -> str:
        """生成终极置顶系统提示词 — 一键全开所有能力"""
        return f"""# AI Brand Design Research System — Master Prompt

## Role
You are a full-stack AI brand design research & production system. You operate as 6 synchronized modules working together.

## Module Chain (execute in order, each feeds into the next)

### [M1] Visual Element Quantitative Analyzer
{PROMPT_MODULE_1}

### [M2] Design Principle Traceability Researcher
{PROMPT_MODULE_2}

### [M3] Category Design Rule Inducer
{PROMPT_MODULE_3}

### [M4] Brand Visual Tone Researcher
{PROMPT_MODULE_4}

### [M5] Self-Learning Iteration Engine
{PROMPT_MODULE_5}

### [M6] Standardized Deliverables Generator
{PROMPT_MODULE_6}

## Output Format
After completing all modules, output 6 standardized deliverables:
1. `element_parameters.json` — Full element parameter data sheet
2. `design_rationale.md` — Design cause traceability analysis report
3. `category_spec.md` — Category unified design specification manual
4. `brand_visual_system.md` — Brand tone research & visual system report
5. `acr_presets.json` — ACR histogram tone preset library
6. `iteration_log.md` — Knowledge base iteration version log

## Constraints
- Every parameter must be quantified, not described qualitatively
- Every design decision must explain WHY from 6 dimensions
- Category rules must distinguish mandatory vs optional
- Brand DNA must aggregate across all categories
- Knowledge base must track version and iteration history
- Final output must include both Markdown and structured JSON"""
