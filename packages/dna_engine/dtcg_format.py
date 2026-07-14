"""
W3C DTCG Design Tokens Format — 2025.10 标准实现

将品牌DNA参数转换为标准W3C设计令牌格式
支持跨工具互操作（Figma/Adobe/代码）
"""
import json, os, uuid
from typing import Optional, Dict, Any, List
from datetime import datetime


def dtcg_wrap(value: Any, token_type: str, description: str = "",
              extensions: Optional[Dict] = None) -> Dict:
    """创建一个W3C DTCG格式的设计令牌"""
    token = {
        "$value": value,
        "$type": token_type,
        "$description": description,
    }
    if extensions:
        token["$extensions"] = extensions
    return token


class DTCGBuilder:
    """W3C DTCG 设计令牌构建器 — 从品牌DNA生成标准令牌"""

    # DTCG 2025.10 支持的类型
    TYPES = {
        "color", "dimension", "fontFamily", "fontWeight", "duration",
        "cubicBezier", "number", "string", "strokeStyle",
        "border", "transition", "shadow", "gradient", "typography",
    }

    def __init__(self, brand_name: str, version: str = "V1.0"):
        self.brand = brand_name
        self.version = version
        self.tokens: Dict[str, Any] = {
            "$metadata": {
                "version": version,
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "Hermes Agent OS Brand DNA Engine",
                "source_brand": brand_name,
            }
        }

    def add_color(self, path: str, hex_val: str, description: str = "",
                  role: str = "") -> "DTCGBuilder":
        """添加颜色令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        token = dtcg_wrap(hex_val, "color", description)
        if role:
            token["$extensions"] = {"brand.role": role}
        current[parts[-1]] = token
        return self

    def add_dimension(self, path: str, value: float, unit: str = "px",
                      description: str = "") -> "DTCGBuilder":
        """添加尺寸令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(f"{value}{unit}", "dimension", description)
        return self

    def add_font(self, path: str, font_name: str, description: str = "") -> "DTCGBuilder":
        """添加字体令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(font_name, "fontFamily", description)
        return self

    def add_typography(self, path: str, font_size: str, font_family: str,
                       line_height: str, font_weight: str, tracking: str = "",
                       description: str = "") -> "DTCGBuilder":
        """添加排版令牌"""
        value = {
            "fontSize": font_size,
            "fontFamily": font_family,
            "lineHeight": line_height,
            "fontWeight": font_weight,
        }
        if tracking:
            value["tracking"] = tracking
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(value, "typography", description)
        return self

    def add_shadow(self, path: str, shadow_value: Dict, description: str = "") -> "DTCGBuilder":
        """添加阴影令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(shadow_value, "shadow", description)
        return self

    def add_border(self, path: str, border_value: Dict, description: str = "") -> "DTCGBuilder":
        """添加边框令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(border_value, "border", description)
        return self

    def add_group(self, path: str, description: str = "") -> "DTCGBuilder":
        """添加令牌分组"""
        parts = path.split(".")
        current = self.tokens
        for p in parts:
            if p not in current:
                current[p] = {}
            current = current[p]
        if description:
            current["$description"] = description
        return self

    def add_numeric(self, path: str, value: float, description: str = "") -> "DTCGBuilder":
        """添加数值令牌"""
        parts = path.split(".")
        current = self.tokens
        for p in parts[:-1]:
            if p not in current:
                current[p] = {}
            current = current[p]
        current[parts[-1]] = dtcg_wrap(value, "number", description)
        return self

    def from_brand_profile(self, profile: Dict) -> "DTCGBuilder":
        """从品牌配置文件批量构建令牌"""
        # Color system
        for role, hex_val in [("primary", ""), ("secondary", ""), ("accent", "")]:
            val = profile.get(f"{role}_palette", profile.get(f"{role}", []))
            if isinstance(val, list) and val:
                self.add_color(f"color.{role}", val[0], f"Brand {role} color", role)
            elif isinstance(val, str):
                self.add_color(f"color.{role}", val, f"Brand {role} color", role)

        # Typography
        typo = profile.get("typography", {})
        if typo:
            families = typo.get("font_families", typo.get("families", {}))
            if isinstance(families, dict):
                for k, v in families.items():
                    self.add_font(f"fontFamily.{k}", v)

        # Spacing
        spacing = profile.get("spacing", {})
        if spacing:
            base = spacing.get("base_unit", spacing.get("base", 8))
            self.add_dimension("spacing.base", base, "px")

        return self

    def to_json(self, indent: int = 2) -> str:
        """输出标准DTCG JSON"""
        return json.dumps(self.tokens, ensure_ascii=False, indent=indent)

    def to_dict(self) -> Dict:
        return self.tokens

    def save(self, filepath: str):
        """保存到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return filepath


# ── 快速测试 ──────────────────────────────────────────
def demo():
    builder = DTCGBuilder("NORHOR", "V1.0")
    builder \
        .add_color("color.primary", "#f5f0e8", "品牌主色") \
        .add_color("color.secondary", "#d4c5b0", "品牌辅色") \
        .add_color("color.accent", "#8b7355", "品牌强调色") \
        .add_color("color.surface.background", "#faf9f7", "背景色") \
        .add_color("color.surface.card", "#ffffff", "卡片色") \
        .add_color("color.text.primary", "#2c2c2c", "主要文字色") \
        .add_color("color.text.muted", "#8b7355", "次要文字色") \
        .add_dimension("spacing.base", 8, "px", "基础间距") \
        .add_dimension("spacing.section", 48, "px", "区块间距") \
        .add_dimension("layout.maxWidth", 1200, "px", "最大内容宽度") \
        .add_dimension("shape.radius.small", 4, "px", "小圆角") \
        .add_dimension("shape.radius.large", 12, "px", "大圆角") \
        .add_font("fontFamily.heading", "Noto Sans SC", "标题字体") \
        .add_font("fontFamily.body", "Noto Sans SC", "正文字体") \
        .add_typography("typography.heading1", "48px", "Noto Sans SC", "1.2", "700", "0.02em") \
        .add_typography("typography.body", "22px", "Noto Sans SC", "1.6", "400") \
        .add_shadow("elevation.low", {"offsetX": "0px", "offsetY": "2px", "blur": "8px", "color": "rgba(0,0,0,0.08)"}) \
        .add_numeric("opacity.high", 0.85) \
        .add_numeric("opacity.medium", 0.60)
    return builder


if __name__ == "__main__":
    b = demo()
    print(b.to_json(indent=2))
