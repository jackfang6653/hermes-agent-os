"""
4A 品牌设计自动化流水线 — CEO 主入口 (v3: page_modules 集成 + 并行 + 缓存 + 降级)

完整流程:
1. 接收输入（产品图URL or 品牌名）
2. URL → page_crawler 抓取分块 → acr_analyzer 逐个并行分析 → style_engine 生成 → validator 校验
3. 保留原有 research/knowledge/dna_engine 调用
4. 缓存: 同一URL 30分钟内不重复抓取
5. 并行: 多个模块的ACR分析同时进行
6. 降级: 某个模块失败不影响其他模块
7. 输出: 包含详细JSON报告 + 图片ZIP

用法：
    from production.pipeline import BrandDesignPipeline
    
    # 从一个产品详情页URL
    result = await pipeline.run_from_image("https://example.com/product/123")
    
    # 从一个品牌名
    result = pipeline.run_from_brand("NORHOR 北欧表情")
"""
import os
import sys
import io
import zipfile
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class BrandDesignPipeline:
    """4A品牌设计全自动流水线 (v3: page_modules + 并行 + 缓存 + 降级)"""

    # ── 降级默认值 ────────────────────────────────────────
    DEFAULT_PALETTE = ["#f5f0e8", "#d4c5b0", "#8b7355", "#2c2c2c"]
    DEFAULT_STYLE = "nordic"
    DEFAULT_CATEGORY = "furniture"
    DEFAULT_MATERIAL = "fabric"
    DEFAULT_COLOR = "beige"

    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None,
                 cache_dir: Optional[str] = None, cache_ttl_minutes: int = 30):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.output_dir = output_dir or os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "brand-pipeline"))
        os.makedirs(self.output_dir, exist_ok=True)

        # ── 缓存: brand_name → result ──────────────────────
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_minutes = cache_ttl_minutes

        # ── page_modules ────────────────────────────────────
        self._page_crawler = None
        self._acr_analyzer = None
        self._style_library = None
        self._prompt_gen = None
        self._validator = None
        self._page_cache_dir = cache_dir

        # 延迟加载各模块（避免循环依赖）
        self._researcher = None
        self._design_analyzer = None
        self._color_analyzer = None
        self._scene_parser = None
        self._scene_renderer = None
        self._knowledge = None
        self._patterns = None
        self._trend_tracker = None
        self._image_gen = None

        # 标记降级模式
        self._degraded = not bool(self.api_key)

    # ═══════════════════════════════════════════════════════
    #  延迟加载（带错误隔离）
    # ═══════════════════════════════════════════════════════

    def _lazy_load(self) -> Dict[str, bool]:
        """延迟加载所有子模块，每个模块独立 try/except。
           返回 {module_name: loaded_successfully} 映射。
        """
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        status: Dict[str, bool] = {}

        # ── page_modules ──
        if not self._page_crawler:
            try:
                from page_modules.page_crawler import PageCrawler
                self._page_crawler = PageCrawler()
                status["page_crawler"] = True
            except Exception as e:
                status["page_crawler"] = False
                print(f"  ⚠️  PageCrawler 加载失败: {e}")

        if not self._acr_analyzer:
            try:
                from page_modules.acr_analyzer import ACRAnalyzer
                self._acr_analyzer = ACRAnalyzer(api_key=self.api_key)
                status["acr_analyzer"] = True
            except Exception as e:
                status["acr_analyzer"] = False
                print(f"  ⚠️  ACRAnalyzer 加载失败: {e}")

        if not self._style_library:
            try:
                from page_modules.style_engine import StyleLibrary, PromptGenerator
                self._style_library = StyleLibrary()
                self._prompt_gen = PromptGenerator()
                status["style_engine"] = True
            except Exception as e:
                status["style_engine"] = False
                print(f"  ⚠️  StyleEngine 加载失败: {e}")

        if not self._validator:
            try:
                from page_modules.validator import Validator
                if self._acr_analyzer:
                    self._validator = Validator(self._acr_analyzer)
                else:
                    status["validator"] = False
                if self._validator:
                    status["validator"] = True
            except Exception as e:
                status["validator"] = False
                print(f"  ⚠️  Validator 加载失败: {e}")

        # ── BrandResearcher ──
        if not self._researcher:
            try:
                from research.brand_researcher import BrandResearcher
                self._researcher = BrandResearcher(self.api_key)
                status["researcher"] = True
            except Exception as e:
                status["researcher"] = False
                print(f"  ⚠️  BrandResearcher 加载失败: {e}")

        # ── DesignAnalyzer ──
        if not self._design_analyzer:
            try:
                from research.design_analyzer import DesignAnalyzer
                self._design_analyzer = DesignAnalyzer(self.api_key)
                status["design_analyzer"] = True
            except Exception as e:
                status["design_analyzer"] = False
                print(f"  ⚠️  DesignAnalyzer 加载失败: {e}")

        # ── ColorSystemAnalyzer ──
        if not self._color_analyzer:
            try:
                from research.color_system import ColorSystemAnalyzer
                self._color_analyzer = ColorSystemAnalyzer(self.api_key)
                status["color_analyzer"] = True
            except Exception as e:
                status["color_analyzer"] = False
                print(f"  ⚠️  ColorSystemAnalyzer 加载失败: {e}")

        # ── SceneParser ──
        if not self._scene_parser:
            try:
                from dna_engine.scene_parser import SceneParser
                self._scene_parser = SceneParser(self.api_key)
                status["scene_parser"] = True
            except Exception as e:
                status["scene_parser"] = False
                print(f"  ⚠️  SceneParser 加载失败: {e}")

        # ── SceneRenderer ──
        if not self._scene_renderer:
            try:
                from dna_engine.scene_renderer import SceneRenderer
                self._scene_renderer = SceneRenderer()
                status["scene_renderer"] = True
            except Exception as e:
                status["scene_renderer"] = False
                print(f"  ⚠️  SceneRenderer 加载失败: {e}")

        # ── BrandKnowledgeBase + BrandProfile ──
        if not self._knowledge:
            try:
                from knowledge.brand_knowledge import BrandKnowledgeBase, BrandProfile
                self._knowledge = BrandKnowledgeBase()
                self._BrandProfile = BrandProfile
                status["knowledge"] = True
            except Exception as e:
                status["knowledge"] = False
                print(f"  ⚠️  BrandKnowledgeBase 加载失败: {e}")

        # ── DesignPatternLibrary ──
        if not self._patterns:
            try:
                from knowledge.design_knowledge import DesignPatternLibrary
                self._patterns = DesignPatternLibrary()
                status["patterns"] = True
            except Exception as e:
                status["patterns"] = False
                print(f"  ⚠️  DesignPatternLibrary 加载失败: {e}")

        # ── TrendTracker ──
        if not self._trend_tracker:
            try:
                from research.trend_tracker import TrendTracker
                self._trend_tracker = TrendTracker()
                status["trend_tracker"] = True
            except Exception as e:
                status["trend_tracker"] = False
                print(f"  ⚠️  TrendTracker 加载失败: {e}")

        # ── Image Generator ──
        if not self._image_gen:
            img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "norhor", "src")
            if os.path.exists(os.path.join(img_path, "detail_image_gen.py")):
                try:
                    sys.path.insert(0, img_path)
                    import importlib
                    self._image_gen = importlib.import_module("detail_image_gen").generate_detail_images
                    status["image_gen"] = True
                except Exception as e_:
                    status["image_gen"] = False
                    status["image_gen_error"] = str(e_)
            else:
                status["image_gen"] = False
                status["image_gen_error"] = f"File not found: {img_path}"

        return status

    # ═══════════════════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════════════════

    @property
    def is_degraded(self) -> bool:
        """是否运行在降级模式（无API key = 仅使用本地知识库）"""
        return self._degraded

    def _can_use_vision(self) -> bool:
        """是否有能力调用视觉/LLM 分析"""
        return bool(self.api_key) and not self._degraded

    def _lookup_knowledge(self, brand_name: str) -> Dict[str, Any]:
        """降级策略：从知识库查找已有品牌数据"""
        fallback = {
            "brand_name": brand_name,
            "source": "knowledge_fallback",
            "palette": self.DEFAULT_PALETTE,
            "style": self.DEFAULT_STYLE,
            "category": self.DEFAULT_CATEGORY,
            "material": self.DEFAULT_MATERIAL,
            "color": self.DEFAULT_COLOR,
        }
        if not self._knowledge:
            return fallback
        try:
            brands = self._knowledge.list_brands() if hasattr(self._knowledge, "list_brands") else []
            for b in brands:
                if brand_name.lower() in str(b).lower():
                    fallback["source"] = "knowledge_match"
                    fallback["match"] = str(b)
                    return fallback
        except Exception:
            pass
        return fallback

    @staticmethod
    def _record_step(step_status: dict, step: str, ok: bool, detail: Any = None,
                     error: str = "", duration: float = 0.0, degraded: bool = False):
        """记录单个步骤状态"""
        step_status[step] = {
            "success": ok,
            "detail": detail,
            "error": error,
            "duration_sec": round(duration, 3),
            "degraded": degraded,
        }

    # ═══════════════════════════════════════════════════════
    #  核心流程: run_from_image (v3 — page_modules 集成)
    # ═══════════════════════════════════════════════════════

    def run_from_image(self, image_url: str, brand_name: Optional[str] = None,
                       force_refresh: bool = False) -> Dict[str, Any]:
        """从一张产品图/URL启动全自动品牌设计 (v3: page_modules + 并行 + 缓存 + 降级)

        新流程:
          URL → page_crawler 抓取分块 → acr_analyzer 并行分析 → style_engine 生成
          → validator 校验 → (可选) 品牌研究/知识库 → image_gen 生成图片

        Args:
            image_url: 产品详情页URL或图片URL
            brand_name: 品牌名（可选，不提供则自动推断）
            force_refresh: 是否跳过缓存

        Returns:
            包含 status, step_status, page_modules_report, validation_report, 
            style_spec, output 等字段的详细报告
        """
        t_start = time.monotonic()
        load_status = self._lazy_load()

        print(f"\n  {'='*60}")
        print("  🏭 4A Design Pipeline v3 — 从图片/URL启动")
        print(f"  {'='*60}")
        print(f"  📸 输入: {image_url}")
        if brand_name:
            print(f"  🏷️  品牌: {brand_name}")
        print(f"  🔑 API: {'✅ 已配置' if self._can_use_vision() else '⚠️  降级模式'}")
        print(f"  🗂️  输出目录: {self.output_dir}")
        print()

        step_status: Dict[str, Dict[str, Any]] = {}
        _rec = lambda step, ok, detail=None, error="", dur=0.0: self._record_step(
            step_status, step, ok, detail, error, dur, not self._can_use_vision()
        )

        # ───────────────────────────────────────────────────
        # Phase 1: page_modules 流程
        # ───────────────────────────────────────────────────

        # Step 1: page_crawler — 抓取分块
        print("  🕷️  [page_modules] Step 1: 页面抓取分块...")
        t1 = time.monotonic()
        crawl_result = None
        crawl_data = None

        if self._page_crawler:
            try:
                crawl_result = self._page_crawler.crawl(image_url, force_refresh=force_refresh)
                crawl_data = crawl_result.to_dict() if hasattr(crawl_result, 'to_dict') else None
                _rec("page_crawler", True,
                     f"抓取完成: {len(crawl_result.chunks)} 个分块, {crawl_result.total_images} 张图片",
                     dur=time.monotonic() - t1)
                print(f"     ✅ {len(crawl_result.chunks)} 个分块, {crawl_result.total_images} 张图片")
            except Exception as e:
                _rec("page_crawler", False, None, error=str(e), dur=time.monotonic() - t1)
                print(f"     ❌ 抓取失败: {e}")
        else:
            _rec("page_crawler", False, None, error="PageCrawler 未加载", dur=0)

        # Step 2: acr_analyzer — 并行分析所有分块
        print("  🔬 [page_modules] Step 2: ACR 并行分析...")
        t2 = time.monotonic()
        acr_result_data = None

        if self._acr_analyzer and crawl_result and crawl_result.chunks:
            try:
                acr_result = self._acr_analyzer.analyze_chunks(
                    crawl_result.chunks,
                    url=image_url,
                    title=getattr(crawl_result, 'title', ''),
                    parallel=True  # 多模块并行分析
                )
                acr_result_data = acr_result.to_dict() if hasattr(acr_result, 'to_dict') else None
                _rec("acr_analyzer", True,
                     f"{acr_result.modules_succeeded}/{acr_result.modules_total} 模块成功"
                     + (f", {acr_result.modules_failed} 失败(已降级)" if acr_result.modules_failed else ""),
                     dur=time.monotonic() - t2)
                print(f"     ✅ {acr_result.modules_succeeded}/{acr_result.modules_total} 模块分析成功"
                      + (f", {acr_result.modules_failed} 降级" if acr_result.modules_failed else ""))
            except Exception as e:
                _rec("acr_analyzer", False, None, error=str(e), dur=time.monotonic() - t2)
                print(f"     ❌ ACR分析失败: {e}")
        else:
            _rec("acr_analyzer", False, None,
                 error="ACRAnalyzer 未加载 或 无分块数据", dur=0)

        # Step 3: style_engine — 生成设计样式
        print("  🎨 [page_modules] Step 3: 样式引擎生成...")
        t3 = time.monotonic()
        style_spec_data = None

        if self._style_engine and acr_result_data:
            try:
                style_spec = self._style_engine.generate(
                    acr_result_data,
                    brand_name=brand_name or "",
                    source_urls=[image_url]
                )
                style_spec_data = style_spec.to_dict() if hasattr(style_spec, 'to_dict') else None
                _rec("style_engine", True,
                     f"样式主题: {style_spec.style_theme}, 色彩: {len(style_spec.primary_palette)}色",
                     dur=time.monotonic() - t3)
                print(f"     ✅ 样式主题: {style_spec.style_theme}")
            except Exception as e:
                _rec("style_engine", False, None, error=str(e), dur=time.monotonic() - t3)
                print(f"     ❌ 样式生成失败: {e}")
        else:
            _rec("style_engine", False, None,
                 error="StyleEngine 未加载 或 无ACR结果", dur=0)

        # Step 4: validator — 校验
        print("  ✅ [page_modules] Step 4: 结果校验...")
        t4 = time.monotonic()
        validation_data = None

        if self._validator:
            try:
                validation = self._validator.validate(
                    style_spec_data or {},
                    acr_result_data or {},
                    crawl_data or {}
                )
                validation_data = validation.to_dict() if hasattr(validation, 'to_dict') else None
                _rec("validator", validation.passed,
                     f"评分: {validation.score}/100, {'PASS' if validation.passed else 'FAIL'}",
                     error="" if validation.passed else f"{validation.errors} errors, {validation.warnings} warnings",
                     dur=time.monotonic() - t4)
                print(f"     {'✅' if validation.passed else '⚠️'}  评分: {validation.score}/100 "
                      f"({'PASS' if validation.passed else 'FAIL'})")
            except Exception as e:
                _rec("validator", False, None, error=str(e), dur=time.monotonic() - t4)
                print(f"     ❌ 校验失败: {e}")
        else:
            _rec("validator", False, None, error="Validator 未加载", dur=0)

        # ───────────────────────────────────────────────────
        # Phase 2: 原有流程 — 品牌研究 / DNA引擎 / 知识库
        # ───────────────────────────────────────────────────

        # Step 5: 品牌网络研究 (如果提供了品牌名)
        print("  🔍 Phase 2: 品牌研究...")
        t5 = time.monotonic()
        research_result = None
        resolved_brand = brand_name

        if brand_name and self._researcher:
            try:
                if self._can_use_vision():
                    research_result = self._researcher.research_brand(brand_name)
                    _rec("brand_research", True, "品牌研究完成", dur=time.monotonic() - t5)
                    print("     ✅ 品牌研究完成")
                else:
                    fallback = self._lookup_knowledge(brand_name)
                    _rec("brand_research", True, fallback,
                         error="降级模式 — 使用知识库", dur=time.monotonic() - t5)
                    print("     ⚠️  降级: 使用知识库数据")
            except Exception as e:
                _rec("brand_research", False, None, error=str(e), dur=time.monotonic() - t5)
                print(f"     ❌ 品牌研究失败: {e}")
        elif not brand_name:
            # 从ACR结果推断品牌名
            if acr_result_data and acr_result_data.get("title"):
                resolved_brand = acr_result_data["title"]
            else:
                resolved_brand = f"brand_{hash(image_url) % 10000}"
            _rec("brand_research", True, f"推断品牌: {resolved_brand}",
                 error="未提供品牌名，自动推断", dur=time.monotonic() - t5)
        else:
            _rec("brand_research", False, None, error="BrandResearcher 未加载", dur=time.monotonic() - t5)

        # Step 6: 并行 — 设计分析 + 色彩分析 + 场景图解析
        print("  ⚡ Phase 2 并行: 设计/色彩/场景分析...")
        time.monotonic()
        parallel_results = {}

        if self._can_use_vision():
            def _do_design():
                t = time.monotonic()
                if not self._design_analyzer:
                    return ("design_analysis", False, None, "DesignAnalyzer 未加载", time.monotonic() - t)
                try:
                    result = self._design_analyzer.analyze_design(image_url)
                    return ("design_analysis", True, result, "", time.monotonic() - t)
                except Exception as e:
                    return ("design_analysis", False, None, str(e), time.monotonic() - t)

            def _do_color():
                t = time.monotonic()
                if not self._color_analyzer:
                    return ("color_system", False, None, "ColorSystemAnalyzer 未加载", time.monotonic() - t)
                try:
                    result = self._color_analyzer.analyze(image_url)
                    return ("color_system", True, result, "", time.monotonic() - t)
                except Exception as e:
                    return ("color_system", False, None, str(e), time.monotonic() - t)

            def _do_scene():
                t = time.monotonic()
                if not self._scene_parser:
                    return ("scene_graph", False, None, "SceneParser 未加载", time.monotonic() - t)
                try:
                    sg = self._scene_parser.parse(image_url)
                    return ("scene_graph", True, sg.to_dict(), "", time.monotonic() - t)
                except Exception as e:
                    return ("scene_graph", False, None, str(e), time.monotonic() - t)

            max_workers = min(6, (os.cpu_count() or 2))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(_do_design): "design",
                    executor.submit(_do_color): "color",
                    executor.submit(_do_scene): "scene",
                }
                for future in as_completed(futures):
                    name, ok, detail, err, dur = future.result()
                    _rec(name, ok, str(detail)[:100] if detail else None, error=err, dur=dur)
                    parallel_results[name] = {"ok": ok, "data": detail}
        else:
            for name in ("design_analysis", "color_system", "scene_graph"):
                _rec(name, True, "降级 — 跳过视觉分析", error="降级模式", dur=0)
                parallel_results[name] = {"ok": True, "data": None}

        design_analysis = parallel_results.get("design_analysis", {}).get("data")
        color_system = parallel_results.get("color_system", {}).get("data")
        scene_graph_json = parallel_results.get("scene_graph", {}).get("data") or {}

        # Step 7: 知识库存储
        print("  💾 知识库存储...")
        t7 = time.monotonic()
        if self._knowledge:
            try:
                if research_result:
                    profile = self._knowledge.build_from_research(
                        resolved_brand,
                        research_result.__dict__ if hasattr(research_result, '__dict__') else {}
                    )
                else:
                    palette = []
                    if color_system and hasattr(color_system, 'primary_palette'):
                        palette = color_system.primary_palette
                    elif style_spec_data:
                        palette = style_spec_data.get("color_system", {}).get("primary_palette", [])
                    profile = self._BrandProfile(brand_name=resolved_brand, primary_palette=palette)
                    self._knowledge.save_brand(profile)

                if self._patterns and design_analysis:
                    self._patterns.add_from_analysis(design_analysis, resolved_brand)
                _rec("knowledge_store", True, "品牌已入库", dur=time.monotonic() - t7)
                print("     ✅ 品牌知识已入库")
            except Exception as e:
                _rec("knowledge_store", False, None, error=str(e), dur=time.monotonic() - t7)
                print(f"     ❌ 入库失败: {e}")
        else:
            _rec("knowledge_store", False, None, error="KnowledgeBase 未加载", dur=time.monotonic() - t7)

        # Step 8: 趋势
        print("  📈 趋势收集...")
        t8 = time.monotonic()
        trends = []
        if self._trend_tracker:
            try:
                trends = self._trend_tracker.learn_from_trends()
                _rec("trends", True, f"{len(trends)}条", dur=time.monotonic() - t8)
            except Exception as e:
                _rec("trends", False, [], error=str(e), dur=time.monotonic() - t8)
        else:
            _rec("trends", True, [], error="TrendTracker 未加载", dur=time.monotonic() - t8)

        # ───────────────────────────────────────────────────
        # Phase 3: 图片生成
        # ───────────────────────────────────────────────────
        print("  🖼️  图片生成...")
        t9 = time.monotonic()
        zip_path = ""

        if self._image_gen:
            try:
                brand = resolved_brand or "unknown"
                palette = list(self.DEFAULT_PALETTE)
                style_str = self.DEFAULT_STYLE

                # 优先使用 style_engine 的输出
                if style_spec_data:
                    cs = style_spec_data.get("color_system", {})
                    if cs.get("primary_palette"):
                        palette = cs["primary_palette"]
                    if style_spec_data.get("style_theme"):
                        style_str = style_spec_data["style_theme"]
                elif color_system:
                    if hasattr(color_system, 'primary_palette') and color_system.primary_palette:
                        palette = color_system.primary_palette
                    if hasattr(color_system, 'temperature'):
                        style_str = color_system.temperature or style_str

                output_path = os.path.join(self.output_dir, brand.lower().replace(' ', '_'))
                zip_path = self._image_gen(
                    product_name=f"{brand} 系列",
                    category=self.DEFAULT_CATEGORY,
                    material=self.DEFAULT_MATERIAL,
                    color=self.DEFAULT_COLOR,
                    style=style_str,
                    scene="品牌场景",
                    brand_score=0.85,
                    palette=palette,
                    output_dir=output_path,
                )
                _rec("image_gen", True, zip_path, dur=time.monotonic() - t9)
                print(f"     ✅ 图片已生成: {zip_path}")
            except Exception as e:
                zip_path = f"Image generation error: {e}"
                _rec("image_gen", False, zip_path, error=str(e), dur=time.monotonic() - t9)
                print(f"     ❌ 生成失败: {e}")
        else:
            _rec("image_gen", False, "", error="ImageGen 未加载", dur=time.monotonic() - t9)

        # ───────────────────────────────────────────────────
        # 汇总报告
        # ───────────────────────────────────────────────────
        total_dur = time.monotonic() - t_start
        all_ok = all(s["success"] for s in step_status.values())
        ok_count = sum(1 for s in step_status.values() if s["success"])

        print(f"\n  {'='*60}")
        print(f"  {'✅' if all_ok else '⚠️'}  流水线完成 ({ok_count}/{len(step_status)} 步骤成功)")
        print(f"  ⏱️  总耗时: {total_dur:.1f}s")
        print(f"  📍 输出: {self.output_dir}")
        print(f"  {'='*60}")

        # 写入缓存
        cache_key = image_url.lower().strip()
        result = {
            "input_url": image_url,
            "brand": resolved_brand,
            "status": "success" if all_ok else "partial",
            "output_path": self.output_dir,
            "zip_file": zip_path,
            "load_status": load_status,
            "degraded": not self._can_use_vision(),
            "from_cache": False,
            "completed_at": _now_iso(),
            "total_duration_sec": round(total_dur, 1),
            "steps_total": len(step_status),
            "steps_succeeded": ok_count,
            "step_status": step_status,

            # page_modules 输出
            "page_modules": {
                "crawl_result": crawl_data,
                "acr_result": acr_result_data,
                "style_spec": style_spec_data,
                "validation": validation_data,
            },

            # 原有流程输出
            "design_analysis": str(design_analysis)[:500] if design_analysis else None,
            "color_system": str(color_system)[:500] if color_system else None,
            "scene_graph": scene_graph_json if isinstance(scene_graph_json, dict) else {},
            "design_patterns_learned": len(trends),

            "knowledge_base": {
                "brands": self._knowledge.list_brands() if self._knowledge else [],
                "patterns_available": len(self._patterns.search()) if self._patterns else 0,
            },
            "summary": {
                "page_crawled": crawl_result is not None and crawl_result.chunks,
                "acr_analyzed": acr_result_data is not None,
                "style_generated": style_spec_data is not None,
                "validated": validation_data is not None,
                "validation_passed": validation_data.get("passed", False) if validation_data else False,
                "research_done": research_result is not None,
                "knowledge_saved": step_status.get("knowledge_store", {}).get("success", False),
                "images_generated": (isinstance(zip_path, str) and bool(zip_path)
                                     and os.path.exists(str(zip_path))),
                "parallel_executed": True,
                "degraded_mode": not self._can_use_vision(),
            },
        }

        self._cache[cache_key] = result
        return result

    # ═══════════════════════════════════════════════════════
    #  核心流程: run_from_brand (v3 — page_modules 集成)
    # ═══════════════════════════════════════════════════════

    def run_from_brand(self, brand_name: str, urls: Optional[List[str]] = None,
                       force_refresh: bool = False) -> Dict[str, Any]:
        """从一个品牌名启动全自动品牌设计 (v3: page_modules + 并行 + 缓存 + 降级)

        新流程:
          品牌名 → 搜索URL → page_crawler 抓取分块 → acr_analyzer 并行分析
          → style_engine 生成 → validator 校验 → 品牌研究/知识库 → image_gen

        Args:
            brand_name: 品牌名称
            urls: 可选的URL列表（不提供则自动搜索）
            force_refresh: 是否强制刷新缓存

        Returns:
            包含 status, step_status, page_modules_report, validation_report 等的详细报告
        """
        t_start = time.monotonic()
        load_status = self._lazy_load()

        # ── 缓存命中检查 ──────────────────────────────────
        cache_key = brand_name.lower().strip()
        if not force_refresh and cache_key in self._cache:
            print(f"  💾 缓存命中 — 直接返回 {brand_name} 的已有结果")
            cached = dict(self._cache[cache_key])
            cached["from_cache"] = True
            cached["cached_at"] = self._cache[cache_key].get("completed_at", "unknown")
            return cached

        print(f"\n  {'='*60}")
        print("  🏭 4A Design Pipeline v3 — 从品牌名启动")
        print(f"  {'='*60}")
        print(f"  🏷️  品牌: {brand_name}")
        print(f"  🔑 API: {'✅ 已配置' if self._can_use_vision() else '⚠️  降级模式'}")
        print(f"  🗂️  输出目录: {self.output_dir}")
        print()

        step_status: Dict[str, Dict[str, Any]] = {}
        _rec = lambda step, ok, detail=None, error="", dur=0.0: self._record_step(
            step_status, step, ok, detail, error, dur, not self._can_use_vision()
        )

        # ───────────────────────────────────────────────────
        # Step 1: 搜索品牌URL
        # ───────────────────────────────────────────────────
        print("  🔍 阶段1: 搜索品牌URL...")
        t1 = time.monotonic()
        target_urls = urls or []

        if not target_urls and self._researcher:
            try:
                target_urls = self._researcher._search_brand_urls(brand_name)
                _rec("search_urls", True, f"找到 {len(target_urls)} 个URL",
                     dur=time.monotonic() - t1)
                print(f"     ✅ 找到 {len(target_urls)} 个URL")
            except Exception as e:
                # 降级：推测品牌URL
                target_urls = [f"https://www.{brand_name.lower().replace(' ', '')}.com"]
                _rec("search_urls", True, target_urls,
                     error=f"搜索失败，使用推测URL: {e}", dur=time.monotonic() - t1)
                print(f"     ⚠️  搜索失败，使用推测URL: {target_urls[0]}")
        elif not target_urls:
            target_urls = [f"https://www.{brand_name.lower().replace(' ', '')}.com"]
            _rec("search_urls", True, target_urls,
                 error="BrandResearcher未加载，使用推测URL", dur=time.monotonic() - t1)

        # ───────────────────────────────────────────────────
        # Phase 1: page_modules 流程 (对找到的每个URL)
        # ───────────────────────────────────────────────────
        all_acr_results = []
        best_style_spec_data = None
        best_validation_data = None
        best_crawl_data = None

        # 限制分析的URL数量
        urls_to_crawl = target_urls[:5]

        for idx, url in enumerate(urls_to_crawl):
            print(f"\n  ── 分析URL [{idx+1}/{len(urls_to_crawl)}]: {url} ──")

            # Step 2: page_crawler — 抓取分块
            print("  🕷️  [page_modules] 页面抓取分块...")
            t = time.monotonic()
            crawl_result = None
            crawl_data = None

            if self._page_crawler:
                try:
                    crawl_result = self._page_crawler.crawl(url, force_refresh=force_refresh)
                    crawl_data = crawl_result.to_dict() if hasattr(crawl_result, 'to_dict') else None
                    status_key = f"page_crawler_{idx}"
                    _rec(status_key, True,
                         f"{len(crawl_result.chunks)}个分块",
                         dur=time.monotonic() - t)
                    print(f"     ✅ {len(crawl_result.chunks)} 个分块")
                except Exception as e:
                    _rec(f"page_crawler_{idx}", False, None, error=str(e), dur=time.monotonic() - t)
                    print(f"     ❌ 抓取失败: {e}")
                    continue
            else:
                _rec(f"page_crawler_{idx}", False, None, error="PageCrawler 未加载", dur=0)
                continue

            # 保存最佳crawl
            if not best_crawl_data:
                best_crawl_data = crawl_data

            # Step 3: acr_analyzer — 并行分析
            print("  🔬 [page_modules] ACR 并行分析...")
            t_ = time.monotonic()
            if self._acr_analyzer and crawl_result and crawl_result.chunks:
                try:
                    acr_result = self._acr_analyzer.analyze_chunks(
                        crawl_result.chunks, url=url,
                        title=getattr(crawl_result, 'title', ''),
                        parallel=True
                    )
                    acr_data = acr_result.to_dict() if hasattr(acr_result, 'to_dict') else None
                    all_acr_results.append(acr_data)
                    _rec(f"acr_analyzer_{idx}", True,
                         f"{acr_result.modules_succeeded}/{acr_result.modules_total}",
                         dur=time.monotonic() - t_)
                    print(f"     ✅ {acr_result.modules_succeeded}/{acr_result.modules_total} 模块成功")
                    print(f"     风格: {acr_result.overall_style}, 置信度: {acr_result.brand_confidence:.2f}")
                except Exception as e:
                    _rec(f"acr_analyzer_{idx}", False, None, error=str(e), dur=time.monotonic() - t_)

        # ── 聚合多个URL的ACR结果 ──
        # Step 4: style_engine — 生成样式
        print("\n  🎨 [page_modules] 样式引擎生成...")
        t4 = time.monotonic()

        if self._style_engine and all_acr_results:
            try:
                # 合并多个ACR结果
                merged_acr = self._merge_acr_results(all_acr_results, brand_name)

                style_spec = self._style_engine.generate(
                    merged_acr,
                    brand_name=brand_name,
                    source_urls=urls_to_crawl
                )
                best_style_spec_data = style_spec.to_dict() if hasattr(style_spec, 'to_dict') else None
                _rec("style_engine", True,
                     f"样式主题: {style_spec.style_theme}, 色彩: {len(style_spec.primary_palette)}色",
                     dur=time.monotonic() - t4)
                print(f"     ✅ 样式主题: {style_spec.style_theme}")
            except Exception as e:
                _rec("style_engine", False, None, error=str(e), dur=time.monotonic() - t4)

                # 降级：使用第一个ACR结果
                if all_acr_results and self._style_engine:
                    try:
                        style_spec = self._style_engine.generate(
                            all_acr_results[0],
                            brand_name=brand_name,
                            source_urls=urls_to_crawl[:1]
                        )
                        best_style_spec_data = style_spec.to_dict() if hasattr(style_spec, 'to_dict') else None
                        _rec("style_engine", True,
                             f"降级: 仅用第1个URL, 主题={style_spec.style_theme}",
                             error=f"合并失败，降级: {e}", dur=time.monotonic() - t4)
                    except Exception as e2:
                        _rec("style_engine", False, None, error=str(e2), dur=time.monotonic() - t4)
        elif self._style_engine:
            _rec("style_engine", False, None, error="无ACR结果，无法生成样式", dur=0)
        else:
            _rec("style_engine", False, None, error="StyleEngine 未加载", dur=0)

        # Step 5: validator — 校验
        print("  ✅ [page_modules] 结果校验...")
        t5 = time.monotonic()
        if self._validator and best_style_spec_data:
            try:
                merged_acr = self._merge_acr_results(all_acr_results, brand_name) if all_acr_results else {}
                validation = self._validator.validate(
                    best_style_spec_data,
                    merged_acr,
                    best_crawl_data or {}
                )
                best_validation_data = validation.to_dict() if hasattr(validation, 'to_dict') else None
                _rec("validator", validation.passed,
                     f"评分: {validation.score}/100, {'PASS' if validation.passed else 'FAIL'}",
                     error="" if validation.passed else f"{validation.errors} errors",
                     dur=time.monotonic() - t5)
                print(f"     {'✅' if validation.passed else '⚠️'}  评分: {validation.score}/100")
            except Exception as e:
                _rec("validator", False, None, error=str(e), dur=time.monotonic() - t5)
        else:
            _rec("validator", False, None, error="Validator未加载或无样式数据", dur=0)

        # ───────────────────────────────────────────────────
        # Phase 2: 品牌研究 + 知识库
        # ───────────────────────────────────────────────────

        print("\n  🔍 Phase 2: 品牌研究 & 知识库...")
        t6 = time.monotonic()
        research_result = None

        if self._can_use_vision() and self._researcher:
            try:
                research_result = self._researcher.research_brand(brand_name, urls=target_urls[:3])
                _rec("brand_research", True, "API 研究完成", dur=time.monotonic() - t6)
                print("     ✅ 品牌研究完成")
            except Exception as e:
                fallback = self._lookup_knowledge(brand_name)
                _rec("brand_research", False, fallback, error=str(e), dur=time.monotonic() - t6)
                print(f"     ⚠️  降级: {e}")
        else:
            fallback = self._lookup_knowledge(brand_name)
            _rec("brand_research", True, fallback, error="降级模式", dur=time.monotonic() - t6)
            print("     ⚠️  降级模式: 使用知识库")

        # ── 知识库存储 ──
        t7 = time.monotonic()
        if self._knowledge:
            try:
                if research_result and hasattr(research_result, '__dict__'):
                    profile = self._BrandProfile(brand_name=brand_name)
                    if hasattr(research_result, 'primary_palette') and research_result.primary_palette:
                        profile.primary_palette = research_result.primary_palette
                    if hasattr(research_result, 'layout_analysis') and research_result.layout_analysis:
                        profile.layout_patterns = [research_result.layout_analysis]
                    if getattr(research_result, 'brand_positioning', None):
                        profile.brand_positioning = research_result.brand_positioning
                    self._knowledge.save_brand(profile)
                else:
                    palette = []
                    if best_style_spec_data:
                        palette = best_style_spec_data.get("color_system", {}).get("primary_palette", [])
                    profile = self._BrandProfile(brand_name=brand_name, primary_palette=palette)
                    self._knowledge.save_brand(profile)

                if self._patterns and research_result and hasattr(research_result, 'design_patterns'):
                    patterns_raw = [
                        p.__dict__ if hasattr(p, '__dict__') else p
                        for p in (research_result.design_patterns or [])
                    ]
                    if patterns_raw:
                        self._patterns.add_from_analysis(
                            {"design_patterns": patterns_raw}, brand_name
                        )
                _rec("knowledge_store", True, f"品牌 {brand_name} 已入库", dur=time.monotonic() - t7)
                print("     ✅ 知识库已更新")
            except Exception as e:
                _rec("knowledge_store", False, None, error=str(e), dur=time.monotonic() - t7)
                print(f"     ❌ {e}")
        else:
            _rec("knowledge_store", False, None, error="KnowledgeBase 未加载", dur=0)

        # 趋势
        t8 = time.monotonic()
        trends = []
        if self._trend_tracker:
            try:
                trends = self._trend_tracker.learn_from_trends()
                _rec("trends", True, f"{len(trends)}条", dur=time.monotonic() - t8)
            except Exception as e:
                _rec("trends", False, [], error=str(e), dur=time.monotonic() - t8)
        else:
            _rec("trends", True, [], error="TrendTracker 未加载", dur=time.monotonic() - t8)

        # ───────────────────────────────────────────────────
        # Phase 3: 图片生成
        # ───────────────────────────────────────────────────
        print("\n  🖼️  Phase 3: 图片生成...")
        t9 = time.monotonic()
        zip_path = ""

        if self._image_gen:
            try:
                palette = list(self.DEFAULT_PALETTE)
                style_str = self.DEFAULT_STYLE

                if best_style_spec_data:
                    cs = best_style_spec_data.get("color_system", {})
                    if cs.get("primary_palette"):
                        palette = cs["primary_palette"]
                    if best_style_spec_data.get("style_theme"):
                        style_str = best_style_spec_data["style_theme"]
                elif research_result and hasattr(research_result, 'primary_palette'):
                    palette = research_result.primary_palette or palette
                    if hasattr(research_result, 'design_style'):
                        style_str = research_result.design_style or style_str

                output_path = os.path.join(
                    self.output_dir, brand_name.lower().replace(' ', '_')
                )
                zip_path = self._image_gen(
                    product_name=f"{brand_name} 系列",
                    category=self.DEFAULT_CATEGORY,
                    material=self.DEFAULT_MATERIAL,
                    color=self.DEFAULT_COLOR,
                    style=style_str,
                    scene="品牌场景",
                    brand_score=0.85,
                    palette=palette,
                    output_dir=output_path,
                )
                _rec("image_gen", True, zip_path, dur=time.monotonic() - t9)
                print(f"     ✅ 图片已生成: {zip_path}")
            except Exception as e:
                zip_path = f"Image generation error: {e}"
                _rec("image_gen", False, zip_path, error=str(e), dur=time.monotonic() - t9)
                print(f"     ❌ {e}")
        else:
            _rec("image_gen", False, "", error="ImageGen 未加载", dur=time.monotonic() - t9)

        # ───────────────────────────────────────────────────
        # 汇总报告
        # ───────────────────────────────────────────────────
        total_dur = time.monotonic() - t_start
        all_ok = all(s["success"] for s in step_status.values())
        ok_count = sum(1 for s in step_status.values() if s["success"])

        print(f"\n  {'='*60}")
        print(f"  {'✅' if all_ok else '⚠️'}  品牌设计流程完成 ({ok_count}/{len(step_status)} 步骤成功)")
        print(f"  ⏱️  总耗时: {total_dur:.1f}s")
        print(f"  📍 输出: {self.output_dir}")
        print(f"  {'='*60}")

        if not all_ok:
            failed_steps = [k for k, v in step_status.items() if not v["success"]]
            print(f"  ❌ 失败步骤: {', '.join(failed_steps)}")

        result = {
            "brand": brand_name,
            "status": "success" if all_ok else "partial",
            "output_path": self.output_dir,
            "zip_file": zip_path,
            "load_status": load_status,
            "degraded": not self._can_use_vision(),
            "from_cache": False,
            "completed_at": _now_iso(),
            "total_duration_sec": round(total_dur, 1),
            "steps_total": len(step_status),
            "steps_succeeded": ok_count,
            "step_status": step_status,

            # page_modules 输出
            "page_modules": {
                "analyzed_urls": urls_to_crawl,
                "acr_results": all_acr_results,
                "style_spec": best_style_spec_data,
                "validation": best_validation_data,
            },

            "research_result": (
                research_result.__dict__
                if research_result and hasattr(research_result, '__dict__')
                else {}
            ),
            "knowledge_base": {
                "brands": self._knowledge.list_brands() if self._knowledge else [],
                "patterns": len(self._patterns.search()) if self._patterns else 0,
            },
            "summary": {
                "urls_found": len(target_urls),
                "urls_crawled": len(urls_to_crawl),
                "acr_performed": len(all_acr_results) > 0,
                "style_generated": best_style_spec_data is not None,
                "validated": best_validation_data is not None,
                "validation_passed": best_validation_data.get("passed", False) if best_validation_data else False,
                "research_done": research_result is not None,
                "knowledge_saved": step_status.get("knowledge_store", {}).get("success", False),
                "images_generated": (
                    isinstance(zip_path, str) and bool(zip_path)
                    and os.path.exists(str(zip_path))
                ),
                "parallel_executed": True,
                "degraded_mode": not self._can_use_vision(),
                "page_modules_integrated": all_acr_results != [],
            },
        }

        # ── 写入缓存 ───────────────────────────────────────
        self._cache[cache_key] = result
        return result

    # ═══════════════════════════════════════════════════════
    #  ACR 合并工具
    # ═══════════════════════════════════════════════════════

    def _merge_acr_results(self, acr_list: List[dict], brand_name: str) -> dict:
        """合并多个URL的ACR结果"""
        if not acr_list:
            return {}

        if len(acr_list) == 1:
            return acr_list[0]

        # 聚合所有模块
        all_modules = []
        all_failed = []
        all_palette = []
        all_fonts = []
        all_patterns = []
        all_styles = []
        confidences = []

        for acr in acr_list:
            all_modules.extend(acr.get("modules", []))
            all_failed.extend(acr.get("failed_modules", []))
            all_palette.extend(acr.get("aggregate_palette", []))
            all_fonts.extend(acr.get("aggregate_fonts", []))
            all_patterns.extend(acr.get("aggregate_patterns", []))
            if acr.get("overall_style"):
                all_styles.append(acr["overall_style"])
            if acr.get("brand_confidence"):
                confidences.append(acr["brand_confidence"])

        # 统计dominant style
        from collections import Counter
        style_counter = Counter(all_styles)
        dominant_style = style_counter.most_common(1)[0][0] if style_counter else "modern"

        # 平均置信度
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "url": f"merged-{len(acr_list)}urls",
            "title": brand_name,
            "analyzed_at": _now_iso(),
            "modules": all_modules,
            "failed_modules": all_failed,
            "overall_style": dominant_style,
            "design_language": f"{dominant_style.title()} Design Language",
            "aggregate_palette": list(dict.fromkeys(all_palette))[:5],
            "aggregate_fonts": list(dict.fromkeys(all_fonts))[:3],
            "aggregate_patterns": list(dict.fromkeys(all_patterns)),
            "brand_confidence": round(avg_conf, 2),
            "modules_total": sum(a.get("modules_total", 0) for a in acr_list),
            "modules_succeeded": sum(a.get("modules_succeeded", 0) for a in acr_list),
            "modules_failed": sum(a.get("modules_failed", 0) for a in acr_list),
        }

    # ═══════════════════════════════════════════════════════
    #  工具方法
    # ═══════════════════════════════════════════════════════

    def get_cache_info(self) -> Dict[str, Any]:
        """查看缓存状态"""
        return {
            "cached_brands": list(self._cache.keys()),
            "cache_size": len(self._cache),
            "entries": {
                brand: {
                    "completed_at": v.get("completed_at", "?"),
                    "status": v.get("status", "?"),
                    "degraded": v.get("degraded", False),
                }
                for brand, v in self._cache.items()
            },
        }

    def clear_cache(self) -> int:
        """清空品牌缓存，返回清除的条目数"""
        count = len(self._cache)
        self._cache.clear()
        return count

    def clear_page_cache(self) -> int:
        """清空页面爬取缓存"""
        if self._page_crawler:
            return self._page_crawler.clear_cache()
        return 0

    def list_knowledge(self) -> Dict[str, Any]:
        """列出知识库状态"""
        self._lazy_load()
        return {
            "brands": self._knowledge.list_brands() if self._knowledge else [],
            "design_patterns": self._patterns.search() if self._patterns else [],
            "research_capabilities": [
                "Page crawling & chunking (page_crawler)",
                "ACR parallel analysis (acr_analyzer)",
                "Style engine generation",
                "Output validation & scoring",
                "Brand web research & analysis",
                "Design language analysis",
                "Color system extraction",
                "Scene graph reconstruction",
                "Trend & community learning",
            ],
            "cache_status": self.get_cache_info(),
            "degraded": self.is_degraded,
        }

    def close(self):
        if self._knowledge:
            try:
                self._knowledge.close()
            except Exception:
                pass
        if self._patterns:
            try:
                self._patterns.close()
            except Exception:
                pass
