"""
Mock-data 验证测试 — 测试 dna_induction 管线: aggregate → induce → design tokens

覆盖:
  1. 单品类聚合 (sofas, lighting 两个品类)
  2. 跨品类品牌 VI 归纳
  3. 设计令牌生成
  4. 边缘情况 (空列表、单品页、单品类)
"""

import os, sys, json

# Ensure we can import from packages/agency
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.agency.dna_induction import (
    aggregate_to_category,
    induce_brand_vi,
    generate_design_tokens,
    run_full_pipeline,
)
from packages.agency.dna_schema import (
    FullPageDNA, CategoryDNASummary, BrandVISystem,
    PageModule, PageLayout, TypographySystem, ColorSystem, ColorSwatch,
    ImageSystem, ImageElement, LightingSystem, LightSource,
)


# ═══════════════════════════════════════════════════════════════════
# Mock data builders
# ═══════════════════════════════════════════════════════════════════

def _mk_page(
    url: str,
    brand: str,
    category: str,
    product: str,
    grid_type: str,
    heading_sizes: dict,
    body_size: int,
    primary_color: str,
    secondary_color: str,
    accent_color: str,
    bg_color: str,
    fg_color: str,
    harmony: str,
    temperature: str,
    reading_pattern: str,
    compositions: list,
    angles: list,
    focal_lengths: list,
    lighting_setup: str,
    font_families: list,
) -> FullPageDNA:
    """Build a minimal but realistic FullPageDNA."""
    # Colors
    swatches = [
        ColorSwatch(hex=primary_color, role="primary", usage_count=20, coverage_ratio=0.3),
        ColorSwatch(hex=secondary_color, role="secondary", usage_count=15, coverage_ratio=0.2),
        ColorSwatch(hex=accent_color, role="accent", usage_count=8, coverage_ratio=0.1),
        ColorSwatch(hex=bg_color, role="background", usage_count=50, coverage_ratio=0.6),
        ColorSwatch(hex=fg_color, role="text", usage_count=40, coverage_ratio=0.1),
        ColorSwatch(hex="#f5f5f5", role="bg_alt", usage_count=10, coverage_ratio=0.1),
    ]

    return FullPageDNA(
        url=url,
        brand=brand,
        product_name=product,
        product_category=category,
        extracted_at="2026-07-14T12:00:00",
        confidence=0.9,
        layout=PageLayout(
            grid_type=grid_type,
            columns=12 if grid_type == "grid" else 2 if grid_type == "two_col" else 1,
            gutter=24,
            content_max_width=1200,
            margin_auto=True,
            reading_pattern=reading_pattern,
            visual_hierarchy_count=4,
            section_gap=64,
            whitespace_ratio=0.35,
        ),
        typography=TypographySystem(
            heading_sizes=heading_sizes,
            body_size=body_size,
            caption_size=12,
            price_size=18,
            font_families=font_families,
            primary_font=font_families[0],
            secondary_font=font_families[1] if len(font_families) > 1 else "",
            type_scale_ratio=1.25,
            base_size=16,
            line_height_system=1.6,
        ),
        colors=ColorSystem(
            swatches=swatches,
            primary=primary_color,
            secondary=secondary_color,
            accent=accent_color,
            background=bg_color,
            text_primary=fg_color,
            text_secondary="#999999",
            border="#e0e0e0",
            primary_ratio=0.3,
            secondary_ratio=0.2,
            accent_ratio=0.1,
            neutral_ratio=0.4,
            harmony_type=harmony,
            temperature=temperature,
            psychology_tags=["minimal", "premium"],
        ),
        images=ImageSystem(
            total_count=12,
            hero_count=2,
            product_count=6,
            lifestyle_count=2,
            detail_count=2,
            spec_count=0,
            common_focal_lengths=focal_lengths,
            common_compositions=compositions,
            common_angles=angles,
        ),
        lighting=LightingSystem(
            light_count=3,
            setup_type=lighting_setup,
            key_to_fill_ratio=2.0,
        ),
    )


# ── Build mock data: NORHOR brand, sofas and lighting categories ──

sofa_pages = [
    _mk_page(
        url="https://www.norhor.com/sofa/001",
        brand="NORHOR",
        category="sofas",
        product="Oslo 三人沙发",
        grid_type="two_col",
        heading_sizes={"h1": 36, "h2": 28, "h3": 20},
        body_size=15,
        primary_color="#2d2d2d",
        secondary_color="#8b7355",
        accent_color="#c4a35a",
        bg_color="#faf8f5",
        fg_color="#2d2d2d",
        harmony="analogous",
        temperature="warm",
        reading_pattern="F_pattern",
        compositions=["centered", "rule_of_thirds"],
        angles=["eye_level", "low_angle"],
        focal_lengths=[50, 85],
        lighting_setup="three_point",
        font_families=["Noto Sans SC", "Georgia"],
    ),
    _mk_page(
        url="https://www.norhor.com/sofa/002",
        brand="NORHOR",
        category="sofas",
        product="Harbor 转角沙发",
        grid_type="two_col",
        heading_sizes={"h1": 34, "h2": 26, "h3": 18},
        body_size=14,
        primary_color="#2d2d2d",
        secondary_color="#8b7355",
        accent_color="#bfa055",
        bg_color="#faf8f5",
        fg_color="#333333",
        harmony="analogous",
        temperature="warm",
        reading_pattern="F_pattern",
        compositions=["centered", "golden_ratio"],
        angles=["eye_level", "front"],
        focal_lengths=[50, 85, 35],
        lighting_setup="three_point",
        font_families=["Noto Sans SC", "Georgia"],
    ),
    _mk_page(
        url="https://www.norhor.com/sofa/003",
        brand="NORHOR",
        category="sofas",
        product="Nordic 双人沙发",
        grid_type="single",
        heading_sizes={"h1": 32, "h2": 24, "h3": 18},
        body_size=15,
        primary_color="#2d2d2d",
        secondary_color="#8b7355",
        accent_color="#d4b060",
        bg_color="#ffffff",
        fg_color="#1a1a1a",
        harmony="monochromatic",
        temperature="warm",
        reading_pattern="Z_pattern",
        compositions=["centered", "leading_lines"],
        angles=["eye_level"],
        focal_lengths=[35, 50],
        lighting_setup="Rembrandt",
        font_families=["Noto Sans SC", "Georgia"],
    ),
]

lighting_pages = [
    _mk_page(
        url="https://www.norhor.com/lighting/001",
        brand="NORHOR",
        category="lighting",
        product="Nordic 吊灯",
        grid_type="single",
        heading_sizes={"h1": 30, "h2": 22, "h3": 16},
        body_size=14,
        primary_color="#2d2d2d",
        secondary_color="#8b7355",
        accent_color="#c4a35a",
        bg_color="#ffffff",
        fg_color="#1a1a1a",
        harmony="analogous",
        temperature="warm",
        reading_pattern="Z_pattern",
        compositions=["centered"],
        angles=["high_angle"],
        focal_lengths=[50, 85],
        lighting_setup="single",
        font_families=["Noto Sans SC", "Georgia"],
    ),
    _mk_page(
        url="https://www.norhor.com/lighting/002",
        brand="NORHOR",
        category="lighting",
        product="工业风落地灯",
        grid_type="single",
        heading_sizes={"h1": 28, "h2": 20, "h3": 16},
        body_size=14,
        primary_color="#2d2d2d",
        secondary_color="#5a5a5a",
        accent_color="#bfa055",
        bg_color="#faf8f5",
        fg_color="#1a1a1a",
        harmony="complementary",
        temperature="neutral",
        reading_pattern="Z_pattern",
        compositions=["centered", "rule_of_thirds"],
        angles=["low_angle"],
        focal_lengths=[35, 50],
        lighting_setup="single",
        font_families=["Noto Sans SC", "Georgia"],
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════

def test_aggregate_to_category_sofas():
    """聚合沙发品类 3 个页面"""
    summary = aggregate_to_category(sofa_pages)
    assert summary.category == "sofas", f"wrong category: {summary.category}"
    assert summary.sample_count == 3, f"wrong count: {summary.sample_count}"
    assert len(summary.heading_size_range) == 3, f"heading range missing: {summary.heading_size_range}"
    assert summary.heading_size_range[0] <= summary.heading_size_range[1]
    assert len(summary.body_size_range) == 3
    assert summary.common_colors, "no common colors"
    assert summary.design_rules, "no design rules extracted"
    assert len(summary.common_grids) > 0
    print("  [PASS] test_aggregate_to_category_sofas")
    print(f"    category={summary.category}, samples={summary.sample_count}")
    print(f"    heading_range={summary.heading_size_range}")
    print(f"    body_range={summary.body_size_range}")
    print(f"    grid patterns: {summary.common_grids}")
    print(f"    design rules ({len(summary.design_rules)}):")
    for r in summary.design_rules:
        print(f"      • {r}")
    return summary


def test_aggregate_to_category_lighting():
    """聚合灯具品类 2 个页面"""
    summary = aggregate_to_category(lighting_pages)
    assert summary.category == "lighting"
    assert summary.sample_count == 2
    assert summary.common_compositions, "no compositions aggregated"
    print("  [PASS] test_aggregate_to_category_lighting")
    print(f"    category={summary.category}, samples={summary.sample_count}")
    print(f"    compositions: {summary.common_compositions}")
    print(f"    lighting setups: {summary.common_lighting_setups}")
    return summary


def test_aggregate_empty():
    """空列表返回空摘要"""
    summary = aggregate_to_category([])
    assert summary.sample_count == 0
    assert summary.category == ""
    print("  [PASS] test_aggregate_empty")


def test_aggregate_single_page():
    """单个页面也能聚合"""
    summary = aggregate_to_category([sofa_pages[0]])
    assert summary.sample_count == 1
    assert summary.design_rules, "single page should still extract rules"
    print("  [PASS] test_aggregate_single_page")


def test_induce_brand_vi():
    """跨品类归纳 NORHOR 品牌VI"""
    cat_sofas = aggregate_to_category(sofa_pages)
    cat_lighting = aggregate_to_category(lighting_pages)

    brand_vi = induce_brand_vi([cat_sofas, cat_lighting], brand="NORHOR")
    assert brand_vi.brand == "NORHOR"
    assert brand_vi.total_pages_analyzed == 5
    assert len(brand_vi.categories_analyzed) == 2
    assert brand_vi.brand_colors, "no brand colors inferred"
    assert "primary" in brand_vi.brand_colors
    assert "secondary" in brand_vi.brand_colors
    assert brand_vi.brand_typography
    assert brand_vi.brand_photography_rules
    assert len(brand_vi.brand_photography_rules) > 0
    assert 0.0 <= brand_vi.consistency_score <= 1.0

    print("  [PASS] test_induce_brand_vi")
    print(f"    brand={brand_vi.brand}, pages={brand_vi.total_pages_analyzed}")
    print(f"    colors: {brand_vi.brand_colors}")
    print(f"    typography: {brand_vi.brand_typography}")
    print(f"    layout: {brand_vi.brand_layout_system}")
    print(f"    consistency_score: {brand_vi.consistency_score}")
    print(f"    photography rules:")
    for r in brand_vi.brand_photography_rules:
        print(f"      • {r}")
    return brand_vi


def test_generate_design_tokens():
    """生成AI设计师可用的设计令牌"""
    cat_sofas = aggregate_to_category(sofa_pages)
    cat_lighting = aggregate_to_category(lighting_pages)
    brand_vi = induce_brand_vi([cat_sofas, cat_lighting], brand="NORHOR")

    tokens = generate_design_tokens(brand_vi)

    # Verify structure
    assert "css_variables" in tokens
    assert "json_tokens" in tokens
    assert "ai_prompt_params" in tokens
    assert "rules" in tokens

    # CSS vars
    css = tokens["css_variables"]
    assert "--brand-primary" in css
    assert css["--brand-primary"] == brand_vi.brand_colors.get("primary")
    assert "--typography-heading-min" in css
    assert "--typography-body-size" in css

    # JSON tokens (DTCG-style)
    jt = tokens["json_tokens"]
    assert "brand" in jt
    assert "colors" in jt["brand"]
    assert "primary" in jt["brand"]["colors"]

    # AI params
    ai = tokens["ai_prompt_params"]
    assert "color_palette" in ai
    assert len(ai["color_palette"]) > 0
    assert "palette_description" in ai
    assert "photography_rules" in ai

    # Rules
    assert tokens["rules"]["color_usage"]
    assert tokens["rules"]["consistency"]

    # Verify tokens are stored back on the object
    assert brand_vi.design_tokens == tokens

    print("  [PASS] test_generate_design_tokens")
    print(f"    CSS vars: {len(css)} entries")
    print(f"    JSON token keys: {list(jt.keys())}")
    print(f"    AI params: {list(ai.keys())}")
    return tokens


def test_run_full_pipeline():
    """一键管线: aggregate→induce→tokens"""
    pages_by_cat = {
        "sofas": sofa_pages,
        "lighting": lighting_pages,
    }
    brand_vi = run_full_pipeline(pages_by_cat, brand="NORHOR")

    assert brand_vi.brand == "NORHOR"
    assert brand_vi.design_tokens, "tokens not populated"
    assert "css_variables" in brand_vi.design_tokens

    print("  [PASS] test_run_full_pipeline")
    print(f"    brand={brand_vi.brand}")
    print(f"    consistency={brand_vi.consistency_score}")
    print(f"    tokens populated: {bool(brand_vi.design_tokens)}")


def test_induce_single_category():
    """单品类归纳 (边缘情况)"""
    cat = aggregate_to_category(sofa_pages)
    brand_vi = induce_brand_vi([cat], brand="NORHOR")
    assert brand_vi.consistency_score == 1.0, "single category should have perfect consistency"
    print("  [PASS] test_induce_single_category")



def test_induce_empty():
    """空品类列表"""
    brand_vi = induce_brand_vi([], brand="TEST")
    assert brand_vi.brand == "TEST"
    assert brand_vi.total_pages_analyzed == 0
    assert brand_vi.consistency_score == 0.0
    print("  [PASS] test_induce_empty")


# ═══════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("品类抽象+品牌VI归纳管线 — 测试")
    print("=" * 60)

    try:
        test_aggregate_empty()
        test_aggregate_single_page()
        test_aggregate_to_category_sofas()
        test_aggregate_to_category_lighting()
        test_induce_brand_vi()
        test_induce_single_category()
        test_induce_empty()
        test_generate_design_tokens()
        test_run_full_pipeline()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
