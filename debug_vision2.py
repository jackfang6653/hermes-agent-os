"""诊断 SceneParser.parse() 精确失败位置"""
import sys, os, json, requests

project_root = r"C:\Users\Administrator\Documents\Hermes Agent OS团队"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "packages"))

api_key = os.environ.get("OPENAI_API_KEY")
image_url = "https://img.muji.net/img/item/4550512828808_1260.jpg"

# 复制 _call_vision 的 prompt 和调用方式
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
      "bbox_center": [x, y, z],
      "bbox_size": [width, height, depth],
      "material": {
        "name": "材质名",
        "type": "fabric/wood/metal/leather/stone/glass/ceramic/composite",
        "albedo": "#hex颜色",
        "roughness": 0-1,
        "metallic": 0-1,
        "normal_strength": 0-1,
        "subsurface": 0-1,
        "clearcoat": 0-1,
        "anisotropy": 0-1,
        "sheen": 0-1,
        "opacity": 0-1,
        "ior": 数值,
        "transmission": 0-1,
        "displacement": 0-1
      }
    }
  ],
  "camera": { "focal_length_mm": 50, "aperture_f": 2.8, "iso": 100 },
  "lights": [],
  "post_processing": {},
  "environment": {"background_color": "#ffffff"}
}
```

**重要提示**：
1. 每个元素的material必须完整填写PBR参数
2. 灯光的position_3d必须相对相机位置合理
3. 如果有多个相似元素，给每个唯一ID"""

print("Step 1: Calling vision API...")
resp = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": SCENE_GRAPH_PROMPT},
            {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}
        ]}],
        "max_tokens": 4096,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    },
    timeout=120
)

print(f"Step 2: Status={resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text[:500]}")
    exit(1)

resp_data = resp.json()
print(f"Step 3: Got response, keys={list(resp_data.keys())}")

choices = resp_data.get("choices", [])
print(f"Step 4: choices count={len(choices)}")

if not choices:
    print("No choices!")
    exit(1)

msg = choices[0].get("message")
print(f"Step 5: message type={type(msg).__name__}, is None={msg is None}")

if msg is None:
    print(f"Choice keys: {list(choices[0].keys())}")
    print(f"Full choice: {json.dumps(choices[0], indent=2)[:500]}")
    exit(1)

content = msg.get("content")
print(f"Step 6: content type={type(content).__name__}, is None={content is None}")
if content:
    print(f"Content length: {len(content)}")
    print(f"First 500 chars:")
    print(content[:500])
    
    # Try parsing as JSON
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        parsed = json.loads(content[start:end])
        print(f"\nStep 7: JSON parsed OK")
        print(f"  scene_id: {parsed.get('scene_id', '?')}")
        print(f"  elements: {len(parsed.get('elements', []))}")
        print(f"  lights: {len(parsed.get('lights', []))}")
        
        # Check for null materials
        for i, elem in enumerate(parsed.get('elements', [])):
            mat = elem.get('material')
            if mat is None:
                print(f"  ⚠️ Element {i} material is None!")
            elif not isinstance(mat, dict):
                print(f"  ⚠️ Element {i} material type: {type(mat).__name__} = {mat}")
    except Exception as e:
        print(f"\nStep 7: JSON parse failed: {e}")
else:
    print("Content is None!")
    print(f"Full message: {json.dumps(msg, indent=2)[:500]}")
