from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
from bot.config import Settings

router = Router()


@router.message(F.text == "/admin")
async def cmd_admin(message: Message, settings: Settings) -> None:
    if not settings.admin_id or message.from_user.id != settings.admin_id:
        await message.answer("Команда доступна только администратору.")
        return

    await message.answer(
        "🛠 <b>Админ-панель Astra Taro</b>\n\n"
        "Пока доступна базовая проверка.\n"
        "Следующие версии: заявки на оплату, статистика, баланс.",
        parse_mode="HTML",
    )
