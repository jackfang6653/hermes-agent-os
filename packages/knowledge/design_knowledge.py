"""
设计模式库 — 可复用设计模式的知识库

存储：
1. 通用设计模式（版式/色彩/排版/留白）
2. 品牌特定模式
3. 场景搭配规则
4. 设计工具参数预设
"""
import json
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class DesignPattern:
    """一个完整的设计模式"""
    name: str
    category: str                          # layout/color/typography/composition/lighting
    description: str = ""
    rationale: str = ""                    # 为什么这样设计
    effect: str = ""                       # 产生的效果
    parameters: Dict[str, Any] = field(default_factory=dict)  # 可复用的参数
    applicable_scenes: List[str] = field(default_factory=list)
    brand_origin: str = ""                 # 来自哪个品牌
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.5


class DesignPatternLibrary:
    """可复用的设计模式库"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "design_patterns.db")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                category TEXT,
                description TEXT,
                rationale TEXT,
                effect TEXT,
                parameters TEXT,
                applicable_scenes TEXT,
                brand_origin TEXT,
                tags TEXT,
                confidence REAL,
                created_at TEXT,
                use_count INTEGER DEFAULT 0
            );
        """)
        self._conn.commit()
        self._seed_default_patterns()

    def _seed_default_patterns(self):
        """种子数据 — 通用设计模式"""
        defaults = [
            ("Z型视觉流", "layout", "产品页采用Z型布局: 左上Logo→右上CTA→左下核心卖点→右下购买",
             "用户阅读习惯从左到右从上到下，Z型布局最大化转化率", "引导用户完成产品认知→兴趣→购买决策",
             {"reading_pattern": "z_shape", "hot_zones": ["top_left", "top_right", "bottom_left", "bottom_right"]},
             ["product_page", "detail_page"], "通用", ["ecommerce", "conversion"], 0.9),

            ("三分法构图", "composition", "产品位于画面左/右三分之一位置，留白三分之二",
             "三分法创造视觉平衡，让产品与场景有呼吸感", "营造高品质、不拥挤的视觉感受",
             {"rule": "rule_of_thirds", "product_position": "left_third", "negative_space": 0.6},
             ["hero_shot", "lifestyle"], "通用", ["photography", "composition"], 0.9),

            ("暖调自然光", "lighting", "4500K自然光为主光源，配合暖色反光板补光",
             "暖调自然光营造温馨、舒适、高级感", "让产品看起来自然、真实、有温度",
             {"key_temperature": 4500, "fill_temperature": 3800, "key_modifier": "softbox"},
             ["living_room", "bedroom", "dining"], "通用", ["warm", "natural"], 0.8),

            ("三角补色配饰", "color", "场景配饰采用主色的补色三角关系: 主色+两个补色邻近色",
             "三角补色创造视觉活力和深度", "让场景丰富但不杂乱，有层次感",
             {"rule": "triadic", "primary_ratio": 0.6, "secondary_ratio": 0.25, "accent_ratio": 0.15},
             ["scene_lifestyle"], "通用", ["color_theory"], 0.85),

            ("留白金线", "layout", "页面顶部保留20%留白区域，仅放品牌Logo和产品名",
             "顶部留白让视觉聚焦产品，不被干扰", "营造高端、简约、自信的品牌感",
             {"top_margin_ratio": 0.2, "logo_position": "top_left", "product_centered": True},
             ["hero_section", "detail_page_top"], "通用", ["minimal", "luxury"], 0.85),
        ]
        for p in defaults:
            try:
                self._conn.execute(
                    "INSERT INTO patterns (name,category,description,rationale,effect,parameters,applicable_scenes,brand_origin,tags,confidence,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (p[0], p[1], p[2], p[3], p[4], json.dumps(p[5]),
                     json.dumps(p[6]), p[7], json.dumps(p[8]), p[9], datetime.utcnow().isoformat())
                )
            except sqlite3.IntegrityError:
                pass
        self._conn.commit()

    def search(self, category: Optional[str] = None, tags: Optional[List[str]] = None, query: str = "") -> List[Dict]:
        """搜索设计模式"""
        sql = "SELECT * FROM patterns WHERE 1=1"
        params = []
        if category:
            sql += " AND category=?"
            params.append(category)
        if tags:
            for t in tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{t}%")
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        sql += " ORDER BY use_count DESC, confidence DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_by_scene(self, scene_type: str) -> List[Dict]:
        """获取适合某场景的设计模式"""
        return self.search(tags=[scene_type])

    def add_from_analysis(self, analysis: Dict[str, Any], brand: str = ""):
        """从品牌分析结果中提取设计模式并存入库"""
        patterns = analysis.get("design_patterns", [])
        if isinstance(patterns, list):
            for p in patterns:
                if isinstance(p, dict) and p.get("name"):
                    try:
                        self._conn.execute(
                            "INSERT OR IGNORE INTO patterns (name,category,description,rationale,effect,parameters,applicable_scenes,brand_origin,tags,confidence,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (p["name"], p.get("category", "general"),
                             p.get("description", ""), p.get("rationale", ""),
                             p.get("effect", ""), json.dumps(p.get("parameters", {})),
                             json.dumps([]), brand,
                             json.dumps(p.get("tags", [])), p.get("confidence", 0.5),
                             datetime.utcnow().isoformat())
                        )
                    except sqlite3.IntegrityError:
                        pass
            self._conn.commit()

    def _row_to_dict(self, r) -> Dict:
        return {
            "id": r[0], "name": r[1], "category": r[2], "description": r[3],
            "rationale": r[4], "effect": r[5], "parameters": json.loads(r[6]),
            "applicable_scenes": json.loads(r[7]), "brand_origin": r[8],
            "tags": json.loads(r[9]), "confidence": r[10],
            "created_at": r[11], "use_count": r[12],
        }

    def close(self):
        self._conn.close()
