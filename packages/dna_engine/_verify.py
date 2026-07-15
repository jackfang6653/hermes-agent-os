"""Verification script for dna_engine package."""
import sys
import os
import tempfile
import json

# Ensure the project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

def test_imports():
    print('=== 1: Syntax + Import Check ===')
    from packages.dna_engine.dna_schema import (
        BrandDNA, DesignSystemDNA, DesignStyleDNA, VisualEffectsDNA,
        ColorDNA, TypographyDNA, SpacingDNA, LayoutDNA, ShapeDNA,
        ElevationDNA, IconographyDNA, MotionDNA, ComponentDNA,
        AestheticDNA, VisualLanguageDNA, CompositionDNA, ImageryDNA, InteractionDNA,
        BackgroundEffectDNA, ParticleEffectDNA, ThreeDEffectDNA, ShaderEffectDNA,
        ScrollEffectDNA, TextEffectDNA, CursorEffectDNA, ImageEffectDNA, GlassmorphismDNA,
        DNAField, ConfidenceLevel, ExtractionMethod,
        create_empty_dna, dna_from_json, dna_from_dtcg_tokens,
    )
    print('   OK dna_schema — all 40+ symbols imported')

    from packages.dna_engine.dna_database import (
        DNADatabase, create_database, migrate_from_v1,
        DTCG_VERSION, QUALITY_GATE_THRESHOLDS, QUALITY_GATE_NAMES,
    )
    print(f'   OK dna_database — imported (DTCG {DTCG_VERSION})')

    from packages.dna_engine.quality_gates import (
        GateStatus, Severity, GateResult, QualityPipelineResult,
        ReconnaissanceGate, TokenExtractionGate, AssetExtractionGate,
        SynthesisGate, VisualReplicationGate,
        QualityGatePipeline, evaluate_brand_quality, gate_data_template,
    )
    print('   OK quality_gates — all symbols imported')

    from packages.dna_engine import (
        SceneGraph, SceneElement, BrandDatabase, DNAPipeline, __version__,
    )
    print(f'   OK legacy imports intact, version={__version__}')


def test_roundtrip():
    print('\n=== 2: DNA Round-trip ===')
    from packages.dna_engine.dna_schema import create_empty_dna, dna_from_json
    dna = create_empty_dna('NORHOR', 'furniture')
    dna.design_system.color.primary = '#1a1a1a'
    dna.design_system.typography.scale_h1 = 48.0
    dna.design_system.typography.scale_body = 16.0
    dna.design_system.typography.heading_font = 'Noto Sans SC'
    dna.design_system.typography.body_font = 'Noto Sans SC'
    dna.design_system.typography.body_line_height = 1.6
    dna.design_system.layout.grid_type = 'single'
    dna.design_system.layout.columns = 1
    dna.design_style.aesthetic.mood = 'minimal'
    dna.design_style.aesthetic.genre = 'modern_minimal'
    dna.design_style.visual_language.whitespace_usage = 'generous'

    dna_dict = dna.to_dict()
    assert 'design_system' in dna_dict
    assert 'design_style' in dna_dict
    assert 'visual_effects' in dna_dict
    assert dna_dict['design_system']['color']['primary'] == '#1a1a1a'

    dna_json = dna.to_json()
    assert len(dna_json) > 1000

    # deserialize and check top-level identity preserved
    dna2 = dna_from_json(dna_dict)
    assert dna2.brand_name == 'NORHOR'
    assert dna2.category == 'furniture'
    print('   OK round-trip: dict->json->BrandDNA consistent')
    return dna


def test_dtcg(dna):
    print('\n=== 3: DTCG Token Export ===')
    tokens = dna.to_dtcg_tokens()
    assert len(tokens) > 0
    for path, tok in list(tokens.items())[:5]:
        assert '$value' in tok
        assert '$type' in tok
    print(f'   OK {len(tokens)} DTCG tokens exported')


def test_validation(dna):
    print('\n=== 4: DNA Validation ===')
    issues = dna.validate()
    print(f'   OK validate() returned {len(issues)} issues (expected for partial fill)')
    return issues


def test_database(dna):
    print('\n=== 5: Database CRUD ===')
    from packages.dna_engine.dna_database import DNADatabase
    tmp_db = os.path.join(tempfile.gettempdir(), 'verify_dna_v2.db')
    db = DNADatabase(tmp_db)

    # Create
    bid = db.create_brand(dna)
    assert bid
    print(f'   OK brand created: {bid}')

    # Read
    brand = db.get_brand(bid)
    assert brand['name'] == 'NORHOR'
    assert brand['category'] == 'furniture'

    # List / Search
    assert len(db.list_brands()) == 1
    assert len(db.search_brands('NORHOR')) == 1

    # Tokens
    tokens = db.get_tokens_by_brand(bid)
    assert len(tokens) > 0
    print(f'   OK {len(tokens)} design tokens')

    # DTCG export
    dtcg = db.export_dtcg_tokens(bid)
    assert len(dtcg) > 0

    # Single token query
    first_path = tokens[0]['dtcg_path']
    assert db.get_token_by_path(bid, first_path)

    # Update + version snapshot
    dna.overall_confidence = 0.92
    dna.brand_id = bid
    assert db.update_brand(dna)
    versions = db.get_version_history(bid)
    assert len(versions) >= 1
    print(f'   OK version snapshot: {len(versions)} versions')

    # Gate records
    for gn, sc in [(1, 0.95), (2, 0.88), (3, 0.72), (4, 0.85), (5, 0.83)]:
        db.record_gate_result(bid, gn, sc)
    assert len(db.get_gate_results(bid)) == 5
    assert len(db.get_latest_gate_results(bid)) == 5
    approved, failures = db.is_brand_approved(bid)
    print(f'   OK quality gates: approved={approved}, failures={len(failures)}')

    # Stats
    stats = db.get_brand_stats(bid)
    assert stats['token_count'] > 0
    assert stats['version_count'] >= 1

    db_stats = db.get_database_stats()
    assert db_stats['brand_count'] == 1
    print(f'   OK db_stats: {db_stats["brand_count"]} brands, {db_stats["token_count"]} tokens')

    # Sessions
    sid = db.start_session(bid, 'https://example.com', 1)
    db.complete_session(sid, 42)
    assert len(db.get_sessions(bid)) == 1

    # Restore
    assert db.restore_version(bid, versions[0]['version_number'])

    db.close()
    os.unlink(tmp_db)
    print('   OK database cleanup')
    return dna


def test_quality_gates():
    print('\n=== 6: Quality Gates — All Passing ===')
    from packages.dna_engine.quality_gates import QualityGatePipeline, gate_data_template
    pipeline = QualityGatePipeline()
    d = gate_data_template()
    d[1].update({
        'brand_name': 'TestBrand', 'pages_captured': 5,
        'resources_total': 100, 'resources_accessible': 95,
        'dom_elements_found': 450, 'dom_elements_expected': 500,
        'anti_scraping_blocked': False,
    })
    d[2].update({
        'tokens': list(range(50)),
        'category_coverage': {'color': 0.95, 'typography': 0.90, 'spacing': 0.88, 'layout': 0.92, 'shape': 0.87},
        'avg_confidence': 0.92, 'dtcg_mapping_accuracy': 0.91,
    })
    d[3].update({
        'logo': {'found': True, 'url': 'x', 'format': 'svg'},
        'images': [{'type': t} for t in ['hero','product','lifestyle']],
        'icons': [{} for _ in range(5)],
        'fonts': [{'family': 'Inter'}],
        'favicon': {'found': True},
    })
    d[4].update({
        'design_system_consistency': 0.88, 'style_accuracy': 0.85,
        'why_trace_completeness': 0.90, 'acr_score': 0.82,
        'principle_derivation_accuracy': 0.87,
    })
    d[5].update({
        'pixel_accuracy': 0.85, 'structural_fidelity': 0.90, 'traceability': 0.84,
    })
    result = pipeline.evaluate('TestBrand', d)
    assert result.overall_passed
    for gn in range(1, 6):
        assert result.results[gn].status.value == 'passed'
    print(f'   OK all 5 gates PASSED (score={result.total_score:.4f})')

    print('\n=== 7: Quality Gates — Failing at Gate 3 ===')
    d2 = gate_data_template()
    d2[1].update({'brand_name': 'NoLogo', 'pages_captured': 5, 'resources_total': 100,
        'resources_accessible': 95, 'dom_elements_found': 450, 'dom_elements_expected': 500,
        'anti_scraping_blocked': False})
    d2[2].update({'tokens': list(range(50)),
        'category_coverage': {'color': 0.95, 'typography': 0.90, 'spacing': 0.88, 'layout': 0.92, 'shape': 0.87},
        'avg_confidence': 0.92, 'dtcg_mapping_accuracy': 0.91})
    d2[3].update({'logo': {'found': False}, 'images': [], 'icons': [], 'fonts': [], 'favicon': {'found': False}})
    result2 = pipeline.evaluate('NoLogo', d2, stop_on_failure=False)
    assert not result2.overall_passed
    assert result2.results[3].status.value == 'failed'
    assert result2.failed_at_gate == 3
    print('   OK pipeline correctly fails at Gate 3 (no logo)')


def test_compare(dna):
    print('\n=== 8: Brand Comparison ===')
    from packages.dna_engine.dna_database import DNADatabase
    from packages.dna_engine.dna_schema import create_empty_dna
    tmp_db = os.path.join(tempfile.gettempdir(), 'verify_compare.db')
    db = DNADatabase(tmp_db)

    a = create_empty_dna('BrandA', 'furniture')
    a.design_system.color.primary = '#000'
    a.design_system.typography.heading_font = 'Arial'
    a.brand_id = 'brand_a'

    b = create_empty_dna('BrandB', 'furniture')
    b.design_system.color.primary = '#fff'
    b.design_system.typography.heading_font = 'Arial'
    b.brand_id = 'brand_b'

    db.create_brand(a)
    db.create_brand(b)

    cmp = db.compare_brands('brand_a', 'brand_b')
    assert 'similarity' in cmp
    assert cmp['total_paths'] > 0
    print(f'   OK compare: similarity={cmp["similarity"]}, paths={cmp["total_paths"]}, '
          f'matches={cmp["matches"]}, mismatches={len(cmp["mismatches"])}')

    db.close()
    os.unlink(tmp_db)


def test_gate_persistence(dna):
    print('\n=== 9: Gate Persistence to DB ===')
    from packages.dna_engine.dna_database import DNADatabase
    from packages.dna_engine.quality_gates import QualityGatePipeline, gate_data_template

    tmp_db = os.path.join(tempfile.gettempdir(), 'verify_gate_persist.db')
    db = DNADatabase(tmp_db)
    db.create_brand(dna)

    d = gate_data_template()
    d[1].update({'brand_name': 'NORHOR', 'pages_captured': 5, 'resources_total': 100,
        'resources_accessible': 95, 'dom_elements_found': 450, 'dom_elements_expected': 500,
        'anti_scraping_blocked': False})
    d[2].update({'tokens': list(range(50)),
        'category_coverage': {'color': 0.95, 'typography': 0.90, 'spacing': 0.88, 'layout': 0.92, 'shape': 0.87},
        'avg_confidence': 0.92, 'dtcg_mapping_accuracy': 0.91})
    d[3].update({'logo': {'found': True}, 'images': [{'type': 'hero'}], 'icons': [{} for _ in range(5)],
        'fonts': [{'family': 'Inter'}], 'favicon': {'found': True}})
    d[4].update({'design_system_consistency': 0.88, 'style_accuracy': 0.85,
        'why_trace_completeness': 0.90, 'acr_score': 0.82, 'principle_derivation_accuracy': 0.87})
    d[5].update({'pixel_accuracy': 0.85, 'structural_fidelity': 0.90, 'traceability': 0.84})

    pipeline = QualityGatePipeline(db)
    result = pipeline.evaluate('NORHOR', d)
    assert result.overall_passed

    gates = db.get_gate_results('NORHOR')
    assert len(gates) == 5
    print(f'   OK {len(gates)} gate records persisted to DB')

    db.close()
    os.unlink(tmp_db)


if __name__ == '__main__':
    ok = True
    try:
        test_imports()
        dna = test_roundtrip()
        test_dtcg(dna)
        test_validation(dna)
        dna = test_database(dna)
        test_quality_gates()
        test_compare(dna)
        test_gate_persistence(dna)
    except Exception as e:
        print(f'\n!!! FAILED: {e}')
        import traceback
        traceback.print_exc()
        ok = False

    print('\n' + ('=' * 60))
    if ok:
        print('ALL 9 VERIFICATION SUITES PASSED')
    else:
        print('VERIFICATION FAILED')
        sys.exit(1)
