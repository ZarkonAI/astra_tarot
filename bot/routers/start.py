from __future__ import annotations

from datetime import date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.config import Settings
from bot.keyboards.user import main_menu
from database.db import Database
from services.tarot.deck import draw_cards
from services.tarot.prompt_builder import build_prompt
from services.ai.base import AIService
from services.safety.content_filter import is_dangerous_question, safe_refusal_text

router = Router()

START_TEXT = """
✨ <b>Astra Taro</b>

Мистический развлекательный сервис с символическими Таро-раскладами.

Здесь можно получить карту дня, задать вопрос и посмотреть на ситуацию через образы старших арканов.

Важно: расклады помогают взглянуть на ситуацию символически и не заменяют решения, помощь специалиста или личную ответственность.
""".strip()


@router.message(F.text == "/start")
async def cmd_start(message: Message, db: Database, settings: Settings) -> None:
    user = message.from_user
    if user:
        await db.upsert_user(user.id, user.username, user.first_name)

    await message.answer(START_TEXT, reply_markup=main_menu(settings.webapp_url), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, settings: Settings) -> None:
    await callback.message.edit_text(START_TEXT, reply_markup=main_menu(settings.webapp_url), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery, settings: Settings) -> None:
    text = """
❔ <b>Как пользоваться Astra Taro</b>

1. Нажмите «Открыть Astra Taro».
2. Выберите расклад.
3. Сформулируйте вопрос.
4. Вытяните карты.
5. Получите мягкую символическую интерпретацию.

🌙 Карта дня доступна бесплатно 1 раз в сутки.
✨ Первый полноценный расклад можно сделать бесплатно на выбор.
""".strip()
    await callback.message.edit_text(text, reply_markup=main_menu(settings.webapp_url), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    free_used = "да" if user and user.get("free_reading_used") else "нет"
    daily_date = user.get("daily_card_date") if user else "—"
    balance = user.get("balance") if user else 0
    text = f"""
👤 <b>Мой профиль</b>

Бесплатный первый расклад использован: <b>{free_used}</b>
Дата последней карты дня: <b>{daily_date or "—"}</b>
Баланс раскладов: <b>{balance}</b>

Оплата и пакеты будут добавлены в следующих версиях.
""".strip()
    await callback.message.edit_text(text, reply_markup=main_menu(settings.webapp_url), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "daily_card")
async def callback_daily_card(callback: CallbackQuery, db: Database, ai_service: AIService, settings: Settings) -> None:
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    today = date.today()

    if user and user.get("daily_card_date") == today.isoformat():
        await callback.answer("Карта дня уже была открыта сегодня ✨", show_alert=True)
        return

    await callback.answer("Astra вытягивает карту дня...")

    question = "Карта дня"
    if is_dangerous_question(question):
        await callback.message.answer(safe_refusal_text())
        return

    cards = draw_cards(1)
    prompt = build_prompt("daily_card", question, cards)

    try:
        response = await ai_service.generate(prompt)
    except Exception as exc:
        response = "Звезда временно скрылась за облаками. Попробуйте немного позже."
        if settings.admin_id:
            try:
                await callback.bot.send_message(settings.admin_id, f"⚠️ Ошибка ИИ при карте дня: {exc}")
            except Exception:
                pass

    await db.set_daily_card_date(telegram_id, today)
    await db.save_reading(telegram_id, "daily_card", question, cards, response, True)

    card_names = ", ".join(card["name"] for card in cards)
    text = f"🌙 <b>Карта дня: {card_names}</b>\n\n{response}"
    await callback.message.answer(text, parse_mode="HTML")
