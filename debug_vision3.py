"""Test if simpler vision prompt avoids refusal"""
import os, json, requests

api_key = os.environ.get("OPENAI_API_KEY")
image_url = "https://img.muji.net/img/item/4550512828808_1260.jpg"

# Simpler prompt
prompt = """Analyze this product photo and return a JSON with these fields:
- product_description: what the product is
- colors: list of hex color codes visible
- lighting_type: type of lighting used
- camera_angle: camera perspective
- background: background description
- materials: list of visible materials

Be specific and precise."""

resp = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}
        ]}],
        "max_tokens": 1000,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    },
    timeout=60
)

print(f"Status: {resp.status_code}")
data = resp.json()
content = data["choices"][0]["message"]["content"]
refusal = data["choices"][0]["message"].get("refusal")
print(f"Refusal: {refusal}")
print(f"Content None: {content is None}")
if content:
    print(f"Content: {content[:500]}")
