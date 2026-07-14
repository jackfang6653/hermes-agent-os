"""
品牌DNA流水线 — 完整版

流程：
1. SceneParser → 图片 → 完整场景图（含PBR材质/灯光/相机/空间关系）
2. BrandDatabase → 存入品牌DNA库（自进化）
3. SceneRenderer → 场景图 → 参数化生图指令
4. (可选) 场景替换 → 保持灯光/相机/材质只换背景
5. (可选) 编辑 → 修改场景图参数后重新生成
"""
from typing import Optional, Dict, Any
from .scene_graph import SceneGraph
from .scene_parser import SceneParser
from .scene_renderer import SceneRenderer
from .brand_db import BrandDatabase


class DNAPipeline:
    """品牌DNA全流程管线"""

    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        self.api_key = api_key
        self.parser = SceneParser(api_key)
        self.renderer = SceneRenderer()
        self.db = BrandDatabase(db_path)

    def analyze(self, image_url: str, brand: str = "norhor") -> Dict[str, Any]:
        """
        完整分析流程：图片→场景图→品牌库→生成指令
        """
        # Step 1: Parse into Scene Graph
        graph = self.parser.parse(image_url)

        # Step 2: Save to brand database
        self.db.save_scene_graph(graph, brand)

        # Step 3: Generate rendering prompt
        prompt = self.renderer.render_generation_prompt(graph)

        # Step 4: Get brand profile
        profile = self.db.get_brand_profile(brand)

        return {
            "scene_graph": graph.to_dict(),
            "generation_prompt": prompt,
            "brand_profile": profile,
            "elements_count": len(graph.elements),
            "lights_count": len(graph.lights),
            "camera": graph.camera.to_dict(),
            "status": "success",
        }

    def replace_scene(self, image_url: str, target_scene: str) -> Dict[str, Any]:
        """场景替换：保持产品/灯光/相机，只换背景"""
        graph = self.parser.parse(image_url)
        prompt = self.renderer.render_generation_prompt(graph, target_scene)
        return {
            "original_scene_graph": graph.to_dict(),
            "scene_replace_prompt": prompt,
            "target_scene": target_scene,
            "status": "success",
        }

    def edit_scene(self, image_url: str, edit_instruction: str) -> Dict[str, Any]:
        """编辑场景：修改变量后重新生成"""
        graph = self.parser.parse(image_url)
        edit_prompt = self.renderer.render_scene_edit(graph, edit_instruction)
        return {
            "original_scene_graph": graph.to_dict(),
            "edit_prompt": edit_prompt,
            "edit_instruction": edit_instruction,
            "status": "success",
        }

    def close(self):
        self.db.close()
