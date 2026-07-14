"""诊断 SceneParser 问题"""
import sys, os, json, requests

project_root = r"C:\Users\Administrator\Documents\Hermes Agent OS团队"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "packages"))

api_key = os.environ.get("OPENAI_API_KEY")

image_url = "https://img.muji.net/img/item/4550512828808_1260.jpg"

prompt = "Describe this image briefly in JSON: {\"description\": \"...\"}"

print(f"API Key loaded: {bool(api_key)}")
print(f"API Key prefix: {api_key[:10] if api_key else 'NONE'}...")

resp = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}
        ]}],
        "max_tokens": 500,
        "temperature": 0.1,
    },
    timeout=60
)

print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    try:
        data = resp.json()
        print(f"Keys: {list(data.keys())}")
        choices = data.get("choices", [])
        print(f"Choices count: {len(choices)}")
        if choices:
            msg = choices[0].get("message", {})
            print(f"Message keys: {list(msg.keys())}")
            content = msg.get("content", "")
            print(f"Content (first 300): {content[:300]}")
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"Raw (first 500): {resp.text[:500]}")
else:
    print(f"Error: {resp.text[:500]}")
