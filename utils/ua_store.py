import os
import sqlite3
from typing import Optional, Tuple, Dict, Set

DB_PATH = os.path.join(os.getcwd(), "worker_data.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: Dict[str, str]) -> None:
    cur = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    for col, ddl in columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS account_fingerprints (
            account_key TEXT PRIMARY KEY,
            user_agent  TEXT NOT NULL,
            width       INTEGER,
            height      INTEGER,
            is_mobile   INTEGER,
            has_touch   INTEGER,
            created_at  TEXT DEFAULT (datetime('now')),

            -- Новые поля устройства
            gpu_vendor  TEXT,
            gpu_model   TEXT,
            webgl_vendor TEXT,
            webgl_renderer TEXT,
            platform_str TEXT,
            device_memory INTEGER,
            hardware_concurrency INTEGER,
            max_touch_points INTEGER,
            color_depth INTEGER,
            noise_level TEXT
        );
        """)
        # Миграция со старой таблицы
        if _table_exists(conn, "account_user_agents"):
            cur = conn.execute("SELECT COUNT(1) FROM account_fingerprints")
            cnt = cur.fetchone()[0]
            if cnt == 0:
                try:
                    conn.execute("""
                        INSERT INTO account_fingerprints(account_key, user_agent)
                        SELECT account_key, user_agent FROM account_user_agents
                        ON CONFLICT(account_key) DO NOTHING
                    """)
                    conn.commit()
                except Exception:
                    pass

        # Гарантируем новые колонки (если таблица была создана раньше)
        _ensure_columns(conn, "account_fingerprints", {
            "gpu_vendor": "gpu_vendor TEXT",
            "gpu_model": "gpu_model TEXT",
            "webgl_vendor": "webgl_vendor TEXT",
            "webgl_renderer": "webgl_renderer TEXT",
            "platform_str": "platform_str TEXT",
            "device_memory": "device_memory INTEGER",
            "hardware_concurrency": "hardware_concurrency INTEGER",
            "max_touch_points": "max_touch_points INTEGER",
            "color_depth": "color_depth INTEGER",
            "noise_level": "noise_level TEXT",
        })

        conn.commit()
    finally:
        conn.close()


def get_fingerprint(account_key: str):
    if not account_key:
        return None
    conn = _get_conn()
    try:
        cur = conn.execute("""
            SELECT user_agent, width, height, COALESCE(is_mobile,0), COALESCE(has_touch,0)
            FROM account_fingerprints WHERE account_key = ?
        """, (account_key,))
        row = cur.fetchone()
        if not row:
            return None
        ua, w, h, is_mob, has_touch = row
        vp = {"width": int(w), "height": int(h)} if (w and h) else None
        return ua, vp, bool(is_mob), bool(has_touch)
    finally:
        conn.close()


def set_fingerprint(account_key: str, user_agent: str, viewport: Dict[str, int], is_mobile: bool = False, has_touch: bool = False) -> None:
    if not account_key or not user_agent:
        return
    w = int(viewport["width"]) if viewport and "width" in viewport else None
    h = int(viewport["height"]) if viewport and "height" in viewport else None
    im = 1 if is_mobile else 0
    ht = 1 if has_touch else 0

    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO account_fingerprints(account_key, user_agent, width, height, is_mobile, has_touch)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_key) DO UPDATE SET
                user_agent = excluded.user_agent,
                width = excluded.width,
                height = excluded.height,
                is_mobile = excluded.is_mobile,
                has_touch = excluded.has_touch
        """, (account_key, user_agent, w, h, im, ht))
        conn.commit()
    finally:
        conn.close()


def get_device_fp(account_key: str) -> Optional[Dict]:
    if not account_key:
        return None
    conn = _get_conn()
    try:
        cur = conn.execute("""
            SELECT gpu_vendor, gpu_model, webgl_vendor, webgl_renderer, platform_str,
                   device_memory, hardware_concurrency, max_touch_points, color_depth, noise_level
            FROM account_fingerprints WHERE account_key = ?
        """, (account_key,))
        row = cur.fetchone()
        if not row:
            return None
        keys = ["gpu_vendor", "gpu_model", "webgl_vendor", "webgl_renderer", "platform_str",
                "device_memory", "hardware_concurrency", "max_touch_points", "color_depth", "noise_level"]
        res = dict(zip(keys, row))
        # Нормализация типов
        for k in ["device_memory", "hardware_concurrency", "max_touch_points", "color_depth"]:
            if res.get(k) is not None:
                try:
                    res[k] = int(res[k])
                except Exception:
                    res[k] = None
        return res
    finally:
        conn.close()


def set_device_fp(account_key: str, fp: Dict) -> None:
    if not account_key or not isinstance(fp, dict):
        return
    conn = _get_conn()
    try:
        conn.execute("""
            UPDATE account_fingerprints
               SET gpu_vendor = :gpu_vendor,
                   gpu_model = :gpu_model,
                   webgl_vendor = :webgl_vendor,
                   webgl_renderer = :webgl_renderer,
                   platform_str = :platform_str,
                   device_memory = :device_memory,
                   hardware_concurrency = :hardware_concurrency,
                   max_touch_points = :max_touch_points,
                   color_depth = :color_depth,
                   noise_level = :noise_level
             WHERE account_key = :account_key
        """, {
            "gpu_vendor": fp.get("gpu_vendor"),
            "gpu_model": fp.get("gpu_model"),
            "webgl_vendor": fp.get("webgl_vendor"),
            "webgl_renderer": fp.get("webgl_renderer"),
            "platform_str": fp.get("platform_str"),
            "device_memory": int(fp["device_memory"]) if fp.get("device_memory") is not None else None,
            "hardware_concurrency": int(fp["hardware_concurrency"]) if fp.get("hardware_concurrency") is not None else None,
            "max_touch_points": int(fp["max_touch_points"]) if fp.get("max_touch_points") is not None else None,
            "color_depth": int(fp["color_depth"]) if fp.get("color_depth") is not None else None,
            "noise_level": fp.get("noise_level"),
            "account_key": account_key,
        })
        conn.commit()
    finally:
        conn.close()


def delete_fingerprint(account_key: str) -> None:
    if not account_key:
        return
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM account_fingerprints WHERE account_key = ?", (account_key,))
        conn.commit()
    finally:
        conn.close()


def get_all_user_agents() -> Set[str]:
    conn = _get_conn()
    try:
        uas: Set[str] = set()
        cur = conn.execute("SELECT user_agent FROM account_fingerprints")
        for (ua,) in cur.fetchall():
            if ua:
                uas.add(ua)
        cur2 = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_user_agents'")
        if cur2.fetchone():
            cur3 = conn.execute("SELECT user_agent FROM account_user_agents")
            for (ua,) in cur3.fetchall():
                if ua:
                    uas.add(ua)
        return uas
    finally:
        conn.close()