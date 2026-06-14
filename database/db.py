from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import aiosqlite


class Database:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self._connection: aiosqlite.Connection | None = None

    async def init(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.database_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                has_used_free_full_spread INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                spread_slug TEXT,
                spread_title TEXT,
                question TEXT,
                cards_json TEXT,
                response_text TEXT,
                is_free INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS daily_usage (
                telegram_id INTEGER,
                usage_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, usage_date)
            );
            """
        )
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database is not initialized")
        return self._connection

    async def upsert_user_from_telegram(self, user: Any) -> None:
        await self.connection.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, last_name, language_code)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                language_code = excluded.language_code,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user.id,
                getattr(user, "username", None),
                getattr(user, "first_name", None),
                getattr(user, "last_name", None),
                getattr(user, "language_code", None),
            ),
        )
        await self.connection.commit()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def has_daily_usage(self, telegram_id: int, usage_date: date | None = None) -> bool:
        usage_date = usage_date or date.today()
        cursor = await self.connection.execute(
            "SELECT 1 FROM daily_usage WHERE telegram_id = ? AND usage_date = ?",
            (telegram_id, usage_date.isoformat()),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row is not None

    async def mark_daily_usage(self, telegram_id: int, usage_date: date | None = None) -> None:
        usage_date = usage_date or date.today()
        await self.connection.execute(
            "INSERT OR IGNORE INTO daily_usage (telegram_id, usage_date) VALUES (?, ?)",
            (telegram_id, usage_date.isoformat()),
        )
        await self.connection.commit()

    async def mark_free_full_spread_used(self, telegram_id: int) -> None:
        await self.connection.execute(
            "UPDATE users SET has_used_free_full_spread = 1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (telegram_id,),
        )
        await self.connection.commit()

    async def reset_user_limits(self, telegram_id: int) -> None:
        await self.connection.execute(
            "DELETE FROM daily_usage WHERE telegram_id = ?",
            (telegram_id,),
        )
        await self.connection.execute(
            "UPDATE users SET has_used_free_full_spread = 0, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (telegram_id,),
        )
        await self.connection.commit()

    async def create_reading(
        self,
        telegram_id: int | None,
        spread_slug: str,
        spread_title: str,
        question: str,
        cards: list[dict[str, Any]],
        response_text: str,
        is_free: bool,
    ) -> int:
        cursor = await self.connection.execute(
            """
            INSERT INTO readings (
                telegram_id, spread_slug, spread_title, question, cards_json, response_text, is_free
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                spread_slug,
                spread_title,
                question,
                json.dumps(cards, ensure_ascii=False),
                response_text,
                1 if is_free else 0,
            ),
        )
        await self.connection.commit()
        return int(cursor.lastrowid)

    async def get_stats(self) -> dict[str, int]:
        users_cursor = await self.connection.execute("SELECT COUNT(*) AS count FROM users")
        readings_cursor = await self.connection.execute("SELECT COUNT(*) AS count FROM readings")
        users_row = await users_cursor.fetchone()
        readings_row = await readings_cursor.fetchone()
        await users_cursor.close()
        await readings_cursor.close()
        return {
            "users": int(users_row["count"] if users_row else 0),
            "readings": int(readings_row["count"] if readings_row else 0),
        }
