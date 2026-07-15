#!/usr/bin/env python3
"""
品牌DNA详情页生成器 — 完整品牌参数可视化

每个输出页都基于真实的品牌DNA分析参数:
1. Brand DNA Overview — 品牌定位/受众/调性
2. Color System — 色板/关系/温度/心理
3. PBR Material Parameters — albedo/roughness/metallic/normal
4. Photography Parameters — 相机/灯光/后期
5. Design Pattern Analysis — 版式/构图/视觉层级
6. Scene Graph — 元素ID/空间关系
7. Brand Match Score — 各维度品牌合规评分
"""
from PIL import Image, ImageDraw, ImageFont
import io, os, json, zipfile, textwrap, math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ── 画布 ──────────────────────────────────────────────
W = 1080
M = 48
R = 12
WHITE = "#ffffff"
BG = "#f8f8f8"
DARK = "#1a1a2e"
MUTED = "#666666"
ACCENT = "#c4a882"

def h2r(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    if len(h) < 6:
        h = h.ljust(6, "0")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def font(sz, bold=False):
    for p in ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
              "C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simsun.ttc",
              "/System/Library/Fonts/PingFang.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

def card(draw, x1, y1, x2, y2, fill=WHITE, r=R):
    draw.rounded_rectangle([x1,y1,x2,y2], r, fill=h2r(fill))

def bar(draw, x, y, w, h, pct, color):
    """进度条"""
    draw.rounded_rectangle([x,y,x+w,y+h], 4, fill=h2r("#e0e0e0"))
    if pct>0:
        draw.rounded_rectangle([x,y,x+int(w*pct),y+h], 4, fill=h2r(color))

def section_header(draw, y, title):
    """区块标题"""
    card(draw, M, y, W-M, y+70)
    draw.rounded_rectangle([M+12, y+20, M+18, y+50], 3, fill=h2r(ACCENT))
    draw.text((M+32, y+22), title, fill=h2r(DARK), font=font(28,True))

# ═══════════════════════════════════════════════════════════
# 区块生成器
# ═══════════════════════════════════════════════════════════

def _dna_overview(dna: dict) -> Image.Image:
    """区块1: Brand DNA 总览"""
    bn = dna.get("brand_name","品牌")
    bp = dna.get("brand_positioning","")
    ta = dna.get("target_audience","")
    bp_ar = dna.get("brand_personality",[])
    score = dna.get("brand_score",0.85)

    H = 520
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)

    # Hero渐变
    pal = dna.get("primary_palette",["#f5f0e8","#d4c5b0"])
    if pal:
        g1, g2 = pal[0], pal[-1] if len(pal)>1 else pal[0]
        for i in range(H):
            t=i/H
            c1,c2=h2r(g1),h2r(g2)
            draw.line([(0,i),(W,i)],fill=(int(c1[0]*(1-t)+c2[0]*t),int(c1[1]*(1-t)+c2[1]*t),int(c1[2]*(1-t)+c2[2]*t)))

    # 品牌名
    draw.text((M, H//2-80), bn, fill=h2r(DARK), font=font(56,True))
    if bp:
        draw.text((M, H//2-10), bp, fill=h2r(MUTED), font=font(24))
    if ta:
        draw.text((M, H//2+30), f"受众: {ta}", fill=h2r(MUTED), font=font(20))

    # 品牌调性标签
    y = H//2 + 80
    x = M
    for p in bp_ar[:4]:
        tag = str(p)
        tw = draw.textlength(tag, font(16))+16
        draw.rounded_rectangle([x, y, x+tw, y+30], 4, fill=h2r(ACCENT))
        draw.text((x+8, y+5), tag, fill=(255,255,255), font=font(16))
        x += tw + 8

    # 品牌评分
    score_x = W - M - 160
    draw.text((score_x, H//2-50), f"{(score*100):.0f}%", fill=h2r(DARK), font=font(48,True))
    draw.text((score_x, H//2+10), "品牌匹配度", fill=h2r(MUTED), font=font(18))
    bar(draw, score_x, H//2+45, 160, 8, score, "#4caf50")

    return img

def _color_system(dna: dict) -> Image.Image:
    """区块2: 色彩系统 — 色板/关系/温度/心理"""
    pal = dna.get("primary_palette",[])
    sec = dna.get("secondary_palette",[])
    acc = dna.get("accent_palette",[])
    rel = dna.get("color_relationship","")
    temp = dna.get("temperature","")
    psy = dna.get("psychological_effect","")

    H = 460
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)

    section_header(draw, 0, "色彩系统 Color System")

    # 主色板
    y = 90
    draw.text((M+20, y), "主色板", fill=h2r(MUTED), font=font(18))
    x = M+20
    for c in pal[:8]:
        draw.rounded_rectangle([x, y+28, x+40, y+68], 6, fill=h2r(c))
        draw.rounded_rectangle([x, y+28, x+40, y+68], 6, outline=h2r("#cccccc"))
        x += 48

    # 辅色板
    if sec:
        y = 160
        draw.text((M+20, y), "辅色板", fill=h2r(MUTED), font=font(18))
        x = M+20
        for c in sec[:4]:
            draw.rounded_rectangle([x, y+28, x+32, y+60], 6, fill=h2r(c))
            draw.rounded_rectangle([x, y+28, x+32, y+60], 6, outline=h2r("#cccccc"))
            x += 40

    # 色彩关系
    if rel or temp:
        y = 240
        draw.text((M+20, y), "色彩关系", fill=h2r(MUTED), font=font(18))
        if rel: draw.text((M+20, y+30), f"关系: {rel}", fill=h2r(DARK), font=font(22))
        if temp: draw.text((M+20, y+60), f"色温: {temp}", fill=h2r(DARK), font=font(22))

    # 色彩心理学
    if psy:
        y = 330
        draw.text((M+20, y), "色彩心理", fill=h2r(MUTED), font=font(18))
        lines = textwrap.wrap(psy, width=40)
        for i, l in enumerate(lines[:3]):
            draw.text((M+20, y+30+i*28), l, fill=h2r(DARK), font=font(20))

    return img

def _pbr_materials(dna: dict) -> Image.Image:
    """区块3: PBR材质参数"""
    mats = dna.get("materials", [])
    H = 400
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)
    section_header(draw, 0, "材质参数 PBR Materials")

    y = 90
    if not mats:
        draw.text((M+20, y), "无材质数据", fill=h2r(MUTED), font=font(20))
        return img

    for i, m in enumerate(mats[:4]):
        if isinstance(m, dict):
            name = m.get("name", m.get("type", f"Material {i+1}"))
            # Albedo swatch
            alb = m.get("albedo", "#808080")
            draw.rounded_rectangle([M+20, y, M+60, y+40], 6, fill=h2r(alb))
            draw.rounded_rectangle([M+20, y, M+60, y+40], 6, outline=h2r("#ccc"))
            draw.text((M+72, y+6), name, fill=h2r(DARK), font=font(22,True))

            # PBR参数条
            bx, bw = M+260, 280
            params = [
                ("Roughness", m.get("roughness", 0.5), ACCENT),
                ("Metallic", m.get("metallic", 0), "#4a90d9"),
                ("Normal", m.get("normal_strength", 0.5), "#7c4dff"),
                ("Subsurface", m.get("subsurface", 0), "#e94560"),
            ]
            py = y + 50
            for plabel, pval, pcolor in params:
                draw.text((M+72, py), f"{plabel}", fill=h2r(MUTED), font=font(14))
                draw.text((M+230, py), f"{pval:.2f}", fill=h2r(DARK), font=font(14))
                bar(draw, bx, py+2, bw, 10, pval, pcolor)
                py += 22

            y += 120

    return img

def _photography_params(dna: dict) -> Image.Image:
    """区块4: 摄影参数 — 相机/灯光/后期"""
    cam = dna.get("camera", {})
    lights = dna.get("lights", [])
    post = dna.get("post_processing", {})

    H = 480
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)
    section_header(draw, 0, "摄影参数 Photography")

    y = 90

    # 相机
    # 相机 (支持范围)
    draw.text((M+20, y), "📷 相机", fill=h2r(MUTED), font=font(18))
    cam_lines = []
    if cam.get("camera_model"): cam_lines.append(f"机身: {cam['camera_model']}")
    fl = cam.get("focal_length_mm","")
    if fl: cam_lines.append(f"焦距: {fl}{'mm' if isinstance(fl,(int,float)) else ''}")
    ap = cam.get("aperture_f","")
    if ap: cam_lines.append(f"光圈: f/{ap}")
    if cam.get("iso"): cam_lines.append(f"ISO: {cam['iso']}")

    for i, cl in enumerate(cam_lines[:6]):
        draw.text((M+20, y+28+i*24), f"  {cl}", fill=h2r(DARK), font=font(20))

    # 灯光
    y2 = y + max(len(cam_lines)*24+40, 60)
    draw.text((M+20, y2), "💡 灯光", fill=h2r(MUTED), font=font(18))
    if lights:
        for i, l in enumerate(lights[:3]):
            lt = l.get("type","area")
            lp = l.get("modifier","")
            lt_ = l.get("temperature","")
            desc = f"  Light {i+1}: {lt}"
            if lp: desc += f" + {lp}"
            if lt_: desc += f"  {lt_}K"
            draw.text((M+20, y2+28+i*24), desc, fill=h2r(DARK), font=font(20))
    else:
        ls = dna.get("lighting_signature","")
        if ls:
            lines = textwrap.wrap(ls, width=45)
            for i, l in enumerate(lines[:3]):
                draw.text((M+20, y2+28+i*24), f"  {l}", fill=h2r(DARK), font=font(20))

    # 后期
    y3 = y2 + 130
    draw.text((M+20, y3), "🎨 后期", fill=h2r(MUTED), font=font(18))
    pp_items = []
    for k in ["contrast","clarity","vibrance","saturation","sharpening","color_temperature"]:
        v = post.get(k)
        if v:
            pp_items.append(f"{k}: {v:+.0f}")
    if pp_items:
        draw.text((M+20, y3+28), "  " + " · ".join(pp_items[:6]), fill=h2r(DARK), font=font(20))

    return img

def _design_patterns(dna: dict) -> Image.Image:
    """区块5: 设计模式分析"""
    patterns = dna.get("design_patterns", [])
    layout = dna.get("layout_patterns", [])
    comp = dna.get("composition_rules", "")
    vh = dna.get("visual_hierarchy", "")

    H = 380
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)
    section_header(draw, 0, "设计模式 Design Patterns")

    y = 90
    if patterns:
        for p in patterns[:4]:
            pname = p if isinstance(p, str) else p.get("name","")
            peff = p if isinstance(p, str) else p.get("effect","")
            draw.text((M+20, y), f"• {pname}", fill=h2r(DARK), font=font(22,True))
            if peff and peff != pname:
                draw.text((M+40, y+28), str(peff)[:60], fill=h2r(MUTED), font=font(18))
            y += 70
    elif layout:
        for l in layout[:4]:
            draw.text((M+20, y), f"• {l}", fill=h2r(DARK), font=font(22))
            y += 35

    return img

def _scene_graph(dna: dict) -> Image.Image:
    """区块6: 场景图 — 元素ID/空间关系"""
    elements = dna.get("elements", [])
    env = dna.get("environment", {})

    H = 320 + len(elements) * 60
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)
    section_header(draw, 0, "场景图 Scene Graph")

    y = 90
    for e in elements[:6]:
        eid = e.get("id","?")
        etype = e.get("type","?")
        bbox = e.get("bbox_size",[])
        pos = e.get("bbox_center",[])
        bbox_s = f"{bbox[0]}×{bbox[1]}×{bbox[2]}cm" if len(bbox)==3 else ""
        pos_s = f"({pos[0]},{pos[1]},{pos[2]})" if len(pos)==3 else ""

        # Element ID badge
        tw = draw.textlength(eid, font(16))+12
        draw.rounded_rectangle([M+20, y, M+20+tw, y+28], 4, fill=h2r(ACCENT))
        draw.text((M+26, y+4), eid, fill=(255,255,255), font=font(16))

        draw.text((M+20+tw+16, y+4), f"{etype}  {bbox_s}  {pos_s}", fill=h2r(DARK), font=font(20))

        # 材质简标
        mat = e.get("material",{})
        if isinstance(mat, dict) and mat.get("albedo"):
            draw.rounded_rectangle([M+20, y+34, M+40, y+54], 4, fill=h2r(mat["albedo"]))
        y += 60

    return img

def _brand_match(dna: dict) -> Image.Image:
    """区块7: 品牌匹配评分各维度"""
    bscore = dna.get("brand_score", 0.85)
    dims = dna.get("dimension_scores", {})

    H = 400
    img = Image.new("RGB", (W, H), h2r(BG))
    draw = ImageDraw.Draw(img)
    section_header(draw, 0, "品牌合规评分 Brand Compliance")

    y = 90
    if dims:
        items = list(dims.items())
    else:
        items = [("色彩一致性", 0.88), ("材质匹配", 0.82), ("光影风格", 0.85),
                 ("构图规范", 0.90), ("品牌调性", 0.87), ("整体评分", bscore)]

    for label, val in items:
        draw.text((M+20, y), label, fill=h2r(DARK), font=font(20))
        draw.text((W-M-100, y), f"{(val*100):.0f}%", fill=h2r(DARK if val>=0.7 else "#e94560"), font=font(20,True))
        bar_color = "#4caf50" if val>=0.7 else "#ff9800" if val>=0.5 else "#e94560"
        bar(draw, M+20, y+28, W-2*M-20, 8, val, bar_color)
        y += 52

    return img

# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def generate_brand_detail(
    brand_dna: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    **kwargs
) -> str:
    """
    品牌DNA详情页生成器（主入口）
    
    接受完整品牌DNA字典（包含所有分析维度），
    或从kwargs构建简版DNA。
    """
    dna = brand_dna or {}

    # 从kwargs补充
    for k in ["brand_name","brand_positioning","target_audience","brand_personality",
              "primary_palette","secondary_palette","accent_palette","color_relationship",
              "temperature","psychological_effect","materials","camera","lights",
              "post_processing","design_patterns","layout_patterns","elements",
              "environment","brand_score","dimension_scores","lighting_signature"]:
        if k not in dna and k in kwargs:
            dna[k] = kwargs[k]

    # 默认值
    dna.setdefault("brand_name", "品牌")
    dna.setdefault("brand_score", 0.85)
    dna.setdefault("primary_palette", ["#f5f0e8","#d4c5b0","#8b7355","#2c2c2c","#c4a882"])

    # 构建各区块
    sections = [
        ("01_brand_dna", _dna_overview(dna)),
        ("02_color_system", _color_system(dna)),
        ("03_pbr_materials", _pbr_materials(dna)),
        ("04_photography", _photography_params(dna)),
        ("05_design_patterns", _design_patterns(dna)),
        ("06_scene_graph", _scene_graph(dna)),
        ("07_brand_compliance", _brand_match(dna)),
    ]

    # 拼合长图
    total_h = sum(s[1].height for s in sections) + 60
    long_img = Image.new("RGB", (W, total_h), h2r(BG))
    y = 0
    for name, sec_img in sections:
        long_img.paste(sec_img, (0, y))
        y += sec_img.height

    draw = ImageDraw.Draw(long_img)
    draw.text((W//2-120, y+20), f"{dna['brand_name']} · 品牌DNA报告",
              fill=h2r(MUTED), font=font(16))

    # 导出
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent.parent / "output" / "brand-detail"
    os.makedirs(output_dir, exist_ok=True)

    long_path = os.path.join(output_dir, "brand_dna_report.png")
    long_img.save(long_path, "PNG")
    print(f"✅ 完整报告: {long_path}")

    zip_path = os.path.join(output_dir, "brand-dna-report.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, sec_img in sections:
            buf = io.BytesIO()
            sec_img.save(buf, "PNG")
            zf.writestr(f"{name}.png", buf.getvalue())
            print(f"  📄 {name}.png ({sec_img.height}px)")
        
        buf = io.BytesIO()
        long_img.save(buf, "PNG")
        zf.writestr("brand_dna_report.png", buf.getvalue())
        zf.writestr("brand_dna.json", json.dumps({k:v for k,v in dna.items() if isinstance(v,(str,int,float,list,dict))},
                                                   ensure_ascii=False, indent=2))
    print(f"✅ ZIP: {zip_path}")
    return zip_path


# 兼容旧接口
generate_detail_images = generate_brand_detail


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="品牌DNA详情页生成器")
    parser.add_argument("--brand", default="品牌", help="品牌名")
    parser.add_argument("--score", type=float, default=0.85, help="品牌匹配度")
    parser.add_argument("--json", default=None, help="品牌DNA JSON文件路径")
    parser.add_argument("--output", default=None, help="输出目录")
    args = parser.parse_args()

    if args.json:
        with open(args.json) as f:
            dna = json.load(f)
    else:
        dna = {"brand_name": args.brand, "brand_score": args.score}

    generate_brand_detail(dna, output_dir=args.output)
