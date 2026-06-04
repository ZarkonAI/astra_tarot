from __future__ import annotations

import json
from pathlib import Path
from datetime import date
from typing import Any

import aiosqlite


class Database:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.schema_path = Path(__file__).with_name("schema.sql")

    async def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            schema = self.schema_path.read_text(encoding="utf-8")
            await db.executescript(schema)
            await db.commit()

    async def upsert_user(self, telegram_id: int, username: str | None, first_name: str | None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
                """,
                (telegram_id, username, first_name),
            )
            await db.commit()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def set_daily_card_date(self, telegram_id: int, value: date) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET daily_card_date = ? WHERE telegram_id = ?", (value.isoformat(), telegram_id))
            await db.commit()

    async def mark_free_reading_used(self, telegram_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET free_reading_used = 1 WHERE telegram_id = ?", (telegram_id,))
            await db.commit()

    async def save_reading(self, telegram_id: int, spread_type: str, question: str, cards: list[dict[str, Any]], ai_response: str, is_free: bool) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                """
                INSERT INTO readings (telegram_id, spread_type, question, cards_json, ai_response, is_free)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, spread_type, question, json.dumps(cards, ensure_ascii=False), ai_response, 1 if is_free else 0),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def log_ai_usage(self, provider: str, model: str | None, prompt: str, response: str | None, status: str, error_message: str | None = None) -> None:
        prompt_tokens = max(1, len(prompt) // 4)
        response_tokens = max(0, len(response or "") // 4)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO ai_usage (provider, model, prompt_tokens_estimated, response_tokens_estimated, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider, model, prompt_tokens, response_tokens, status, error_message),
            )
            await db.commit()
