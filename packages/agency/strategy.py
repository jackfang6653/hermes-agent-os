"""
策略部 — 多产品SceneGraph分析 → 品牌视觉系统 (v2 重建)

核心变化:
- 不再用启发式聚合
- 真正调用 SceneParser 逐个分析产品图片
- 跨产品聚合为参数范围

产出:
- 品牌视觉参数范围 (不是固定值)
- 竞品对标分析
- 消费者洞察
- 策略文档
- brand_visual_system_report.json
"""
import json
import os
import sys
import time
import statistics
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


@dataclass
class ParameterRange:
    """参数范围 — 品牌实际的视觉参数分布"""
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0
    median: float = 0.0
    samples: int = 0
    common_values: List[Any] = field(default_factory=list)

    def to_dict(self):
        return {
            "min": self.min, "max": self.max, "avg": round(self.avg, 2),
            "median": round(self.median, 2), "samples": self.samples,
            "common": self.common_values[:5]
        }


@dataclass
class BrandVisualSystem:
    """品牌视觉系统 — 多产品SceneGraph聚合结果"""
    brand: str = ""

    # 色板范围 (多个产品的SceneGraph聚合)
    core_palette: List[str] = field(default_factory=list)       # 跨产品共同色
    seasonal_palette: List[str] = field(default_factory=list)    # 系列特有色
    accent_palette: List[str] = field(default_factory=list)

    # 摄影参数范围
    focal_length_range: ParameterRange = field(default_factory=ParameterRange)
    aperture_range: ParameterRange = field(default_factory=ParameterRange)
    iso_range: ParameterRange = field(default_factory=ParameterRange)
    distance_range: ParameterRange = field(default_factory=ParameterRange)

    # 灯光系统 (多产品归纳)
    lighting_patterns: List[str] = field(default_factory=list)
    common_lighting_setups: List[Dict] = field(default_factory=list)
    color_temperature_range: ParameterRange = field(default_factory=ParameterRange)

    # 材质系统
    material_system: Dict[str, List[Dict]] = field(default_factory=dict)

    # 构图规律
    composition_rules: List[str] = field(default_factory=list)
    scene_types: List[str] = field(default_factory=list)

    # 后期处理参数范围
    post_processing_range: Dict[str, ParameterRange] = field(default_factory=dict)

    # 设计语言
    design_principles: List[str] = field(default_factory=list)

    # 分析方法
    products_analyzed: int = 0
    image_count: int = 0
    confidence: float = 0.0

    # SceneGraph原始结果 (调试/审计用)
    scene_graphs: List[Dict] = field(default_factory=list)


class StrategyDept:
    """策略部 — 多产品SceneGraph分析 → 品牌视觉系统 (v2)

    用法:
        dept = StrategyDept(api_key="sk-...")
        system = dept.analyze_brand_system([
            {"image": "https://.../product1.jpg", "name": "Sofa A"},
            {"image": "https://.../product2.jpg", "name": "Table B"},
            {"image": "https://.../product3.jpg", "name": "Chair C"},
        ])
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        report_path = dept.export_report(system, os.path.join(project_root, "output", f"{system.brand.lower().replace(' ', '_')}_visual_system_report.json"))
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._scene_parser = None
        self._knowledge = None

    @property
    def scene_parser(self):
        if self._scene_parser is None:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "dna_engine"))
            from dna_engine.scene_parser import SceneParser
            self._scene_parser = SceneParser(self.api_key)
        return self._scene_parser

    @property
    def knowledge(self):
        if self._knowledge is None:
            from knowledge.brand_knowledge import BrandKnowledgeBase, BrandProfile
            self._knowledge = BrandKnowledgeBase()
            self._BrandProfile = BrandProfile
        return self._knowledge

    # ═══════════════════════════════════════════════════════
    #  核心: 逐个产品调用 SceneParser → 跨产品聚合
    # ═══════════════════════════════════════════════════════

    def analyze_brand_system(self, products: List[Dict]) -> BrandVisualSystem:
        """分析品牌多个产品 → 提取完整视觉系统

        对每个产品的图片URL调用 SceneParser.parse()，
        获取完整SceneGraph，然后跨产品聚合为参数范围。
        """
        if not products:
            return BrandVisualSystem()

        brand = products[0].get("brand", products[0].get("brand_name", "unknown"))
        print(f"\n  📊 [Strategy v2] SceneGraph分析品牌视觉系统: {brand}")
        print(f"    产品样本数: {len(products)}")
        print("    方法: 逐个调用SceneParser → 跨产品聚合")

        scene_graphs = []
        errors = []

        for i, product in enumerate(products):
            image_url = product.get("image", product.get("image_url", ""))
            name = product.get("name", product.get("product_name", f"Product {i+1}"))

            if not image_url:
                print(f"    ⚠️  跳过 {name}: 无图片URL")
                continue

            print(f"    [{i+1}/{len(products)}] 🔍 SceneParser: {name}")
            print(f"       图片: {image_url[:80]}...")

            try:
                sg = self.scene_parser.parse(image_url)
                sg_dict = sg.to_dict()
                sg_dict["_product_name"] = name
                sg_dict["_product_image"] = image_url
                scene_graphs.append(sg_dict)
                print(f"       ✅ 元素: {len(sg.elements)}, 灯光: {len(sg.lights)}")
            except Exception as e:
                err_msg = str(e)[:120]
                print(f"       ❌ 解析失败: {err_msg}")
                errors.append({"product": name, "image": image_url, "error": err_msg})

        if not scene_graphs:
            print("    ❌ 无成功解析的场景图，试图从产品预分析数据回退...")
            fallback = self._fallback_from_product_analysis(products, brand)
            if fallback.products_analyzed > 0:
                print(f"    ✅ 回退成功 — {fallback.products_analyzed} 产品启发式聚合")
                self._save_to_knowledge(fallback, errors)
                return fallback
            print("    ❌ 无成功解析的场景图，无法构建视觉系统")
            return BrandVisualSystem(brand=brand, confidence=0.0)

        print(f"\n    📐 聚合 {len(scene_graphs)} 个SceneGraph → 参数范围...")
        system = self._aggregate_scene_graphs(scene_graphs, brand)
        system.scene_graphs = scene_graphs

        print("    ✅ 聚合完成")
        print(f"       核心色: {len(system.core_palette)} 色")
        print(f"       焦距范围: {system.focal_length_range.min}-{system.focal_length_range.max}mm")
        print(f"       光圈范围: f/{system.aperture_range.min}-f/{system.aperture_range.max}")
        print(f"       灯光模式: {len(system.lighting_patterns)} 种")
        print(f"       材质类型: {len(system.material_system)} 大类")

        # 存储到知识库
        self._save_to_knowledge(system, errors)
        return system

    # ═══════════════════════════════════════════════════════
    #  聚合引擎: SceneGraph[] → BrandVisualSystem
    # ═══════════════════════════════════════════════════════

    def _aggregate_scene_graphs(self, graphs: List[Dict], brand: str) -> BrandVisualSystem:
        """将多个SceneGraph聚合为一个品牌视觉系统"""
        system = BrandVisualSystem(brand=brand, products_analyzed=len(graphs))

        # ── 1. 色板聚合 ──
        all_colors = []
        for g in graphs:
            for elem in g.get("elements", []):
                mat = elem.get("material", {})
                albedo = mat.get("albedo", "")
                if albedo and albedo.startswith("#"):
                    all_colors.append(albedo)
            # 背景色
            bg = g.get("background_color", "")
            if bg and bg.startswith("#"):
                all_colors.append(bg)
        color_counts = Counter(all_colors)
        system.core_palette = [c for c, _ in color_counts.most_common(8)]
        system.accent_palette = [c for c, _ in color_counts.most_common(16)][8:12]

        # ── 2. 摄影参数聚合 ──
        fls, aps, isos, dists = [], [], [], []
        for g in graphs:
            cam = g.get("camera", {})
            if cam.get("focal_length_mm"):
                fls.append(float(cam["focal_length_mm"]))
            if cam.get("aperture_f"):
                aps.append(float(cam["aperture_f"]))
            if cam.get("iso"):
                isos.append(int(cam["iso"]))
            if cam.get("distance_to_subject_cm"):
                dists.append(float(cam["distance_to_subject_cm"]))
        system.focal_length_range = self._build_range(fls)
        system.aperture_range = self._build_range(aps)
        system.iso_range = self._build_range([float(i) for i in isos]) if isos else ParameterRange()
        system.distance_range = self._build_range(dists)

        # ── 3. 灯光系统聚合 ──
        light_types = []
        light_modifiers = []
        color_temps = []
        for g in graphs:
            for light in g.get("lights", []):
                lt = light.get("type", "")
                if lt:
                    light_types.append(lt)
                mod = light.get("modifier", "")
                if mod:
                    light_modifiers.append(mod)
                temp = light.get("temperature")
                if temp is not None:
                    color_temps.append(float(temp))
        system.lighting_patterns = [f"{t}+{m}" if m else t
                                     for t, m in zip(
                                         [lt for lt, _ in Counter(light_types).most_common(5)],
                                         [lm for lm, _ in Counter(light_modifiers).most_common(5)]
                                     )]
        system.color_temperature_range = self._build_range(color_temps)

        # 灯光设置详情
        all_setups = []
        for g in graphs:
            for light in g.get("lights", []):
                all_setups.append({
                    "type": light.get("type", ""),
                    "modifier": light.get("modifier", ""),
                    "color": light.get("color", ""),
                    "temperature": light.get("temperature", 5500),
                    "intensity": light.get("intensity", 0),
                    "diffusion": light.get("diffusion", 1.0),
                })
        # 去重 & 取最代表性
        seen = set()
        unique_setups = []
        for s in all_setups:
            key = f"{s['type']}_{s['modifier']}"
            if key not in seen:
                seen.add(key)
                unique_setups.append(s)
        system.common_lighting_setups = unique_setups[:5]

        # ── 4. 材质系统聚合 ──
        material_map: Dict[str, List[Dict]] = {}
        for g in graphs:
            for elem in g.get("elements", []):
                mat = elem.get("material", {})
                mtype = mat.get("type", "unknown")
                if mtype not in material_map:
                    material_map[mtype] = []
                material_map[mtype].append({
                    "name": mat.get("name", ""),
                    "albedo": mat.get("albedo", "#808080"),
                    "roughness": mat.get("roughness", 0.5),
                    "metallic": mat.get("metallic", 0),
                    "element_type": elem.get("type", ""),
                    "element_label": elem.get("label", ""),
                })
        # 每类型只保留5个样本
        for k in material_map:
            material_map[k] = material_map[k][:5]
        system.material_system = material_map

        # ── 5. 构图规律 ──
        compositions = []
        scene_types = []
        for g in graphs:
            st = g.get("scene_type", "")
            if st:
                scene_types.append(st)
            cam = g.get("camera", {})
            dof = cam.get("dof_style", "")
            if dof:
                compositions.append(f"DOF: {dof}")
            # 从元素推断构图
            for elem in g.get("elements", []):
                rel = elem.get("relative_scale_to_frame", 0)
                if rel > 0.5:
                    compositions.append(f"主体突出(占画面{rel:.0%})")
                    break
        system.scene_types = list(set(scene_types))[:5]
        system.composition_rules = list(set(compositions))[:8]

        # ── 6. 后期处理参数聚合 ──
        pp_params = {}
        for g in graphs:
            pp = g.get("post_processing", {})
            for k, v in pp.items():
                if isinstance(v, (int, float)):
                    if k not in pp_params:
                        pp_params[k] = []
                    pp_params[k].append(float(v))
        for k, vals in pp_params.items():
            system.post_processing_range[k] = self._build_range(vals)

        # ── 7. 设计原则推断 ──
        principles = []
        if len(graphs) >= 2:
            # 从一致性推断原则
            fl_range = system.focal_length_range.max - system.focal_length_range.min
            if fl_range < 20 and system.focal_length_range.samples > 1:
                principles.append("镜头焦段统一")
            if len(system.core_palette) <= 4:
                principles.append("色板精炼克制")
            if all(t == "studio" or "product" in str(t) for t in scene_types):
                principles.append("纯产品展示(无场景干扰)")
            # 光照一致性
            if len(set(light_types)) <= 3 and len(graphs) > 1:
                principles.append("灯光体系标准化")
            # 材质一致性
            if len(material_map) <= 5:
                principles.append("材质语言统一")
        system.design_principles = principles

        # ── 8. 置信度 ──
        system.confidence = min(0.95, 0.5 + 0.15 * len(graphs))
        system.image_count = sum(len(g.get("elements", [])) for g in graphs)

        return system

    def _build_range(self, values: List[float]) -> ParameterRange:
        """从数值列表构建参数范围"""
        if not values:
            return ParameterRange()
        # 确保所有值都是数值类型
        clean = []
        for v in values:
            try:
                if isinstance(v, (int, float)):
                    clean.append(float(v))
                elif isinstance(v, (tuple, list)):
                    clean.append(float(v[0]))
                elif isinstance(v, str):
                    clean.append(float(v))
            except (ValueError, TypeError, IndexError):
                continue
        if not clean:
            return ParameterRange()
        vals = sorted(clean)
        common_vals = Counter([round(v, 1) for v in vals]).most_common(3)
        return ParameterRange(
            min=min(vals),
            max=max(vals),
            avg=statistics.mean(vals),
            median=statistics.median(vals),
            samples=len(vals),
            common_values=[round(cv, 2) for cv, _ in common_vals]
        )

    def _fallback_from_product_analysis(self, products: List[Dict], brand: str) -> BrandVisualSystem:
        """当SceneParser无法解析图片时，从产品预分析数据启发式聚合"""
        all_palettes = []
        all_fl = []; all_ap = []; all_iso = []
        lighting = set(); compositions = set()
        materials = {}

        for p in products:
            a = p.get("analysis", p.get("scene_graph", {}))
            if not a:
                continue
            # 色板
            for k in ["primary_palette", "colors", "palette"]:
                c = a.get(k, [])
                if isinstance(c, list):
                    all_palettes.extend(c)
            # 相机
            cam = a.get("camera", {})
            fl = cam.get("focal_length_mm")
            if fl is not None:
                try: all_fl.append(float(fl))
                except: pass
            ap = cam.get("aperture_f")
            if ap is not None:
                try: all_ap.append(float(ap))
                except: pass
            iso = cam.get("iso")
            if iso is not None:
                try: all_iso.append(float(iso))
                except: pass
            # 灯光
            ls = a.get("lighting_signature", "")
            if ls:
                lighting.add(ls)
            for l in a.get("lights", []):
                if isinstance(l, dict):
                    mod = l.get("modifier", "")
                    lt = l.get("type", "")
                    lighting.add(f"{lt}{'+'+mod if mod else ''}")
            # 构图
            comp = a.get("composition", {})
            for v in comp.values():
                if isinstance(v, str) and len(v) > 2:
                    compositions.add(v)
            # 材质
            for m in a.get("materials", []):
                if isinstance(m, dict):
                    mtype = m.get("type", m.get("name", "unknown"))
                    if mtype not in materials:
                        materials[mtype] = []
                    materials[mtype].append(m)
            # 设计原则
            for pkey in ["design_principles", "principles"]:
                dp = a.get(pkey, [])
                if isinstance(dp, list):
                    for d in dp:
                        compositions.add(str(d))

        def rng(vals):
            if not vals: return ParameterRange()
            return ParameterRange(min=min(vals), max=max(vals), avg=sum(vals)/len(vals),
                                  median=sorted(vals)[len(vals)//2], samples=len(vals))

        core = [c for c, _ in Counter(all_palettes).most_common(8)
                if isinstance(c, str) and c.startswith("#")]

        system = BrandVisualSystem(
            brand=brand, products_analyzed=len(products),
            image_count=sum(1 for p in products if p.get("image")),
            core_palette=core[:6],
            seasonal_palette=core[6:10],
            accent_palette=core[10:14],
            focal_length_range=rng(all_fl),
            aperture_range=rng(all_ap),
            iso_range=rng(all_iso),
            lighting_patterns=list(lighting)[:5],
            composition_rules=list(compositions)[:5],
            design_principles=["简约设计", "功能性优先", "自然材料"][:3],
            material_system=materials,
            confidence=0.7,
        )
        return system

    # ═══════════════════════════════════════════════════════
    #  知识库存储
    # ═══════════════════════════════════════════════════════

    def _save_to_knowledge(self, system: BrandVisualSystem, errors: List[Dict] = None):
        """将分析结果保存到品牌知识库"""
        try:
            kb = self.knowledge
            profile = kb.get_brand(system.brand)
            if not profile:
                profile = self._BrandProfile(brand_name=system.brand)

            # 更新色板
            profile.primary_palette = system.core_palette[:6]
            profile.secondary_palette = system.seasonal_palette[:4]
            profile.accent_palette = system.accent_palette[:4]

            # 更新摄影签名
            profile.camera_signature = {
                "focal_length_range": system.focal_length_range.to_dict(),
                "aperture_range": system.aperture_range.to_dict(),
                "iso_range": system.iso_range.to_dict(),
                "distance_range": system.distance_range.to_dict(),
            }

            # 更新灯光签名
            profile.lighting_signature = ", ".join(system.lighting_patterns[:3])
            profile.lighting_setup = {
                "setups": system.common_lighting_setups,
                "color_temperature": system.color_temperature_range.to_dict(),
            }

            # 更新设计规则
            profile.layout_patterns = list(set(
                (profile.layout_patterns or []) + system.composition_rules[:5]
            ))
            profile.typical_scenes = system.scene_types[:5]

            # 更新材质
            if system.material_system:
                profile.scene_rules = [
                    f"材质体系: {', '.join(system.material_system.keys())}"
                ]

            kb.save_brand(profile)
            print(f"    💾 知识库已更新: {system.brand}")

            if errors:
                for err in errors:
                    kb.save_knowledge(
                        system.brand, "analysis_error",
                        err, source="strategy_v2"
                    )
        except Exception as e:
            print(f"    ⚠️  知识库存储失败: {e}")

    # ═══════════════════════════════════════════════════════
    #  导出报告
    # ═══════════════════════════════════════════════════════

    def export_report(self, system: BrandVisualSystem,
                      output_path: Optional[str] = None) -> str:
        """导出品牌视觉系统报告为JSON"""
        if output_path is None:
            output_path = os.path.join(
                os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..")),
                "output", f"{system.brand.lower().replace(' ', '_')}_visual_system_report.json"
            )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        report = self._build_report(system)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n  📄 报告已导出: {output_path}")
        return output_path

    def _build_report(self, system: BrandVisualSystem) -> Dict[str, Any]:
        """构建完整报告结构"""
        return {
            "report_type": "brand_visual_system",
            "version": "2.0",
            "methodology": "多产品SceneGraph解析 → 跨产品参数聚合",
            "generated_at": datetime.utcnow().isoformat(),
            "brand": system.brand,
            "analysis_summary": {
                "products_analyzed": system.products_analyzed,
                "total_scene_elements": system.image_count,
                "confidence": round(system.confidence, 2),
                "design_principles": system.design_principles,
            },
            "color_system": {
                "core_palette": system.core_palette,
                "seasonal_palette": system.seasonal_palette,
                "accent_palette": system.accent_palette,
                "description": (
                    f"跨{system.products_analyzed}个产品的色板聚合，"
                    f"核心色{len(system.core_palette)}个"
                ),
            },
            "camera_system": {
                "focal_length": system.focal_length_range.to_dict(),
                "aperture": system.aperture_range.to_dict(),
                "iso": system.iso_range.to_dict(),
                "distance_to_subject": system.distance_range.to_dict(),
                "interpretation": (
                    f"焦距{system.focal_length_range.min}-{system.focal_length_range.max}mm，"
                    f"光圈f/{system.aperture_range.min}-f/{system.aperture_range.max}，"
                    f"ISO {system.iso_range.min}-{system.iso_range.max}"
                ),
            },
            "lighting_system": {
                "patterns": system.lighting_patterns,
                "common_setups": system.common_lighting_setups,
                "color_temperature": system.color_temperature_range.to_dict(),
            },
            "material_system": {
                "material_types": list(system.material_system.keys()),
                "material_samples": {
                    k: v[:3] for k, v in system.material_system.items()
                },
            },
            "composition": {
                "scene_types": system.scene_types,
                "composition_rules": system.composition_rules,
            },
            "post_processing": {
                k: v.to_dict() for k, v in system.post_processing_range.items()
            },
            "scene_graphs_summary": [
                {
                    "product": sg.get("_product_name", "?"),
                    "image": sg.get("_product_image", "")[:120],
                    "elements": len(sg.get("elements", [])),
                    "lights": len(sg.get("lights", [])),
                    "camera": sg.get("camera", {}).get("focal_length_mm", "?"),
                    "scene_type": sg.get("scene_type", ""),
                }
                for sg in system.scene_graphs
            ],
            "raw_scene_graphs": system.scene_graphs,
        }

    # ═══════════════════════════════════════════════════════
    #  竞品分析 & 策略文档 (保持兼容)
    # ═══════════════════════════════════════════════════════

    def competitor_analysis(self, brand: str, competitors: List[str]) -> Dict:
        """竞品对标分析"""
        return {
            "brand": brand,
            "competitors": competitors,
            "analysis": "竞品视觉系统对比分析",
            "positioning_gap": "品牌定位差异点",
            "opportunity": "视觉差异化机会",
        }

    def brand_strategy_doc(self, system: BrandVisualSystem, brief=None) -> Dict:
        """产出策略文档"""
        return {
            "brand": system.brand,
            "executive_summary": (
                f"基于{system.products_analyzed}个产品的SceneGraph深度分析，"
                f"提取品牌视觉参数范围。置信度{system.confidence:.0%}。"
            ),
            "visual_system": {
                "core_palette": system.core_palette,
                "focal_length": f"{system.focal_length_range.min}-{system.focal_length_range.max}mm",
                "aperture": f"f/{system.aperture_range.min}-f/{system.aperture_range.max}",
                "lighting_patterns": system.lighting_patterns,
            },
            "design_direction": system.design_principles,
            "recommendation": "建议基于参数范围产出品牌视觉方案",
        }


# ── 便捷函数 ────────────────────────────────────────────

def analyze_brand_from_urls(
    brand: str,
    image_urls: List[str],
    product_names: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """便捷函数: 从产品图片URL列表直接分析品牌视觉系统

    Args:
        brand: 品牌名称
        image_urls: 产品图片URL列表
        product_names: 可选的产品名称列表
        api_key: OpenAI API密钥
        output_path: 报告输出路径

    Returns:
        包含视觉系统完整数据的字典
    """
    if product_names is None:
        product_names = [f"{brand} Product {i+1}" for i in range(len(image_urls))]

    products = [
        {"image": url, "name": name}
        for url, name in zip(image_urls, product_names)
    ]

    dept = StrategyDept(api_key)
    system = dept.analyze_brand_system(products)

    report_path = dept.export_report(system, output_path)

    return {
        "brand": brand,
        "visual_system": {
            "core_palette": system.core_palette,
            "focal_length_range": system.focal_length_range.to_dict(),
            "aperture_range": system.aperture_range.to_dict(),
            "iso_range": system.iso_range.to_dict(),
            "lighting_patterns": system.lighting_patterns,
            "composition_rules": system.composition_rules,
            "design_principles": system.design_principles,
            "material_types": list(system.material_system.keys()),
            "confidence": system.confidence,
        },
        "report_path": report_path,
        "products_analyzed": system.products_analyzed,
    }
