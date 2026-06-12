from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards import main_menu
from bot.texts import HELP_TEXT, WELCOME_TEXT
from database.db import Database


router = Router(name="start")


@router.message(Command("start"))
async def start_command(message: Message, settings: Settings, db: Database) -> None:
    if message.from_user is not None:
        await db.upsert_user_from_telegram(message.from_user)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu(settings.miniapp_url),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("id"))
async def id_command(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram ID.")
        return
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")
