#!/usr/bin/env python3
"""
通用品牌详情页 — 长图 + 分图 + ZIP 生成器
支持任意品牌风格，自动匹配调色板、字体、版式
"""
from PIL import Image, ImageDraw, ImageFont
import io, os, json, zipfile, textwrap, math
from pathlib import Path
from typing import Optional, List, Dict, Any

# ── 品牌风格预设 ──────────────────────────────────────

BRAND_STYLES = {
    "nordic": {
        "name": "北欧风格",
        "palette": ["#f5f0e8", "#d4c5b0", "#8b7355", "#2c2c2c", "#c4a882", "#faf9f7"],
        "font_color": "#2c2c2c", "muted": "#8b7355", "bg": "#faf9f7",
        "card_bg": "#ffffff", "accent": "#c4a882",
        "hero_gradient": ("#f5f0e8", "#efe6d8"),
        "radius": 12, "font_vibe": "elegant",
    },
    "minimal": {
        "name": "极简风格",
        "palette": ["#ffffff", "#f0f0f0", "#333333", "#666666", "#000000", "#f8f8f8"],
        "font_color": "#111111", "muted": "#666666", "bg": "#f8f8f8",
        "card_bg": "#ffffff", "accent": "#333333",
        "hero_gradient": ("#ffffff", "#f0f0f0"),
        "radius": 4, "font_vibe": "modern",
    },
    "luxury": {
        "name": "奢华风格",
        "palette": ["#1a1a2e", "#16213e", "#0f3460", "#e94560", "#c4a882", "#f5f0e8"],
        "font_color": "#1a1a2e", "muted": "#0f3460", "bg": "#f5f0e8",
        "card_bg": "#ffffff", "accent": "#e94560",
        "hero_gradient": ("#1a1a2e", "#16213e"),
        "radius": 8, "font_vibe": "premium",
    },
    "natural": {
        "name": "自然风格",
        "palette": ["#4a7c59", "#8cb369", "#f4a261", "#e9c46a", "#6b705c", "#fefae0"],
        "font_color": "#2d3436", "muted": "#6b705c", "bg": "#fefae0",
        "card_bg": "#ffffff", "accent": "#4a7c59",
        "hero_gradient": ("#4a7c59", "#8cb369"),
        "radius": 16, "font_vibe": "organic",
    },
    "tech": {
        "name": "科技风格",
        "palette": ["#0a0a23", "#1a1a3e", "#3a86ff", "#8338ec", "#ff006e", "#f8f9fa"],
        "font_color": "#0a0a23", "muted": "#3a86ff", "bg": "#f8f9fa",
        "card_bg": "#ffffff", "accent": "#8338ec",
        "hero_gradient": ("#0a0a23", "#1a1a3e"),
        "radius": 4, "font_vibe": "futuristic",
    },
}

DEFAULT_STYLE = "nordic"

# ── 画布尺寸 ──────────────────────────────────────────
W = 1080
MARGIN = 48

# ── 辅助 ──────────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def try_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc", "/System/Library/Fonts/PingFang.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def get_style(name: str) -> dict:
    return BRAND_STYLES.get(name, BRAND_STYLES[DEFAULT_STYLE])

# ── 区块生成器 ────────────────────────────────────────

def _draw_hero(product_name, category, material, color, style, scene, brand_score, bs):
    """Hero区块"""
    H = 600
    img = Image.new("RGB", (W, H), hex_to_rgb(bs["bg"]))
    draw = ImageDraw.Draw(img)
    g1, g2 = bs["hero_gradient"]
    for i in range(H):
        t = i / H
        r = int(hex_to_rgb(g1)[0]*(1-t) + hex_to_rgb(g2)[0]*t)
        g = int(hex_to_rgb(g1)[1]*(1-t) + hex_to_rgb(g2)[1]*t)
        b = int(hex_to_rgb(g1)[2]*(1-t) + hex_to_rgb(g2)[2]*t)
        draw.line([(0,i),(W,i)], fill=(r,g,b))

    font_big = try_font(48, bold=True)
    font_mid = try_font(28)
    font_tag = try_font(16)
    
    # 品牌标签
    tag_w = draw.textlength(bs["name"], font_tag) + 20
    draw.rounded_rectangle([MARGIN, 30, MARGIN+tag_w, 60], 6, fill=hex_to_rgb(bs["accent"]))
    draw.text((MARGIN+10, 34), bs["name"], fill=(255,255,255), font=font_tag)

    # 产品名
    draw.text((MARGIN, H//2 - 60), product_name, fill=hex_to_rgb(bs["font_color"]), font=font_big)
    draw.text((MARGIN, H//2 + 10), f"{category} · {material} · {color}",
              fill=hex_to_rgb(bs["muted"]), font=font_mid)

    # 标签
    tags_y = H//2 + 70
    score_text = f"品牌匹配 {(brand_score*100):.0f}%"
    tags = [style, scene, score_text]
    x = MARGIN
    for t in tags:
        tw = draw.textlength(t, font_tag) + 24
        draw.rounded_rectangle([x, tags_y, x+tw, tags_y+34], 6, fill=hex_to_rgb(bs["accent"]))
        draw.text((x+12, tags_y+5), t, fill=(255,255,255), font=font_tag)
        x += tw + 12
    return img

def _draw_section(title, items, bs, note=None):
    """通用区块"""
    font_title = try_font(32, bold=True)
    font_body = try_font(22)
    font_small = try_font(18)
    item_h = 50
    title_h = 80
    line_h = 40
    
    content_h = len(items) * item_h + (60 if note else 0)
    section_h = title_h + content_h + MARGIN * 2
    total_h = section_h + MARGIN

    img = Image.new("RGB", (W, total_h), hex_to_rgb(bs["bg"]))
    draw = ImageDraw.Draw(img)
    
    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, MARGIN+section_h],
                            bs["radius"], fill=hex_to_rgb(bs["card_bg"]))
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(bs["accent"]))
    draw.text((MARGIN+32, MARGIN+24), title, fill=hex_to_rgb(bs["font_color"]), font=font_title)

    y = MARGIN + title_h
    for item in items:
        if isinstance(item, tuple):
            k, v = item
            draw.text((MARGIN+32, y), k, fill=hex_to_rgb(bs["muted"]), font=font_small)
            draw.text((MARGIN+200, y), str(v), fill=hex_to_rgb(bs["font_color"]), font=font_body)
        else:
            draw.text((MARGIN+32, y), f"• {item}", fill=hex_to_rgb(bs["font_color"]), font=font_body)
        y += item_h

    if note:
        draw.text((MARGIN+32, y+10), note, fill=hex_to_rgb(bs["accent"]), font=font_small)
    return img

def _draw_scene(scene_name, palette, mood_keywords, bs):
    """场景区块"""
    H = 300
    img = Image.new("RGB", (W, H), hex_to_rgb(bs["bg"]))
    draw = ImageDraw.Draw(img)
    font_title = try_font(32, bold=True)
    font_tag = try_font(16)

    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, H-MARGIN],
                            bs["radius"], fill=hex_to_rgb(bs["card_bg"]))
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(bs["accent"]))
    draw.text((MARGIN+32, MARGIN+24), f"场景搭配 · {scene_name}",
              fill=hex_to_rgb(bs["font_color"]), font=font_title)

    # 色板
    y = MARGIN + 90; x = MARGIN + 32
    for c in palette[:6]:
        draw.rounded_rectangle([x, y, x+40, y+40], 6, fill=hex_to_rgb(c))
        draw.rounded_rectangle([x, y, x+40, y+40], 6, outline=hex_to_rgb("#cccccc"))
        x += 52

    # 氛围标签
    y = MARGIN + 150; x = MARGIN + 32
    for m in mood_keywords[:4]:
        tw = draw.textlength(m, font_tag) + 20
        draw.rounded_rectangle([x, y, x+tw, y+30], 4, fill=hex_to_rgb(bs["bg"]))
        draw.text((x+10, y+4), m, fill=hex_to_rgb(bs["font_color"]), font=font_tag)
        x += tw + 8
    return img

def _draw_story(bs):
    """品牌故事"""
    H = 280
    img = Image.new("RGB", (W, H), hex_to_rgb(bs["bg"]))
    draw = ImageDraw.Draw(img)
    font_title = try_font(32, bold=True)
    font_body = try_font(22)

    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, H-MARGIN],
                            bs["radius"], fill=hex_to_rgb(bs["card_bg"]))
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(bs["accent"]))
    draw.text((MARGIN+32, MARGIN+24), "品牌故事", fill=hex_to_rgb(bs["font_color"]), font=font_title)
    story = f"{bs['name']} 专注于将{bs['font_vibe']}设计融入日常生活。精选材质，融合传统工艺与现代美学，为每个空间带来独特的气质与温度。"
    lines = textwrap.wrap(story, width=28)
    y = MARGIN + 90
    for line in lines:
        draw.text((MARGIN+32, y), line, fill=hex_to_rgb(bs["font_color"]), font=font_body)
        y += 36
    return img

# ── 主生成函数 ────────────────────────────────────────

def generate_detail_images(
    product_name="产品名",
    category="category",
    material="材质",
    color="颜色",
    style="Nordic",
    scene="场景",
    brand_score=0.85,
    palette: Optional[List[str]] = None,
    mood_keywords: Optional[List[str]] = None,
    features: Optional[List] = None,
    brand_style: str = "nordic",
    output_dir: Optional[str] = None,
) -> str:
    """生成品牌详情页全套图片"""
    bs = get_style(brand_style)
    if palette is None:
        palette = bs["palette"]
    if mood_keywords is None:
        mood_keywords = ["elegant", "refined", "timeless"]
    if features is None:
        features = [("材质", material), ("颜色", color), ("风格", style)]

    sections = [
        ("00_hero", _draw_hero(product_name, category, material, color, style, scene, brand_score, bs)),
        ("01_features", _draw_section("产品特征", features, bs)),
        ("02_material", _draw_section("材质故事",
            [f"精选{material}材质", "自然质感表面", "手工精制细节", "耐用环保工艺"],
            bs, note=f"每一处细节都体现 {bs['name']} 的品质坚持")),
        ("03_scene", _draw_scene(scene, palette, mood_keywords, bs)),
        ("04_story", _draw_story(bs)),
    ]

    total_h = sum(s[1].height for s in sections) + 60
    long_img = Image.new("RGB", (W, total_h), hex_to_rgb(bs["bg"]))
    y = 0
    for name, sec_img in sections:
        long_img.paste(sec_img, (0, y))
        y += sec_img.height

    draw = ImageDraw.Draw(long_img)
    font_small = try_font(16)
    draw.text((W//2 - 100, y+20), f"{bs['name']} · 品牌详情页",
              fill=hex_to_rgb(bs["muted"]), font=font_small)

    # 导出
    if output_dir is None:
        output_dir = Path.home() / "Desktop" / "brand-detail"
    os.makedirs(output_dir, exist_ok=True)

    long_path = os.path.join(output_dir, "detail_long.png")
    long_img.save(long_path, "PNG")
    print(f"✅ 长图: {long_path}")

    zip_path = os.path.join(output_dir, "brand-detail-images.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, sec_img in sections:
            buf = io.BytesIO()
            sec_img.save(buf, "PNG")
            zf.writestr(f"{name}.png", buf.getvalue())
            print(f"  📄 分图: {name}.png ({sec_img.height}px)")
        
        buf = io.BytesIO()
        long_img.save(buf, "PNG")
        zf.writestr("detail_long.png", buf.getvalue())
        
        import json
        zf.writestr("product_data.json", json.dumps({
            "product": product_name, "category": category,
            "material": material, "color": color, "style": style,
            "scene": scene, "brand_score": brand_score,
            "palette": palette, "mood_keywords": mood_keywords,
            "brand_style": brand_style,
        }, ensure_ascii=False, indent=2))

    print(f"✅ ZIP包: {zip_path}")

    # 多风格批量生成
    if brand_style == "all":
        for style_name in BRAND_STYLES:
            if style_name != "nordic":
                style_dir = os.path.join(output_dir, style_name)
                generate_detail_images(
                    product_name, category, material, color, style, scene,
                    brand_score, palette, mood_keywords, features,
                    brand_style=style_name, output_dir=style_dir,
                )

    return zip_path


# ── CLI ───────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="通用品牌详情页生成器")
    parser.add_argument("--name", default="产品", help="产品名")
    parser.add_argument("--category", default="furniture", help="品类")
    parser.add_argument("--material", default="精选材质", help="材质")
    parser.add_argument("--color", default="品牌色", help="颜色")
    parser.add_argument("--style", default="现代", help="风格")
    parser.add_argument("--scene", default="生活场景", help="场景")
    parser.add_argument("--score", type=float, default=0.85, help="品牌匹配度")
    parser.add_argument("--brand-style", default="nordic", 
        choices=list(BRAND_STYLES.keys()) + ["all"], help="品牌视觉风格")
    parser.add_argument("--output", default=None, help="输出目录")
    args = parser.parse_args()

    generate_detail_images(
        product_name=args.name, category=args.category,
        material=args.material, color=args.color,
        style=args.style, scene=args.scene,
        brand_score=args.score, brand_style=args.brand_style,
        output_dir=args.output,
    )
