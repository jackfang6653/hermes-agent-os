"""
深度品牌研究引擎 — 多源全网抓取 + 全维度分析

工作流:
1. 多源搜索 (Bing/DDG/Google)
2. 并行抓取 (5-10个页面)
3. GPT-4o 全维度分析
4. 输出丰富结构化DNA

输出格式 (最终):
- brand_profile: 品牌档案 (定位/历史/理念)
- visual_dna: 视觉DNA (色彩/字体/版式/构图/摄影)
- market_position: 市场定位 (价格/人群/差异化)
- competitor_landscape: 竞争格局 (TOP5竞品分析)
- design_patterns: 设计模式 (提取可复用规则)
- why_rationale: WHY溯源 (每条设计决策的依据)
- trend_alignment: 趋势契合度
"""
import os, json, requests, re, time, hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed


class DeepBrandResearcher:
    """深度品牌研究引擎"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        self.cache: Dict[str, str] = {}

    # ── 搜索层 (多源) ──

    def search_brand(self, brand: str, category: str = "") -> List[str]:
        """多源搜索品牌信息 (Bing + DDG + 直接抓取已知站点)"""
        urls = []
        queries = [
            f"{brand} brand identity visual system",
            f"{brand} design philosophy logo color",
        ]
        if category:
            queries.insert(0, f"{category} brand {brand}")
        
        # Bing搜索
        for q in queries:
            try:
                results = self._search_bing(q, 5)
                urls.extend(results)
            except:
                pass
            if len(urls) >= 10:
                break

        # 去重
        seen = set()
        unique = []
        for u in urls:
            # 过滤无效URL
            if any(domain in u for domain in ['bing.com','microsoft.com','r.bing']):
                continue
            u = u.split('?')[0]  # 去掉查询参数
            if u not in seen and len(u) < 200:
                seen.add(u)
                unique.append(u)
        
        return unique[:12]

    def _search_bing(self, query: str, limit: int = 5) -> List[str]:
        """Bing搜索提取真实结果"""
        urls = []
        r = self.session.get(
            "https://www.bing.com/search",
            params={"q": query, "count": limit},
            timeout=10
        )
        if r.ok:
            # 提取<li class="b_algo">中的真实链接
            for match in re.finditer(r'<a[^>]*href="(https?://[^"]*)"[^>]*>', r.text):
                u = match.group(1)
                # 跳过Bing自身的链接
                if any(skip in u for skip in ['bing.com','go.microsoft','r.bing']):
                    continue
                if u.startswith(('http://','https://')):
                    urls.append(u)
        return urls[:limit]

    def _search_duck(self, query: str, limit: int = 2) -> List[str]:
        """DuckDuckGo搜索"""
        urls = []
        r = self.session.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=8
        )
        if r.ok:
            for match in re.finditer(r'<a[^>]*href="(https?://[^"]+)"', r.text):
                u = match.group(1)
                if u.startswith(("https://", "http://")):
                    urls.append(u)
        return urls[:limit]

    # ── 抓取层 (并行) ──

    def fetch_pages(self, urls: List[str], max_pages: int = 8) -> Dict[str, str]:
        """并行抓取多个页面"""
        results = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futs = {pool.submit(self._fetch_single, u): u for u in urls[:max_pages]}
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    text = fut.result()
                    if text:
                        results[u] = text
                except:
                    pass
        return results

    def _fetch_single(self, url: str) -> Optional[str]:
        """抓取单个页面并提取正文"""
        if url in self.cache:
            return self.cache[url]
        try:
            r = self.session.get(url, timeout=10)
            if not r.ok:
                return None
            text = r.text
            # 提取正文: 去掉script/style标签
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = text[:5000]  # 截断
            self.cache[url] = text
            return text
        except:
            return None

    # ── 分析层 (GPT全维度) ──

    def analyze_brand(self, brand: str, category: str = "",
                      pages: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """用GPT进行全维度品牌分析"""
        if not self.api_key:
            return self._fallback_analysis(brand, category)

        # 构建页面上下文
        context_parts = []
        if pages:
            for url, text in list(pages.items())[:6]:
                context_parts.append(f"[Source: {url}]\n{text[:2000]}")
        context = "\n\n---\n\n".join(context_parts) if context_parts else ""
        no_data_note = ""
        if not pages or len(pages) == 0:
            no_data_note = """[IMPORTANT] No web data was successfully retrieved. Use ONLY your extensive training knowledge about this brand.
You MUST still provide a comprehensive analysis. World's best-known brands like Nike, Apple, MUJI, IKEA etc. are well-documented in your training.
For less known brands, infer from their category and positioning.
DO NOT output minimal data just because web fetch failed. You have the knowledge - use it."""

        prompt = f"""You are a senior brand strategist and design critic at a top 4A agency. Analyze the brand comprehensively.

Brand: {brand}
Category: {category or "general"}

{no_data_note}

{context[:12000]}

Output complete JSON with ALL sections populated. Aim for:
- 3-5 primary colors with hex codes and WHY for each
- 2-4 secondary colors
- Detailed typography analysis
- 3-5 top competitors with visual style analysis
- 3-5 design patterns with extractable rules
- 3-5 key design decisions with WHY rationale

```json
{{
    "brand_profile": {{ ... }},
    "visual_dna": {{
        "color_system": {{
            "primary_colors": [{{"name":"","hex":"#HEX","usage":"","why":""}}],
            "secondary_colors": [],
            "accent_colors": [],
            "color_psychology": "",
            "color_temperature": "",
            "contrast_style": ""
        }},
        "typography": {{
            "heading_font": {{"name":"","category":"","weights":[],"why":""}},
            "body_font": {{"name":"","category":"","why":""}},
            "type_scale": "",
            "line_height": ""
        }},
        "layout_grid": {{"type":"","columns":"","information_density":0.5,"white_space_usage":""}},
        "photography_style": {{"lighting_setup":"","color_tone":"","composition":"","product_staging":""}}
    }},
    "market_position": {{"price_tier":"","differentiation":"","competitors":[""]}},
    "competitor_landscape": {{
        "top_competitors": [
            {{"name":"","positioning":"","visual_style":"","strength":"","weakness":"","our_differentiation":""}}
        ]
    }},
    "design_patterns": [
        {{"pattern_name":"","description":"","category":"","extractable_rule":"","why_effective":""}}
    ],
    "why_rationale": {{
        "overall_design_philosophy": "",
        "key_design_decisions": [
            {{"decision":"","supporting_research":"","psychological_effect":"","market_value":""}}
        ]
    }},
    "extracted_parameters": {{
        "camera_style":"","lighting_temperature":"","contrast_range":"","saturation_level":"","information_hierarchy":""
    }}
}}
```
"""

        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8192,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
                timeout=120
            )
            if not resp.ok:
                return self._fallback_analysis(brand, category)
            
            text = resp.json()["choices"][0]["message"]["content"]
            # Parse JSON from response
            start = text.index("{")
            end = text.rindex("}") + 1
            result = json.loads(text[start:end])
            
            result["_meta"] = {
                "brand": brand,
                "category": category,
                "sources": list(pages.keys()) if pages else [],
                "analyzed_at": datetime.utcnow().isoformat(),
                "model": "gpt-4o",
                "pages_analyzed": len(pages) if pages else 0,
            }
            return result
            
        except Exception as e:
            return self._fallback_analysis(brand, category, error=str(e))

    def _fallback_analysis(self, brand: str, category: str = "", error: str = "") -> Dict[str, Any]:
        """降级分析"""
        return {
            "brand_profile": {"full_name": brand, "short_description": f"{category}品牌", "brand_philosophy": ""},
            "visual_dna": {"color_system": {"primary_colors": []}, "typography": {}, "layout_grid": {}},
            "market_position": {"price_tier": "mid", "competitors": []},
            "design_patterns": [],
            "why_rationale": {"key_design_decisions": []},
            "_meta": {"brand": brand, "error": error, "fallback": True, "analyzed_at": datetime.utcnow().isoformat()}
        }

    # ── 全流程 ──

    def full_research(self, brand: str, category: str = "") -> Dict[str, Any]:
        """全流程: 搜索-抓取-分析-输出"""
        print(f"\n  🔍 深度研究: {brand} ({category})")
        
        # Step 1: 搜索
        print("  📡 多源搜索...", end=" ")
        urls = self.search_brand(brand, category)
        print(f"{len(urls)} URLs")
        for u in urls[:5]:
            print(f"     {u}")

        # Step 2: 抓取
        print("  📄 并行抓取...", end=" ")
        pages = self.fetch_pages(urls, 8)
        print(f"{len(pages)} 页成功")
        
        # Step 3: 分析
        print("  🧠 GPT全维度分析...", end=" ")
        result = self.analyze_brand(brand, category, pages)
        ok = "error" not in result.get("_meta", {})
        print(f"{'✅' if ok else '⚠️'} (fallback)" if not ok else "✅")
        
        # 摘要
        profile = result.get("brand_profile", {})
        dna = result.get("visual_dna", {})
        print(f"\n  📊 分析摘要:")
        print(f"     定位: {profile.get('short_description','')[:60]}")
        print(f"     色彩: {len(dna.get('color_system',{}).get('primary_colors',[]))} 主色")
        print(f"     字体: {dna.get('typography',{}).get('heading_font',{}).get('name','')}")
        print(f"     竞品: {len(result.get('competitor_landscape',{}).get('top_competitors',[]))} 家")
        print(f"     模式: {len(result.get('design_patterns',[]))} 条")
        print(f"     决策: {len(result.get('why_rationale',{}).get('key_design_decisions',[]))} 条")
        
        return result

    def save_result(self, result: Dict[str, Any], output_dir: str = "output/brand_dna"):
        """保存结果为JSON"""
        brand = result.get("_meta", {}).get("brand", "unknown")
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{brand.lower().replace(' ','_')}_dna.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  💾 保存到: {path}")
        return path
