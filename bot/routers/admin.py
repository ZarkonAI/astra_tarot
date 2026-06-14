from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards import admin_menu
from database.db import Database
from services.ai.service import AIService
from bot.routers.readings import _send_reading


router = Router(name="admin")


def _is_admin_message(message: Message, settings: Settings) -> bool:
    return settings.is_admin(message.from_user.id if message.from_user else None)


def _is_admin_callback(callback: CallbackQuery, settings: Settings) -> bool:
    return settings.is_admin(callback.from_user.id if callback.from_user else None)


async def _send_stats(message: Message, db: Database) -> None:
    stats = await db.get_stats()
    await message.answer(
        "Статистика Astra Tarot\n\n"
        f"Пользователей: {stats['users']}\n"
        f"Раскладов: {stats['readings']}"
    )


@router.message(Command("stats"))
async def stats_command(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin_message(message, settings):
        await message.answer("Команда доступна только администратору.")
        return

    await _send_stats(message, db)


@router.message(Command("admin"))
async def admin_command(message: Message, settings: Settings) -> None:
    if not _is_admin_message(message, settings):
        await message.answer("Эта команда доступна только администратору.")
        return

    await message.answer("Админ-панель Astra Tarot", reply_markup=admin_menu())


@router.message(Command("reset_me"))
async def reset_me_command(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin_message(message, settings):
        await message.answer("Эта команда доступна только администратору.")
        return
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram ID.")
        return

    await db.reset_user_limits(message.from_user.id)
    await message.answer("Лимиты для вашего аккаунта сброшены.")


@router.callback_query(F.data == "admin:reset_me")
async def admin_reset_callback(callback: CallbackQuery, settings: Settings, db: Database) -> None:
    if not _is_admin_callback(callback, settings):
        await callback.answer("Недоступно", show_alert=True)
        return

    await db.reset_user_limits(callback.from_user.id)
    await callback.answer("Готово")
    if isinstance(callback.message, Message):
        await callback.message.answer("Лимиты для вашего аккаунта сброшены.", reply_markup=admin_menu())


@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(callback: CallbackQuery, settings: Settings, db: Database) -> None:
    if not _is_admin_callback(callback, settings):
        await callback.answer("Недоступно", show_alert=True)
        return

    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_stats(callback.message, db)


@router.callback_query(F.data == "admin:test_daily")
async def admin_test_daily_callback(
    callback: CallbackQuery,
    settings: Settings,
    db: Database,
    ai_service: AIService,
) -> None:
    if not _is_admin_callback(callback, settings):
        await callback.answer("Недоступно", show_alert=True)
        return
    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    await callback.answer()
    await _send_reading(callback.message, callback.from_user, settings, db, ai_service, "daily_card")


@router.callback_query(F.data == "admin:test_deep")
async def admin_test_deep_callback(
    callback: CallbackQuery,
    settings: Settings,
    db: Database,
    ai_service: AIService,
) -> None:
    if not _is_admin_callback(callback, settings):
        await callback.answer("Недоступно", show_alert=True)
        return
    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    await callback.answer()
    await _send_reading(callback.message, callback.from_user, settings, db, ai_service, "deep", "Админская проверка глубокого расклада")
