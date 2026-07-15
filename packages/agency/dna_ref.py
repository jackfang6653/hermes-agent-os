"""
品牌DNA参考系统 — AI设计师可查询的品牌规则库

核心价值:
- 积累的品牌知识可以被后续AI设计师查询和复用
- 每个设计决策都记录了WHY
- 设计师可以问:"IKEA通常用什么焦距？为什么？"
- 自动回答参数 + 理由 + 可参照的规则

查询方式:
    ref = BrandDNARef()
    rules = ref.query("NORHOR", "camera")
    # → [{"参数": "85mm", "理由": "..."}]
"""
import os
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime


class BrandDNARef:
    """品牌DNA参考系统 — AI设计师知识库"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", "brand_dna_ref.db")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS brand_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                category TEXT NOT NULL,       -- camera/lighting/color/composition/material
                parameter TEXT NOT NULL,       -- focal_length/aperture/roughness
                value_range TEXT,              -- "35-85mm"
                typical_value TEXT,            -- "50mm"
                why TEXT,                      -- 为什么选这个值
                brand_strategy TEXT,           -- 关联品牌策略
                psychological_effect TEXT,     -- 心理效果
                alternatives TEXT,             -- 替代方案
                confidence REAL DEFAULT 0.7,
                source_product TEXT,
                created_at TEXT,
                use_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS brand_philosophy (
                brand TEXT PRIMARY KEY,
                design_philosophy TEXT,
                brand_dna_summary TEXT,
                key_takeaways TEXT,
                total_analyses INTEGER DEFAULT 0,
                last_updated TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_rules_query ON brand_rules(brand, category);
        """)
        self._conn.commit()

    # ── 存储 ──────────────────────────────────────────

    def store_rationale(self, brand: str, rationale_report) -> int:
        """存储设计理由报告到可查询数据库"""
        now = datetime.utcnow().isoformat()
        count = 0
        
        # 从dataclass提取items
        categories = [
            ("camera", getattr(rationale_report, 'camera_rationale', [])),
            ("lighting", getattr(rationale_report, 'lighting_rationale', [])),
            ("color", getattr(rationale_report, 'color_rationale', [])),
            ("composition", getattr(rationale_report, 'composition_rationale', [])),
            ("material", getattr(rationale_report, 'material_rationale', [])),
        ]
        
        for cat, items in categories:
            for item in items:
                if hasattr(item, 'parameter') and item.parameter:
                    self._conn.execute(
                        "INSERT INTO brand_rules (brand,category,parameter,value_range,typical_value,why,brand_strategy,psychological_effect,alternatives,confidence,source_product,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (brand, cat, item.parameter, item.value, item.value,
                         getattr(item, 'why', ''), getattr(item, 'brand_strategy_link', ''),
                         getattr(item, 'psychological_effect', ''),
                         json.dumps(getattr(item, 'alternative_options', []), ensure_ascii=False),
                         getattr(item, 'confidence', 0.7), '', now)
                    )
                    count += 1
        
        # 品牌哲学
        summary = getattr(rationale_report, 'brand_dna_summary', '')
        philosophy = getattr(rationale_report, 'design_philosophy', '')
        takeaways = getattr(rationale_report, 'key_takeaways', [])
        if summary or philosophy:
            self._conn.execute(
                "INSERT OR REPLACE INTO brand_philosophy (brand,design_philosophy,brand_dna_summary,key_takeaways,total_analyses,last_updated) VALUES (?,?,?,?,COALESCE((SELECT total_analyses FROM brand_philosophy WHERE brand=?),0)+1,?)",
                (brand, philosophy, summary, json.dumps(takeaways, ensure_ascii=False), brand, now)
            )
        
        self._conn.commit()
        return count

    # ── 查询 ──────────────────────────────────────────

    def query(self, brand: str, category: Optional[str] = None, 
              parameter: Optional[str] = None) -> List[Dict]:
        """查询品牌DNA规则 — AI设计师可调用"""
        sql = "SELECT * FROM brand_rules WHERE brand=?"
        params = [brand]
        if category:
            sql += " AND category=?"
            params.append(category)
        if parameter:
            sql += " AND parameter=?"
            params.append(parameter)
        sql += " ORDER BY use_count DESC, confidence DESC"
        
        rows = self._conn.execute(sql, params).fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0], "brand": r[1], "category": r[2], "parameter": r[3],
                "value": r[4] or r[5], "typical": r[5],
                "why": r[6], "strategy": r[7], "psychology": r[8],
                "alternatives": json.loads(r[9]) if r[9] else [],
                "confidence": r[10],
            })
        return results

    def get_philosophy(self, brand: str) -> Dict:
        """获取品牌设计哲学"""
        row = self._conn.execute(
            "SELECT * FROM brand_philosophy WHERE brand=?", (brand,)
        ).fetchone()
        if row:
            return {
                "brand": row[0], "philosophy": row[1], "dna_summary": row[2],
                "takeaways": json.loads(row[3]) if row[3] else [],
                "total_analyses": row[4], "last_updated": row[5],
            }
        return {}

    def search(self, query_text: str) -> List[Dict]:
        """全文搜索 — 搜索所有品牌的知识"""
        rows = self._conn.execute(
            "SELECT * FROM brand_rules WHERE why LIKE ? OR brand_strategy LIKE ? LIMIT 20",
            (f"%{query_text}%", f"%{query_text}%")
        ).fetchall()
        return [{"brand": r[1], "parameter": r[3], "why": r[6][:100]} for r in rows]

    def list_brands(self) -> List[str]:
        rows = self._conn.execute("SELECT DISTINCT brand FROM brand_rules ORDER BY brand").fetchall()
        return [r[0] for r in rows]

    def get_designer_reference(self, brand: str) -> str:
        """给AI设计师看的品牌参考摘要"""
        rules = self.query(brand)
        philosophy = self.get_philosophy(brand)
        
        lines = [f"## {brand} 品牌设计参考\n"]
        if philosophy:
            lines.append(f"**设计哲学**: {philosophy.get('philosophy','')}")
            lines.append(f"**DNA摘要**: {philosophy.get('dna_summary','')}\n")
        
        for cat in ["camera", "lighting", "color", "composition", "material"]:
            cat_rules = [r for r in rules if r["category"] == cat]
            if cat_rules:
                lines.append(f"\n### {cat.upper()}")
                for r in cat_rules[:3]:
                    lines.append(f"- **{r['parameter']}**: {r['value']}")
                    lines.append(f"  WHY: {r['why'][:80]}...")
                    if r['psychology']:
                        lines.append(f"  心理效果: {r['psychology'][:60]}...")
        
        return "\n".join(lines)

    def close(self):
        self._conn.close()
