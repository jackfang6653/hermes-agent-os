"""
4A 品牌设计自动化流水线 — CEO 主入口 (v2: 缓存/降级/并行/错误隔离)

完整流程：
1. 接收输入（产品图 or 品牌名）
2. 自动品牌研究 → 网络信息搜集 → 设计体系分析
3. 品牌DNA蒸馏 → 场景图构建
4. 知识库存储
5. 自动产出：详情页长图 + 分图 + ZIP + 设计报告

v2 新增:
- 缓存机制: brand_name -> result，同一品牌无需重复研究
- 降级策略: 无 API key 时跳过 vision 调用，使用知识库已有数据
- 并行执行: concurrent.futures 加速独立的分析步骤
- 错误隔离: 每个步骤独立 try/except，输出详细状态报告

用法：
    from production.pipeline import BrandDesignPipeline
    
    # 从一张产品图
    result = await pipeline.run_from_image("https://...product.jpg")
    
    # 从一个品牌名
    result = pipeline.run_from_brand("NORHOR 北欧表情")
"""
import os, sys, io, zipfile, time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class BrandDesignPipeline:
    """4A品牌设计全自动流水线 (v2: 缓存/降级/并行/错误隔离)"""

    # ── 降级默认值 ────────────────────────────────────────
    DEFAULT_PALETTE = ["#f5f0e8", "#d4c5b0", "#8b7355", "#2c2c2c"]
    DEFAULT_STYLE = "nordic"
    DEFAULT_CATEGORY = "furniture"
    DEFAULT_MATERIAL = "fabric"
    DEFAULT_COLOR = "beige"

    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.output_dir = output_dir or os.path.expanduser("~/Desktop/norhor-output")
        os.makedirs(self.output_dir, exist_ok=True)

        # ── 缓存: brand_name → result ──────────────────────
        self._cache: Dict[str, Dict[str, Any]] = {}

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
            # detail_image_gen is in packages/norhor/src/
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
    #  降级判断
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

    # ═══════════════════════════════════════════════════════
    #  run_from_brand — 核心：缓存/降级/并行/错误隔离
    # ═══════════════════════════════════════════════════════

    def run_from_brand(self, brand_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """从一个品牌名启动全自动品牌设计。

        Args:
            brand_name: 品牌名称
            force_refresh: 是否强制刷新缓存

        Returns:
            包含 status, step_status, output 等字段的详细报告
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

        print(f"\n  🏭 4A Design Pipeline v2 — 从品牌名启动")
        print(f"  🏷️  品牌: {brand_name}")
        print(f"  🔑 API: {'✅ 已配置' if self._can_use_vision() else '⚠️  降级模式（无API key，仅用知识库）'}")
        print()

        # ── 每步状态追踪（错误隔离核心）───────────────────
        step_status: Dict[str, Dict[str, Any]] = {}

        def _record(step: str, ok: bool, detail: Any = None, error: str = "", duration: float = 0.0):
            step_status[step] = {
                "success": ok,
                "detail": detail,
                "error": error,
                "duration_sec": round(duration, 3),
                "degraded": not self._can_use_vision(),
            }

        def _record_standalone(step, ok, detail, error="", duration=0.0):
            step_status[step] = {
                "success": ok,
                "detail": detail,
                "error": error,
                "duration_sec": round(duration, 3),
            }

        # ───────────────────────────────────────────────────
        # Step 1: 品牌网络研究
        # ───────────────────────────────────────────────────
        print("  🔍 阶段1: 品牌网络研究...")
        t1 = time.monotonic()
        research_result = None
        research_error = ""

        if self._can_use_vision() and self._researcher:
            try:
                research_result = self._researcher.research_brand(brand_name)
                _record("research", True, "API 研究完成", duration=time.monotonic() - t1)
            except Exception as e:
                research_error = str(e)
                print(f"  ⚠️  品牌研究 API 失败: {e}，尝试知识库降级...")
                fallback = self._lookup_knowledge(brand_name)
                _record("research", False, fallback, error=research_error,
                        duration=time.monotonic() - t1)
        else:
            print("  ℹ️  降级模式 — 从知识库获取品牌信息...")
            fallback = self._lookup_knowledge(brand_name)
            _record("research", True, fallback, error="降级模式",
                    duration=time.monotonic() - t1)

        # ───────────────────────────────────────────────────
        # 并行: Step 2 (设计模式分析) || Step 3 (知识库存储)
        # 两者都依赖 research_result，但彼此独立
        # ───────────────────────────────────────────────────
        print("  🎨 并行阶段2+3: 设计模式分析 & 知识库存储...")
        t_parallel = time.monotonic()

        def _step2_design_patterns():
            """Step 2: 设计模式分析"""
            t2 = time.monotonic()
            if not self._can_use_vision() or not self._patterns:
                return ("design_patterns", True, "降级 — 跳过设计模式分析",
                        "降级模式", time.monotonic() - t2)
            try:
                if research_result and hasattr(research_result, 'design_patterns') and research_result.design_patterns:
                    patterns_raw = [
                        p.__dict__ if hasattr(p, '__dict__') else p
                        for p in research_result.design_patterns
                    ]
                    self._patterns.add_from_analysis(
                        {"design_patterns": patterns_raw},
                        brand_name
                    )
                    return ("design_patterns", True, f"存储了 {len(patterns_raw)} 个设计模式",
                            "", time.monotonic() - t2)
                else:
                    return ("design_patterns", True, "无设计模式数据",
                            "", time.monotonic() - t2)
            except Exception as e:
                return ("design_patterns", False, None, str(e), time.monotonic() - t2)

        def _step3_knowledge():
            """Step 3: 知识库存储"""
            t3 = time.monotonic()
            if not self._knowledge:
                return ("knowledge_store", False, None, "KnowledgeBase 未加载",
                        time.monotonic() - t3)
            try:
                if research_result and hasattr(research_result, '__dict__'):
                    rd = research_result.__dict__
                    profile = self._BrandProfile(brand_name=brand_name)
                    if hasattr(research_result, 'primary_palette') and research_result.primary_palette:
                        profile.primary_palette = research_result.primary_palette
                    if hasattr(research_result, 'layout_analysis') and research_result.layout_analysis:
                        profile.layout_patterns = [research_result.layout_analysis]
                    if hasattr(research_result, 'brand_positioning') and research_result.brand_positioning:
                        profile.brand_positioning = research_result.brand_positioning
                    self._knowledge.save_brand(profile)
                    return ("knowledge_store", True, f"品牌 {brand_name} 已入库", "", time.monotonic() - t3)
                else:
                    profile = self._BrandProfile(brand_name=brand_name)
                    self._knowledge.save_brand(profile)
                    return ("knowledge_store", True, f"品牌 {brand_name} 已入库(空)", "", time.monotonic() - t3)
            except Exception as e:
                return ("knowledge_store", False, None, str(e), time.monotonic() - t3)

        # 并行执行
        parallel_results = {}
        max_workers = min(4, (os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_step2_design_patterns): "design_patterns",
                executor.submit(_step3_knowledge): "knowledge_store",
            }
            for future in as_completed(futures):
                name, ok, detail, err, dur = future.result()
                step_status[name] = {
                    "success": ok,
                    "detail": detail,
                    "error": err,
                    "duration_sec": round(dur, 3),
                    "parallel": True,
                }
                parallel_results[name] = ok

        # ───────────────────────────────────────────────────
        # Step 4: 趋势信息收集
        # ───────────────────────────────────────────────────
        print("  📈 阶段4: 趋势信息收集...")
        t4 = time.monotonic()
        trends = []
        if self._trend_tracker:
            try:
                trends = self._trend_tracker.learn_from_trends()
                _record_standalone("trends", True, f"收集了 {len(trends)} 条趋势",
                                   duration=time.monotonic() - t4)
            except Exception as e:
                _record_standalone("trends", False, [], error=str(e),
                                   duration=time.monotonic() - t4)
        else:
            _record_standalone("trends", True, [], error="TrendTracker 未加载",
                               duration=time.monotonic() - t4)

        # ───────────────────────────────────────────────────
        # Step 5: 提取品牌参数并生成详情页
        # ───────────────────────────────────────────────────
        print("  🖼️  阶段5: 生成品牌详情页...")
        t5 = time.monotonic()
        zip_path = ""

        if self._image_gen:
            try:
                brand_palette = list(self.DEFAULT_PALETTE)
                brand_style = self.DEFAULT_STYLE

                if research_result:
                    if hasattr(research_result, 'primary_palette') and research_result.primary_palette:
                        brand_palette = research_result.primary_palette
                    if hasattr(research_result, 'design_style'):
                        brand_style = research_result.design_style or brand_style
                else:
                    fallback = self._lookup_knowledge(brand_name)
                    brand_palette = fallback.get("palette", brand_palette)
                    brand_style = fallback.get("style", brand_style)

                output_path = os.path.join(self.output_dir, brand_name.lower().replace(' ', '_'))
                zip_path = self._image_gen(
                    product_name=f"{brand_name} 系列",
                    category=self.DEFAULT_CATEGORY,
                    material=self.DEFAULT_MATERIAL,
                    color=self.DEFAULT_COLOR,
                    style=brand_style,
                    scene="品牌场景",
                    brand_score=0.85,
                    palette=brand_palette,
                    output_dir=output_path,
                )
                _record_standalone("image_gen", True, zip_path,
                                   duration=time.monotonic() - t5)
            except Exception as e:
                zip_path = f"Image generation error: {e}"
                _record_standalone("image_gen", False, zip_path, error=str(e),
                                   duration=time.monotonic() - t5)
        else:
            _record_standalone("image_gen", False, "", error="ImageGen 模块未加载",
                               duration=time.monotonic() - t5)

        # ───────────────────────────────────────────────────
        # 汇总报告
        # ───────────────────────────────────────────────────
        total_duration = time.monotonic() - t_start
        all_ok = all(s["success"] for s in step_status.values())
        steps_succeeded = sum(1 for s in step_status.values() if s["success"])
        steps_total = len(step_status)

        print(f"\n  {'✅' if all_ok else '⚠️'}  品牌设计流程完成 ({steps_succeeded}/{steps_total} 步骤成功)")
        print(f"  ⏱️  总耗时: {total_duration:.1f}s")
        print(f"  📍 输出: {self.output_dir}")

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
            "total_duration_sec": round(total_duration, 1),
            "steps_total": steps_total,
            "steps_succeeded": steps_succeeded,
            "step_status": step_status,
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
                "research_done": research_result is not None,
                "knowledge_saved": step_status.get("knowledge_store", {}).get("success", False),
                "images_generated": (
                    isinstance(zip_path, str) and os.path.exists(zip_path)
                ),
                "parallel_executed": True,
                "degraded_mode": not self._can_use_vision(),
            },
        }

        # ── 写入缓存 ───────────────────────────────────────
        self._cache[cache_key] = result
        return result

    # ═══════════════════════════════════════════════════════
    #  run_from_image — 同样增强错误隔离 + 降级
    # ═══════════════════════════════════════════════════════

    def run_from_image(self, image_url: str, brand_name: Optional[str] = None) -> Dict[str, Any]:
        """从一张产品图启动全自动品牌设计"""
        t_start = time.monotonic()
        load_status = self._lazy_load()

        print(f"\n  🏭 4A Design Pipeline v2 — 从产品图启动")
        print(f"  📸 图片: {image_url}")
        if brand_name:
            print(f"  🏷️  品牌: {brand_name}")
        print(f"  🔑 API: {'✅ 已配置' if self._can_use_vision() else '⚠️  降级模式'}")
        print()

        step_status: Dict[str, Dict[str, Any]] = {}

        def _rec(step, ok, detail=None, error="", dur=0.0):
            step_status[step] = {
                "success": ok, "detail": detail, "error": error,
                "duration_sec": round(dur, 3), "degraded": not self._can_use_vision(),
            }

        # Step 1: 品牌研究
        t1 = time.monotonic()
        research_result = None
        if brand_name:
            print("  🔍 阶段1: 品牌网络研究...")
            if self._can_use_vision() and self._researcher:
                try:
                    research_result = self._researcher.research_brand(brand_name)
                    _rec("research", True, "API 研究完成", dur=time.monotonic()-t1)
                except Exception as e:
                    _rec("research", False, None, error=str(e), dur=time.monotonic()-t1)
            else:
                _rec("research", True, "降级 — 使用品牌名直接推断",
                     error="降级模式", dur=time.monotonic()-t1)
            brand = brand_name
        else:
            print("  🔍 阶段1: 分析图片推断品牌...")
            research_result = None
            brand = f"brand_{hash(image_url) % 10000}"
            _rec("research", True, "推断品牌名", dur=time.monotonic()-t1)

        # ── 并行: Step 2 (设计分析) || Step 3 (色彩系统) || Step 4 (场景图解析) ──
        print("  ⚡ 并行阶段2-4: 设计/色彩/场景图分析...")
        t_parallel = time.monotonic()

        design_analysis = None
        color_system = None
        scene_graph_json = None

        def _do_design():
            t = time.monotonic()
            if not self._can_use_vision() or not self._design_analyzer:
                return ("design_analysis", True, "降级 — 跳过视觉设计分析",
                        None, "降级模式", time.monotonic()-t)
            try:
                result = self._design_analyzer.analyze_design(image_url)
                return ("design_analysis", True, "设计分析完成", result,
                        "", time.monotonic()-t)
            except Exception as e:
                return ("design_analysis", False, None, {"raw": str(e)},
                        str(e), time.monotonic()-t)

        def _do_color():
            t = time.monotonic()
            if not self._can_use_vision() or not self._color_analyzer:
                return ("color_system", True, "降级 — 跳过色彩分析",
                        None, "降级模式", time.monotonic()-t)
            try:
                result = self._color_analyzer.analyze(image_url)
                return ("color_system", True, "色彩分析完成", result,
                        "", time.monotonic()-t)
            except Exception as e:
                return ("color_system", False, None, None, str(e), time.monotonic()-t)

        def _do_scene():
            t = time.monotonic()
            if not self._can_use_vision() or not self._scene_parser:
                return ("scene_graph", True, "降级 — 跳过场景图解析",
                        None, "降级模式", time.monotonic()-t)
            try:
                sg = self._scene_parser.parse(image_url)
                sg_json = sg.to_dict()
                return ("scene_graph", True, "场景图解析完成", sg_json,
                        "", time.monotonic()-t)
            except Exception as e:
                return ("scene_graph", False, None, {"error": str(e)},
                        str(e), time.monotonic()-t)

        parallel_data = {}
        max_workers = min(6, (os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_do_design): "design",
                executor.submit(_do_color): "color",
                executor.submit(_do_scene): "scene",
            }
            for future in as_completed(futures):
                step_name, ok, msg, data, err, dur = future.result()
                _rec(step_name, ok, msg, error=err, dur=dur)
                parallel_data[futures[future]] = (data, ok)

        design_analysis = parallel_data.get("design", (None,))[0]
        color_system = parallel_data.get("color", (None,))[0]
        scene_graph_json = parallel_data.get("scene", (None,))[0]
        if scene_graph_json is None:
            scene_graph_json = {}

        # Step 5: 生成参数化指令
        print("  📝 阶段5: 生成参数化指令...")
        t5 = time.monotonic()
        try:
            if scene_graph_json and not isinstance(scene_graph_json, dict):
                scene_graph_json = {}
            if scene_graph_json and "error" not in scene_graph_json and self._scene_renderer:
                from dna_engine.scene_graph import SceneGraph
                sg = SceneGraph()
                for k, v in scene_graph_json.items():
                    if hasattr(sg, k):
                        setattr(sg, k, v)
                gen_prompt = self._scene_renderer.render_generation_prompt(sg)
            else:
                gen_prompt = "降级 — 场景分析不可用，使用默认提示词"
            _rec("generation_prompt", True, gen_prompt, dur=time.monotonic()-t5)
        except Exception as e:
            gen_prompt = f"Prompt generation error: {e}"
            _rec("generation_prompt", False, gen_prompt, error=str(e), dur=time.monotonic()-t5)

        # Step 6: 知识库存储
        print("  💾 阶段6: 存入品牌知识库...")
        t6 = time.monotonic()
        try:
            if self._knowledge:
                if research_result:
                    profile = self._knowledge.build_from_research(
                        brand,
                        research_result.__dict__ if hasattr(research_result, '__dict__') else {}
                    )
                else:
                    palette = []
                    if color_system and hasattr(color_system, 'primary_palette'):
                        palette = color_system.primary_palette
                    profile = self._BrandProfile(brand_name=brand, primary_palette=palette)
                    self._knowledge.save_brand(profile)

                if self._patterns and design_analysis:
                    self._patterns.add_from_analysis(design_analysis, brand)

                if self._knowledge and color_system:
                    self._knowledge.save_knowledge(brand, "color_system",
                        color_system.__dict__ if hasattr(color_system, '__dict__') else {})
                _rec("knowledge_store", True, "品牌已入库", dur=time.monotonic()-t6)
            else:
                _rec("knowledge_store", False, None, error="KnowledgeBase 未加载", dur=time.monotonic()-t6)
        except Exception as e:
            print(f"  ⚠️  知识库存储: {e}")
            _rec("knowledge_store", False, None, error=str(e), dur=time.monotonic()-t6)

        # Step 7: 趋势
        print("  📈 阶段7: 趋势信息收集...")
        t7 = time.monotonic()
        trends = []
        if self._trend_tracker:
            try:
                trends = self._trend_tracker.learn_from_trends()
                _rec("trends", True, f"{len(trends)} 条", dur=time.monotonic()-t7)
            except Exception as e:
                _rec("trends", False, [], error=str(e), dur=time.monotonic()-t7)
        else:
            _rec("trends", True, [], error="TrendTracker 未加载", dur=time.monotonic()-t7)

        # Step 8: 图片生成
        print("  🖼️  阶段8: 生成详情页图片...")
        t8 = time.monotonic()
        zip_path = ""
        if self._image_gen:
            try:
                product_name = brand
                category = self.DEFAULT_CATEGORY
                material = self.DEFAULT_MATERIAL
                color = self.DEFAULT_COLOR
                style = self.DEFAULT_STYLE
                palette = list(self.DEFAULT_PALETTE)

                if color_system:
                    if hasattr(color_system, 'primary_palette') and color_system.primary_palette:
                        palette = color_system.primary_palette
                    if hasattr(color_system, 'temperature'):
                        style = color_system.temperature or style

                output_path = os.path.join(self.output_dir, f"{brand.lower().replace(' ', '_')}")
                zip_path = self._image_gen(
                    product_name=product_name,
                    category=category,
                    material=material,
                    color=color,
                    style=style,
                    scene="北欧客厅",
                    brand_score=0.85,
                    palette=palette,
                    output_dir=output_path,
                )
                _rec("image_gen", True, zip_path, dur=time.monotonic()-t8)
            except Exception as e:
                zip_path = f"Image generation error: {e}"
                _rec("image_gen", False, zip_path, error=str(e), dur=time.monotonic()-t8)
        else:
            _rec("image_gen", False, "", error="ImageGen 未加载", dur=time.monotonic()-t8)

        # ── 汇总 ──
        total_dur = time.monotonic() - t_start
        all_ok = all(s["success"] for s in step_status.values())
        ok_count = sum(1 for s in step_status.values() if s["success"])

        print(f"\n  {'✅' if all_ok else '⚠️'}  品牌设计全流程完成 ({ok_count}/{len(step_status)} 步骤成功)")
        print(f"  ⏱️  总耗时: {total_dur:.1f}s")
        print(f"  📍 输出: {self.output_dir}")

        return {
            "brand": brand,
            "status": "success" if all_ok else "partial",
            "output_path": self.output_dir,
            "zip_file": zip_path,
            "load_status": load_status,
            "degraded": not self._can_use_vision(),
            "completed_at": _now_iso(),
            "total_duration_sec": round(total_dur, 1),
            "steps_total": len(step_status),
            "steps_succeeded": ok_count,
            "step_status": step_status,
            "scene_graph": scene_graph_json,
            "generation_prompt": gen_prompt,
            "design_analysis": design_analysis,
            "design_patterns_learned": len(trends),
            "knowledge_base": {
                "brands": self._knowledge.list_brands() if self._knowledge else [],
                "patterns_available": len(self._patterns.search()) if self._patterns else 0,
            },
            "summary": {
                "research_done": research_result is not None,
                "design_analyzed": "visual_grammar" in str(design_analysis),
                "color_system_analyzed": color_system is not None,
                "scene_graph_built": (
                    isinstance(scene_graph_json, dict)
                    and "error" not in str(scene_graph_json)
                ),
                "knowledge_saved": step_status.get("knowledge_store", {}).get("success", False),
                "images_generated": (
                    isinstance(zip_path, str)
                    and bool(zip_path)
                    and os.path.exists(str(zip_path))
                ),
                "parallel_executed": True,
                "degraded_mode": not self._can_use_vision(),
            },
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
        """清空缓存，返回清除的条目数"""
        count = len(self._cache)
        self._cache.clear()
        return count

    def list_knowledge(self) -> Dict[str, Any]:
        """列出知识库状态"""
        self._lazy_load()
        return {
            "brands": self._knowledge.list_brands() if self._knowledge else [],
            "design_patterns": self._patterns.search() if self._patterns else [],
            "research_capabilities": [
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
