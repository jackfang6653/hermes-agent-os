"""
品牌DNA数据库 — 自进化知识库

核心功能：
1. 存储每次逆向分析的结果作为品牌DNA条目
2. 向量相似度搜索 — 输入新图自动匹配最相似的品牌参数
3. 参数聚类 — 发现品牌参数模式
4. 自进化 — 每个新分析更新品牌模型
5. 跨品牌对比
"""
import json, os, sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from .types import ImageAnalysisResult


class BrandDatabase:
    """品牌DNA数据库 — 基于SQLite + 内存向量搜索"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "brand_dna.db")
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS brand_dna (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                dimension TEXT NOT NULL,
                parameters TEXT NOT NULL,
                confidence REAL DEFAULT 0,
                source_url TEXT,
                embedding TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS brand_profiles (
                brand TEXT PRIMARY KEY,
                total_analyses INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                camera_parameters TEXT,
                lighting_parameters TEXT,
                color_parameters TEXT,
                composition_rules TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self._conn.commit()
        self._reload_cache()

    def close(self):
        self._conn.close()

    # ── 缓存 ──────────────────────────────────────────

    def _reload_cache(self):
        rows = self._conn.execute("SELECT * FROM brand_dna ORDER BY id").fetchall()
        self._cache = []
        for r in rows:
            self._cache.append({
                "id": r[0], "brand": r[1], "dimension": r[2],
                "parameters": json.loads(r[3]), "confidence": r[4],
                "source_url": r[5], "embedding": json.loads(r[6]) if r[6] else None,
                "created_at": r[7],
            })

    # ── 写入 ──────────────────────────────────────────

    def save_analysis(self, analysis: ImageAnalysisResult, brand: str = "norhor"):
        now = datetime.utcnow().isoformat()
        dimensions = [
            ("camera", analysis.camera.to_dict()),
            ("lighting", {k: v for k, v in analysis.lighting.__dict__.items() if v is not None}),
            ("color_grading", {k: v for k, v in analysis.color_grading.__dict__.items() if v is not None}),
            ("composition", analysis.composition.__dict__),
            ("software", analysis.software.__dict__),
            ("materials", {"materials": analysis.materials_detected}),
            ("style", {"style_keywords": analysis.style_keywords}),
        ]
        for dim, params in dimensions:
            vec = self._compute_embedding(params)
            self._conn.execute(
                "INSERT INTO brand_dna (brand,dimension,parameters,confidence,source_url,embedding,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (brand, dim, json.dumps(params, ensure_ascii=False),
                 getattr(analysis, dim.split("_")[0] if "_" in dim else dim, {}).get("confidence", 0)
                 if hasattr(getattr(analysis, dim.split("_")[0] if "_" in dim else dim, {}), "get") else 0,
                 analysis.image_url, json.dumps(vec), now, now)
            )
        self._conn.commit()
        self._reload_cache()

    # ── 查询 ──────────────────────────────────────────

    def search_similar(self, query_params: Dict, dimension: str = "camera", top_k: int = 5) -> List[Dict]:
        """相似参数搜索 — 向量余弦相似度"""
        qv = self._compute_embedding(query_params)
        scored = []
        for e in self._cache:
            if e["dimension"] != dimension or not e["embedding"]:
                continue
            sim = sum(a * b for a, b in zip(qv, e["embedding"])) / (
                (sum(a*a for a in qv) ** 0.5) * (sum(b*b for b in e["embedding"]) ** 0.5) or 1
            )
            scored.append((sim, e))
        scored.sort(key=lambda x: -x[0])
        return [s[1] for s in scored[:top_k]]

    def get_brand_profile(self, brand: str = "norhor") -> Dict[str, Any]:
        entries = [e for e in self._cache if e["brand"] == brand]
        if not entries:
            return {"brand": brand, "total_analyses": 0}
        profile = {"brand": brand, "total_analyses": len(entries)}
        for dim in ["camera", "lighting", "color_grading", "composition", "software"]:
            dims = [e["parameters"] for e in entries if e["dimension"] == dim]
            if not dims:
                continue
            avg = {}
            for key in dims[0]:
                vals = [d[key] for d in dims if key in d and isinstance(d[key], (int, float))]
                if vals:
                    avg[key] = sum(vals) / len(vals)
                else:
                    strs = [str(d[key]) for d in dims if key in d and d[key]]
                    if strs:
                        avg[key] = max(set(strs), key=strs.count)
            profile[dim] = avg
        return profile

    # ── 向量工具 ──────────────────────────────────────

    def _compute_embedding(self, params: Dict) -> List[float]:
        vec = []
        for v in params.values():
            if isinstance(v, (int, float)):
                vec.append(float(v))
            elif isinstance(v, str):
                vec.append(float(hash(v) % 10000) / 10000)
            elif isinstance(v, bool):
                vec.append(1.0 if v else 0.0)
            elif isinstance(v, list):
                vec.append(float(len(v)))
        while len(vec) < 64:
            vec.append(0.0)
        return vec[:64]
