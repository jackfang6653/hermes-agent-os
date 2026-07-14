#!/usr/bin/env python3
"""
Agency 5阶段全流程测试 — IKEA 3产品

运行: python test_agency_ikea.py
"""
import os, sys, json

# 确保 packages 目录在path中
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from packages.agency.agency import Agency4A
from packages.agency.ikea_test_data import IKEA_PRODUCTS, IKEA_COMPETITORS, IKEA_BRAND


def main():
    output_dir = os.path.join(ROOT, "output", "ikea-4a-test")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  🧪  Agency 5阶段全流程测试")
    print(f"  品牌: {IKEA_BRAND}")
    print(f"  产品: {len(IKEA_PRODUCTS)}个")
    print(f"  竞品: {', '.join(IKEA_COMPETITORS)}")
    print(f"  输出: {output_dir}")
    print("=" * 60)

    agency = Agency4A()

    result = agency.run(
        brand=IKEA_BRAND,
        products=IKEA_PRODUCTS,
        competitors=IKEA_COMPETITORS,
        output_dir=output_dir,
        project_name="IKEA-4A-Full-Pipeline-Test",
        skip_execution=False,
    )

    # ── 输出结果摘要 ──
    print("\n" + "=" * 60)
    print("  📊  测试结果摘要")
    print("=" * 60)

    print(f"\n  状态: {result['status']}")
    print(f"  耗时: {result['duration_sec']}s")
    print(f"  产品数: {result['products_analyzed']}")
    print(f"  概念数: {result['concepts_produced']}")
    print(f"  推荐方案: {result['recommended_concept']}")

    if result.get("visual_system_summary"):
        vs = result["visual_system_summary"]
        print(f"\n  视觉系统摘要:")
        print(f"    核心色: {vs.get('core_colors', [])}")
        print(f"    焦距范围: {vs.get('focal_range', 'N/A')}")
        print(f"    光圈范围: {vs.get('aperture_range', 'N/A')}")
        print(f"    灯光模式: {vs.get('lighting_patterns', [])}")
        print(f"    构图规则: {vs.get('composition_rules', [])}")

    print(f"\n  输出文件:")
    for key, path in result.get("output", {}).items():
        exists = os.path.exists(path) if path else False
        icon = "✅" if exists else "❌"
        print(f"    {icon} {key}: {path}")

    # ── Step Status ──
    print(f"\n  各阶段状态:")
    for phase, ps in result.get("step_status", {}).items():
        icon = "✅" if ps.get("status") == "ok" else "⚠️" if ps.get("status") == "skipped" else "❌"
        print(f"    {icon} {phase}: {ps.get('status')}")

    # 写入完整结果
    result_path = os.path.join(output_dir, "agency_result.json")
    # 不可序列化的对象移除
    clean_result = {
        k: v for k, v in result.items()
        if isinstance(v, (str, int, float, bool, list, dict, type(None)))
    }
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(clean_result, f, ensure_ascii=False, indent=2)
    print(f"\n  📋 完整结果: {result_path}")

    # 验证
    print(f"\n{'='*60}")
    errors = []
    if result["status"] != "success":
        errors.append("整体状态非success")
    if result["products_analyzed"] != 3:
        errors.append(f"产品数是{result['products_analyzed']}而非3")
    if result["concepts_produced"] != 5:
        errors.append(f"概念数是{result['concepts_produced']}而非5")

    # 检查输出是否存在
    for key, path in result.get("output", {}).items():
        if path and not os.path.exists(path):
            errors.append(f"输出文件缺失: {key} → {path}")

    if errors:
        print("  ❌ 验证失败:")
        for e in errors:
            print(f"     • {e}")
        sys.exit(1)
    else:
        print("  ✅ 全部验证通过!")

    print("=" * 60)
    return result


if __name__ == "__main__":
    main()
