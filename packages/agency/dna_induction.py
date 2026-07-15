"""
品类抽象 + 品牌VI归纳管线 — aggregate → induce → design tokens

管线三阶段:
  1. aggregate_to_category()    — 多个 FullPageDNA 页面 → 品类统计摘要
  2. induce_brand_vi()          — 多个品类摘要 → 品牌VI系统
  3. generate_design_tokens()   — 品牌VI → AI设计师可用的设计令牌

引用: packages/agency/dna_schema.py (FullPageDNA, CategoryDNASummary, BrandVISystem)
"""

import statistics
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple

from .dna_schema import (
    FullPageDNA, CategoryDNASummary, BrandVISystem,
    PageModule, PageLayout, TypographySystem, ColorSystem, ColorSwatch,
    ImageSystem, ImageElement, LightingSystem, LightSource, InteractionRule,
    TextElement, WhyTrace,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AGGREGATE — 多页面 → 品类摘要
# ═══════════════════════════════════════════════════════════════════════════════

def aggregate_to_category(pages: List[FullPageDNA]) -> CategoryDNASummary:
    """
    将同一品类下的多个产品详情页 DNA 聚合为品类统计摘要。

    Args:
        pages: 同一品类下的 FullPageDNA 列表

    Returns:
        CategoryDNASummary — 包含参数范围、颜色频率、布局模式、设计规则
    """
    if not pages:
        return CategoryDNASummary()

    category = pages[0].product_category or "unknown"
    n = len(pages)

    # ── 1. Typography ranges ──
    all_heading_px: Dict[str, List[int]] = {}  # "h1" | "h2" | "h3" → [px...]
    body_sizes: List[int] = []
    caption_sizes: List[int] = []
    all_font_families: Counter = Counter()
    all_primary_fonts: Counter = Counter()

    for page in pages:
        t = page.typography
        for level, px in (t.heading_sizes or {}).items():
            all_heading_px.setdefault(level, []).append(px)
        if t.body_size:
            body_sizes.append(t.body_size)
        if t.caption_size:
            caption_sizes.append(t.caption_size)
        for ff in t.font_families:
            all_font_families[ff] += 1
        if t.primary_font:
            all_primary_fonts[t.primary_font] += 1

    heading_size_range: List[int] = []
    if all_heading_px:
        # Flatten all heading sizes for an overall range
        all_h_sizes = [s for sizes in all_heading_px.values() for s in sizes]
        if all_h_sizes:
            heading_size_range = [
                min(all_h_sizes),
                max(all_h_sizes),
                int(statistics.median(all_h_sizes)),
            ]

    body_size_range: List[int] = []
    if body_sizes:
        body_size_range = [min(body_sizes), max(body_sizes),
                           int(statistics.median(body_sizes))]

    # ── 2. Color frequency ──
    color_counter: Counter = Counter()
    for page in pages:
        for swatch in page.colors.swatches:
            if swatch.hex:
                color_counter[swatch.hex] += swatch.usage_count

    # Normalize to 0-1 frequency
    total_color_uses = sum(color_counter.values()) or 1
    common_colors: Dict[str, float] = {
        hex_: round(cnt / total_color_uses, 4)
        for hex_, cnt in color_counter.most_common(30)
    }

    # ── 3. Layout patterns ──
    grid_counter: Counter = Counter()
    reading_counter: Counter = Counter()
    for page in pages:
        l = page.layout
        if l.grid_type:
            grid_counter[l.grid_type] += 1
        if l.reading_pattern:
            reading_counter[l.reading_pattern] += 1

    common_grids: Dict[str, int] = dict(grid_counter.most_common())
    common_reading_patterns: Dict[str, int] = dict(reading_counter.most_common())

    # ── 4. Photography patterns ──
    fl_counter: Counter = Counter()
    comp_counter: Counter = Counter()
    angle_counter: Counter = Counter()
    for page in pages:
        img = page.images
        for fl in img.common_focal_lengths:
            fl_counter[fl] += 1
        for comp in img.common_compositions:
            comp_counter[comp] += 1
        for angle in img.common_angles:
            angle_counter[angle] += 1

    common_focal_lengths: Dict[int, int] = dict(fl_counter.most_common())
    common_compositions: Dict[str, int] = dict(comp_counter.most_common())
    common_angles: Dict[str, int] = dict(angle_counter.most_common())

    # ── 5. Lighting patterns ──
    lighting_counter: Counter = Counter()
    for page in pages:
        lgt = page.lighting
        if lgt.setup_type:
            lighting_counter[lgt.setup_type] += 1

    common_lighting_setups: Dict[str, int] = dict(lighting_counter.most_common())

    # ── 6. Design rules (heuristics) ──
    design_rules = _extract_category_design_rules(
        pages=pages, n=n,
        heading_size_range=heading_size_range,
        body_size_range=body_size_range,
        common_grids=common_grids,
        common_reading_patterns=common_reading_patterns,
        common_colors=common_colors,
        common_compositions=common_compositions,
        common_angles=common_angles,
        common_lighting_setups=common_lighting_setups,
        common_focal_lengths=common_focal_lengths,
        all_primary_fonts=all_primary_fonts,
    )

    return CategoryDNASummary(
        category=category,
        sample_count=n,
        heading_size_range=heading_size_range,
        body_size_range=body_size_range,
        common_colors=common_colors,
        common_grids=common_grids,
        common_reading_patterns=common_reading_patterns,
        common_focal_lengths=common_focal_lengths,
        common_compositions=common_compositions,
        common_angles=common_angles,
        common_lighting_setups=common_lighting_setups,
        design_rules=design_rules,
    )


def _extract_category_design_rules(
    pages: List[FullPageDNA],
    n: int,
    heading_size_range: List[int],
    body_size_range: List[int],
    common_grids: Dict[str, int],
    common_reading_patterns: Dict[str, int],
    common_colors: Dict[str, float],
    common_compositions: Dict[str, int],
    common_angles: Dict[str, int],
    common_lighting_setups: Dict[str, int],
    common_focal_lengths: Dict[int, int],
    all_primary_fonts: Counter,
) -> List[str]:
    """Extract human-readable design rules from statistical patterns."""
    rules: List[str] = []

    threshold = max(2, n // 2)  # at least 2 pages or half the sample

    # Typography rules
    if heading_size_range and len(heading_size_range) >= 3:
        rules.append(
            f"标题字号范围 {heading_size_range[0]}–{heading_size_range[1]}px，"
            f"中位数 {heading_size_range[2]}px"
        )
    if body_size_range and len(body_size_range) >= 3:
        rules.append(
            f"正文字号范围 {body_size_range[0]}–{body_size_range[1]}px，"
            f"中位数 {body_size_range[2]}px"
        )
    top_font = all_primary_fonts.most_common(1)
    if top_font:
        rules.append(f"主字体: {top_font[0][0]} (出现 {top_font[0][1]}/{n} 页面)")

    # Layout rules
    top_grid = common_grids and max(common_grids, key=common_grids.get)
    if top_grid and common_grids[top_grid] >= threshold:
        rules.append(f"主导网格: {top_grid} ({common_grids[top_grid]}/{n} 页面)")

    top_reading = common_reading_patterns and max(common_reading_patterns, key=common_reading_patterns.get)
    if top_reading and common_reading_patterns[top_reading] >= threshold:
        rules.append(f"视觉流模式: {top_reading} ({common_reading_patterns[top_reading]}/{n} 页面)")

    # Color rules
    if common_colors:
        top_colors = sorted(common_colors.items(), key=lambda x: x[1], reverse=True)[:3]
        rules.append(
            "高频颜色: " +
            ", ".join(f"{h} ({freq:.0%})" for h, freq in top_colors)
        )

    # Temperature rule
    temp_counter = Counter(p.colors.temperature for p in pages if p.colors.temperature)
    if temp_counter:
        dominant_temp = max(temp_counter, key=temp_counter.get)
        rules.append(f"色调倾向: {dominant_temp} ({temp_counter[dominant_temp]}/{n} 页面)")

    # Harmony rule
    harmony_counter = Counter(p.colors.harmony_type for p in pages if p.colors.harmony_type)
    if harmony_counter:
        dominant_harmony = max(harmony_counter, key=harmony_counter.get)
        rules.append(f"色彩和谐: {dominant_harmony} ({harmony_counter[dominant_harmony]}/{n} 页面)")

    # Photography rules
    top_comp = common_compositions and max(common_compositions, key=common_compositions.get)
    if top_comp:
        rules.append(f"主导构图: {top_comp}")

    top_angle = common_angles and max(common_angles, key=common_angles.get)
    if top_angle:
        rules.append(f"主导拍摄角度: {top_angle}")

    # Lighting rules
    top_lighting = common_lighting_setups and max(common_lighting_setups, key=common_lighting_setups.get)
    if top_lighting:
        rules.append(f"主导布光: {top_lighting}")

    # Focal length range
    if common_focal_lengths:
        fls = list(common_focal_lengths.keys())
        if fls:
            rules.append(f"常用焦距: {min(fls)}–{max(fls)}mm")

    return rules


# ═══════════════════════════════════════════════════════════════════════════════
# 2. INDUCE — 多品类 → 品牌VI规范
# ═══════════════════════════════════════════════════════════════════════════════

def induce_brand_vi(categories: List[CategoryDNASummary], brand: str = "") -> BrandVISystem:
    """
    跨品类归纳品牌 VI 规范系统。

    从多个品类摘要中提取跨品类共通的品牌色彩、字体、摄影规则、布局系统，
    并计算跨品类一致性分数。

    Args:
        categories: 多个 CategoryDNASummary（同一品牌下不同品类）
        brand: 品牌名称

    Returns:
        BrandVISystem — 品牌VI核心 + 设计令牌
    """
    if not categories:
        return BrandVISystem(brand=brand)

    categories_analyzed = [c.category for c in categories]
    total_pages = sum(c.sample_count for c in categories)
    len(categories)

    # ── 1. Brand colors (cross-category weighted aggregation) ──
    # Fuse common_colors across categories with sample_count weighting
    fused_color_weights: Counter = Counter()
    for cat in categories:
        weight = cat.sample_count
        for hex_, freq in cat.common_colors.items():
            fused_color_weights[hex_] += freq * weight

    total_weight = sum(fused_color_weights.values()) or 1
    fused_colors = {
        h: round(w / total_weight, 4)
        for h, w in fused_color_weights.most_common(30)
    }

    # Map colors to semantic roles via heuristics
    brand_colors = _infer_brand_color_roles(fused_colors)

    # ── 2. Brand typography ──
    # Aggregate heading/body size ranges across categories
    all_heading_mins: List[int] = []
    all_heading_maxs: List[int] = []
    all_body_mins: List[int] = []
    all_body_maxs: List[int] = []
    all_body_medians: List[int] = []

    for cat in categories:
        if len(cat.heading_size_range) >= 3:
            all_heading_mins.append(cat.heading_size_range[0])
            all_heading_maxs.append(cat.heading_size_range[1])
        if len(cat.body_size_range) >= 3:
            all_body_mins.append(cat.body_size_range[0])
            all_body_maxs.append(cat.body_size_range[1])
            all_body_medians.append(cat.body_size_range[2])

    brand_typography: Dict[str, Any] = {
        "heading_size_range": [
            min(all_heading_mins) if all_heading_mins else 0,
            max(all_heading_maxs) if all_heading_maxs else 0,
        ],
        "body_size_range": [
            min(all_body_mins) if all_body_mins else 0,
            max(all_body_maxs) if all_body_maxs else 0,
        ],
        "body_size_median": (
            int(statistics.median(all_body_medians)) if all_body_medians else 0
        ),
    }

    # Collect all design rules mentioning typography/color/layout from each category
    # to synthesize brand-level photography rules
    brand_photography_rules = _synthesize_brand_photography_rules(categories)

    # ── 3. Brand layout system ──
    layout_counter: Counter = Counter()
    for cat in categories:
        for grid, count in cat.common_grids.items():
            layout_counter[grid] += count
    brand_layout_system = layout_counter.most_common(1)[0][0] if layout_counter else ""

    # ── 4. Consistency score ──
    consistency_score = _compute_consistency_score(categories, brand_colors)

    return BrandVISystem(
        brand=brand,
        categories_analyzed=categories_analyzed,
        total_pages_analyzed=total_pages,
        brand_colors=brand_colors,
        brand_typography=brand_typography,
        brand_photography_rules=brand_photography_rules,
        brand_layout_system=brand_layout_system,
        consistency_score=round(consistency_score, 2),
        design_tokens={},  # filled by generate_design_tokens
    )


def _infer_brand_color_roles(fused_colors: Dict[str, float]) -> Dict[str, str]:
    """
    Heuristically assign semantic roles to the top fused colors.

    Strategy:
      - Partition colors into neutral (R≈G≈B) vs. chromatic (saturated).
      - Primary / secondary / accent come from chromatic colors (brand identity).
      - Background / text_primary / text_secondary come from neutrals.
      - If no chromatic colors exist, fall back to the top neutrals.

    Returns role→hex mapping.
    """
    sorted_colors = sorted(fused_colors.items(), key=lambda x: x[1], reverse=True)
    roles: Dict[str, str] = {}

    chromatic = [(h, f) for h, f in sorted_colors if not _is_neutral_hex(h)]
    neutral = [(h, f) for h, f in sorted_colors if _is_neutral_hex(h)]

    # Brand identity colors (primary / secondary / accent) from chromatic palette
    if len(chromatic) >= 1:
        roles["primary"] = chromatic[0][0]
    else:
        roles["primary"] = sorted_colors[0][0] if sorted_colors else "#000000"

    if len(chromatic) >= 2:
        roles["secondary"] = chromatic[1][0]
    elif len(chromatic) == 1 and len(neutral) >= 1:
        # Use the top neutral as secondary when only one chromatic exists
        roles["secondary"] = neutral[0][0]
    elif len(sorted_colors) >= 2:
        roles["secondary"] = sorted_colors[1][0]
    else:
        roles["secondary"] = "#666666"

    if len(chromatic) >= 3:
        roles["accent"] = chromatic[2][0]
    elif len(chromatic) == 2 and len(neutral) >= 1:
        roles["accent"] = neutral[0][0]
    elif len(sorted_colors) >= 3:
        roles["accent"] = sorted_colors[2][0]
    else:
        roles["accent"] = "#0066cc"

    # Surface / text colors from neutral palette
    if neutral:
        # Background = brightest neutral (white-ish)
        bg_candidate = max(neutral, key=lambda x: _hex_brightness(x[0]))
        roles["background"] = bg_candidate[0]

        # Text primary = darkest neutral
        dark_neutrals = [(h, f) for h, f in neutral if _hex_brightness(h) < 0.3]
        if dark_neutrals:
            roles["text_primary"] = min(dark_neutrals, key=lambda x: _hex_brightness(x[0]))[0]
        else:
            roles["text_primary"] = "#1a1a1a"

        # Text secondary = medium neutral
        mid_neutrals = [
            (h, f) for h, f in neutral
            if 0.3 <= _hex_brightness(h) <= 0.7
        ]
        if mid_neutrals:
            roles["text_secondary"] = mid_neutrals[0][0]
        else:
            roles["text_secondary"] = "#666666"
    else:
        roles["background"] = "#FFFFFF"
        roles["text_primary"] = "#1a1a1a"
        roles["text_secondary"] = "#666666"

    # Border: pick a medium-brightness neutral or fallback
    if neutral and len(neutral) >= 2:
        # Second-lightest neutral
        by_brightness = sorted(neutral, key=lambda x: _hex_brightness(x[0]))
        roles["border"] = by_brightness[len(by_brightness) // 2][0]
    else:
        roles["border"] = "#e5e5e5"

    return roles


def _hex_to_rgb(hex_str: str) -> Tuple[float, float, float]:
    """Convert hex color to normalized RGB tuple."""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
    )


def _hex_brightness(hex_str: str) -> float:
    """Perceived brightness (0-1) of a hex color using luminance formula."""
    r, g, b = _hex_to_rgb(hex_str)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _is_neutral_hex(hex_str: str) -> bool:
    """Check if hex is near-grey (R≈G≈B)."""
    r, g, b = _hex_to_rgb(hex_str)
    return abs(r - g) < 0.15 and abs(g - b) < 0.15 and abs(r - b) < 0.15


def _synthesize_brand_photography_rules(
    categories: List[CategoryDNASummary],
) -> List[str]:
    """Synthesize brand-level photography rules from category-level patterns."""
    rules: List[str] = []

    # Aggregate compositions
    comp_counter: Counter = Counter()
    angle_counter: Counter = Counter()
    fl_counter: Counter = Counter()
    lighting_counter: Counter = Counter()

    for cat in categories:
        for comp, cnt in cat.common_compositions.items():
            comp_counter[comp] += cnt
        for angle, cnt in cat.common_angles.items():
            angle_counter[angle] += cnt
        for fl, cnt in cat.common_focal_lengths.items():
            fl_counter[fl] += cnt
        for setup, cnt in cat.common_lighting_setups.items():
            lighting_counter[setup] += cnt

    top_comps = comp_counter.most_common(3)
    if top_comps:
        rules.append(
            "常用构图: " + ", ".join(f"{c} ({cnt})" for c, cnt in top_comps)
        )

    top_angles = angle_counter.most_common(3)
    if top_angles:
        rules.append(
            "常用拍摄角度: " + ", ".join(f"{a} ({cnt})" for a, cnt in top_angles)
        )

    top_fls = fl_counter.most_common(3)
    if top_fls:
        fl_strs = [f"{fl}mm ({cnt})" for fl, cnt in top_fls]
        rules.append("常用焦距: " + ", ".join(fl_strs))

    top_lights = lighting_counter.most_common(3)
    if top_lights:
        rules.append(
            "常用布光: " + ", ".join(f"{s} ({cnt})" for s, cnt in top_lights)
        )

    return rules


def _compute_consistency_score(
    categories: List[CategoryDNASummary],
    brand_colors: Dict[str, str],
) -> float:
    """
    Compute a brand VI consistency score (0.0–1.0) measuring how consistent
    the visual identity is across categories.

    Factors:
      - Color overlap: how much do category color palettes overlap?
      - Typography stability: how tight is the heading/body size range?
      - Layout consistency: do categories share the same grid type?
      - Photography consistency: do categories share composition/angle patterns?
    """
    if len(categories) <= 1:
        return 1.0

    scores: List[float] = []

    # ── Color Jaccard overlap ──
    color_sets = [set(cat.common_colors.keys()) for cat in categories]
    pairwise_jaccards = []
    for i in range(len(color_sets)):
        for j in range(i + 1, len(color_sets)):
            a, b = color_sets[i], color_sets[j]
            if a and b:
                jaccard = len(a & b) / len(a | b)
                pairwise_jaccards.append(jaccard)
    if pairwise_jaccards:
        scores.append(statistics.mean(pairwise_jaccards))

    # ── Typography range tightness ──
    heading_mins = []
    heading_maxs = []
    body_mins = []
    body_maxs = []
    for cat in categories:
        if len(cat.heading_size_range) >= 3:
            heading_mins.append(cat.heading_size_range[0])
            heading_maxs.append(cat.heading_size_range[1])
        if len(cat.body_size_range) >= 3:
            body_mins.append(cat.body_size_range[0])
            body_maxs.append(cat.body_size_range[1])

    if heading_mins and heading_maxs:
        heading_span = max(heading_maxs) - min(heading_mins)
        heading_range = max(heading_maxs)  # normalizer
        if heading_range > 0:
            scores.append(max(0.0, 1.0 - heading_span / heading_range))

    if body_mins and body_maxs:
        body_span = max(body_maxs) - min(body_mins)
        body_range = max(body_maxs)
        if body_range > 0:
            scores.append(max(0.0, 1.0 - body_span / body_range))

    # ── Grid consistency ──
    grid_sets = [set(cat.common_grids.keys()) for cat in categories]
    g_pairwise = []
    for i in range(len(grid_sets)):
        for j in range(i + 1, len(grid_sets)):
            a, b = grid_sets[i], grid_sets[j]
            if a and b:
                g_pairwise.append(len(a & b) / len(a | b))
    if g_pairwise:
        scores.append(statistics.mean(g_pairwise))

    # ── Photography consistency ──
    comp_sets = [set(cat.common_compositions.keys()) for cat in categories]
    c_pairwise = []
    for i in range(len(comp_sets)):
        for j in range(i + 1, len(comp_sets)):
            a, b = comp_sets[i], comp_sets[j]
            if a and b:
                c_pairwise.append(len(a & b) / len(a | b))
    if c_pairwise:
        scores.append(statistics.mean(c_pairwise))

    angle_sets = [set(cat.common_angles.keys()) for cat in categories]
    a_pairwise = []
    for i in range(len(angle_sets)):
        for j in range(i + 1, len(angle_sets)):
            a, b = angle_sets[i], angle_sets[j]
            if a and b:
                a_pairwise.append(len(a & b) / len(a | b))
    if a_pairwise:
        scores.append(statistics.mean(a_pairwise))

    return statistics.mean(scores) if scores else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DESIGN TOKENS — 品牌VI → 可执行令牌
# ═══════════════════════════════════════════════════════════════════════════════

def generate_design_tokens(brand_vi: BrandVISystem) -> Dict[str, Any]:
    """
    将 BrandVISystem 转换为 AI 设计师可直接使用的设计令牌。

    输出格式兼容 CSS 自定义属性、JSON 设计令牌 (W3C DTCG spec-inspired)、
    以及 AI 图文生图 prompt 可直接引用的参数。

    Args:
        brand_vi: 品牌VI系统

    Returns:
        设计令牌字典，含 css_variables / json_tokens / ai_prompt_params / rules
    """
    bc = brand_vi.brand_colors
    bt = brand_vi.brand_typography

    tokens: Dict[str, Any] = {

        # ── CSS custom properties (可直接注入 :root) ──
        "css_variables": {
            "--brand-primary": bc.get("primary", "#000000"),
            "--brand-secondary": bc.get("secondary", "#666666"),
            "--brand-accent": bc.get("accent", "#0066cc"),
            "--brand-background": bc.get("background", "#FFFFFF"),
            "--brand-text-primary": bc.get("text_primary", "#1a1a1a"),
            "--brand-text-secondary": bc.get("text_secondary", "#666666"),
            "--brand-border": bc.get("border", "#e5e5e5"),
            "--typography-heading-min": (
                f"{bt.get('heading_size_range', [0, 0])[0]}px"
            ),
            "--typography-heading-max": (
                f"{bt.get('heading_size_range', [0, 0])[1]}px"
            ),
            "--typography-body-size": f"{bt.get('body_size_median', 14)}px",
            "--layout-grid-type": brand_vi.brand_layout_system,
        },

        # ── W3C DTCG-style JSON tokens ──
        "json_tokens": {
            "brand": {
                "colors": {
                    "primary": {"value": bc.get("primary", "#000000")},
                    "secondary": {"value": bc.get("secondary", "#666666")},
                    "accent": {"value": bc.get("accent", "#0066cc")},
                    "background": {"value": bc.get("background", "#FFFFFF")},
                    "text": {
                        "primary": {"value": bc.get("text_primary", "#1a1a1a")},
                        "secondary": {"value": bc.get("text_secondary", "#666666")},
                    },
                    "border": {"value": bc.get("border", "#e5e5e5")},
                },
                "typography": {
                    "heading": {
                        "size": {
                            "min": {"value": bt.get("heading_size_range", [0, 0])[0]},
                            "max": {"value": bt.get("heading_size_range", [0, 0])[1]},
                        }
                    },
                    "body": {
                        "size": {"value": bt.get("body_size_median", 14)}
                    },
                },
                "layout": {
                    "grid": {"value": brand_vi.brand_layout_system},
                },
            },
            "meta": {
                "consistency_score": {"value": brand_vi.consistency_score},
                "categories_analyzed": {
                    "value": brand_vi.categories_analyzed
                },
                "total_pages_analyzed": {"value": brand_vi.total_pages_analyzed},
            },
        },

        # ── AI prompt 可直接引用的参数 (text-to-image / image generation) ──
        "ai_prompt_params": {
            "color_palette": [
                bc.get("primary", ""),
                bc.get("secondary", ""),
                bc.get("accent", ""),
                bc.get("background", ""),
                bc.get("text_primary", ""),
                bc.get("text_secondary", ""),
            ],
            "palette_description": (
                f"主色 {bc.get('primary','')}, "
                f"辅色 {bc.get('secondary','')}, "
                f"强调色 {bc.get('accent','')}, "
                f"背景 {bc.get('background','')}"
            ),
            "typography_summary": (
                f"标题 {bt.get('heading_size_range',[0,0])[0]}–"
                f"{bt.get('heading_size_range',[0,0])[1]}px, "
                f"正文 {bt.get('body_size_median',14)}px"
            ),
            "photography_rules": brand_vi.brand_photography_rules,
            "layout_system": brand_vi.brand_layout_system,
        },

        # ── 设计规则 (自然语言，供 LLM agents 理解) ──
        "rules": {
            "color_usage": (
                f"Primary '{bc.get('primary','')}' 用于关键CTA和品牌标志; "
                f"Secondary '{bc.get('secondary','')}' 用于辅助元素; "
                f"Accent '{bc.get('accent','')}' 用于高亮和装饰; "
                f"Background '{bc.get('background','')}' 用于大面积底色; "
                f"Text primary '{bc.get('text_primary','')}' 用于正文标题; "
                f"Text secondary '{bc.get('text_secondary','')}' 用于辅助文字"
            ),
            "typography_usage": (
                f"标题字号范围 {bt.get('heading_size_range',[0,0])[0]}–"
                f"{bt.get('heading_size_range',[0,0])[1]}px；"
                f"正文字号 {bt.get('body_size_median',14)}px"
            ),
            "photography_usage": brand_vi.brand_photography_rules,
            "layout_usage": f"主导布局: {brand_vi.brand_layout_system}",
            "consistency": (
                f"跨品类VI一致性: {brand_vi.consistency_score:.0%}"
            ),
        },
    }

    # Mutate the brand_vi object in place to carry tokens
    brand_vi.design_tokens = tokens

    return tokens


# ═══════════════════════════════════════════════════════════════════════════════
# 辅助 — 管线便捷函数
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_pipeline(
    pages_by_category: Dict[str, List[FullPageDNA]],
    brand: str = "",
) -> BrandVISystem:
    """
    一键运行完整管线: aggregate → induce → tokens。

    Args:
        pages_by_category: {category_name: [FullPageDNA, ...], ...}
        brand: 品牌名称

    Returns:
        BrandVISystem (含 design_tokens)
    """
    # Stage 1: Aggregate each category
    category_summaries = [
        aggregate_to_category(pages)
        for pages in pages_by_category.values()
    ]

    # Stage 2: Induce brand VI
    brand_vi = induce_brand_vi(category_summaries, brand=brand)

    # Stage 3: Generate design tokens
    generate_design_tokens(brand_vi)

    return brand_vi
