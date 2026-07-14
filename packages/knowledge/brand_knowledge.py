"""
品牌知识库 — 结构化存储所有品牌研究成果

存储内容：
1. 品牌基本信息（定位/受众/调性）
2. 色彩系统（色板/关系/心理学）
3. 版式规则（网格/层级/留白）
4. 场景规则（构成/配饰/灯光）
5. 设计模式库
6. 设计理念（WHY）

每个品牌有完整档案，支持查询和复用
"""
import os, json, sqlite3, time
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BrandProfile:
    """品牌完整档案"""
    brand_name: str
    category: str = ""
    
    # 品牌定位
    brand_positioning: str = ""
    target_audience: str = ""
    brand_personality: List[str] = field(default_factory=list)
    brand_voice: str = ""
    competitive_advantage: str = ""
    
    # 视觉系统
    primary_palette: List[str] = field(default_factory=list)
    secondary_palette: List[str] = field(default_factory=list)
    accent_palette: List[str] = field(default_factory=list)
    color_psychology: str = ""
    color_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # 版式系统
    grid_system: str = ""
    typography: Dict[str, Any] = field(default_factory=dict)
    layout_patterns: List[str] = field(default_factory=list)
    whitespace_philosophy: str = ""
    
    # 场景系统
    typical_scenes: List[str] = field(default_factory=list)
    scene_rules: List[str] = field(default_factory=list)
    lighting_signature: str = ""
    prop_styling_rules: List[str] = field(default_factory=list)
    
    # 摄影参数（聚合）
    camera_signature: Dict[str, Any] = field(default_factory=dict)
    lighting_setup: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    research_count: int = 0
    last_researched: str = ""
    confidence: float = 0.0


class BrandKnowledgeBase:
    """品牌知识库 — 永续存储和自进化"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "brand_knowledge.db")
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS brands (
                name TEXT PRIMARY KEY,
                category TEXT,
                profile TEXT NOT NULL,
                research_count INTEGER DEFAULT 0,
                last_researched TEXT,
                confidence REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS design_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                knowledge_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS research_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                source_url TEXT,
                analysis_result TEXT,
                created_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_brand_knowledge ON design_knowledge(brand, knowledge_type);
        """)
        self._conn.commit()

    # ── 品牌档案 ──────────────────────────────────────

    def save_brand(self, profile: BrandProfile):
        """保存/更新品牌档案"""
        now = datetime.utcnow().isoformat()
        existing = self.get_brand(profile.brand_name)
        if existing:
            profile.research_count = existing.research_count + 1
        else:
            profile.research_count = 1
        profile.last_researched = now

        self._conn.execute(
            "INSERT OR REPLACE INTO brands (name, category, profile, research_count, last_researched, confidence, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (profile.brand_name, profile.category, json.dumps(profile.__dict__, ensure_ascii=False),
             profile.research_count, profile.last_researched, profile.confidence,
             now, now)
        )
        self._conn.commit()

    def get_brand(self, brand_name: str) -> Optional[BrandProfile]:
        row = self._conn.execute("SELECT * FROM brands WHERE name=?", (brand_name,)).fetchone()
        if row:
            data = json.loads(row[2])
            return BrandProfile(**data)
        return None

    def list_brands(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT name, category, research_count, last_researched, confidence FROM brands ORDER BY research_count DESC").fetchall()
        return [{"name": r[0], "category": r[1], "research_count": r[2], "last_researched": r[3], "confidence": r[4]} for r in rows]

    # ── 设计知识 ──────────────────────────────────────

    def save_knowledge(self, brand: str, knowledge_type: str, content: Any, source: str = ""):
        """存储一条设计知识"""
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO design_knowledge (brand, knowledge_type, content, source, created_at) VALUES (?,?,?,?,?)",
            (brand, knowledge_type, json.dumps(content, ensure_ascii=False), source, now)
        )
        self._conn.commit()

    def get_knowledge(self, brand: str, knowledge_type: Optional[str] = None) -> List[Dict]:
        if knowledge_type:
            rows = self._conn.execute(
                "SELECT * FROM design_knowledge WHERE brand=? AND knowledge_type=? ORDER BY created_at DESC",
                (brand, knowledge_type)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM design_knowledge WHERE brand=? ORDER BY created_at DESC", (brand,)
            ).fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0], "brand": r[1], "type": r[2],
                "content": json.loads(r[3]), "source": r[4], "created_at": r[5]
            })
        return results

    # ── 品牌间对比 ────────────────────────────────────

    def compare_brands(self, brands: List[str]) -> Dict[str, Any]:
        """对比多个品牌的视觉系统"""
        profiles = {}
        for b in brands:
            p = self.get_brand(b)
            if p:
                profiles[b] = {
                    "primary_palette": p.primary_palette,
                    "color_psychology": p.color_psychology,
                    "grid_system": p.grid_system,
                    "lighting_signature": p.lighting_signature,
                }
        return profiles

    # ── 从Research结果构建品牌档案 ────────────────────

    def build_from_research(self, brand_name: str, research_result: Dict[str, Any]) -> BrandProfile:
        """从品牌研究结果构建品牌档案"""
        profile = self.get_brand(brand_name) or BrandProfile(brand_name=brand_name)

        def safe_get(d, *keys):
            for k in keys:
                if isinstance(d, dict):
                    d = d.get(k, {})
                else:
                    return ""
            return d if isinstance(d, (str, list, dict)) else ""

        palette = research_result.get("primary_palette", [])
        if palette:
            profile.primary_palette = palette

        rationale = research_result.get("design_rationale", {})
        if rationale.get("brand_positioning"):
            profile.brand_positioning = rationale["brand_positioning"]
        if rationale.get("target_audience"):
            profile.target_audience = rationale["target_audience"]
        if rationale.get("design_principles"):
            profile.layout_patterns = rationale["design_principles"]
        if rationale.get("psychological_effect"):
            profile.color_psychology = rationale["psychological_effect"]

        scene = research_result.get("scene_composition", "")
        if scene:
            profile.typical_scenes = [scene]

        self.save_brand(profile)
        return profile

    def close(self):
        self._conn.close()
