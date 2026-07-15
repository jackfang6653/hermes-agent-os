"""
4A品牌案例自进化引擎 — 自动研究顶尖4A公司案例 → 丰富品牌DNA库

流程:
1. 搜索4A公司最新品牌设计案例
2. 分析案例的设计参数/色彩/版式/WHY
3. 提取可复用的设计模式
4. 存入品牌DNA数据库 → 优化决策数据支撑
5. 定时执行 (cron)
"""
import os
import json
import requests
import time
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


# ── 4A公司列表 ────────────────────────────────────────

TOP_4A_AGENCIES = [
    {"name": "Ogilvy", "url": "https://www.ogilvy.com", "network": "WPP"},
    {"name": "Saatchi & Saatchi", "url": "https://saatchi.com", "network": "Publicis"},
    {"name": "BBDO", "url": "https://www.bbdo.com", "network": "Omnicom"},
    {"name": "Droga5", "url": "https://www.droga5.com", "network": "Accenture"},
    {"name": "Pentagram", "url": "https://www.pentagram.com", "network": "Independent"},
    {"name": "Landor", "url": "https://landor.com", "network": "WPP"},
    {"name": "Wolff Olins", "url": "https://www.wolffolins.com", "network": "Independent"},
    {"name": "Interbrand", "url": "https://www.interbrand.com", "network": "Omnicom"},
    {"name": "Siegel+Gale", "url": "https://www.siegelgale.com", "network": "Omnicom"},
    {"name": "Studio Dumbar", "url": "https://www.studiodumbar.com", "network": "Independent"},
]


@dataclass
class AgencyCase:
    """4A公司的一个品牌设计案例"""
    agency: str = ""
    brand: str = ""                      # 服务品牌
    project_name: str = ""               # 项目名称
    url: str = ""                        # 案例URL
    category: str = ""                   # 品牌全案/VI/包装/数字
    
    # 设计参数
    design_parameters: Dict[str, Any] = field(default_factory=dict)
    color_palette: List[str] = field(default_factory=list)
    typography: Dict[str, Any] = field(default_factory=dict)
    layout_patterns: List[str] = field(default_factory=list)
    visual_grammar: Dict[str, Any] = field(default_factory=dict)
    
    # WHY分析
    design_rationale: str = ""           # 为什么这样设计
    strategic_thinking: str = ""         # 策略思考
    consumer_insight: str = ""           # 消费者洞察
    differentiation: str = ""            # 差异化策略
    
    # 元数据
    source: str = ""
    extracted_at: str = ""
    confidence: float = 0.0


class FourAResearcher:
    """4A公司品牌案例研究引擎"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.cases: List[AgencyCase] = []
        self.knowledge_base = None

    def connect_knowledge_base(self, kb):
        """连接品牌知识库"""
        self.knowledge_base = kb

    # ── 搜索 ──────────────────────────────────────────

    def search_agency_cases(self, agency_name: str, limit: int = 3) -> List[str]:
        """搜索某4A公司的最新品牌案例"""
        urls = []
        queries = [
            f"{agency_name} brand identity case study {datetime.now().year}",
            f"{agency_name} visual identity design project",
            f"{agency_name} branding portfolio",
        ]
        for q in queries:
            try:
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": q},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                )
                if r.ok:
                    found = re.findall(r'<a[^>]*href="(https?://[^"]*)"[^>]*>', r.text)
                    for u in found:
                        if agency_name.lower().replace(" ","") in u.lower() and u not in urls:
                            urls.append(u)
            except:
                pass
            time.sleep(0.5)
        return urls[:limit]

    def fetch_case_content(self, url: str) -> Optional[str]:
        """获取案例页面内容"""
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.ok:
                text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:6000]
        except:
            pass
        return None

    # ── 分析 ──────────────────────────────────────────

    def analyze_case(self, agency: str, brand: str = "", url: str = "",
                     content: Optional[str] = None) -> AgencyCase:
        """用GPT分析一个品牌案例（无需网页内容，GPT用内部知识分析）"""
        if not self.api_key:
            return AgencyCase(agency=agency, brand=brand, url=url, source="no_api_key")

        brand_info = f"品牌: {brand}" if brand else "(知名品牌客户)"
        prompt = f"""你是一位顶尖品牌策略总监。分析这家4A公司为品牌做的设计案例。

4A Agency: {agency}
{brand_info}
{"URL: " + url if url else ""}

请基于你的专业知识和训练数据，分析这家4A公司的典型品牌设计风格和方法论。
即使你不知道具体案例细节，也可以根据该公司的市场定位和设计声誉进行分析。

输出JSON:
{{
    "project_name": "典型项目类型",
    "category": "擅长领域",
    "design_parameters": {{
        "color_strategy": "色彩策略特点",
        "typography_style": "字体风格",
        "layout_approach": "版式方法",
        "visual_language": "视觉语言特征",
        "brand_expression": "品牌表达方式"
    }},
    "color_palette": ["典型用色"],
    "typography": {{"heading":"常用字体","body":"常用字体"}},
    "layout_patterns": ["常用版式模式"],
    "visual_grammar": {{"composition":"构图","hierarchy":"层级","rhythm":"节奏","balance":"平衡"}},
    "design_rationale": "WHY——该公司的设计哲学和核心理念",
    "strategic_thinking": "策略思考方法",
    "consumer_insight": "消费者洞察方法",
    "differentiation": "差异化策略",
    "extracted_patterns": ["可复用的设计模式"],
    "key_parameters": {{
        "contrast_style": "对比风格",
        "color_temperature": "色调冷暖",
        "information_density": 0.5,
        "visual_hierarchy_clarity": 0.8,
        "brand_consistency": 0.9
    }}
}}
"""
        try:
            if not self.api_key:
                return AgencyCase(agency=agency, brand=brand, url=url, source="no_api_key")

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
                timeout=60
            )
            if resp.status_code != 200:
                return AgencyCase(agency=agency, brand=brand, url=url, source=f"api_error_{resp.status_code}")

            text = resp.json()["choices"][0]["message"]["content"]
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])

            return AgencyCase(
                agency=agency, brand=brand, url=url,
                project_name=data.get("project_name", ""),
                category=data.get("category", ""),
                design_parameters=data.get("design_parameters", {}),
                color_palette=data.get("color_palette", []),
                typography=data.get("typography", {}),
                layout_patterns=data.get("layout_patterns", []),
                visual_grammar=data.get("visual_grammar", {}),
                design_rationale=data.get("design_rationale", ""),
                strategic_thinking=data.get("strategic_thinking", ""),
                consumer_insight=data.get("consumer_insight", ""),
                differentiation=data.get("differentiation", ""),
                source="gpt_analysis",
                extracted_at=datetime.utcnow().isoformat(),
                confidence=0.7,
            )
        except Exception as e:
            return AgencyCase(agency=agency, brand=brand, url=url, source=f"error:{e}")

    # ── 批量研究 ──────────────────────────────────────

    def research_top_agencies(self, max_cases_per_agency: int = 2) -> List[AgencyCase]:
        """研究TOP 4A公司的最新案例"""
        all_cases = []
        for agency_info in TOP_4A_AGENCIES[:5]:  # 前5家
            name = agency_info["name"]
            url = agency_info["url"]
            print(f"  🔍 分析: {name}...", end=" ")
            
            case = self.analyze_case(name, "", url)
            if case.source == "gpt_analysis":
                all_cases.append(case)
                print(f"✅ ({case.design_rationale[:40]}...)")
            else:
                print(f"❌ ({case.source})")
            time.sleep(1.5)  # 避免限流

        self.cases.extend(all_cases)
        return all_cases

    # ── 入库 ──────────────────────────────────────────

    def save_to_knowledge_base(self):
        """将研究的案例存入品牌知识库"""
        if not self.knowledge_base:
            print("  ⚠️  未连接知识库")
            return 0

        count = 0
        for case in self.cases:
            if case.source != "gpt_analysis":
                continue
            brand = case.brand or f"4a_case_{case.agency}"
            self.knowledge_base.save_knowledge(
                brand, "4a_case_study",
                {
                    "agency": case.agency,
                    "project": case.project_name,
                    "url": case.url,
                    "design_parameters": case.design_parameters,
                    "color_palette": case.color_palette,
                    "typography": case.typography,
                    "layout_patterns": case.layout_patterns,
                    "visual_grammar": case.visual_grammar,
                    "design_rationale": case.design_rationale,
                    "strategic_thinking": case.strategic_thinking,
                    "consumer_insight": case.consumer_insight,
                    "differentiation": case.differentiation,
                }
            )
            # 也存一份到品牌档案
            profile = self._build_profile_from_case(case)
            self.knowledge_base.save_brand(profile)
            count += 1

        return count

    def _build_profile_from_case(self, case: AgencyCase):
        """从案例构建品牌档案"""
        from knowledge.brand_knowledge import BrandProfile
        return BrandProfile(
            brand_name=case.brand or f"{case.agency}_case",
            category=case.category,
            brand_positioning=case.strategic_thinking[:200] if case.strategic_thinking else "",
            brand_personality=["4A_case"],
            primary_palette=case.color_palette[:6],
            layout_patterns=case.layout_patterns,
            confidence=case.confidence,
        )


# ── 自进化调度器 ──────────────────────────────────────

class EvolutionScheduler:
    """品牌DNA自进化调度器"""

    def __init__(self, researcher: FourAResearcher, knowledge_base=None):
        self.researcher = researcher
        self.knowledge_base = knowledge_base
        self.history: List[Dict] = []

    def run_evolution_cycle(self, deep_research: bool = False) -> Dict[str, Any]:
        """执行一轮自进化"""
        print(f"\n  🧬 品牌DNA自进化周期 [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"  {'='*40}")

        cycle = {
            "started_at": datetime.utcnow().isoformat(),
            "steps": {},
        }

        # Step 1: 研究4A案例
        print("  📡 阶段1: 研究4A公司案例...")
        try:
            cases = self.researcher.research_top_agencies(
                max_cases_per_agency=2 if deep_research else 1
            )
            cycle["steps"]["research"] = f"{len(cases)} cases"
            print(f"     获取 {len(cases)} 个案例")
        except Exception as e:
            cycle["steps"]["research"] = f"❌ {e}"
            print(f"     ❌ {e}")

        # Step 2: 入库
        print("  💾 阶段2: 存入品牌知识库...")
        try:
            if cases:
                if self.knowledge_base:
                    saved = self.researcher.save_to_knowledge_base()
                    cycle["steps"]["store"] = f"{saved} saved"
                    print(f"     存入 {saved} 条")
                else:
                    cycle["steps"]["store"] = "no kb"
                    print("     无知识库连接，跳过")
            else:
                cycle["steps"]["store"] = "no cases"
        except Exception as e:
            cycle["steps"]["store"] = f"❌ {e}"

        # Step 3: 优化WHY数据
        print("  🤔 阶段3: 分析设计WHY逻辑...")
        try:
            rationale_count = len([c for c in self.researcher.cases if c.design_rationale])
            cycle["steps"]["why"] = f"{rationale_count} rationales"
            print(f"     {rationale_count} 条设计理念")
        except Exception as e:
            cycle["steps"]["why"] = f"❌ {e}"

        cycle["completed_at"] = datetime.utcnow().isoformat()
        cycle["total_cases"] = len(self.researcher.cases)
        self.history.append(cycle)
        return cycle

    def generate_evolution_report(self) -> str:
        """生成进化报告"""
        lines = ["# 品牌DNA自进化报告", f"生成时间: {datetime.now().isoformat()}", ""]
        lines.append("## 总览")
        lines.append(f"- 4A公司: {len(TOP_4A_AGENCIES)} 家")
        lines.append(f"- 已研究案例: {len(self.researcher.cases)} 个")
        lines.append(f"- 进化周期: {len(self.history)} 轮")
        lines.append("")
        
        if self.researcher.cases:
            lines.append("## 最新案例")
            for c in self.researcher.cases[-5:]:
                lines.append(f"- [{c.agency}] {c.project_name or c.brand}")
                if c.design_rationale:
                    lines.append(f"  WHY: {c.design_rationale[:100]}...")
        
        return "\n".join(lines)
