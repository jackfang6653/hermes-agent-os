"""
Hermes OS — 统一知识库 (单数据库替代5个分散库)

合并:
- knowledge/brand_knowledge.db  (品牌档案)
- knowledge/design_patterns.db  (设计模式)
- dna_engine/brand_db.py       (DNA条目)
- dna_engine/dna_database.py   (DTCG令牌)
- agency/dna_ref.py            (参考数据)
"""
import os, json, sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime


class UnifiedKnowledge:
    """统一品牌知识库 — 单数据库"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "unified_brand.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """初始化所有表"""
        self.conn.executescript("""
            -- 品牌档案
            CREATE TABLE IF NOT EXISTS brands (
                name TEXT PRIMARY KEY,
                category TEXT,
                profile TEXT,
                research_count INTEGER DEFAULT 0,
                last_researched TEXT,
                confidence REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );
            -- 设计知识
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                knowledge_type TEXT NOT NULL,
                content TEXT,
                source TEXT,
                created_at TEXT
            );
            -- 设计模式
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                category TEXT,
                description TEXT,
                rationale TEXT,
                parameters TEXT,
                tags TEXT,
                confidence REAL,
                use_count INTEGER DEFAULT 0,
                created_at TEXT
            );
            -- 设计令牌 (DTCG)
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                token_type TEXT,
                token_name TEXT,
                token_value TEXT,
                dtcg_path TEXT,
                created_at TEXT
            );
            -- 质量门禁
            CREATE TABLE IF NOT EXISTS quality_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT,
                gate_name TEXT,
                passed INTEGER,
                score REAL,
                details TEXT,
                created_at TEXT
            );
            -- 4A案例
            CREATE TABLE IF NOT EXISTS agency_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency TEXT,
                brand TEXT,
                project_name TEXT,
                design_rationale TEXT,
                strategic_thinking TEXT,
                color_palette TEXT,
                layout_patterns TEXT,
                confidence REAL,
                created_at TEXT
            );
            -- 进化日志
            CREATE TABLE IF NOT EXISTS evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_type TEXT,
                summary TEXT,
                details TEXT,
                created_at TEXT
            );
        """)
        self.conn.commit()

    # ── 品牌档案 ──

    def save_brand(self, name: str, category: str = "", profile: Optional[Dict] = None):
        now = datetime.utcnow().isoformat()
        existing = self.conn.execute("SELECT research_count FROM brands WHERE name=?", (name,)).fetchone()
        count = (existing[0] if existing else 0) + 1
        self.conn.execute(
            "INSERT OR REPLACE INTO brands (name,category,profile,research_count,last_researched,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (name, category, json.dumps(profile or {}, ensure_ascii=False), count, now, now, now))
        self.conn.commit()

    def get_brand(self, name: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM brands WHERE name=?", (name,)).fetchone()
        if row:
            return {"name": row[0], "category": row[1], "profile": json.loads(row[2]),
                    "research_count": row[3], "confidence": row[5]}
        return None

    def list_brands(self) -> List[Dict]:
        rows = self.conn.execute("SELECT name, category, research_count FROM brands ORDER BY research_count DESC").fetchall()
        return [{"name": r[0], "category": r[1], "research_count": r[2]} for r in rows]

    # ── 设计知识 ──

    def save_knowledge(self, brand: str, ktype: str, content: Any, source: str = ""):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO knowledge (brand, knowledge_type, content, source, created_at) VALUES (?,?,?,?,?)",
            (brand, ktype, json.dumps(content, ensure_ascii=False), source, now))
        self.conn.commit()

    def get_knowledge(self, brand: str, ktype: Optional[str] = None) -> List[Dict]:
        if ktype:
            rows = self.conn.execute(
                "SELECT * FROM knowledge WHERE brand=? AND knowledge_type=? ORDER BY created_at DESC", (brand, ktype)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM knowledge WHERE brand=? ORDER BY created_at DESC", (brand,)).fetchall()
        return [{"id": r[0], "brand": r[1], "type": r[2], "content": json.loads(r[3]),
                 "source": r[4], "created_at": r[5]} for r in rows]

    # ── 设计模式 ──

    def save_pattern(self, name: str, category: str, description: str, rationale: str = "",
                     parameters: Optional[Dict] = None, tags: Optional[List] = None,
                     confidence: float = 0.5):
        now = datetime.utcnow().isoformat()
        try:
            self.conn.execute(
                "INSERT INTO patterns (name,category,description,rationale,parameters,tags,confidence,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (name, category, description, rationale,
                 json.dumps(parameters or {}), json.dumps(tags or []), confidence, now))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def search_patterns(self, category: Optional[str] = None, tag: Optional[str] = None, query: str = "") -> List[Dict]:
        sql = "SELECT * FROM patterns WHERE 1=1"
        params = []
        if category:
            sql += " AND category=?"
            params.append(category)
        if tag:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        sql += " ORDER BY use_count DESC, confidence DESC"
        return [self._row_dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def seed_patterns(self):
        """种子设计模式"""
        defaults = [
            ("Z型视觉流", "layout", "Z型布局引导视线: 左上→右上→左下→右下",
             "用户阅读习惯从左到右", {"reading_pattern": "z_shape"}, ["ecommerce"], 0.9),
            ("三分法构图", "composition", "产品位于三分之一位置",
             "创造视觉平衡", {"rule": "rule_of_thirds"}, ["photography"], 0.9),
            ("暖调自然光", "lighting", "4500K自然光+暖色反光板",
             "营造温馨高级感", {"key_temperature": 4500}, ["warm"], 0.8),
            ("三角补色", "color", "主色+两个补色邻近色",
             "创造视觉活力", {"rule": "triadic"}, ["color_theory"], 0.85),
        ]
        for d in defaults:
            self.save_pattern(*d)

    # ── 4A案例 ──

    def save_agency_case(self, agency: str, brand: str, project: str,
                          rationale: str = "", strategy: str = "",
                          palette: Optional[List] = None, patterns: Optional[List] = None,
                          confidence: float = 0.0):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO agency_cases (agency,brand,project_name,design_rationale,strategic_thinking,color_palette,layout_patterns,confidence,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (agency, brand, project, rationale, strategy,
             json.dumps(palette or []), json.dumps(patterns or []), confidence, now))
        self.conn.commit()

    def list_agency_cases(self, limit: int = 10) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM agency_cases ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r[0], "agency": r[1], "brand": r[2], "project": r[3],
                 "rationale": r[4][:100] if r[4] else ""} for r in rows]

    # ── 工具箱 ──

    def _row_dict(self, r) -> Dict:
        return {"id": r[0], "name": r[1], "category": r[2], "description": r[3],
                "rationale": r[4], "parameters": json.loads(r[5]) if r[5] else {},
                "tags": json.loads(r[6]) if r[6] else [], "confidence": r[7],
                "use_count": r[8]}

    def stats(self) -> Dict[str, int]:
        return {
            "brands": self.conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
            "knowledge": self.conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0],
            "patterns": self.conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0],
            "tokens": self.conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
            "agency_cases": self.conn.execute("SELECT COUNT(*) FROM agency_cases").fetchone()[0],
            "evolution_log": self.conn.execute("SELECT COUNT(*) FROM evolution_log").fetchone()[0],
        }

    def close(self):
        self.conn.close()
