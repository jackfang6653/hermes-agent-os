"""
场景解析器 — GPT-4o Vision → 完整场景图

从一张产品图中提取完整场景图，包含：
- 每个场景元素（ID/尺寸/结构/位置/材质/透视）
- PBR 材质参数
- 每盏灯的完整参数
- 相机系统参数
- 后期处理参数
- 空间关系（遮挡/比例/层次）
"""
import os, json, requests
from typing import Optional
from .scene_graph import *


def _call_vision(image_url: str, prompt: str, api_key: str, retry_on_refusal: bool = True) -> str:
    """调用Vision API, 自动处理 refusal 降级"""
    def _do_call(model: str, detail: str, p: str) -> dict:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": p},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": detail}}
                ]}],
                "max_tokens": 8192,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            },
            timeout=120
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Vision API error {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    data = _do_call("gpt-4o", "high", prompt)
    content = data["choices"][0]["message"]["content"]
    refusal = data["choices"][0]["message"].get("refusal")

    if content is None and refusal and retry_on_refusal:
        # 降级: 用 gpt-4o-mini + low detail 重试
        print(f"    ⚠️  GPT-4o refused (\"{refusal[:60]}...\"), 降级到 gpt-4o-mini...")
        data = _do_call("gpt-4o-mini", "low", prompt)
        content = data["choices"][0]["message"]["content"]

    if content is None:
        raise RuntimeError(f"Vision API returned null content. Refusal: {refusal}")

    return content


SCENE_GRAPH_PROMPT = """你是一位顶级3D场景解析专家。请从这张产品图片中提取**完整场景图**，输出JSON。

## 要求
- 每个元素必须有唯一ID
- 所有尺寸使用厘米(cm)作为单位
- 坐标系: 相机在Z轴负方向, Y轴向上
- 尽可能精确, 如不确定用null

## 输出结构

```json
{
  "scene_id": "唯一场景ID",
  "scene_type": "product_photography",
  "brand": "推测品牌",

  "elements": [
    {
      "id": "product_01",
      "type": "product/floor/wall/prop/decoration",
      "label": "元素名称",
      "bbox_center": [x, y, z],     // 3D包围盒中心cm
      "bbox_size": [width, height, depth],  // 尺寸cm
      "rotation": [pitch, yaw, roll],       // 欧拉角
      "distance_to_camera_cm": 数值,
      "angle_to_camera_deg": 数值,          // 相对相机角度
      "relative_scale_to_frame": 0-1,       // 占画面比例
      "occlusion_relation": "遮挡描述",
      
      // PBR材质——这是最关键的部分
      "material": {
        "name": "材质名",
        "type": "fabric/wood/metal/leather/stone/glass/ceramic/composite",
        "albedo": "#hex颜色",
        "roughness": 0-1,            // 粗糙度 0=镜面 1=全粗
        "metallic": 0-1,             // 金属度
        "normal_strength": 0-1,      // 法线强度
        "subsurface": 0-1,           // 次表面散射(皮肤/蜡/织物)
        "clearcoat": 0-1,            // 清漆层
        "anisotropy": 0-1,           // 各向异性(拉丝金属)
        "sheen": 0-1,                // 绒毛光泽(织物)
        "opacity": 0-1,              // 不透明度
        "ior": 数值,                  // 折射率(玻璃1.5/钻石2.4)
        "transmission": 0-1,         // 透射
        "displacement": 0-1,         // 置换强度
        "texture_description": "纹理描述(编织方向/木纹走向/皮革毛孔等)"
      }
    }
  ],

  "camera": {
    "camera_model": "推测机身",
    "lens_model": "推测镜头",
    "sensor_size": "full_frame/aps_c/medium_format",
    "focal_length_mm": 35mm等效焦距,
    "aperture_f": 光圈,
    "aperture_blades": 光圈叶片数,
    "shutter_speed": "快门",
    "iso": 数值,
    "position_3d": [x, y, z],
    "target": [x, y, z],
    "distance_to_subject_cm": 数值,
    "focus_distance_cm": 数值,
    "dof_style": "natural/tilt_shift/macro",
    "lens_distortion": -1~1
  },

  "lights": [
    {
      "id": "key_01",
      "type": "area/point/spot",
      "shape": "rectangle/disc",
      "position_3d": [x, y, z],
      "target": [x, y, z],
      "intensity": 流明,
      "color": "#hex",
      "temperature": 色温K,
      "exposure": 曝光补偿,
      "size": [宽cm, 高cm],
      "modifier": "softbox/beauty_dish/umbrella/grid/reflector",
      "grid_angle": 蜂巢角度或null,
      "diffusion": 柔光程度0-1
    }
  ],

  "post_processing": {
    "exposure": 数值, "contrast": 数值,
    "highlights": 数值, "shadows": 数值,
    "whites": 数值, "blacks": 数值,
    "texture": 数值, "clarity": 数值,
    "vibrance": 数值, "saturation": 数值,
    "color_temperature": -100~100,
    "tint": -100~100,
    "sharpening": 数值, "noise_reduction": 数值,
    "crop_aspect": "宽高比或null",
    "vignette": 暗角-100~100,
    "lut_description": "推测的LUT风格描述"
  },

  "environment": {
    "hdri_description": "环境光描述",
    "background_color": "#hex",
    "ground_visible": true/false,
    "ground_material": "地板材质描述"
  }
}
```

**重要提示**：
1. 每个元素的material必须完整填写PBR参数
2. 灯光的position_3d必须相对相机位置合理
3. 空间关系必须自洽（产品在相机前，灯光在产品周围）
4. 如果有多个相似元素，给每个唯一ID"""


class SceneParser:
    """图片→场景图解析器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要OPENAI_API_KEY")

    def parse(self, image_url: str) -> SceneGraph:
        """解析图片为完整场景图"""
        raw = _call_vision(image_url, SCENE_GRAPH_PROMPT, self.api_key)
        data = self._parse_json(raw)
        return self._build_graph(data, image_url)

    def _parse_json(self, text: str) -> dict:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except Exception as e:
            raise ValueError(f"Failed to parse GPT response as JSON: {e}\nRaw: {text[:500]}")

    def _build_graph(self, data: dict, image_url: str) -> SceneGraph:
        graph = SceneGraph(
            scene_id=data.get("scene_id", f"scene_{hash(image_url) % 10000}"),
            scene_type=data.get("scene_type", "product_photography"),
            brand=data.get("brand", ""),
            source_image_url=image_url,
        )

        # Elements
        for ed in data.get("elements", []):
            mat_data = ed.get("material", {})
            material = PBRMaterial(
                id=f"{ed.get('id', 'elem')}_mat",
                name=mat_data.get("name", ""),
                type=mat_data.get("type", "unknown"),
                albedo=mat_data.get("albedo", "#808080"),
                roughness=mat_data.get("roughness", 0.5),
                metallic=mat_data.get("metallic", 0),
                normal_strength=mat_data.get("normal_strength", 0.5),
                subsurface=mat_data.get("subsurface", 0),
                clearcoat=mat_data.get("clearcoat", 0),
                anisotropy=mat_data.get("anisotropy", 0),
                sheen=mat_data.get("sheen", 0),
                opacity=mat_data.get("opacity", 1),
                ior=mat_data.get("ior", 1.5),
                transmission=mat_data.get("transmission", 0),
                displacement=mat_data.get("displacement", 0),
            )
            element = SceneElement(
                id=ed.get("id", "unknown"),
                type=ed.get("type", "unknown"),
                label=ed.get("label", ""),
                bbox_center=tuple(ed.get("bbox_center", [0, 0, 0])),
                bbox_size=tuple(ed.get("bbox_size", [100, 100, 100])),
                rotation=tuple(ed.get("rotation", [0, 0, 0])),
                scale=tuple(ed.get("scale", [1, 1, 1])),
                material=material,
                distance_to_camera_cm=ed.get("distance_to_camera_cm", 0),
                angle_to_camera_deg=ed.get("angle_to_camera_deg", 0),
                relative_scale_to_frame=ed.get("relative_scale_to_frame", 0),
            )
            graph.elements.append(element)

        # Camera
        cd = data.get("camera", {})
        if cd:
            graph.camera = CameraSystem(
                camera_model=cd.get("camera_model"),
                lens_model=cd.get("lens_model"),
                sensor_size=cd.get("sensor_size", "full_frame"),
                focal_length_mm=cd.get("focal_length_mm", 85),
                aperture_f=cd.get("aperture_f", 2.8),
                aperture_blades=cd.get("aperture_blades", 9),
                shutter_speed=cd.get("shutter_speed", "1/125"),
                iso=cd.get("iso", 100),
                position_3d=tuple(cd.get("position_3d", [0, 80, -400])),
                target=tuple(cd.get("target", [0, 0, 0])),
                distance_to_subject_cm=cd.get("distance_to_subject_cm", 400),
                focus_distance_cm=cd.get("focus_distance_cm", 400),
                dof_style=cd.get("dof_style", "natural"),
                lens_distortion=cd.get("lens_distortion", 0),
                confidence=0.85,
            )

        # Lights
        for ld in data.get("lights", []):
            light = Light(
                id=ld.get("id", "light_01"),
                type=ld.get("type", "area"),
                shape=ld.get("shape", "rectangle"),
                position_3d=tuple(ld.get("position_3d", [0, 0, 0])),
                target=tuple(ld.get("target", [0, 0, 0])) if ld.get("target") else None,
                intensity=ld.get("intensity", 1000),
                color=ld.get("color", "#ffffff"),
                temperature=ld.get("temperature", 5500),
                exposure=ld.get("exposure", 0),
                size=tuple(ld.get("size", [60, 90])),
                modifier=ld.get("modifier"),
                grid_angle=ld.get("grid_angle"),
                diffusion=ld.get("diffusion", 1.0),
            )
            graph.lights.append(light)

        # Post
        pd = data.get("post_processing", {})
        if pd:
            graph.post_processing = PostProcessing(
                exposure=pd.get("exposure", 0),
                contrast=pd.get("contrast", 0),
                highlights=pd.get("highlights", 0),
                shadows=pd.get("shadows", 0),
                whites=pd.get("whites", 0),
                blacks=pd.get("blacks", 0),
                texture=pd.get("texture", 0),
                clarity=pd.get("clarity", 0),
                vibrance=pd.get("vibrance", 0),
                saturation=pd.get("saturation", 0),
                color_temperature=pd.get("color_temperature", 0),
                tint=pd.get("tint", 0),
                sharpening=pd.get("sharpening", 0),
                noise_reduction=pd.get("noise_reduction", 0),
                crop_aspect=pd.get("crop_aspect"),
                vignette=pd.get("vignette", 0),
            )

        # Environment
        env = data.get("environment", {})
        if env:
            graph.background_color = env.get("background_color", "#f5f0e8")

        return graph
