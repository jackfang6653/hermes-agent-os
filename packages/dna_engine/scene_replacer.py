"""
场景替换引擎 — 匹配原有相机/灯光参数替换背景

核心能力：
1. 保持原有相机参数（焦距、光圈、景深）
2. 保持原有灯光方案（主光位置、填充比、色温）
3. 保持产品姿态和位置
4. 仅替换场景/背景
5. 输出匹配后的生图Prompt
"""
import os
import json
from typing import Optional
from .types import ImageAnalysisResult, SceneReplaceRequest

# ── 场景库 ─────────────────────────────────────────────

SCENE_LIBRARY = {
    "nordic_living": {
        "name": "北欧客厅",
        "background": "bright nordic living room with light wood floors, white walls, large windows with sheer curtains",
        "props": "minimal decor, wool rug, ceramic vase, linen throw pillow",
        "mood": "calm, airy, natural",
        "default_lighting": {"type": "natural", "temperature": 4500, "direction": "diffuse_window"},
    },
    "modern_dining": {
        "name": "现代餐厅",
        "background": "modern dining room with warm wood table, pendant lighting, subtle wall art",
        "props": "minimal table setting, ceramic plates, linen napkins, candle holder",
        "mood": "warm, intimate, sophisticated",
        "default_lighting": {"type": "warm_ambient", "temperature": 3200, "direction": "top_pendant"},
    },
    "boutique_studio": {
        "name": "精品展厅",
        "background": "clean white studio with soft gray seamless backdrop, subtle texture",
        "props": "minimal, single accent piece, neutral props",
        "mood": "clean, professional, premium",
        "default_lighting": {"type": "studio", "temperature": 5500, "direction": "softbox_45"},
    },
    "outdoor_patina": {
        "name": "户外庭院",
        "background": "sunlit outdoor patio with natural stone, greenery, warm afternoon light",
        "props": "potted plants, textured throw, natural fiber rug",
        "mood": "relaxed, organic, warm",
        "default_lighting": {"type": "golden_hour", "temperature": 3800, "direction": "low_side"},
    },
}


class SceneReplacer:
    """场景替换引擎 — 保持品牌参数替换场景"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def build_prompt(self, analysis: ImageAnalysisResult, request: SceneReplaceRequest) -> str:
        """
        从逆向分析结果 + 场景替换请求 → 构建精确的生图Prompt
        核心：保持相机/灯光参数，只替换场景背景
        """
        scene = SCENE_LIBRARY.get(request.target_scene, SCENE_LIBRARY["boutique_studio"])
        params = []

        # 产品描述
        product_desc = f"{analysis.materials_detected[0] if analysis.materials_detected else ''} product"
        params.append(f"Product: {product_desc}")
        if analysis.style_keywords:
            params.append(f"Style: {', '.join(analysis.style_keywords)}")

        # 相机参数（保持原有）
        cam = analysis.camera
        cam_desc = []
        if cam.focal_length_mm:
            cam_desc.append(f"{cam.focal_length_mm}mm lens")
        if cam.aperture_f:
            cam_desc.append(f"f/{cam.aperture_f}")
        if cam.camera_model:
            cam_desc.append(f"shot on {cam.camera_model}")
        if cam_desc:
            params.append(f"Camera: {', '.join(cam_desc)}")
            params.append("Depth of field: shallow, natural bokeh")

        # 灯光参数（保留原有 + 场景默认混合）
        lit = analysis.lighting
        lit_desc = []
        if lit.studio:
            if lit.light_count:
                lit_desc.append(f"{lit.light_count}-light studio setup")
            if lit.key_light_position:
                lit_desc.append(f"key light at {lit.key_light_position}")
            if lit.light_types:
                lit_desc.append(f"using {', '.join(lit.light_types[:2])}")
            if lit.color_temperature_k:
                lit_desc.append(f"{lit.color_temperature_k}K color temperature")
        else:
            # 没有灯光分析时用场景默认
            dl = scene["default_lighting"]
            lit_desc.append(f"{dl['type']} lighting from {dl['direction']}")
            lit_desc.append(f"{dl['temperature']}K")
        if lit_desc:
            params.append(f"Lighting: {', '.join(lit_desc)}")

        # 色彩参数
        col = analysis.color_grading
        col_desc = []
        if col.dominant_color_tone:
            col_desc.append(f"{col.dominant_color_tone} color tone")
        if col.color_temperature_shift:
            col_desc.append(f"color temp shifted {col.color_temperature_shift:+.0f}")
        if col.contrast:
            if col.contrast > 0:
                col_desc.append("higher contrast")
            elif col.contrast < 0:
                col_desc.append("lower contrast")
        if col_desc:
            params.append(f"Color grading: {', '.join(col_desc)}")

        # 场景（替换部分）
        params.append(f"Scene: {scene['background']}")
        params.append(f"Props: {scene['props']}")
        params.append(f"Mood: {scene['mood']}")

        # 相机视角
        comp = analysis.composition
        angle = "three-quarter view"
        if comp.product_position == "center":
            angle = "front-facing, product centered"
        params.append(f"Angle: {angle}")
        params.append(f"Aspect ratio: {comp.aspect_ratio}")

        # Quality
        params.append("Photography: commercial product photography, high-end e-commerce")
        params.append("Quality: 8K, sharp focus, natural shadows, professional color grading")
        params.append("Negative: low quality, blurry, distorted, amateur, snapshot, watermark, text")

        return "\n".join(params)

    def available_scenes(self) -> list:
        return list(SCENE_LIBRARY.keys())
