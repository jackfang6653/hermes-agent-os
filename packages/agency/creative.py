"""
创意部 — 多概念发想与执行落地 (Creative Phase)

核心升级:
- 接收 StrategyDept 输出的 BrandVisualSystem (参数范围，不是固定值)
- 用 SceneRenderer 生成 5 套创意方案 Prompt (每套基于视觉系统参数范围生成)
- 评分: 创意新颖度 / 品牌合规度 (基于参数匹配) / 可执行性

5 套概念:
  1. Pure Studio     — 纯净影棚，核心色板，标准焦距
  2. Living Context   — 生活场景，环境光，自然氛围
  3. Dramatic Editorial — 戏剧光影，高对比，时尚大片
  4. Material Focus   — 材质特写，极致细节，微距视角
  5. Mood Atmosphere  — 氛围情绪，季节色板，主题光影

用法:
    creative = CreativeDept()
    concepts = creative.brainstorm(brand_visual_system, "IKEA")
    best = creative.select_best_concept()
"""
import sys, os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 确保 dna_engine 可导入
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from packages.dna_engine.scene_graph import (
    SceneGraph, SceneElement, PBRMaterial,
    Light, CameraSystem, PostProcessing,
)
from packages.dna_engine.scene_renderer import SceneRenderer
from packages.agency.strategy import BrandVisualSystem, ParameterRange


@dataclass
class CreativeConcept:
    """一个创意概念 — 包含完整参数方案"""
    concept_name: str = ""
    concept_description: str = ""
    rationale: str = ""              # 创意理由

    # 场景方案
    scene_type: str = ""
    scene_parameters: Dict[str, Any] = field(default_factory=dict)

    # 灯光方案
    lighting_plan: Dict[str, Any] = field(default_factory=dict)

    # 颜色方案
    color_variant: List[str] = field(default_factory=list)

    # 排版方案
    layout_style: str = ""

    # 输出规格
    output_specs: Dict[str, Any] = field(default_factory=dict)

    # AI生成Prompt (由 SceneRenderer 产出)
    generation_prompt: str = ""

    # 评分
    creative_score: float = 0.0      # 创意新颖度
    brand_compliance: float = 0.0    # 品牌合规度 (基于参数范围匹配)
    feasibility: float = 0.0         # 可执行性


class CreativeDept:
    """创意部 — SceneGraph → 5套创意概念"""

    def __init__(self):
        self._concepts: List[CreativeConcept] = []
        self._renderer = SceneRenderer()
        self._visual_system: Optional[BrandVisualSystem] = None

    # ── 入口 ───────────────────────────────────────────────
    def brainstorm(self, visual_system=None,
                   brand_name: str = "", strategy_doc: dict = None) -> List[CreativeConcept]:
        """
        基于 BrandVisualSystem 参数范围生成 5 套创意概念。

        每套概念:
        1. 从参数范围中抽样构造 SceneGraph (不是硬编码)
        2. 用 SceneRenderer 生成精确 generation_prompt
        3. 计算创意新颖度 / 品牌合规度 / 可执行性

        兼容旧接口: 若传入 dict (strategy_doc)，降级为启发式生成。
        """
        # 向后兼容: 如果传入 dict 而非 BrandVisualSystem
        if isinstance(visual_system, dict):
            return self._brainstorm_from_dict(visual_system, brand_name)

        if visual_system is None:
            print("    ⚠️ 无视觉系统数据，返回空")
            return []

        self._visual_system = visual_system
        brand = brand_name or visual_system.brand or "Brand"
        print(f"  🎨 [Creative] 创意发想 — {brand}")
        print(f"    视觉系统: {visual_system.products_analyzed} 产品, "
              f"焦距 {visual_system.focal_length_range.min:.0f}-{visual_system.focal_length_range.max:.0f}mm")

        concepts = [
            self._concept_pure_studio(visual_system, brand),
            self._concept_living_context(visual_system, brand),
            self._concept_dramatic_editorial(visual_system, brand),
            self._concept_material_focus(visual_system, brand),
            self._concept_mood_atmosphere(visual_system, brand),
        ]

        concepts = [c for c in concepts if c is not None]

        # 评分
        for c in concepts:
            c.creative_score = self._score_creativity(c)
            c.brand_compliance = self._score_brand_compliance(c, visual_system)
            c.feasibility = self._score_feasibility(c)

        self._concepts = concepts
        print(f"    ✅ 产出 {len(concepts)} 个创意概念")
        for c in concepts:
            print(f"      {c.concept_name}: 创意{c.creative_score:.0%} "
                  f"品牌{c.brand_compliance:.0%} 可行{c.feasibility:.0%}")
        return concepts

    def _brainstorm_from_dict(self, strategy_doc: dict, brand_name: str = "") -> List[CreativeConcept]:
        """向后兼容: 从旧版 strategy_doc dict 生成概念 (不依赖 SceneGraph)"""
        print(f"  🎨 [Creative] 创意发想 (兼容模式) — {brand_name}")
        vs_data = strategy_doc.get("visual_system", {})

        concepts = [
            CreativeConcept(
                concept_name="纯净影棚 Pure Studio",
                concept_description="纯色背景，标准产品视角",
                rationale="兼容模式下生成",
                scene_type="studio",
                scene_parameters={"background": "纯白", "mood": "专业"},
                lighting_plan={"type": "影棚三灯"},
                color_variant=vs_data.get("core_palette", [])[:3] or ["白底"],
                layout_style="产品居中",
                generation_prompt="Studio product photography on clean background",
            ),
            CreativeConcept(
                concept_name="生活场景 Living Context",
                concept_description="真实生活场景",
                rationale="兼容模式下生成",
                scene_type="lifestyle",
                scene_parameters={"background": "生活场景", "mood": "自然"},
                lighting_plan={"type": "自然光+补光"},
                color_variant=["暖调", "冷调"],
                layout_style="场景融入",
                generation_prompt="Lifestyle product photography in natural setting",
            ),
            CreativeConcept(
                concept_name="戏剧大片 Editorial",
                concept_description="杂志风格戏剧光影",
                rationale="兼容模式下生成",
                scene_type="editorial",
                scene_parameters={"background": "深色", "mood": "高级"},
                lighting_plan={"type": "戏剧光"},
                color_variant=["暗调", "黑白"],
                layout_style="杂志式",
                generation_prompt="Editorial product photography with dramatic lighting",
            ),
            CreativeConcept(
                concept_name="材质特写 Material Focus",
                concept_description="微距材质细节",
                rationale="兼容模式下生成",
                scene_type="macro",
                scene_parameters={"background": "纯色", "mood": "质感"},
                lighting_plan={"type": "微距布光"},
                color_variant=vs_data.get("core_palette", [])[:2] or ["材质本色"],
                layout_style="满版",
                generation_prompt="Macro product detail photography",
            ),
            CreativeConcept(
                concept_name="氛围情绪 Mood Atmosphere",
                concept_description="情绪氛围场景",
                rationale="兼容模式下生成",
                scene_type="atmospheric",
                scene_parameters={"background": "氛围", "mood": "沉浸"},
                lighting_plan={"type": "氛围光"},
                color_variant=["暖调氛围", "冷调氛围"],
                layout_style="故事性",
                generation_prompt="Atmospheric product photography with mood lighting",
            ),
        ]

        for c in concepts:
            c.creative_score = 0.7
            c.brand_compliance = 0.8
            c.feasibility = 0.75

        self._concepts = concepts
        print(f"    ✅ 产出 {len(concepts)} 个创意概念 (兼容模式)")
        return concepts

    # ═══════════════════════════════════════════════════════
    # 5 套创意概念 — 全部从参数范围生成
    # ═══════════════════════════════════════════════════════

    def _concept_pure_studio(self, vs: BrandVisualSystem, brand: str) -> CreativeConcept:
        """纯净影棚 — 白/灰底 + 核心色板 + 标准产品焦距"""
        # ── 场景参数 ──
        bg_colors = ["#fafafa", "#f0f0f0", "#e8e8e8", "#ffffff"]
        bg = self._pick(bg_colors, 0)
        scene_params = {
            "background": "纯色无缝纸",
            "background_color": bg,
            "props": "无/极简底座",
            "mood": "专业清晰",
        }

        # ── 灯光方案 (品牌灯光模式 → 实际灯光参数) ──
        light_mod = self._pick(vs.lighting_patterns, "softbox")
        lighting = {
            "setup": "三灯影棚标准",
            "key_light": {"type": light_mod, "position": "45°左前上", "temperature": 5500},
            "fill_light": {"type": "softbox", "position": "右前平", "ratio": 0.4},
            "rim_light": {"type": "strip_softbox", "position": "后上", "temperature": 5500},
            "ambient": "无",
        }

        # ── 颜色变体 ──
        color_variants = self._palette_variants(vs.core_palette, vs.seasonal_palette, count=3)

        # ── 构建 SceneGraph ──
        graph = self._build_base_scenegraph(brand, "pure_studio", bg)
        self._apply_camera(graph, vs, focal_length="standard", aperture="mid")
        self._apply_studio_lighting(graph)
        prompt = self._renderer.render_generation_prompt(graph)

        return CreativeConcept(
            concept_name="纯净影棚 Pure Studio",
            concept_description="纯色背景，标准产品视角，聚焦产品形态与核心色彩",
            rationale=f"电商标准拍法，突出品牌核心色板 {', '.join(vs.core_palette[:3])}，"
                      f"焦距范围 {vs.focal_length_range.min:.0f}-{vs.focal_length_range.max:.0f}mm 内取标准焦段",
            scene_type="studio",
            scene_parameters=scene_params,
            lighting_plan=lighting,
            color_variant=color_variants,
            layout_style="产品居中，对称构图，大量留白",
            output_specs={"resolution": "8K", "aspect": "1:1", "background": "可去底"},
            generation_prompt=prompt,
        )

    def _concept_living_context(self, vs: BrandVisualSystem, brand: str) -> CreativeConcept:
        """生活场景 — 真实环境 + 自然光 + 品牌氛围"""
        bg = "#f5efe0"
        scene_params = {
            "background": "真实生活场景 (客厅/卧室/书房)",
            "background_color": bg,
            "props": "生活方式配饰 (书籍/绿植/织物)",
            "mood": "温馨自然，生活气息",
        }

        light_pattern = self._pick(vs.lighting_patterns, "自然光+补光")
        lighting = {
            "setup": "自然光主导 + 辅助补光",
            "key_light": {"type": "window_light", "position": "左侧大面积窗光", "temperature": 5000},
            "fill_light": {"type": "bounce", "position": "右侧反光板", "ratio": 0.3},
            "ambient": {"type": "室内环境光", "temperature": 3200, "mix": 0.2},
        }

        color_variants = self._palette_variants(vs.core_palette, vs.seasonal_palette, count=3)

        graph = self._build_base_scenegraph(brand, "living_context", bg)
        self._apply_camera(graph, vs, focal_length="wide", aperture="mid")
        self._apply_natural_lighting(graph)
        # 添加场景道具
        self._add_prop(graph, "plant_01", "plant", (120, 30, 80), (90, 200, 200), "#4a7c59")
        self._add_prop(graph, "book_01", "book", (-80, 2, 60), (30, 3, 20), "#c4a882")
        prompt = self._renderer.render_generation_prompt(graph)

        return CreativeConcept(
            concept_name="生活场景 Living Context",
            concept_description="将产品置于真实生活场景，让消费者想象使用时刻",
            rationale="生活场景激发情感连接，提升购买转化。品牌灯光模式提示使用混合自然光",
            scene_type="lifestyle",
            scene_parameters=scene_params,
            lighting_plan=lighting,
            color_variant=color_variants,
            layout_style="场景融入式，产品与环境互动",
            output_specs={"resolution": "8K", "aspect": "4:3"},
            generation_prompt=prompt,
        )

    def _concept_dramatic_editorial(self, vs: BrandVisualSystem, brand: str) -> CreativeConcept:
        """戏剧性时尚大片 — 高对比 + 戏剧光 + 长焦压缩"""
        bg = "#1a1a2e"
        scene_params = {
            "background": "深色戏剧化背景",
            "background_color": bg,
            "props": "精选艺术装置/雕塑/金属元素",
            "mood": "高级时尚，电影感",
        }

        lighting = {
            "setup": "戏剧性三点布光",
            "key_light": {"type": "fresnel", "position": "侧逆光45°", "temperature": 4200, "intensity": "高"},
            "fill_light": {"type": "snoot", "position": "正面低角度", "ratio": 0.15, "temperature": 3200},
            "rim_light": {"type": "bare_bulb", "position": "后上轮廓光", "temperature": 5600},
            "atmosphere": "微弱烟雾/haze",
        }

        color_variants = self._palette_variants(vs.accent_palette, vs.core_palette, count=3)
        if not color_variants:
            color_variants = ["暗调奢华 #1a1a2e", "高对比黑白", "金属质感"]

        graph = self._build_base_scenegraph(brand, "editorial", bg)
        self._apply_camera(graph, vs, focal_length="telephoto", aperture="wide")
        self._apply_dramatic_lighting(graph)
        self._add_prop(graph, "pedestal", "stone", (0, -30, 30), (50, 30, 50), "#2a2a2a")
        prompt = self._renderer.render_generation_prompt(graph)

        return CreativeConcept(
            concept_name="戏剧大片 Dramatic Editorial",
            concept_description="杂志封面级光影，高对比戏剧化呈现",
            rationale="提升品牌调性，适合高端产品线和品牌形象建设。"
                      f"使用长焦端 {vs.focal_length_range.max:.0f}mm 增强压缩感",
            scene_type="editorial",
            scene_parameters=scene_params,
            lighting_plan=lighting,
            color_variant=color_variants,
            layout_style="杂志跨页式，黄金比例构图",
            output_specs={"resolution": "8K", "aspect": "3:4"},
            generation_prompt=prompt,
        )

    def _concept_material_focus(self, vs: BrandVisualSystem, brand: str) -> CreativeConcept:
        """材质特写 — 微距 + 材质纹理 + 极致细节"""
        bg = "#e8e0d5"
        scene_params = {
            "background": "柔和纯色/材质呼应背景",
            "background_color": bg,
            "props": "无 — 纯粹聚焦产品",
            "mood": "极致质感，工匠精神",
        }

        # 从材质系统中推导灯光
        mat_info = self._extract_material_info(vs)
        lighting = {
            "setup": "材质展示专用布光",
            "key_light": {"type": "beauty_dish", "position": "正面微侧", "temperature": 5500,
                          "purpose": "展现纹理细节"},
            "fill_light": {"type": "strip_softbox", "position": "侧向掠光", "ratio": 0.3,
                           "purpose": "勾边 + 立体感"},
            "special": "偏振滤镜消除反光" if mat_info.get("metallic", False) else "柔光箱最大化纹理",
        }

        color_variants = self._palette_variants(vs.core_palette, [], count=3)

        graph = self._build_base_scenegraph(brand, "material_focus", bg)
        self._apply_camera(graph, vs, focal_length="macro", aperture="mid")
        self._apply_macro_lighting(graph)
        # 使用品牌材质参数更新 PBR
        self._set_material(graph, mat_info)
        prompt = self._renderer.render_generation_prompt(graph)

        return CreativeConcept(
            concept_name="材质特写 Material Focus",
            concept_description="微距镜头极致放大，展现材质纹理与工艺细节",
            rationale=f"品牌材质系统包含 {len(vs.material_system)} 类材质，"
                      f"微距呈现工匠品质。材质细节是品牌溢价的核心支撑",
            scene_type="macro",
            scene_parameters=scene_params,
            lighting_plan=lighting,
            color_variant=color_variants,
            layout_style="满版构图，细节填满画面",
            output_specs={"resolution": "8K", "aspect": "1:1", "macro": True},
            generation_prompt=prompt,
        )

    def _concept_mood_atmosphere(self, vs: BrandVisualSystem, brand: str) -> CreativeConcept:
        """氛围情绪 — 季节色板 + 情绪化光影 + 故事感"""
        bg = self._pick(vs.seasonal_palette, "#d4c5b9")
        scene_params = {
            "background": "主题氛围场景",
            "background_color": bg,
            "props": "季节元素 (植物/织物/光影投射)",
            "mood": "沉浸情绪，故事氛围",
        }

        lighting = {
            "setup": "氛围情绪布光",
            "key_light": {"type": "projected_light", "position": "侧上方",
                          "temperature": self._kelvin_from_hex(bg),
                          "gobo": "自然光影纹理"},
            "fill_light": {"type": "ambient_bounce", "ratio": 0.5},
            "accent": {"type": "practical_light", "position": "场景内点光源",
                       "temperature": 2800, "purpose": "温暖氛围点"},
        }

        color_variants = self._palette_variants(vs.seasonal_palette, vs.core_palette, count=3)

        graph = self._build_base_scenegraph(brand, "mood_atmosphere", bg)
        self._apply_camera(graph, vs, focal_length="standard", aperture="mid")
        self._apply_atmospheric_lighting(graph, bg)
        prompt = self._renderer.render_generation_prompt(graph)

        design_principles = ", ".join(vs.design_principles[:3]) if vs.design_principles else "品牌调性"
        return CreativeConcept(
            concept_name="氛围情绪 Mood Atmosphere",
            concept_description="以季节色板为基调，营造沉浸式情绪氛围",
            rationale=f"季节色板 {', '.join(vs.seasonal_palette[:3])} 赋予时效性和新鲜感。"
                      f"品牌设计原则: {design_principles}",
            scene_type="atmospheric",
            scene_parameters=scene_params,
            lighting_plan=lighting,
            color_variant=color_variants,
            layout_style="故事性构图，环境与产品融合",
            output_specs={"resolution": "8K", "aspect": "16:9"},
            generation_prompt=prompt,
        )

    # ═══════════════════════════════════════════════════════
    # SceneGraph 构建工具方法
    # ═══════════════════════════════════════════════════════

    def _build_base_scenegraph(self, brand: str, scene_type: str,
                                bg_color: str) -> SceneGraph:
        """构建基础场景图 (含产品元素)"""
        product = SceneElement(
            id="product_01",
            type="product",
            label=brand,
            bbox_center=(0, 0, 0),
            bbox_size=(80, 120, 60),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            material=PBRMaterial(
                id="mat_product",
                name=f"{brand}_main",
                type="unknown",
                albedo="#808080",
                roughness=0.4,
                metallic=0.1,
                normal_strength=0.5,
                ior=1.5,
            ),
            distance_to_camera_cm=350,
            angle_to_camera_deg=0,
            relative_scale_to_frame=0.55,
        )

        floor = SceneElement(
            id="floor_01",
            type="floor",
            label="floor",
            bbox_center=(0, -110, 0),
            bbox_size=(600, 20, 600),
            material=PBRMaterial(
                id="mat_floor",
                type="stone",
                albedo="#d5d0c8",
                roughness=0.7,
                metallic=0.0,
            ),
            distance_to_camera_cm=420,
            angle_to_camera_deg=-15,
            relative_scale_to_frame=0.3,
        )

        wall = SceneElement(
            id="wall_01",
            type="wall",
            label="backdrop",
            bbox_center=(0, 60, -150),
            bbox_size=(500, 400, 5),
            material=PBRMaterial(
                id="mat_wall",
                type="painted",
                albedo=bg_color,
                roughness=0.5,
                metallic=0.0,
            ),
            distance_to_camera_cm=500,
        )

        camera = CameraSystem(
            focal_length_mm=85,
            aperture_f=5.6,
            shutter_speed="1/125",
            iso=100,
            position_3d=(0, 100, -400),
            target=(0, 30, 0),
            focus_distance_cm=380,
        )

        return SceneGraph(
            scene_id=f"{brand}_{scene_type}",
            scene_type=scene_type,
            brand=brand,
            elements=[product, floor, wall],
            camera=camera,
            lights=[],
            post_processing=PostProcessing(),
            background_color=bg_color,
        )

    def _apply_camera(self, graph: SceneGraph, vs: BrandVisualSystem,
                      focal_length: str = "standard", aperture: str = "mid"):
        """从 BrandVisualSystem 参数范围应用相机参数"""
        fl_range = vs.focal_length_range
        ap_range = vs.aperture_range

        fl_map = {
            "wide": fl_range.min if fl_range.min > 0 else 35,
            "standard": fl_range.avg if fl_range.avg > 0 else 85,
            "telephoto": fl_range.max if fl_range.max > 0 else 135,
            "macro": 100,
        }
        ap_map = {
            "wide": ap_range.min if ap_range.min > 0 else 2.0,
            "mid": ap_range.avg if ap_range.avg > 0 else 5.6,
            "narrow": ap_range.max if ap_range.max > 0 else 11,
        }

        graph.camera.focal_length_mm = fl_map.get(focal_length, fl_range.avg or 85)
        graph.camera.aperture_f = ap_map.get(aperture, ap_range.avg or 5.6)

    def _apply_studio_lighting(self, graph: SceneGraph):
        """标准三灯影棚"""
        graph.lights = [
            Light(id="key", type="area", shape="rectangle",
                  position_3d=(-120, 150, -250), target=(0, 0, 0),
                  intensity=2000, temperature=5500, size=(60, 90),
                  modifier="softbox", diffusion=0.9),
            Light(id="fill", type="area", shape="rectangle",
                  position_3d=(100, 80, -200), target=(0, 0, 0),
                  intensity=800, temperature=5500, size=(60, 90),
                  modifier="softbox", diffusion=0.9),
            Light(id="rim", type="area", shape="rectangle",
                  position_3d=(0, 180, -300), target=(0, 30, 0),
                  intensity=1200, temperature=5500, size=(20, 120),
                  modifier="strip_softbox", diffusion=0.7),
        ]

    def _apply_natural_lighting(self, graph: SceneGraph):
        """自然光 + 辅助补光"""
        graph.lights = [
            Light(id="window", type="area", shape="rectangle",
                  position_3d=(-200, 150, -200), target=(0, 0, 0),
                  intensity=3000, temperature=5000, size=(120, 180),
                  diffusion=1.0),
            Light(id="bounce", type="area", shape="disc",
                  position_3d=(150, 40, -180), target=(0, 0, 0),
                  intensity=600, temperature=5000, size=(80, 80),
                  diffusion=1.0),
            Light(id="ambient", type="point",
                  position_3d=(0, 200, 0),
                  intensity=400, temperature=3200, size=(10, 10),
                  falloff_type="inverse_square"),
        ]

    def _apply_dramatic_lighting(self, graph: SceneGraph):
        """戏剧性高对比布光"""
        graph.lights = [
            Light(id="key_dramatic", type="spot", shape="disc",
                  position_3d=(-80, 180, -200), target=(0, 0, 0),
                  intensity=4000, temperature=4200, size=(30, 30),
                  modifier="fresnel", grid_angle=20, diffusion=0.3),
            Light(id="fill_dramatic", type="spot", shape="disc",
                  position_3d=(60, 30, -300), target=(0, -20, 0),
                  intensity=600, temperature=3200, size=(15, 15),
                  modifier="snoot", diffusion=0.1),
            Light(id="rim_glow", type="point",
                  position_3d=(0, 200, -350), target=(0, 0, 0),
                  intensity=2500, temperature=5600, size=(5, 5),
                  diffusion=0.2),
        ]

    def _apply_macro_lighting(self, graph: SceneGraph):
        """微距材质展示布光"""
        graph.lights = [
            Light(id="macro_key", type="area", shape="disc",
                  position_3d=(0, 60, -80), target=(0, 0, 0),
                  intensity=1500, temperature=5500, size=(40, 40),
                  modifier="beauty_dish", diffusion=0.7),
            Light(id="macro_grazing", type="area", shape="rectangle",
                  position_3d=(-40, 30, -50), target=(0, 0, 0),
                  intensity=800, temperature=5500, size=(10, 80),
                  modifier="strip_softbox", diffusion=0.5),
        ]
        # 微距: 更新相机距离
        graph.camera.position_3d = (0, 50, -200)
        graph.camera.focus_distance_cm = 200
        graph.camera.distance_to_subject_cm = 200

    def _apply_atmospheric_lighting(self, graph: SceneGraph, bg_color: str):
        """氛围情绪布光 — 用背景色反推色温"""
        kelvin = self._kelvin_from_hex(bg_color)
        graph.lights = [
            Light(id="mood_key", type="area", shape="rectangle",
                  position_3d=(-100, 160, -220), target=(0, 0, 0),
                  intensity=1800, temperature=kelvin, size=(80, 120),
                  modifier="softbox", diffusion=0.8),
            Light(id="mood_accent", type="point",
                  position_3d=(60, 70, -280), target=(0, 0, 0),
                  intensity=500, temperature=2800, size=(8, 8),
                  diffusion=0.5),
            Light(id="mood_ambient", type="area", shape="disc",
                  position_3d=(0, 220, -100),
                  intensity=400, temperature=kelvin, size=(100, 100),
                  diffusion=1.0),
        ]

    def _add_prop(self, graph: SceneGraph, pid: str, ptype: str,
                  pos: tuple, size: tuple, albedo: str):
        """向场景图添加道具元素"""
        prop = SceneElement(
            id=pid, type="prop", label=ptype,
            bbox_center=pos, bbox_size=size,
            material=PBRMaterial(
                id=f"mat_{pid}", type=ptype, albedo=albedo,
                roughness=0.6, metallic=0.0,
            ),
            distance_to_camera_cm=380,
            angle_to_camera_deg=15 if pos[0] > 0 else -15,
            relative_scale_to_frame=0.15,
        )
        graph.elements.append(prop)

    def _set_material(self, graph: SceneGraph, mat_info: dict):
        """将品牌材质参数应用到产品元素"""
        for el in graph.elements:
            if el.type == "product":
                if mat_info.get("type"):
                    el.material.type = mat_info["type"]
                if mat_info.get("roughness") is not None:
                    el.material.roughness = mat_info["roughness"]
                if mat_info.get("metallic") is not None:
                    el.material.metallic = mat_info["metallic"]
                break

    # ═══════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════

    def _pick(self, items: list, default=None):
        """从列表中取第一个有效值，或返回默认值"""
        if items:
            return items[0]
        return default

    def _palette_variants(self, primary: List[str], secondary: List[str],
                          count: int = 3) -> List[str]:
        """从色板生成颜色变体描述"""
        variants = []
        for c in (primary[:2] + secondary[:1]):
            if isinstance(c, str) and c.strip():
                variants.append(c.strip())
        while len(variants) < count:
            variants.append("品牌主色调")
        return variants[:count]

    def _extract_material_info(self, vs: BrandVisualSystem) -> dict:
        """从材质系统提取关键材质信息"""
        if not vs.material_system:
            return {}
        # 取第一个材质类型
        for mat_type, variations in vs.material_system.items():
            if variations:
                return {"type": mat_type, "variations": len(variations)}
        return {}

    def _kelvin_from_hex(self, hex_color: str) -> int:
        """从暖色调 hex 粗略估算色温"""
        if not hex_color or not hex_color.startswith("#"):
            return 4500
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            # 暖色调 (r > b) → 低色温; 冷色调 → 高色温
            return max(2800, min(6500, int(6500 - (r - g) * 10)))
        except:
            return 4500

    # ═══════════════════════════════════════════════════════
    # 评分系统
    # ═══════════════════════════════════════════════════════

    def _score_creativity(self, c: CreativeConcept) -> float:
        """创意新颖度 — 不同概念类型有不同基准，再微调"""
        base = {
            "studio": 0.60,
            "lifestyle": 0.72,
            "editorial": 0.88,
            "macro": 0.85,
            "atmospheric": 0.82,
        }
        score = base.get(c.scene_type, 0.70)

        # 有颜色变体加分
        if len(c.color_variant) >= 3:
            score += 0.04
        # 有详细灯光方案加分
        if len(c.lighting_plan) >= 3:
            score += 0.03

        return min(1.0, score)

    def _score_brand_compliance(self, c: CreativeConcept,
                                 vs: BrandVisualSystem) -> float:
        """
        品牌合规度 — 基于视觉系统参数范围匹配
        检查: 色板使用 / 灯光模式 / 材质 / 构图规则
        """
        score = 0.80  # 基线

        # 色板匹配: 颜色变体中是否包含品牌色板中的色
        all_palette = vs.core_palette + vs.seasonal_palette + vs.accent_palette
        matched = 0
        for cv in c.color_variant:
            for pc in all_palette:
                if isinstance(cv, str) and isinstance(pc, str) and pc in cv:
                    matched += 1
                    break
        if matched > 0:
            score += min(0.10, matched * 0.03)

        # 灯光模式匹配
        if vs.lighting_patterns:
            score += 0.05

        # 构图规则存在
        if vs.composition_rules:
            score += 0.05

        # 材质系统存在
        if vs.material_system:
            score += 0.03

        # 置信度加权
        score *= (0.7 + 0.3 * vs.confidence)

        return min(1.0, score)

    def _score_feasibility(self, c: CreativeConcept) -> float:
        """
        可执行性 — 场景越复杂可行性越低
        """
        complexity = {
            "studio": 0.95,       # 最简单
            "macro": 0.82,
            "lifestyle": 0.72,
            "atmospheric": 0.65,
            "editorial": 0.58,    # 最复杂
        }
        base = complexity.get(c.scene_type, 0.70)

        # 道具越多可行性越低
        if c.scene_parameters.get("props") and "无" not in str(c.scene_parameters["props"]):
            base -= 0.05

        return min(1.0, max(0.3, base))

    # ═══════════════════════════════════════════════════════
    # 选择与输出
    # ═══════════════════════════════════════════════════════

    def select_best_concept(self) -> CreativeConcept:
        """综合评分选最优: 创意30% + 品牌40% + 可行30%"""
        if not self._concepts:
            return CreativeConcept()
        scored = [(c,
                   c.creative_score * 0.3 +
                   c.brand_compliance * 0.4 +
                   c.feasibility * 0.3)
                  for c in self._concepts]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def get_concepts(self) -> List[CreativeConcept]:
        return self._concepts

    def concept_summary(self) -> List[Dict]:
        """所有概念的摘要 (供 Pitch 使用)"""
        return [
            {
                "name": c.concept_name,
                "description": c.concept_description,
                "rationale": c.rationale,
                "scene_type": c.scene_type,
                "color_variants": c.color_variant,
                "scores": {
                    "creativity": round(c.creative_score, 2),
                    "brand_compliance": round(c.brand_compliance, 2),
                    "feasibility": round(c.feasibility, 2),
                },
            }
            for c in self._concepts
        ]
