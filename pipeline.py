"""
Hermes Agent OS — 统一 Pipeline 入口

替代 production/pipeline, page_modules/pipeline, agency/agency 三个分散入口。
统一为单一入口，内部按阶段调度各子模块。

使用方式:
    from pipeline import HermesPipeline
    
    # 从产品图
    result = pipe.run(image_url="https://...product.jpg", brand="NORHOR")
    
    # 从品牌名
    result = pipe.run(brand="MUJI 無印良品", category="home")
    
    # 品牌全案研究
    result = pipe.run_fullcase(brand="MUJI", category="home")
"""
import os, sys, json, time
from typing import Optional, Dict, Any, List
from datetime import datetime


class HermesPipeline:
    """统一 Pipeline — 6 阶段归一化流程"""

    def __init__(self, api_key: Optional[str] = None,
                 output_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.output_dir = output_dir or os.path.normpath(
            os.path.join(os.path.dirname(__file__), "output")
        )
        os.makedirs(self.output_dir, exist_ok=True)

        # 延迟加载的子模块
        self._modules: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        """加载全部子模块（延迟加载，每个独立try/except）"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages"))
        errors = []

        # Stage 1-2: 研究与分析
        for name, import_path, attr in [
            ("brand_researcher", "research.brand_researcher", "BrandResearcher"),
            ("design_analyzer", "research.design_analyzer", "DesignAnalyzer"),
            ("color_analyzer", "research.color_system", "ColorSystemAnalyzer"),
            ("scene_parser", "dna_engine.scene_parser", "SceneParser"),
            ("acr_analyzer", "page_modules.acr_analyzer", "ACRAnalyzer"),
        ]:
            try:
                mod = __import__(import_path, fromlist=[attr])
                self._modules[name] = getattr(mod, attr)(self.api_key)
            except Exception as e:
                errors.append(f"{name}: {e}")

        # Stage 3: 知识库
        try:
            from knowledge.brand_knowledge import BrandKnowledgeBase
            self._modules["knowledge"] = BrandKnowledgeBase()
        except Exception as e:
            errors.append(f"knowledge: {e}")

        # Stage 4: 风格引擎
        try:
            from page_modules.style_engine import StyleLibrary, PromptGenerator
            self._modules["style_lib"] = StyleLibrary()
            self._modules["prompt_gen"] = PromptGenerator()
        except Exception as e:
            errors.append(f"style: {e}")

        # Stage 5: 校验
        if self._modules.get("acr_analyzer"):
            try:
                from page_modules.validator import Validator
                self._modules["validator"] = Validator(self._modules["acr_analyzer"])
            except Exception as e:
                errors.append(f"validator: {e}")

        # Stage 6: 进化
        try:
            from dna_engine.mcp_bridge import DesignMCPBridge
            self._modules["mcp"] = DesignMCPBridge()
        except Exception as e:
            errors.append(f"mcp: {e}")

        # 品牌全案
        try:
            from page_modules.brand_fullcase import BrandFullCase
            self._modules["fullcase"] = BrandFullCase(self.api_key, self.output_dir)
        except Exception as e:
            errors.append(f"fullcase: {e}")

        # 详情页图片生成
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "norhor", "src"))
            from detail_image_gen import generate_detail_images
            self._modules["image_gen"] = generate_detail_images
        except Exception as e:
            errors.append(f"image_gen: {e}")

        if errors:
            for e in errors:
                print(f"  ⚠️  {e}")

    def _get(self, name: str):
        return self._modules.get(name)

    # ═══════════════════════════════════════════════════
    #  主入口
    # ═══════════════════════════════════════════════════

    def run(self, image_url: Optional[str] = None,
            brand: Optional[str] = None,
            category: str = "furniture") -> Dict[str, Any]:
        """统一入口: 产品图或品牌名 → 完整品牌设计产出"""
        print(f"\n  🏭 Hermes Pipeline — 统一入口")
        result = {
            "brand": brand or f"brand_{abs(hash(str(image_url))) % 10000}",
            "started_at": datetime.utcnow().isoformat(),
            "stages": {},
            "output": {},
        }

        # Stage 1: 品牌研究
        if brand:
            researcher = self._get("brand_researcher")
            if researcher:
                try:
                    print("  📡 Stage 1: 品牌网络研究...")
                    research = researcher.research_brand(brand)
                    result["stages"]["research"] = "✅"
                    if self._get("knowledge"):
                        self._get("knowledge").build_from_research(
                            brand, research.__dict__ if hasattr(research, '__dict__') else {})
                except Exception as e:
                    result["stages"]["research"] = f"⚠️ {e}"

        # Stage 2: 场景图分析
        if image_url:
            parser = self._get("scene_parser")
            if parser:
                try:
                    print("  📐 Stage 2: 场景图分析...")
                    graph = parser.parse(image_url)
                    result["scene_graph"] = graph.to_dict()
                    result["stages"]["scene_graph"] = "✅"
                except Exception as e:
                    result["stages"]["scene_graph"] = f"⚠️ {e}"

        # Stage 3: 生成详情页图片
        image_gen = self._get("image_gen")
        if image_gen:
            try:
                print("  🖼️  Stage 3: 生成详情页...")
                out_dir = os.path.join(self.output_dir,
                                       (brand or "product").lower().replace(" ", "_"))
                zip_path = image_gen(
                    product_name=brand or "产品",
                    category=category,
                    brand_style="nordic",
                    output_dir=out_dir,
                )
                result["output"]["zip"] = zip_path
                result["stages"]["generate"] = "✅"
            except Exception as e:
                result["stages"]["generate"] = f"⚠️ {e}"

        result["completed_at"] = datetime.utcnow().isoformat()
        ok = sum(1 for s in result["stages"].values() if s == "✅")
        print(f"\n  ✅ 完成: {ok}/{len(result['stages'])} 阶段成功")
        return result

    def run_fullcase(self, brand: str, category: str = "furniture",
                     product_desc: str = "") -> Dict[str, Any]:
        """品牌全案研究入口"""
        fc = self._get("fullcase")
        if not fc:
            return {"error": "BrandFullCase module not loaded"}
        return fc.run_full_research(brand, category, product_desc)

    def run_evolution(self) -> Dict[str, Any]:
        """自进化入口"""
        mcp = self._get("mcp")
        if not mcp:
            return {"error": "MCP bridge not loaded"}
        from research.agency_researcher import EvolutionScheduler, FourAResearcher
        r = FourAResearcher(self.api_key)
        kb = self._get("knowledge")
        if kb:
            r.connect_knowledge_base(kb)
        s = EvolutionScheduler(r, kb)
        return s.run_evolution_cycle()

    def status(self) -> Dict[str, bool]:
        """查看各模块加载状态"""
        return {k: v is not None for k, v in self._modules.items()}
