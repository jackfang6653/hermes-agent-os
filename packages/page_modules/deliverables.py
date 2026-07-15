"""
标准化交付物产出 — 6 套研究成果文档生成器

模块6按文档要求产出:
1. Element parameter disassembled data sheet  (.json)
2. Design cause traceability analysis report    (.md)
3. Category unified design specification manual (.md)
4. Brand tone research & visual system report   (.md)
5. ACR histogram tone preset library            (.json)
6. Knowledge base iteration version log         (.md)

输出: 每个文档同时有 Markdown + JSON 两种格式
"""
import os
import json
import zipfile
import io
from typing import Optional, Dict, Any, List
from datetime import datetime


class DeliverablesGenerator:
    """6 套标准化交付物生成器"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self, brand_name: str, research_results: Dict[int, Any],
                     category: str = "furniture", version: str = "V1.0") -> str:
        """生成全部6套文档，返回ZIP包路径"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.output_dir, f"{brand_name}_{version}_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)

        docs = {}

        # 1. Element parameter data sheet
        docs["element_parameters"] = self._build_element_sheet(research_results)
        self._write_json(session_dir, "element_parameters.json", docs["element_parameters"])
        
        # 2. Design rationale report
        docs["design_rationale"] = self._build_rationale_report(research_results)
        self._write_md(session_dir, "design_rationale.md", docs["design_rationale"])
        
        # 3. Category specification manual
        docs["category_spec"] = self._build_category_spec(research_results, category)
        self._write_md(session_dir, "category_specification.md", docs["category_spec"])
        
        # 4. Brand visual system report
        docs["brand_visual"] = self._build_brand_visual(research_results, brand_name)
        self._write_md(session_dir, "brand_visual_system.md", docs["brand_visual"])
        
        # 5. ACR preset library
        docs["acr_presets"] = self._build_acr_presets(research_results)
        self._write_json(session_dir, "acr_presets.json", docs["acr_presets"])
        
        # 6. Iteration log
        docs["iteration_log"] = self._build_iteration_log(version)
        self._write_md(session_dir, "iteration_log.md", docs["iteration_log"])

        # 打包ZIP
        zip_path = os.path.join(self.output_dir, f"{brand_name}_{version}_deliverables.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(session_dir):
                fpath = os.path.join(session_dir, fname)
                zf.write(fpath, fname)
        
        # 写入 summary JSON
        summary = {
            "brand": brand_name, "category": category, "version": version,
            "generated_at": datetime.utcnow().isoformat(),
            "deliverables": list(docs.keys()),
            "modules_completed": len(research_results),
        }
        self._write_json(session_dir, "summary.json", summary)

        print(f"  📦 交付物ZIP: {zip_path}")
        return zip_path

    def _write_json(self, base: str, name: str, data: dict):
        path = os.path.join(base, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_md(self, base: str, name: str, content: str):
        path = os.path.join(base, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _extract_data(self, results: Dict[int, Any], module_id: int) -> dict:
        """从研究结果中提取结构化数据"""
        r = results.get(module_id)
        if r and hasattr(r, 'structured_data') and r.structured_data:
            return r.structured_data
        if r and hasattr(r, 'raw_output') and r.raw_output:
            try:
                start = r.raw_output.index("{")
                end = r.raw_output.rindex("}") + 1
                return json.loads(r.raw_output[start:end])
            except:
                return {"raw": r.raw_output[:500]}
        return {}

    def _build_element_sheet(self, results: dict) -> dict:
        m1 = self._extract_data(results, 1)
        self._extract_data(results, 5)
        return {
            "document_type": "Element Parameter Disassembled Data Sheet",
            "source_modules": {"element_analysis": "M1", "iteration_data": "M5"},
            "elements": m1.get("elements", m1.get("parameters", m1)),
            "total_elements": len(m1.get("elements", m1.get("parameters", []))),
            "acr_histogram_bindings": m1.get("acr", m1.get("histogram", {})),
            "dependency_relationships": m1.get("dependencies", m1.get("relationships", [])),
        }

    def _build_rationale_report(self, results: dict) -> str:
        m2 = self._extract_data(results, 2)
        m1 = self._extract_data(results, 1)
        elements = m1.get("elements", [])
        
        md = f"""# Design Cause Traceability Analysis Report
Generated: {datetime.utcnow().isoformat()}

## Overview
Analyzed {len(elements)} elements across 6 dimensions:
1. Product Attribute
2. Visual Balance
3. Consumer Psychology
4. Scene Atmosphere
5. Brand Tone
6. E-commerce Conversion

## Element-by-Element Analysis
"""
        if isinstance(elements, list):
            for i, el in enumerate(elements[:20]):  # limit to 20
                name = el.get("name", el.get("id", f"Element_{i+1}"))
                md += f"\n### {i+1}. {name}\n"
                for dim in ["product_attribute", "visual_balance", "psychology",
                            "scene", "brand_tone", "conversion"]:
                    rationale = el.get(dim) or el.get(f"why_{dim}", "")
                    if rationale:
                        md += f"- **{dim.replace('_',' ').title()}**: {rationale}\n"

        # 添加从 M2 提取的规则
        rules = m2.get("design_rules", m2.get("rules", []))
        if rules:
            md += "\n## Extracted Design Rules\n"
            for r in rules:
                if isinstance(r, dict):
                    md += f"- **{r.get('rule', r.get('name',''))}**: {r.get('rationale', r.get('why',''))}\n"
                else:
                    md += f"- {r}\n"

        md += f"\n## 6-Dimension Analysis Summary\n```json\n{json.dumps(m2, ensure_ascii=False, indent=2)[:2000]}\n```\n"
        return md

    def _build_category_spec(self, results: dict, category: str) -> str:
        m3 = self._extract_data(results, 3)
        mandatory = m3.get("mandatory_rules", m3.get("fixed_rules", []))
        optional = m3.get("optional_rules", m3.get("variable_rules", []))
        
        md = f"""# Category Unified Design Specification Manual
Category: {category}
Generated: {datetime.utcnow().isoformat()}

## 1. Mandatory Fixed Rules
"""
        if isinstance(mandatory, list):
            for r in mandatory:
                md += f"- {r if isinstance(r, str) else r.get('rule', str(r))}\n"
        else:
            md += f"{mandatory}\n"

        md += "\n## 2. Optional Variable Rules\n"
        if isinstance(optional, list):
            for r in optional:
                md += f"- {r if isinstance(r, str) else r.get('rule', str(r))}\n"
        else:
            md += f"{optional}\n"

        md += f"\n## 3. Complete Specification\n```json\n{json.dumps(m3, ensure_ascii=False, indent=2)[:3000]}\n```\n"
        return md

    def _build_brand_visual(self, results: dict, brand: str) -> str:
        m4 = self._extract_data(results, 4)
        m2 = self._extract_data(results, 2)
        
        color_system = m4.get("color_system", m4.get("brand_colors", {}))
        if not color_system:
            color_system = m2.get("color_system", {})
        
        md = f"""# Brand Visual System Research Report
Brand: {brand}
Generated: {datetime.utcnow().isoformat()}

## Brand DNA
"""
        for key in ["style_orientation", "target_audience", "visual_dna",
                     "color_system", "tone_preference", "composition_habit",
                     "material_tendency", "font_tone", "layout_style",
                     "scene_atmosphere", "differentiation"]:
            val = m4.get(key, "")
            if val:
                md += f"\n### {key.replace('_',' ').title()}\n{val}\n"

        md += f"\n## Complete Report\n```json\n{json.dumps(m4, ensure_ascii=False, indent=2)[:3000]}\n```\n"
        return md

    def _build_acr_presets(self, results: dict) -> dict:
        m1 = self._extract_data(results, 1)
        m5 = self._extract_data(results, 5)
        
        acr = m1.get("acr", m1.get("histogram", {}))
        if not acr:
            acr = m5.get("acr_presets", {})
        
        return {
            "document_type": "ACR Histogram Tone Preset Library",
            "version": "V1.0",
            "presets": {
                "module_default": acr,
                "recommended_range": acr,
            },
            "compatibility": "Adobe Camera Raw / Lightroom",
            "parameters": acr,
        }

    def _build_iteration_log(self, version: str) -> str:
        return f"""# Knowledge Base Iteration Version Log
Version: {version}
Generated: {datetime.utcnow().isoformat()}

## Change History
| Version | Date | Changes |
|---------|------|---------|
| {version} | {datetime.now().strftime('%Y-%m-%d')} | Initial brand research & design rule extraction |

## Current Status
- Total brands in knowledge base: N/A
- Total patterns in library: N/A
- Total categories analyzed: N/A
- Average confidence: N/A

## Next Iteration Goals
- Expand category coverage
- Increase sample diversity
- Validate rules against more cases
- Merge with trend tracker findings
"""
