#!/usr/bin/env python3
"""
NORHOR 电商详情页 — 长图 + 分图 生成器
输出: 品牌风格详情页长图 + 分段切片 + ZIP包
"""

from PIL import Image, ImageDraw, ImageFont
import io, os, json, zipfile, textwrap, math
from pathlib import Path

# ── 品牌配置 ──────────────────────────────────────────
BRAND = {
    "name": "NORHOR 北欧表情",
    "palette": ["#f5f0e8", "#d4c5b0", "#8b7355", "#2c2c2c", "#c4a882", "#faf9f7"],
    "font_color": "#2c2c2c",
    "muted": "#8b7355",
    "bg": "#faf9f7",
    "card_bg": "#ffffff",
    "accent": "#c4a882",
}

# ── 画布尺寸 ──────────────────────────────────────────
W = 1080          # 详情页宽度（手机端优化）
MARGIN = 48
CARD_RADIUS = 12

# ── 辅助函数 ──────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rounded_rect(draw, xy, r, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, r, fill=hex_to_rgb(fill))

def try_font(size, bold=False):
    """尝试加载中文字体，fallback到默认"""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

# ── 区块构造器 ────────────────────────────────────────

def draw_bg(draw, h):
    draw.rectangle([0, 0, W, h], fill=hex_to_rgb(BRAND["bg"]))

def draw_section_bg(draw, y, section_h):
    draw.rectangle([MARGIN, y, W - MARGIN, y + section_h],
                   fill=hex_to_rgb(BRAND["card_bg"]))

def draw_product_hero(name, category, material, color, style, scene, brand_score):
    """区块1: 产品主图 Hero"""
    font_big = try_font(48, bold=True)
    font_mid = try_font(28)
    font_small = try_font(20)
    font_tag = try_font(16)

    H = 600
    img = Image.new("RGB", (W, H), hex_to_rgb(BRAND["bg"]))
    draw = ImageDraw.Draw(img)

    # Hero 渐变背景
    for i in range(H):
        t = i / H
        r = int(hex_to_rgb(BRAND["palette"][0])[0] * (1-t) + hex_to_rgb(BRAND["palette"][1])[0] * t)
        g = int(hex_to_rgb(BRAND["palette"][0])[1] * (1-t) + hex_to_rgb(BRAND["palette"][1])[1] * t)
        b = int(hex_to_rgb(BRAND["palette"][0])[2] * (1-t) + hex_to_rgb(BRAND["palette"][1])[2] * t)
        draw.line([(0,i),(W,i)], fill=(r,g,b))

    # 产品名
    draw.text((MARGIN, H//2 - 60), name, fill=hex_to_rgb(BRAND["font_color"]), font=font_big)
    draw.text((MARGIN, H//2 + 10), f"{category} · {material} · {color}",
              fill=hex_to_rgb(BRAND["muted"]), font=font_mid)

    # 标签
    tags_y = H//2 + 70
    tags = [style, scene, f"品牌匹配 {(brand_score*100):.0f}%"]
    x = MARGIN
    for t in tags:
        tw = draw.textlength(t, font=font_tag) + 24
        draw.rounded_rectangle([x, tags_y, x+tw, tags_y+34], 6, fill=hex_to_rgb(BRAND["accent"]))
        draw.text((x+12, tags_y+5), t, fill=(255,255,255), font=font_tag)
        x += tw + 12

    return img

def draw_section(title, items, note=None):
    """通用区块"""
    font_title = try_font(32, bold=True)
    font_body = try_font(22)
    font_small = try_font(18)
    line_h = 40
    item_h = 50

    title_h = 80
    content_h = len(items) * item_h + (note and 60 or 0)
    section_h = title_h + content_h + MARGIN * 2
    total_h = section_h + MARGIN

    img = Image.new("RGB", (W, total_h), hex_to_rgb(BRAND["bg"]))
    draw = ImageDraw.Draw(img)

    # Card background
    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, MARGIN+section_h],
                            CARD_RADIUS, fill=hex_to_rgb(BRAND["card_bg"]))

    # 左侧品牌色条
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(BRAND["accent"]))

    # Title
    draw.text((MARGIN+32, MARGIN+24), title, fill=hex_to_rgb(BRAND["font_color"]), font=font_title)

    # Items
    y = MARGIN + title_h
    for item in items:
        if isinstance(item, tuple):
            k, v = item
            draw.text((MARGIN+32, y), k, fill=hex_to_rgb(BRAND["muted"]), font=font_small)
            draw.text((MARGIN+200, y), str(v), fill=hex_to_rgb(BRAND["font_color"]), font=font_body)
        else:
            draw.text((MARGIN+32, y), f"• {item}", fill=hex_to_rgb(BRAND["font_color"]), font=font_body)
        y += item_h

    if note:
        draw.text((MARGIN+32, y+10), note, fill=hex_to_rgb(BRAND["accent"]), font=font_small)

    return img

def draw_scene_section(scene_name, palette, mood_keywords):
    """场景应用区块"""
    font_title = try_font(32, bold=True)
    font_body = try_font(22)
    font_tag = try_font(16)

    H = 300
    img = Image.new("RGB", (W, H), hex_to_rgb(BRAND["bg"]))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, H-MARGIN],
                            CARD_RADIUS, fill=hex_to_rgb(BRAND["card_bg"]))
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(BRAND["accent"]))
    draw.text((MARGIN+32, MARGIN+24), f"场景应用 · {scene_name}",
              fill=hex_to_rgb(BRAND["font_color"]), font=font_title)

    # Color palette swatches
    y = MARGIN + 90
    x = MARGIN + 32
    for c in palette:
        draw.rounded_rectangle([x, y, x+40, y+40], 6, fill=hex_to_rgb(c))
        draw.rounded_rectangle([x, y, x+40, y+40], 6, outline=hex_to_rgb("#dddddd"))
        x += 52

    # Mood tags
    y = MARGIN + 150
    x = MARGIN + 32
    for m in mood_keywords:
        tw = draw.textlength(m, font=font_tag) + 20
        draw.rounded_rectangle([x, y, x+tw, y+30], 4, fill=hex_to_rgb(BRAND["bg"]))
        draw.text((x+10, y+4), m, fill=hex_to_rgb(BRAND["font_color"]), font=font_tag)
        x += tw + 8

    return img

def draw_brand_story():
    """品牌故事"""
    font_title = try_font(32, bold=True)
    font_body = try_font(22)
    H = 280
    img = Image.new("RGB", (W, H), hex_to_rgb(BRAND["bg"]))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([MARGIN, MARGIN, W-MARGIN, H-MARGIN],
                            CARD_RADIUS, fill=hex_to_rgb(BRAND["card_bg"]))
    draw.rounded_rectangle([MARGIN+8, MARGIN+24, MARGIN+14, MARGIN+24+32],
                            4, fill=hex_to_rgb(BRAND["accent"]))
    draw.text((MARGIN+32, MARGIN+24), "品牌故事", fill=hex_to_rgb(BRAND["font_color"]), font=font_title)
    story = "NORHOR 北欧表情，专注于现代北欧设计家具。精选天然材质，融合传统手工艺与现代美学，为每个空间带来温暖与质感。"
    lines = textwrap.wrap(story, width=28)
    y = MARGIN + 90
    for line in lines:
        draw.text((MARGIN+32, y), line, fill=hex_to_rgb(BRAND["font_color"]), font=font_body)
        y += 36
    return img

# ── 主生成函数 ────────────────────────────────────────

def generate_detail_images(
    product_name="Cloud Sofa",
    category="sofa",
    material="Linen",
    color="Beige",
    style="Nordic",
    scene="Nordic Living Room",
    brand_score=0.85,
    palette=None,
    mood_keywords=None,
    features=None,
    output_dir=None,
):
    if palette is None:
        palette = BRAND["palette"]
    if mood_keywords is None:
        mood_keywords = ["calm", "warm", "refined"]
    if features is None:
        features = [
            ("材质", material),
            ("颜色", color),
            ("风格", style),
            ("坐深", "60cm"),
            ("座高", "45cm"),
        ]

    # 生成各区块
    sections = []
    sections.append(("00_hero", draw_product_hero(product_name, category, material, color, style, scene, brand_score)))
    sections.append(("01_features", draw_section("产品特征", features)))
    sections.append(("02_material", draw_section("材质故事", [f"精选{material}材质", "自然质感表面", "手工缝制细节", "耐用环保工艺"], note="每一处细节都体现 NORHOR 对品质的坚持")))
    sections.append(("03_scene", draw_scene_section(scene, palette, mood_keywords)))
    sections.append(("04_brand", draw_brand_story()))

    # 拼合长图
    total_h = sum(s[1].height for s in sections) + 60  # footer
    long_img = Image.new("RGB", (W, total_h), hex_to_rgb(BRAND["bg"]))
    y = 0
    for name, sec_img in sections:
        long_img.paste(sec_img, (0, y))
        y += sec_img.height

    # Footer
    draw = ImageDraw.Draw(long_img)
    font_small = try_font(16)
    draw.text((W//2 - 100, y+20), "NORHOR 北欧表情 · 品牌详情", fill=hex_to_rgb(BRAND["muted"]), font=font_small)

    # 导出
    if output_dir is None:
        output_dir = Path.home() / "Desktop" / "norhor-detail"
    os.makedirs(output_dir, exist_ok=True)

    # 保存长图
    long_path = os.path.join(output_dir, "detail_long.png")
    long_img.save(long_path, "PNG")
    print(f"✅ 长图: {long_path}")

    # 保存分图 + 打包 ZIP
    zip_path = os.path.join(output_dir, "norhor-detail-images.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 保存每段分图
        y = 0
        for name, sec_img in sections:
            sec_path = f"{name}.png"
            buf = io.BytesIO()
            sec_img.save(buf, "PNG")
            zf.writestr(sec_path, buf.getvalue())
            print(f"  📄 分图: {sec_path} ({sec_img.height}px)")

        # 长图也加入zip
        buf = io.BytesIO()
        long_img.save(buf, "PNG")
        zf.writestr("detail_long.png", buf.getvalue())

        # 数据json
        data = {
            "product": product_name,
            "category": category,
            "material": material,
            "color": color,
            "style": style,
            "scene": scene,
            "brand_score": brand_score,
            "palette": palette,
            "mood_keywords": mood_keywords,
        }
        zf.writestr("product_data.json", json.dumps(data, ensure_ascii=False, indent=2))

    print(f"✅ ZIP包: {zip_path}")
    return zip_path


# ── CLI 入口 ───────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NORHOR 详情页长图生成器")
    parser.add_argument("--name", default="北欧云朵沙发", help="产品名")
    parser.add_argument("--category", default="sofa", help="品类")
    parser.add_argument("--material", default="亚麻面料", help="材质")
    parser.add_argument("--color", default="米白", help="颜色")
    parser.add_argument("--style", default="Nordic", help="风格")
    parser.add_argument("--scene", default="北欧客厅", help="场景")
    parser.add_argument("--score", type=float, default=0.85, help="品牌匹配度")
    parser.add_argument("--output", default=None, help="输出目录")
    args = parser.parse_args()

    generate_detail_images(
        product_name=args.name,
        category=args.category,
        material=args.material,
        color=args.color,
        style=args.style,
        scene=args.scene,
        brand_score=args.score,
        output_dir=args.output,
    )
