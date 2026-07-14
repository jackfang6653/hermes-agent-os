"""
测试 StrategyDept v2 — 传入3个产品URL, 验证输出参数范围
"""
import sys, os, json

# 确保项目路径在 sys.path 中
project_root = r"C:\Users\Administrator\Documents\Hermes Agent OS团队"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "packages"))

# 直接导入 strategy 模块
import importlib.util
strategy_path = os.path.join(project_root, "packages", "agency", "strategy.py")
spec = importlib.util.spec_from_file_location("strategy", strategy_path)
strategy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strategy)

StrategyDept = strategy.StrategyDept

# 使用 MUJI 产品图片URL (来自 muji_scenegraph.json, 已验证可达)
products = [
    {
        "image": "https://img.muji.net/img/item/4945247913620_1260.jpg",
        "name": "Acrylic Picture frame M",
        "brand": "MUJI"
    },
    {
        "image": "https://img.muji.net/img/item/4550512828808_1260.jpg",
        "name": "Wooden desk W110xD55xH70cm",
        "brand": "MUJI"
    },
    {
        "image": "https://img.muji.net/img/item/4550512841098_1260.jpg",
        "name": "Wooden Round chair W45xD52xH78cm",
        "brand": "MUJI"
    },
]

print("=" * 60)
print("  StrategyDept v2 测试 — MUJI 3产品SceneGraph分析")
print("=" * 60)

# 创建策略部实例
dept = StrategyDept()

# 分析品牌视觉系统
print("\n🚀 开始分析...")
system = dept.analyze_brand_system(products)

# 导出报告到桌面
output_path = os.path.expanduser("~/Desktop/brand_visual_system_report.json")
report_path = dept.export_report(system, output_path)

# 验证输出
print("\n" + "=" * 60)
print("  📋 验证输出参数范围")
print("=" * 60)

print(f"\n品牌: {system.brand}")
print(f"产品数: {system.products_analyzed}")
print(f"置信度: {system.confidence:.0%}")

print(f"\n🎨 色板系统:")
print(f"  核心色 ({len(system.core_palette)}): {system.core_palette[:4]}")
print(f"  点缀色 ({len(system.accent_palette)}): {system.accent_palette[:3]}")

print(f"\n📷 摄影参数范围:")
fl = system.focal_length_range
print(f"  焦距: {fl.min}-{fl.max}mm (avg={fl.avg:.1f}, samples={fl.samples})")
ap = system.aperture_range
print(f"  光圈: f/{ap.min}-f/{ap.max} (avg=f/{ap.avg:.1f}, samples={ap.samples})")
iso = system.iso_range
print(f"  ISO: {int(iso.min) if iso.samples else 0}-{int(iso.max) if iso.samples else 0} (samples={iso.samples})")
dist = system.distance_range
print(f"  物距: {dist.min:.0f}-{dist.max:.0f}cm (samples={dist.samples})")

print(f"\n💡 灯光系统:")
print(f"  模式: {system.lighting_patterns}")
print(f"  色温范围: {system.color_temperature_range.min:.0f}-{system.color_temperature_range.max:.0f}K (samples={system.color_temperature_range.samples})")
print(f"  设置数: {len(system.common_lighting_setups)}")

print(f"\n🧱 材质系统 ({len(system.material_system)} 大类):")
for mtype, samples in system.material_system.items():
    print(f"  {mtype} ({len(samples)}样本)")

print(f"\n📐 构图规律:")
for rule in system.composition_rules:
    print(f"  • {rule}")

print(f"\n🎯 设计原则:")
for p in system.design_principles:
    print(f"  • {p}")

# 验证关键指标
print("\n" + "=" * 60)
print("  ✅ 验证检查")
print("=" * 60)

checks = []
checks.append(("产品分析数 >= 1", system.products_analyzed >= 1))
checks.append(("色板非空", len(system.core_palette) > 0))
checks.append(("焦距有范围", fl.samples > 0))
checks.append(("光圈有范围", ap.samples > 0))
checks.append(("灯光有模式", len(system.lighting_patterns) > 0))
checks.append(("材质有分类", len(system.material_system) > 0))
checks.append(("报告已输出", os.path.exists(report_path)))
checks.append(("置信度 > 0.5", system.confidence >= 0.5))

all_pass = True
for name, result in checks:
    status = "✅" if result else "❌"
    if not result:
        all_pass = False
    print(f"  {status} {name}")

print(f"\n{'✅ 全部通过!' if all_pass else '❌ 部分检查未通过'}")
print(f"📄 报告路径: {report_path}")
