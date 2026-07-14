"""
场景渲染器 — 场景图 → 参数化生成指令

将完整的SceneGraph转换为：
1. 精确生图Prompt（含全部PBR/灯光/相机参数）
2. 3D渲染场景描述（可导入Blender/C4D等）
3. 场景替换Prompt（保持灯光/相机只换背景）

核心能力：从参数→完美复原同款
"""
from typing import Optional
from .scene_graph import *


class SceneRenderer:
    """场景渲染器 — 参数化复原生成"""

    def render_generation_prompt(self, graph: SceneGraph, target_scene: Optional[str] = None) -> str:
        """从SceneGraph生成精确生图Prompt"""
        lines = []

        # 场景描述
        lines.append("PRODUCT PHOTOGRAPHY — PARAMETRIC GENERATION")
        lines.append("=" * 50)

        # 1. 产品描述
        products = [e for e in graph.elements if e.type == "product"]
        if products:
            p = products[0]
            lines.append(f"\n## PRODUCT")
            lines.append(f"Type: {p.label or p.id}")
            lines.append(f"Position: center of frame")
            lines.append(f"Scale in frame: {p.relative_scale_to_frame:.0%}")
            lines.append(f"Distance from camera: {p.distance_to_camera_cm}cm")
            lines.append(f"Rotation: pitch={p.rotation[0]}° yaw={p.rotation[1]}° roll={p.rotation[2]}°")
            lines.append(f"3D BBox: {p.bbox_size[0]}×{p.bbox_size[1]}×{p.bbox_size[2]}cm")

            # PBR 材质
            m = p.material
            lines.append(f"\n### Material: {m.name or m.type}")
            lines.append(f"Albedo: {m.albedo}")
            lines.append(f"Roughness: {m.roughness:.2f}")
            lines.append(f"Metallic: {m.metallic:.2f}")
            if m.normal_strength:
                lines.append(f"Normal strength: {m.normal_strength:.2f}")
            if m.subsurface:
                lines.append(f"Subsurface: {m.subsurface:.2f}")
            if m.clearcoat:
                lines.append(f"Clearcoat: {m.clearcoat:.2f}")
            if m.anisotropy:
                lines.append(f"Anisotropy: {m.anisotropy:.2f}")
            if m.sheen:
                lines.append(f"Sheen: {m.sheen:.2f}")
            lines.append(f"IOR: {m.ior:.2f}")
            if m.opacity < 1:
                lines.append(f"Opacity: {m.opacity:.0%}")

        # 2. 场景元素
        props = [e for e in graph.elements if e.type not in ("product", "floor", "wall")]
        floors = [e for e in graph.elements if e.type == "floor"]
        walls = [e for e in graph.elements if e.type == "wall"]

        lines.append(f"\n## SCENE ENVIRONMENT")
        if target_scene:
            lines.append(f"Target scene: {target_scene}")
        lines.append(f"Background: {graph.background_color}")
        if floors:
            f = floors[0]
            lines.append(f"Floor: {f.material.type}, albedo={f.material.albedo}, roughness={f.material.roughness:.2f}")
        if walls:
            w = walls[0]
            lines.append(f"Wall: {w.material.type}, albedo={w.material.albedo}")
        if props:
            lines.append(f"Props ({len(props)}):")
            for pr in props:
                lines.append(f"  - {pr.label or pr.id}: {pr.bbox_size[0]}×{pr.bbox_size[1]}×{pr.bbox_size[2]}cm at pos{pr.bbox_center}")

        # 3. 空间关系
        lines.append(f"\n## SPATIAL RELATIONS")
        for e in graph.elements:
            if e.distance_to_camera_cm:
                lines.append(f"{e.id}: {e.distance_to_camera_cm}cm from camera, {e.angle_to_camera_deg}° angle")

        # 4. 相机参数
        c = graph.camera
        lines.append(f"\n## CAMERA SYSTEM")
        if c.camera_model:
            lines.append(f"Body: {c.camera_model}")
        if c.lens_model:
            lines.append(f"Lens: {c.lens_model}")
        lines.append(f"Sensor: {c.sensor_size} ({c.sensor_width_mm}×{c.sensor_height_mm}mm)")
        lines.append(f"Focal length (35mm eq): {c.focal_length_mm}mm")
        lines.append(f"Aperture: f/{c.aperture_f}")
        lines.append(f"Shutter: {c.shutter_speed}, ISO: {c.iso}")
        lines.append(f"Camera position: {c.position_3d}")
        lines.append(f"Focus distance: {c.focus_distance_cm}cm")
        if c.aperture_blades:
            lines.append(f"Aperture blades: {c.aperture_blades}")

        # 5. 灯光系统
        lines.append(f"\n## LIGHTING SYSTEM ({len(graph.lights)} lights)")
        for i, l in enumerate(graph.lights):
            lines.append(f"\n### Light {i+1}: {l.id} ({l.type})")
            lines.append(f"Position: {l.position_3d}")
            if l.target:
                lines.append(f"Target: {l.target}")
            lines.append(f"Shape: {l.shape}, Size: {l.size[0]}×{l.size[1]}cm")
            lines.append(f"Intensity: {l.intensity}lm, Exposure: {l.exposure}EV")
            lines.append(f"Color: {l.color}, Temperature: {l.temperature}K")
            lines.append(f"Falloff: {l.falloff_type}")
            if l.modifier:
                lines.append(f"Modifier: {l.modifier}")
            if l.grid_angle:
                lines.append(f"Grid angle: {l.grid_angle}°")
            lines.append(f"Diffusion: {l.diffusion:.0%}")

        # 6. 后期
        pp = graph.post_processing
        lines.append(f"\n## POST PROCESSING")
        for key in ["exposure", "contrast", "highlights", "shadows", "whites", "blacks",
                     "texture", "clarity", "vibrance", "saturation",
                     "color_temperature", "tint", "sharpening", "noise_reduction", "vignette"]:
            val = getattr(pp, key, 0)
            if val:
                lines.append(f"{key}: {val:+d}" if isinstance(val, int) else f"{key}: {val:+.1f}")

        # 7. 质量控制
        lines.append(f"\n## QUALITY CONTROL")
        lines.append("Sharp focus on product")
        lines.append("Natural depth of field")
        lines.append("Professional color grading")
        lines.append("8K resolution, no distortion")
        lines.append("No watermark, no text overlay")

        # 8. Negative
        lines.append(f"\n## NEGATIVE PROMPT")
        lines.append("amateur, snapshot, low quality, blurry, distorted, deformed, watermark, text, logo, signature")

        return "\n".join(lines)

    def render_scene_edit(self, graph: SceneGraph, edit_instruction: str) -> str:
        """根据编辑指令修改场景参数"""
        return f"""
SCENE EDIT INSTRUCTION
======================
Original scene: {graph.scene_id}
Edit: {edit_instruction}

PARAMETERS TO MODIFY
--------------------
Based on the edit instruction, identify which parameters change.
Keep all other parameters from the original scene graph unchanged.

Original camera: {graph.camera.focal_length_mm}mm f/{graph.camera.aperture_f}
Original lights: {len(graph.lights)} lights
Original elements: {len(graph.elements)} elements

Output ONLY the modified parameters as a partial JSON update.
"""
