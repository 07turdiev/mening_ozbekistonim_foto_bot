"""SQLite ma'lumotlar bazasi qatlami."""
from __future__ import annotations

from typing import Any, Iterable

import aiosqlite

from config import cfg

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    fio         TEXT,
    phone       TEXT,
    agreed_at   TEXT,
    created_at  TEXT DEFAULT (datetime('now','+5 hours')),
    is_blocked  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS photos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    file_id      TEXT NOT NULL,
    file_unique  TEXT,
    file_hash    TEXT,
    file_name    TEXT,
    file_path    TEXT,
    width        INTEGER,
    height       INTEGER,
    file_size    INTEGER,
    has_exif     INTEGER DEFAULT 0,
    exif_info    TEXT,
    title        TEXT,
    place        TEXT,
    shot_date    TEXT,
    description  TEXT,
    status       TEXT DEFAULT 'pending',
    reject_reason TEXT,
    reviewed_by  INTEGER,
    reviewed_at  TEXT,
    created_at   TEXT DEFAULT (datetime('now','+5 hours')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_photos_user   ON photos(user_id);
CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status);
CREATE INDEX IF NOT EXISTS idx_photos_hash   ON photos(file_hash);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


async def _conn() -> aiosqlite.Connection:
    db = await aiosqlite.connect(cfg.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await _conn()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()


async def fetch_one(sql: str, params: Iterable[Any] = ()) -> aiosqlite.Row | None:
    db = await _conn()
    try:
        async with db.execute(sql, tuple(params)) as cur:
            return await cur.fetchone()
    finally:
        await db.close()


async def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[aiosqlite.Row]:
    db = await _conn()
    try:
        async with db.execute(sql, tuple(params)) as cur:
            return list(await cur.fetchall())
    finally:
        await db.close()


async def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """INSERT/UPDATE/DELETE bajaradi, lastrowid qaytaradi."""
    db = await _conn()
    try:
        cur = await db.execute(sql, tuple(params))
        await db.commit()
        return cur.lastrowid or 0
    finally:
        await db.close()


# ---------------------------------------------------------------- foydalanuvchi

async def upsert_user(user_id: int, username: str | None) -> None:
    await execute(
        "INSERT INTO users (user_id, username) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET username = excluded.username",
        (user_id, username),
    )


async def get_user(user_id: int) -> aiosqlite.Row | None:
    return await fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))


async def set_agreement(user_id: int) -> None:
    await execute(
        "UPDATE users SET agreed_at = datetime('now','+5 hours') WHERE user_id = ? AND agreed_at IS NULL",
        (user_id,),
    )


async def save_profile(user_id: int, fio: str, phone: str) -> None:
    await execute("UPDATE users SET fio = ?, phone = ? WHERE user_id = ?", (fio, phone, user_id))


async def is_registered(user_id: int) -> bool:
    row = await get_user(user_id)
    return bool(row and row["fio"] and row["phone"])


# ---------------------------------------------------------------------- suratlar

ACTIVE_STATUSES = ("pending", "approved")


async def count_active_photos(user_id: int) -> int:
    row = await fetch_one(
        "SELECT COUNT(*) AS c FROM photos WHERE user_id = ? AND status IN (?, ?)",
        (user_id, *ACTIVE_STATUSES),
    )
    return row["c"] if row else 0


async def find_duplicate(file_hash: str) -> aiosqlite.Row | None:
    return await fetch_one(
        "SELECT * FROM photos WHERE file_hash = ? AND status IN (?, ?) LIMIT 1",
        (file_hash, *ACTIVE_STATUSES),
    )


async def add_photo(data: dict[str, Any]) -> int:
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    return await execute(f"INSERT INTO photos ({cols}) VALUES ({marks})", tuple(data.values()))


async def get_photo(photo_id: int) -> aiosqlite.Row | None:
    return await fetch_one(
        "SELECT p.*, u.fio, u.phone, u.username FROM photos p "
        "JOIN users u ON u.user_id = p.user_id WHERE p.id = ?",
        (photo_id,),
    )


async def user_photos(user_id: int) -> list[aiosqlite.Row]:
    return await fetch_all(
        "SELECT * FROM photos WHERE user_id = ? ORDER BY id", (user_id,)
    )


async def set_status(photo_id: int, status: str, admin_id: int, reason: str | None = None) -> None:
    await execute(
        "UPDATE photos SET status = ?, reject_reason = ?, reviewed_by = ?, "
        "reviewed_at = datetime('now','+5 hours') WHERE id = ?",
        (status, reason, admin_id, photo_id),
    )


async def photos_by_status(status: str, limit: int, offset: int) -> list[aiosqlite.Row]:
    return await fetch_all(
        "SELECT p.*, u.fio, u.phone, u.username FROM photos p "
        "JOIN users u ON u.user_id = p.user_id "
        "WHERE p.status = ? ORDER BY p.id LIMIT ? OFFSET ?",
        (status, limit, offset),
    )


async def count_by_status(status: str) -> int:
    row = await fetch_one("SELECT COUNT(*) AS c FROM photos WHERE status = ?", (status,))
    return row["c"] if row else 0


async def all_photos_full() -> list[aiosqlite.Row]:
    return await fetch_all(
        "SELECT p.*, u.fio, u.phone, u.username FROM photos p "
        "JOIN users u ON u.user_id = p.user_id ORDER BY p.id"
    )


async def search_users(query: str) -> list[aiosqlite.Row]:
    like = f"%{query}%"
    return await fetch_all(
        "SELECT * FROM users WHERE fio LIKE ? OR phone LIKE ? OR CAST(user_id AS TEXT) = ? "
        "ORDER BY user_id LIMIT 20",
        (like, like, query),
    )


# ------------------------------------------------------------------- statistika

async def stats() -> dict[str, int]:
    row = await fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM users)                                   AS users_total,
          (SELECT COUNT(*) FROM users WHERE fio IS NOT NULL)             AS users_reg,
          (SELECT COUNT(*) FROM photos)                                  AS photos_total,
          (SELECT COUNT(*) FROM photos WHERE status='pending')           AS pending,
          (SELECT COUNT(*) FROM photos WHERE status='approved')          AS approved,
          (SELECT COUNT(*) FROM photos WHERE status='rejected')          AS rejected,
          (SELECT COUNT(DISTINCT user_id) FROM photos
             WHERE status IN ('pending','approved'))                     AS participants,
          (SELECT COUNT(*) FROM photos
             WHERE date(created_at)=date('now','+5 hours'))              AS today
        """
    )
    return dict(row) if row else {}


async def all_user_ids() -> list[int]:
    rows = await fetch_all("SELECT user_id FROM users WHERE is_blocked = 0")
    return [r["user_id"] for r in rows]


# --------------------------------------------------------------------- sozlamalar

async def get_setting(key: str, default: str = "") -> str:
    row = await fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    await execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


async def acceptance_paused() -> bool:
    return await get_setting("paused", "0") == "1"
