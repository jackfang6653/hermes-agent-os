"""
品牌研究员 — 自动抓取、分析、理解品牌设计

核心能力：
1. 自动抓取品牌官网/电商详情页
2. 分析页面版式设计（为什么要这样排版）
3. 识别设计模式和工具链
4. 理解设计效果和目的
5. 产出结构化设计报告
"""
import os, json, requests, re, time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote, quote
from bs4 import BeautifulSoup


@dataclass
class DesignRationale:
    """设计理念分析 — WHY"""
    layout_purpose: str = ""              # 排版目的 e.g. "引导视线从产品→细节→购买"
    visual_hierarchy: List[str] = field(default_factory=list)  # 视觉层级
    psychological_effect: str = ""         # 心理效果 e.g. "营造高端信任感"
    target_audience: str = ""              # 目标受众
    brand_positioning: str = ""            # 品牌定位
    conversion_goal: str = ""              # 转化目标
    design_principles: List[str] = field(default_factory=list)  # 设计原则
    cultural_context: str = ""             # 文化背景


@dataclass
class DesignPattern:
    """设计模式"""
    name: str = ""
    category: str = ""                    # layout/color/typography/spacing
    description: str = ""
    effect: str = ""                       # 产生的效果
    used_by_brands: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class BrandDesignReport:
    """品牌设计完整分析报告"""
    brand_name: str = ""
    source_url: str = ""
    
    # 设计分析
    layout_analysis: str = ""              # 版式分析
    design_rationale: DesignRationale = field(default_factory=DesignRationale)
    design_patterns: List[DesignPattern] = field(default_factory=list)
    
    # 工具链
    tools_detected: List[str] = field(default_factory=list)  # 检测到的设计工具
    workflow_estimated: str = ""           # 估计的工作流程
    
    # 色彩系统
    primary_palette: List[str] = field(default_factory=list)
    secondary_palette: List[str] = field(default_factory=list)
    color_relationship: str = ""           # 色彩关系描述
    color_psychology: str = ""             # 色彩心理学分析
    
    # 排版
    typography: Dict[str, Any] = field(default_factory=dict)
    grid_system: str = ""
    
    # 场景
    scene_composition: str = ""            # 场景构成
    prop_placement_rationale: str = ""     # 配饰摆放理由
    lighting_mood: str = ""                # 灯光氛围
    
    # 元数据
    analyzed_at: str = ""
    confidence: float = 0.0
    raw_analysis: str = ""


class BrandResearcher:
    """品牌研究员 — 自动研究品牌设计"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def research_brand(self, brand_name: str, urls: Optional[List[str]] = None) -> BrandDesignReport:
        """
        研究一个品牌的完整设计体系
        
        流程：
        1. 搜索品牌信息
        2. 抓取产品页面
        3. 分析设计体系
        4. 理解设计理念
        5. 产出完整报告
        """
        if not self.api_key:
            raise ValueError("需要 OPENAI_API_KEY")

        # 如果没有提供URL，自动搜索
        if not urls:
            urls = self._search_brand_urls(brand_name)

        # 抓取并分析页面
        all_analyses = []
        for url in urls[:3]:  # 最多分析3页
            try:
                html = self._fetch_page(url)
                if html:
                    analysis = self._analyze_page_design(brand_name, url, html)
                    all_analyses.append(analysis)
            except Exception as e:
                print(f"  ⚠️  {url}: {e}")

        # 综合所有分析
        if all_analyses:
            return self._synthesize_report(brand_name, all_analyses, urls[0] if urls else "")
        
        # 如果没有抓取成功，用GPT直接分析品牌
        return self._analyze_brand_from_knowledge(brand_name)

    def _search_brand_urls(self, brand: str) -> List[str]:
        """自动搜索品牌相关URL — DDG HTML + Bing + Wikipedia + GitHub

        使用 requests + BeautifulSoup4 + re 进行多引擎搜索，
        任一引擎失败不影响其他，返回汇总后去重的 URL 列表。
        """
        urls = []
        seen = set()

        # --- 1. DuckDuckGo HTML 搜索 (requests + BeautifulSoup + re) ---
        ddg_queries = [
            f"{brand} official website",
            f"{brand} product design",
            f"{brand} brand design style",
        ]
        for q in ddg_queries:
            try:
                for u in self._search_ddg_html(q):
                    if u not in seen:
                        urls.append(u)
                        seen.add(u)
            except Exception:
                pass
            time.sleep(0.3)

        # --- 1.5. Bing 搜索 (DDG 被限流时的回退) ---
        if len(urls) < 3:
            try:
                for q in ddg_queries[:2]:
                    for u in self._search_bing(q):
                        if u not in seen:
                            urls.append(u)
                            seen.add(u)
            except Exception:
                pass
            time.sleep(0.3)

        # --- 2. Wikipedia API ---
        try:
            for u in self._search_wikipedia(brand):
                if u not in seen:
                    urls.append(u)
                    seen.add(u)
        except Exception:
            pass

        # --- 3. GitHub API (搜索品牌相关仓库) ---
        try:
            for u in self._search_github(brand):
                if u not in seen:
                    urls.append(u)
                    seen.add(u)
        except Exception:
            pass

        # --- 4. Fallback: 推测常见品牌URL ---
        if len(urls) < 3:
            for u in self._guess_brand_urls(brand):
                if u not in seen:
                    urls.append(u)
                    seen.add(u)

        return urls[:10]

    def _search_ddg_html(self, query: str) -> List[str]:
        """DuckDuckGo HTML 搜索结果解析 — requests + BeautifulSoup4 + re

        优先使用 BeautifulSoup 解析 DDG HTML 结果页；
        若 DDG 返回空或反爬页面，回退到 re 正则提取 uddg 链接；
        若仍无结果，返回空列表让调用方走其他搜索源。
        """
        urls = []
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
        except requests.RequestException:
            return urls
        if r.status_code not in (200, 202):
            return urls

        # ── 方法1: BeautifulSoup 解析已知选择器 ──
        soup = BeautifulSoup(r.text, "html.parser")
        result_selectors = [".result__body", ".result", ".results_links", ".web-result",
                            "a.result__a", "a[class*=\"result\"]", ".links_main a"]
        for selector in result_selectors:
            for el in soup.select(selector):
                link_el = el if el.name == "a" else el.select_one("a")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if not href:
                    continue
                actual_url = self._decode_ddg_url(href)
                if actual_url not in urls:
                    urls.append(actual_url)

        # ── 方法2: re 正则回退，直接解析 HTML 中的 uddg=... 参数 ──
        if not urls:
            raw = r.text
            # 匹配 uddg=<urlencoded_url> 模式
            uddg_matches = re.findall(r'uddg=([^&\'\"]+)', raw)
            for encoded in uddg_matches:
                try:
                    actual_url = unquote(encoded)
                    if actual_url not in urls:
                        urls.append(actual_url)
                except Exception:
                    pass

            # 备用: 直接匹配 https?:// 链接（排除搜索引擎自身）
            if not urls:
                raw_urls = re.findall(r'https?://[^\s\'\"<>]+', raw)
                for u in raw_urls:
                    u_clean = u.rstrip('.,;:)')
                    if 'duckduckgo.com' not in u_clean and 'google.com' not in u_clean:
                        if u_clean not in urls and len(u_clean) > 20:
                            urls.append(u_clean)

        # ── 过滤搜索引擎页面 ──
        skip_domains = ["duckduckgo.com", "google.com", "bing.com", "yahoo.com",
                        "yandex.com", "baidu.com", "startpage.com", "brave.com"]
        urls = [u for u in urls if not any(d in u.lower() for d in skip_domains)]

        return urls

    def _search_bing(self, query: str) -> List[str]:
        """Bing 搜索 — requests + re 解析 (DDG 不可用时的回退)"""
        urls = []
        try:
            r = requests.get(
                "https://www.bing.com/search",
                params={"q": query, "count": "10"},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=12,
            )
        except requests.RequestException:
            return urls
        if r.status_code != 200:
            return urls

        # 用 re 提取 URL — Bing 结果页中外部链接通常出现在 href 属性里
        raw = r.text
        # 方案1: 匹配 Bing 重定向格式内的真实 URL
        href_matches = re.findall(r'href="(https?://[^"]+)"', raw)
        for href in href_matches:
            if len(href) < 30:
                continue
            skip = ["bing.com", "microsoft.com", "live.com", "msn.com", "go.microsoft.com"]
            if any(s in href.lower() for s in skip):
                continue
            if href not in urls:
                urls.append(href)

        # 方案2: 匹配所有可见域名
        if not urls:
            domain_matches = re.findall(r'(?:https?://)?([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}[^\s<>\"\')\]]*', raw)
            seen_domains = set()
            for dm in domain_matches:
                dm_clean = dm.strip('.,;:!?')
                if dm_clean.startswith('http'):
                    full = dm_clean
                else:
                    full = f"https://{dm_clean}"
                domain_part = urlparse(full).netloc.lower()
                if domain_part and domain_part not in seen_domains:
                    skip = ["bing.com", "microsoft.com", "live.com", "msn.com",
                            "w3.org", "schema.org"]
                    if not any(s in domain_part for s in skip):
                        seen_domains.add(domain_part)
                        urls.append(full)

        return urls

    @staticmethod
    def _decode_ddg_url(href: str) -> str:
        """解码 DDG HTML 重定向链接，提取真实 URL"""
        if "uddg=" in href:
            full = "https:" + href if href.startswith("//") else href
            parsed = urlparse(full)
            uddg = parse_qs(parsed.query).get("uddg", [None])[0]
            if uddg:
                return unquote(uddg)
        return href

    def _search_wikipedia(self, brand: str) -> List[str]:
        """Wikipedia API 搜索品牌页面"""
        urls = []
        try:
            r = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": brand,
                    "srlimit": 3,
                    "format": "json",
                },
                headers={"User-Agent": "BrandResearchBot/1.0"},
                timeout=10,
            )
        except requests.RequestException:
            return urls
        if not r.ok:
            return urls

        data = r.json()
        for page in data.get("query", {}).get("search", []):
            title = page.get("title", "")
            if title:
                safe_title = title.replace(" ", "_")
                urls.append(f"https://en.wikipedia.org/wiki/{quote(safe_title)}")
        return urls

    def _search_github(self, brand: str) -> List[str]:
        """GitHub API 搜索品牌相关仓库"""
        urls = []
        github_token = os.environ.get("GITHUB_TOKEN", "")
        headers = {
            "User-Agent": "BrandResearchBot/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": brand, "per_page": 3, "sort": "stars"},
                headers=headers,
                timeout=10,
            )
        except requests.RequestException:
            return urls
        if not r.ok:
            return urls

        data = r.json()
        for item in data.get("items", []):
            html_url = item.get("html_url", "")
            if html_url:
                urls.append(html_url)
        return urls

    def _guess_brand_urls(self, brand: str) -> List[str]:
        """Fallback: 推测常见品牌URL"""
        brand_lower = brand.lower().replace(" ", "")
        return [
            f"https://www.{brand_lower}.com",
            f"https://en.wikipedia.org/wiki/{quote(brand)}",
        ]

    def _fetch_page(self, url: str) -> Optional[str]:
        """抓取页面内容"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; BrandResearchBot/1.0)"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.ok:
                # 提取可读文本
                text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:8000]  # 截取前8000字符
        except:
            return None

    def _analyze_page_design(self, brand: str, url: str, html: str) -> Dict[str, Any]:
        """分析单页面的设计体系"""
        prompt = f"""你是一位资深品牌设计策略师和4A创意总监。分析这个品牌页面的设计体系。

品牌: {brand}
URL: {url}
页面内容:
{html[:6000]}

请输出JSON分析：

1. layout_analysis: 版式分析 — 为什么这样排版？视觉流是什么？
2. design_rationale: {{
    "layout_purpose": "排版目的",
    "visual_hierarchy": ["视觉层级1", "视觉层级2"],
    "psychological_effect": "对用户产生的心理效果",
    "target_audience": "目标受众",
    "brand_positioning": "品牌定位",
    "conversion_goal": "转化目标",
    "design_principles": ["设计原则"],
    "cultural_context": "文化背景"
   }}
3. design_patterns: [{{"name":"模式名","category":"layout/color/typography","description":"描述","effect":"效果"}}]
4. tools_detected: ["检测到的工具"]
5. primary_palette: ["#hex"]
6. secondary_palette: ["#hex"]
7. color_relationship: "色彩关系描述"
8. color_psychology: "色彩心理学分析"
9. typography: {{"font_families":[],"heading_style":"","body_style":""}}
10. grid_system: "grid描述"
11. scene_composition: "场景构成描述"
12. prop_placement_rationale: "配饰摆放的理由"
13. lighting_mood: "灯光氛围"
14. workflow_estimated: "估计的工作流程"

重点理解 WHY：为什么要这样设计？达到了什么效果？"""
        return self._call_gpt(prompt)

    def _analyze_brand_from_knowledge(self, brand: str) -> BrandDesignReport:
        """当无法抓取时，用GPT的已有知识分析品牌"""
        prompt = f"""作为品牌设计策略师，分析"{brand}"的品牌设计体系。

输出JSON:
{{
    "layout_analysis": "该品牌典型的版式风格",
    "design_rationale": {{...}},
    "design_patterns": [...],
    "tools_detected": [...],
    "primary_palette": [...],
    "secondary_palette": [...],
    "color_relationship": "...",
    "color_psychology": "...",
    "typography": {{...}},
    "grid_system": "...",
    "scene_composition": "...",
    "prop_placement_rationale": "...",
    "lighting_mood": "...",
    "workflow_estimated": "..."
}}
"""
        data = self._call_gpt(prompt)
        return self._to_report(data, brand, "")

    def _call_gpt(self, prompt: str) -> Dict[str, Any]:
        """调用GPT-4o分析"""
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3,
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

    def _synthesize_report(self, brand: str, analyses: List[Dict], url: str) -> BrandDesignReport:
        """综合多个页面的分析为完整报告"""
        # 合并分析结果
        combined = {}
        for a in analyses:
            for k, v in a.items():
                if k not in combined:
                    combined[k] = v
                elif isinstance(v, list):
                    if isinstance(combined[k], list):
                        combined[k].extend(v)
                    else:
                        combined[k] = v
                elif isinstance(v, dict) and isinstance(combined[k], dict):
                    combined[k].update(v)

        return self._to_report(combined, brand, url)

    def _to_report(self, data: Dict, brand: str, url: str) -> BrandDesignReport:
        rationale = data.get("design_rationale", {})
        patterns = data.get("design_patterns", [])
        return BrandDesignReport(
            brand_name=brand,
            source_url=url,
            layout_analysis=data.get("layout_analysis", ""),
            design_rationale=DesignRationale(
                layout_purpose=rationale.get("layout_purpose", ""),
                visual_hierarchy=rationale.get("visual_hierarchy", []),
                psychological_effect=rationale.get("psychological_effect", ""),
                target_audience=rationale.get("target_audience", ""),
                brand_positioning=rationale.get("brand_positioning", ""),
                conversion_goal=rationale.get("conversion_goal", ""),
                design_principles=rationale.get("design_principles", []),
                cultural_context=rationale.get("cultural_context", ""),
            ),
            design_patterns=[DesignPattern(**p) if isinstance(p, dict) else DesignPattern() for p in patterns],
            tools_detected=data.get("tools_detected", []),
            workflow_estimated=data.get("workflow_estimated", ""),
            primary_palette=data.get("primary_palette", []),
            secondary_palette=data.get("secondary_palette", []),
            color_relationship=data.get("color_relationship", ""),
            color_psychology=data.get("color_psychology", ""),
            typography=data.get("typography", {}),
            grid_system=data.get("grid_system", ""),
            scene_composition=data.get("scene_composition", ""),
            prop_placement_rationale=data.get("prop_placement_rationale", ""),
            lighting_mood=data.get("lighting_mood", ""),
            analyzed_at=datetime.utcnow().isoformat(),
            confidence=0.75,
            raw_analysis=json.dumps(data, ensure_ascii=False),
        )
