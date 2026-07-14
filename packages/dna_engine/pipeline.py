"""
品牌DNA流水线 — 全流程编排

完整流程:
1. 接收产品图URL
2. ReverseEngineer → 全维度逆向分析（相机/灯光/后期/构图/软件/材质）
3. BrandDatabase → 保存分析结果到品牌DNA库
4. BrandDatabase → 搜索相似历史配置
5. BrandDatabase → 更新品牌聚合配置文件
6. (可选) SceneReplacer → 场景替换Prompt
7. 输出: 分析报告 + 品牌匹配度 + 场景替换Prompt
"""
import os, json
from typing import Optional, Dict, Any
from .types import ImageAnalysisResult, SceneReplaceRequest
from .reverse_engineer import ReverseEngineer
from .brand_db import BrandDatabase
from .scene_replacer import SceneReplacer


class DNAPipeline:
    """品牌DNA全流程管线"""

    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        self.api_key = api_key
        self.engine = ReverseEngineer(api_key)
        self.db = BrandDatabase(db_path)
        self.replacer = SceneReplacer(api_key)

    def run_analysis(self, image_url: str, brand: str = "norhor") -> Dict[str, Any]:
        """
        执行完整的品牌DNA分析流程
        
        返回:
        {
            "analysis": ImageAnalysisResult (dict),
            "brand_profile": 品牌聚合参数,
            "similar_history": 相似历史配置,
            "scene_prompts": 各场景替换Prompt,
        }
        """
        # Step 1: 逆向分析
        result = self.engine.analyze(image_url)

        # Step 2: 存入品牌库
        self.db.save_analysis(result, brand)

        # Step 3: 获取品牌聚合配置
        profile = self.db.get_brand_profile(brand)

        # Step 4: 搜索相似历史
        similar_camera = self.db.search_similar(result.camera.to_dict(), "camera", 3)
        similar_lighting = self.db.search_similar(
            {k: v for k, v in result.lighting.__dict__.items() if v is not None},
            "lighting", 3
        )

        # Step 5: 为每个场景生成替换Prompt
        scene_prompts = {}
        for scene_id in self.replacer.available_scenes():
            req = SceneReplaceRequest(
                product_image_url=image_url,
                target_scene=scene_id,
            )
            prompt = self.replacer.build_prompt(result, req)
            scene_prompts[scene_id] = prompt

        return {
            "analysis": {
                "camera": result.camera.to_dict(),
                "lighting": {k: v for k, v in result.lighting.__dict__.items() if v is not None},
                "color_grading": {k: v for k, v in result.color_grading.__dict__.items() if v is not None},
                "composition": result.composition.__dict__,
                "software": result.software.__dict__,
                "materials": result.materials_detected,
                "style_keywords": result.style_keywords,
                "brand_match": result.brand_match,
                "raw": result.raw_analysis,
            },
            "brand_profile": profile,
            "similar_history": {
                "camera": similar_camera,
                "lighting": similar_lighting,
            },
            "scene_prompts": scene_prompts,
            "total_brand_analyses": profile.get("total_analyses", 0),
            "status": "success",
        }

    def search_similar_images(self, params: dict, dimension: str = "camera") -> list:
        """搜索相似参数的历史图像"""
        return self.db.search_similar(params, dimension)
