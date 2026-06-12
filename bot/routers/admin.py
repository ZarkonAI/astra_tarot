from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import Settings
from database.db import Database


router = Router(name="admin")


@router.message(Command("stats"))
async def stats_command(message: Message, settings: Settings, db: Database) -> None:
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        await message.answer("Команда доступна только администратору.")
        return

    stats = await db.get_stats()
    await message.answer(
        "Статистика Astra Tarot\n\n"
        f"Пользователей: {stats['users']}\n"
        f"Раскладов: {stats['readings']}"
    )
