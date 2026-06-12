from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, User

from bot.texts import (
    BAD_WEBAPP_DATA_TEXT,
    DAILY_ALREADY_USED_TEXT,
    FREE_FULL_SPREAD_USED_TEXT,
    UNKNOWN_SPREAD_TEXT,
)
from database.db import Database
from services.ai.service import AIService
from services.readings.engine import DrawnCard, create_draw
from services.tarot.spreads import FULL_SPREAD_SLUGS, get_spread


router = Router(name="readings")


def _format_cards(drawn_cards: list[DrawnCard]) -> str:
    return "\n".join(
        f"{index}. {drawn.position}: {drawn.card.title} ({drawn.card.symbol})"
        for index, drawn in enumerate(drawn_cards, start=1)
    )


async def _send_reading(
    message: Message,
    telegram_user: User | None,
    db: Database,
    ai_service: AIService,
    spread_slug: str,
    question: str = "",
) -> None:
    if telegram_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    spread = get_spread(spread_slug)
    if spread is None:
        await message.answer(UNKNOWN_SPREAD_TEXT)
        return

    await db.upsert_user_from_telegram(telegram_user)
    user = await db.get_user(telegram_user.id)

    is_free = True
    if spread.is_daily:
        if await db.has_daily_usage(telegram_user.id):
            await message.answer(DAILY_ALREADY_USED_TEXT)
            return
    elif spread.slug in FULL_SPREAD_SLUGS:
        if user and int(user.get("has_used_free_full_spread", 0)) == 1:
            await message.answer(FREE_FULL_SPREAD_USED_TEXT)
            return

    drawn_cards = create_draw(spread)
    await message.answer(
        f"{spread.title}\n\nКарты открыты:\n{_format_cards(drawn_cards)}\n\nГотовлю толкование..."
    )
    response_text = await ai_service.generate_reading(spread, question, drawn_cards)

    if spread.is_daily:
        await db.mark_daily_usage(telegram_user.id)
    elif spread.slug in FULL_SPREAD_SLUGS:
        await db.mark_free_full_spread_used(telegram_user.id)

    await db.create_reading(
        telegram_id=telegram_user.id,
        spread_slug=spread.slug,
        spread_title=spread.title,
        question=question,
        cards=[drawn.to_public_dict() for drawn in drawn_cards],
        response_text=response_text,
        is_free=is_free,
    )
    await message.answer(response_text)


@router.callback_query(F.data.startswith("spread:"))
async def spread_callback(callback: CallbackQuery, db: Database, ai_service: AIService) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    spread_slug = (callback.data or "").split(":", maxsplit=1)[-1]
    await callback.answer()
    await _send_reading(callback.message, callback.from_user, db, ai_service, spread_slug)


@router.message(F.web_app_data)
async def web_app_data_handler(message: Message, db: Database, ai_service: AIService) -> None:
    raw_data = message.web_app_data.data if message.web_app_data else ""
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        await message.answer(BAD_WEBAPP_DATA_TEXT)
        return

    if payload.get("action") != "select_spread":
        await message.answer(BAD_WEBAPP_DATA_TEXT)
        return

    spread_slug = str(payload.get("spread") or "")
    question = str(payload.get("question") or "").strip()
    await _send_reading(message, message.from_user, db, ai_service, spread_slug, question)
