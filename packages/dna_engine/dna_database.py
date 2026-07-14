"""
品牌DNA数据库 — 完整知识库系统

基于 SQLite，升级到 W3C DTCG 2025.10 设计令牌格式。
支持品牌档案、设计令牌、质量门禁记录、版本迭代。

表结构:
- brand_profiles: 品牌档案表 (含完整DNA JSON、令牌集、质量门禁结果)
- design_tokens: 设计令牌表 (W3C DTCG 2025.10 兼容路径)
- quality_gate_records: 质量门禁记录表 (5门)
- dna_versions: 版本迭代表 (品牌DNA随时间的演变)
- extraction_sessions: 提取会话表
"""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from typing import Optional, List, Dict, Any, Tuple, Iterator
from datetime import datetime
from contextlib import contextmanager

from .dna_schema import BrandDNA, DesignSystemDNA, DesignStyleDNA, VisualEffectsDNA, dna_from_json


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

DTCG_VERSION = "2025.10"
DEFAULT_DB_NAME = "brand_dna_v2.db"

QUALITY_GATE_THRESHOLDS = {
    "gate1_recon": 0.85,
    "gate2_tokens": 0.85,
    "gate3_assets": 0.60,
    "gate4_synthesis": 0.80,
    "gate5_visual": 0.83,
}

QUALITY_GATE_NAMES = {
    "gate1": "Reconnaissance",
    "gate2": "Token Extraction",
    "gate3": "Asset Extraction",
    "gate4": "Synthesis & Interpretation",
    "gate5": "Visual Replication",
}


# ═══════════════════════════════════════════════════════════════
# 数据库核心类
# ═══════════════════════════════════════════════════════════════

class DNADatabase:
    """品牌DNA数据库 — 支持 W3C DTCG 2025.10 设计令牌格式"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_db()

    # ── Schema 初始化 ──────────────────────────────────────

    def _init_db(self):
        """初始化所有表结构（W3C DTCG 2025.10兼容）"""
        # 品牌档案表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS brand_profiles (
                brand_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                sub_category TEXT DEFAULT '',
                dna_schema TEXT NOT NULL DEFAULT '{}',
                token_set TEXT NOT NULL DEFAULT '{}',
                quality_gates TEXT NOT NULL DEFAULT '{}',
                source_url TEXT DEFAULT '',
                source_page_count INTEGER DEFAULT 0,
                overall_confidence REAL DEFAULT 0.0,
                dtcg_version TEXT DEFAULT '2025.10',
                extraction_version TEXT DEFAULT '2.0.0',
                status TEXT DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 设计令牌表 (W3C DTCG 2025.10 格式)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS design_tokens (
                token_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                token_type TEXT NOT NULL,
                token_name TEXT NOT NULL,
                token_value TEXT NOT NULL,
                dtcg_path TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                extraction_method TEXT DEFAULT 'heuristic',
                source_element TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brand_profiles(brand_id) ON DELETE CASCADE
            )
        """)

        # 设计令牌集索引
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tokens_brand ON design_tokens(brand_id)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tokens_dtcg_path ON design_tokens(dtcg_path)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tokens_type ON design_tokens(token_type)
        """)

        # 质量门禁记录表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS quality_gate_records (
                record_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                gate_name TEXT NOT NULL,
                gate_number INTEGER NOT NULL,
                score REAL NOT NULL DEFAULT 0.0,
                threshold REAL NOT NULL,
                passed INTEGER NOT NULL DEFAULT 0,
                blocking_criteria TEXT DEFAULT '[]',
                details TEXT DEFAULT '{}',
                evaluated_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brand_profiles(brand_id) ON DELETE CASCADE
            )
        """)

        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_gates_brand ON quality_gate_records(brand_id)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_gates_passed ON quality_gate_records(passed)
        """)

        # 版本迭代表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS dna_versions (
                version_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                dna_schema_snapshot TEXT NOT NULL,
                token_set_snapshot TEXT NOT NULL,
                quality_gates_snapshot TEXT NOT NULL,
                change_summary TEXT DEFAULT '',
                overall_confidence REAL DEFAULT 0.0,
                created_by TEXT DEFAULT 'auto',
                created_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brand_profiles(brand_id) ON DELETE CASCADE
            )
        """)

        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_brand ON dna_versions(brand_id, version_number DESC)
        """)

        # 提取会话表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS extraction_sessions (
                session_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                source_url TEXT DEFAULT '',
                page_count INTEGER DEFAULT 1,
                extracted_fields INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0.0,
                errors TEXT DEFAULT '[]',
                status TEXT DEFAULT 'running',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (brand_id) REFERENCES brand_profiles(brand_id) ON DELETE CASCADE
            )
        """)

        self._conn.commit()

    # ── 上下文管理器 ──────────────────────────────────────

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ═══════════════════════════════════════════════════════
    # 品牌档案 CRUD
    # ═══════════════════════════════════════════════════════

    def create_brand(self, brand: BrandDNA) -> str:
        """创建新品牌档案，返回 brand_id"""
        brand_id = brand.brand_id or f"brand_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        with self.transaction():
            self._conn.execute("""
                INSERT OR REPLACE INTO brand_profiles
                    (brand_id, name, category, sub_category, dna_schema, token_set,
                     quality_gates, source_url, source_page_count, overall_confidence,
                     dtcg_version, extraction_version, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """, (
                brand_id,
                brand.brand_name,
                brand.category,
                brand.sub_category,
                brand.to_json(),
                json.dumps(brand.to_dtcg_tokens(), ensure_ascii=False),
                json.dumps(brand.gate_results, ensure_ascii=False),
                brand.source_url,
                brand.source_page_count,
                brand.overall_confidence,
                DTCG_VERSION,
                brand.extraction_version,
                now, now,
            ))

            # 同步写入设计令牌
            self._sync_tokens(brand_id, brand.to_dtcg_tokens(), now)

        return brand_id

    def update_brand(self, brand: BrandDNA) -> bool:
        """更新品牌档案"""
        if not brand.brand_id:
            raise ValueError("brand_id is required for update")

        now = datetime.now().isoformat()

        # 先存档当前版本
        self._snapshot_version(brand.brand_id)

        with self.transaction():
            self._conn.execute("""
                UPDATE brand_profiles SET
                    name=?, category=?, sub_category=?, dna_schema=?, token_set=?,
                    quality_gates=?, source_url=?, source_page_count=?,
                    overall_confidence=?, updated_at=?
                WHERE brand_id=?
            """, (
                brand.brand_name, brand.category, brand.sub_category,
                brand.to_json(),
                json.dumps(brand.to_dtcg_tokens(), ensure_ascii=False),
                json.dumps(brand.gate_results, ensure_ascii=False),
                brand.source_url, brand.source_page_count,
                brand.overall_confidence, now,
                brand.brand_id,
            ))

            # 同步令牌
            self._sync_tokens(brand.brand_id, brand.to_dtcg_tokens(), now)

        return True

    def get_brand(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """获取品牌档案"""
        row = self._conn.execute(
            "SELECT * FROM brand_profiles WHERE brand_id=?",
            (brand_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_brand_dna(self, brand_id: str) -> Optional[BrandDNA]:
        """获取品牌DNA对象"""
        row = self.get_brand(brand_id)
        if row is None:
            return None
        data = json.loads(row["dna_schema"])
        return dna_from_json(data)

    def list_brands(self, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """列出品牌档案"""
        if category:
            rows = self._conn.execute(
                "SELECT brand_id, name, category, overall_confidence, status, created_at, updated_at "
                "FROM brand_profiles WHERE category=? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (category, limit, offset)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT brand_id, name, category, overall_confidence, status, created_at, updated_at "
                "FROM brand_profiles ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
        return [dict(r) for r in rows]

    def search_brands(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """按名称/类别搜索品牌"""
        rows = self._conn.execute(
            "SELECT * FROM brand_profiles WHERE name LIKE ? OR category LIKE ? "
            "ORDER BY overall_confidence DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_brand(self, brand_id: str) -> bool:
        """删除品牌及其所有关联数据"""
        with self.transaction():
            self._conn.execute("DELETE FROM design_tokens WHERE brand_id=?", (brand_id,))
            self._conn.execute("DELETE FROM quality_gate_records WHERE brand_id=?", (brand_id,))
            self._conn.execute("DELETE FROM dna_versions WHERE brand_id=?", (brand_id,))
            self._conn.execute("DELETE FROM extraction_sessions WHERE brand_id=?", (brand_id,))
            self._conn.execute("DELETE FROM brand_profiles WHERE brand_id=?", (brand_id,))
        return True

    # ═══════════════════════════════════════════════════════
    # 设计令牌 CRUD (W3C DTCG 2025.10)
    # ═══════════════════════════════════════════════════════

    def _sync_tokens(self, brand_id: str, tokens: Dict[str, Any], now: str):
        """同步设计令牌（先删后插，保证与DNA Schema一致）"""
        self._conn.execute("DELETE FROM design_tokens WHERE brand_id=?", (brand_id,))

        for dtcg_path, token_data in tokens.items():
            value = token_data.get("$value")
            token_type = token_data.get("$type", "string")
            token_name = dtcg_path.split(".")[-1]

            # Infer token type category from path
            type_category = dtcg_path.split(".")[0] if "." in dtcg_path else "unknown"

            token_id = f"{brand_id}_{dtcg_path.replace('.', '_')}"

            self._conn.execute("""
                INSERT INTO design_tokens
                    (token_id, brand_id, token_type, token_name, token_value,
                     dtcg_path, confidence, extraction_method, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token_id, brand_id, token_type, token_name,
                json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                dtcg_path, 0.85, "heuristic", now, now,
            ))

    def get_tokens_by_brand(self, brand_id: str, token_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取品牌的所有设计令牌"""
        if token_type:
            rows = self._conn.execute(
                "SELECT * FROM design_tokens WHERE brand_id=? AND token_type=? ORDER BY dtcg_path",
                (brand_id, token_type)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM design_tokens WHERE brand_id=? ORDER BY dtcg_path",
                (brand_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_token_by_path(self, brand_id: str, dtcg_path: str) -> Optional[Dict[str, Any]]:
        """按DTCG路径获取令牌"""
        row = self._conn.execute(
            "SELECT * FROM design_tokens WHERE brand_id=? AND dtcg_path=?",
            (brand_id, dtcg_path)
        ).fetchone()
        return dict(row) if row else None

    def export_dtcg_tokens(self, brand_id: str) -> Dict[str, Any]:
        """导出完整 W3C DTCG 2025.10 令牌JSON"""
        tokens = self.get_tokens_by_brand(brand_id)
        result = {}
        for t in tokens:
            value = t["token_value"]
            try:
                parsed = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                parsed = value
            result[t["dtcg_path"]] = {
                "$value": parsed,
                "$type": t["token_type"],
            }
        return result

    def import_dtcg_tokens(self, brand_id: str, tokens: Dict[str, Any]):
        """从W3C DTCG格式导入令牌"""
        now = datetime.now().isoformat()
        with self.transaction():
            self._conn.execute("DELETE FROM design_tokens WHERE brand_id=?", (brand_id,))
            self._sync_tokens(brand_id, tokens, now)

    # ═══════════════════════════════════════════════════════
    # 质量门禁记录
    # ═══════════════════════════════════════════════════════

    def record_gate_result(self, brand_id: str, gate_number: int, score: float,
                           threshold: Optional[float] = None,
                           blocking_criteria: Optional[List[str]] = None,
                           details: Optional[Dict[str, Any]] = None) -> str:
        """记录一次质量门禁评估"""
        record_id = f"gate_{brand_id}_{gate_number}_{uuid.uuid4().hex[:8]}"
        gate_name = QUALITY_GATE_NAMES.get(f"gate{gate_number}", f"Gate {gate_number}")

        if threshold is None:
            threshold = QUALITY_GATE_THRESHOLDS.get(f"gate{gate_number}_recon" if gate_number == 1 else
                f"gate{gate_number}_tokens" if gate_number == 2 else
                f"gate{gate_number}_assets" if gate_number == 3 else
                f"gate{gate_number}_synthesis" if gate_number == 4 else
                f"gate{gate_number}_visual", 0.80)

        passed = 1 if score >= threshold else 0
        now = datetime.now().isoformat()

        with self.transaction():
            self._conn.execute("""
                INSERT INTO quality_gate_records
                    (record_id, brand_id, gate_name, gate_number, score, threshold,
                     passed, blocking_criteria, details, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, brand_id, gate_name, gate_number, score, threshold,
                passed,
                json.dumps(blocking_criteria or [], ensure_ascii=False),
                json.dumps(details or {}, ensure_ascii=False),
                now,
            ))
        return record_id

    def get_gate_results(self, brand_id: str) -> List[Dict[str, Any]]:
        """获取品牌所有门禁结果"""
        rows = self._conn.execute(
            "SELECT * FROM quality_gate_records WHERE brand_id=? ORDER BY gate_number ASC, evaluated_at DESC",
            (brand_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_gate_results(self, brand_id: str) -> Dict[int, Dict[str, Any]]:
        """获取最新一次各门的评估结果"""
        results = {}
        for gate_num in range(1, 6):
            row = self._conn.execute(
                "SELECT * FROM quality_gate_records WHERE brand_id=? AND gate_number=? "
                "ORDER BY evaluated_at DESC LIMIT 1",
                (brand_id, gate_num)
            ).fetchone()
            if row:
                results[gate_num] = dict(row)
        return results

    def is_brand_approved(self, brand_id: str) -> Tuple[bool, List[str]]:
        """检查品牌是否通过所有门禁，返回 (通过/未通过, 失败列表)"""
        latest = self.get_latest_gate_results(brand_id)
        failures = []
        for gate_num in range(1, 6):
            if gate_num not in latest:
                failures.append(f"Gate {gate_num}: not evaluated")
            elif not latest[gate_num]["passed"]:
                failures.append(
                    f"Gate {gate_num} ({latest[gate_num]['gate_name']}): "
                    f"score={latest[gate_num]['score']:.2f} < threshold={latest[gate_num]['threshold']:.2f}"
                )
        return len(failures) == 0, failures

    # ═══════════════════════════════════════════════════════
    # 版本迭代
    # ═══════════════════════════════════════════════════════

    def _snapshot_version(self, brand_id: str) -> str:
        """创建当前状态的版本快照"""
        row = self._conn.execute(
            "SELECT * FROM brand_profiles WHERE brand_id=?", (brand_id,)
        ).fetchone()
        if not row:
            return ""

        # 获取当前最大版本号
        max_ver = self._conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) FROM dna_versions WHERE brand_id=?",
            (brand_id,)
        ).fetchone()[0]

        version_id = f"ver_{brand_id}_{max_ver + 1}"
        now = datetime.now().isoformat()

        self._conn.execute("""
            INSERT INTO dna_versions
                (version_id, brand_id, version_number, dna_schema_snapshot,
                 token_set_snapshot, quality_gates_snapshot, change_summary,
                 overall_confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, brand_id, max_ver + 1,
            row["dna_schema"], row["token_set"], row["quality_gates"],
            f"Auto-snapshot before update", row["overall_confidence"],
            now,
        ))
        self._conn.commit()
        return version_id

    def get_version_history(self, brand_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取版本历史"""
        rows = self._conn.execute(
            "SELECT version_id, version_number, change_summary, overall_confidence, created_at "
            "FROM dna_versions WHERE brand_id=? ORDER BY version_number DESC LIMIT ?",
            (brand_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_version(self, brand_id: str, version_number: int) -> Optional[Dict[str, Any]]:
        """获取特定版本快照"""
        row = self._conn.execute(
            "SELECT * FROM dna_versions WHERE brand_id=? AND version_number=?",
            (brand_id, version_number)
        ).fetchone()
        return dict(row) if row else None

    def restore_version(self, brand_id: str, version_number: int) -> bool:
        """恢复到指定版本"""
        version = self.get_version(brand_id, version_number)
        if not version:
            return False

        now = datetime.now().isoformat()
        with self.transaction():
            self._conn.execute("""
                UPDATE brand_profiles SET
                    dna_schema=?, token_set=?, quality_gates=?,
                    overall_confidence=?, updated_at=?
                WHERE brand_id=?
            """, (
                version["dna_schema_snapshot"],
                version["token_set_snapshot"],
                version["quality_gates_snapshot"],
                version["overall_confidence"],
                now,
                brand_id,
            ))
        return True

    # ═══════════════════════════════════════════════════════
    # 提取会话
    # ═══════════════════════════════════════════════════════

    def start_session(self, brand_id: str, source_url: str = "", page_count: int = 1) -> str:
        """开始新的提取会话"""
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        now = datetime.now().isoformat()
        self._conn.execute("""
            INSERT INTO extraction_sessions
                (session_id, brand_id, source_url, page_count, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
        """, (session_id, brand_id, source_url, page_count, now))
        self._conn.commit()
        return session_id

    def complete_session(self, session_id: str, extracted_fields: int = 0,
                         errors: Optional[List[str]] = None, status: str = "completed"):
        """完成提取会话"""
        now = datetime.now().isoformat()
        self._conn.execute("""
            UPDATE extraction_sessions SET
                status=?, extracted_fields=?, errors=?, completed_at=?
            WHERE session_id=?
        """, (
            status,
            extracted_fields,
            json.dumps(errors or [], ensure_ascii=False),
            now,
            session_id,
        ))
        self._conn.commit()

    def get_sessions(self, brand_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取提取会话列表"""
        rows = self._conn.execute(
            "SELECT * FROM extraction_sessions WHERE brand_id=? ORDER BY started_at DESC LIMIT ?",
            (brand_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    # ═══════════════════════════════════════════════════════
    # 聚合查询
    # ═══════════════════════════════════════════════════════

    def get_brand_stats(self, brand_id: str) -> Dict[str, Any]:
        """获取品牌聚合统计"""
        token_count = self._conn.execute(
            "SELECT COUNT(*) FROM design_tokens WHERE brand_id=?", (brand_id,)
        ).fetchone()[0]

        gate_avg = self._conn.execute(
            "SELECT AVG(score) FROM quality_gate_records WHERE brand_id=?",
            (brand_id,)
        ).fetchone()[0] or 0.0

        version_count = self._conn.execute(
            "SELECT COUNT(*) FROM dna_versions WHERE brand_id=?", (brand_id,)
        ).fetchone()[0]

        session_count = self._conn.execute(
            "SELECT COUNT(*) FROM extraction_sessions WHERE brand_id=?", (brand_id,)
        ).fetchone()[0]

        return {
            "brand_id": brand_id,
            "token_count": token_count,
            "gate_avg_score": round(gate_avg, 4),
            "version_count": version_count,
            "session_count": session_count,
        }

    def get_database_stats(self) -> Dict[str, Any]:
        """获取整个数据库的聚合统计"""
        brand_count = self._conn.execute("SELECT COUNT(*) FROM brand_profiles").fetchone()[0]
        token_count = self._conn.execute("SELECT COUNT(*) FROM design_tokens").fetchone()[0]
        gate_count = self._conn.execute("SELECT COUNT(*) FROM quality_gate_records").fetchone()[0]
        version_count = self._conn.execute("SELECT COUNT(*) FROM dna_versions").fetchone()[0]

        # Category distribution
        categories = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM brand_profiles GROUP BY category ORDER BY cnt DESC"
        ).fetchall()

        return {
            "brand_count": brand_count,
            "token_count": token_count,
            "gate_record_count": gate_count,
            "version_count": version_count,
            "category_distribution": [dict(r) for r in categories],
            "dtcg_version": DTCG_VERSION,
        }

    # ═══════════════════════════════════════════════════════
    # 比较与相似度
    # ═══════════════════════════════════════════════════════

    def compare_brands(self, brand_id_a: str, brand_id_b: str) -> Dict[str, Any]:
        """比较两个品牌的设计令牌差异"""
        tokens_a = {t["dtcg_path"]: t["token_value"] for t in self.get_tokens_by_brand(brand_id_a)}
        tokens_b = {t["dtcg_path"]: t["token_value"] for t in self.get_tokens_by_brand(brand_id_b)}

        all_paths = set(tokens_a.keys()) | set(tokens_b.keys())
        matches = 0
        mismatches = []
        only_in_a = []
        only_in_b = []

        for path in sorted(all_paths):
            if path in tokens_a and path in tokens_b:
                if tokens_a[path] == tokens_b[path]:
                    matches += 1
                else:
                    mismatches.append({
                        "path": path,
                        "brand_a": tokens_a[path],
                        "brand_b": tokens_b[path],
                    })
            elif path in tokens_a:
                only_in_a.append(path)
            else:
                only_in_b.append(path)

        total = len(all_paths)
        similarity = matches / total if total > 0 else 0.0

        return {
            "total_paths": total,
            "matches": matches,
            "mismatches": mismatches,
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "similarity": round(similarity, 4),
        }

    # ═══════════════════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════════════════

    def close(self):
        """关闭数据库连接"""
        self._conn.close()

    def vacuum(self):
        """优化数据库存储"""
        self._conn.execute("VACUUM")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def create_database(db_path: Optional[str] = None) -> DNADatabase:
    """创建并初始化数据库"""
    db = DNADatabase(db_path)
    return db

def migrate_from_v1(v1_db_path: str, v2_db_path: Optional[str] = None) -> DNADatabase:
    """从 v1 (brand_dna.db) 迁移到 v2 (W3C DTCG格式)"""
    v2_db = create_database(v2_db_path)

    if not os.path.exists(v1_db_path):
        return v2_db

    v1_conn = sqlite3.connect(v1_db_path)
    v1_conn.row_factory = sqlite3.Row

    try:
        rows = v1_conn.execute("SELECT DISTINCT brand FROM brand_dna").fetchall()
        for row in rows:
            brand_name = row["brand"]
            brand_id = f"brand_{brand_name}"

            # Create minimal brand profile
            brand = BrandDNA(
                brand_id=brand_id,
                brand_name=brand_name,
                category="migrated",
                extraction_version="1.0.0",
            )
            v2_db.create_brand(brand)

        print(f"Migrated {len(rows)} brands from v1 to v2")

    finally:
        v1_conn.close()

    return v2_db
