from __future__ import annotations

import asyncio
import json
import logging
import random

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, User

from bot.config import Settings
from bot.keyboards import admin_menu, main_menu
from bot.texts import (
    BAD_WEBAPP_DATA_TEXT,
    DAILY_ALREADY_USED_TEXT,
    FREE_FULL_SPREAD_USED_TEXT,
    UNKNOWN_SPREAD_TEXT,
)
from database.db import Database
from services.ai.service import AIService
from services.readings.engine import DrawnCard, create_draw
from services.tarot.cards import build_public_asset_url
from services.tarot.spreads import FULL_SPREAD_SLUGS, Spread, get_spread


router = Router(name="readings")
logger = logging.getLogger(__name__)


def _human_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        repaired = text.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("�") <= text.count("�") else text


def _format_cards(drawn_cards: list[DrawnCard]) -> str:
    return "\n".join(
        f"{index}. {_human_text(drawn.position)}: {_human_text(drawn.card.title)} ({_human_text(drawn.card.symbol)})"
        for index, drawn in enumerate(drawn_cards, start=1)
    )


def _public_base_url(settings: Settings) -> str:
    return settings.public_base_url or settings.miniapp_url


def _random_delay(min_seconds: float, max_seconds: float, seed: str | None = None) -> float:
    lower = max(0.0, float(min_seconds))
    upper = max(0.0, float(max_seconds))
    if upper < lower:
        lower, upper = upper, lower
    rng = random.Random(seed) if seed is not None else random.Random()
    return rng.uniform(lower, upper)


def _ritual_delay_range(settings: Settings, spread: Spread, is_admin: bool) -> tuple[float, float]:
    if not settings.ritual_delays_enabled:
        return 0.0, 0.0
    if is_admin and settings.admin_skip_ritual_delays:
        return 0.2, 0.5
    if spread.is_daily:
        return settings.ritual_card_delay_daily_min, settings.ritual_card_delay_daily_max
    if spread.slug == "quick":
        return settings.ritual_card_delay_quick_min, settings.ritual_card_delay_quick_max
    return settings.ritual_card_delay_full_min, settings.ritual_card_delay_full_max


def _interpretation_delay_range(settings: Settings, is_admin: bool) -> tuple[float, float]:
    if not settings.ritual_delays_enabled:
        return 0.0, 0.0
    if is_admin and settings.admin_skip_ritual_delays:
        return 0.2, 0.5
    return settings.ritual_interpretation_delay_min, settings.ritual_interpretation_delay_max


def _ritual_message(spread: Spread) -> str:
    messages = {
        "daily_card": "Звезда выбирает карту дня...",
        "quick": "Звезда перемешивает карты для быстрого ответа...",
        "love": "Звезда мягко раскрывает сердечный расклад...",
        "money": "Звезда собирает знаки денежного пути...",
        "deep": "Звезда раскладывает карты и собирает нити смысла...",
    }
    return messages.get(spread.slug, "Звезда выбирает карты...")


async def _send_chat_action(message: Message, action: str) -> None:
    try:
        await message.bot.send_chat_action(message.chat.id, action)
    except Exception:
        logger.debug("Failed to send chat action", exc_info=True)


async def _send_card_photos(
    message: Message,
    drawn_cards: list[DrawnCard],
    public_base_url: str,
) -> None:
    for drawn in drawn_cards:
        image_url = build_public_asset_url(public_base_url, drawn.card.image_path)
        caption = f"{_human_text(drawn.position)}: {_human_text(drawn.card.title)}"
        try:
            await _send_chat_action(message, "upload_photo")
            await message.answer_photo(photo=image_url, caption=caption)
        except Exception as exc:
            logger.warning(
                "Failed to send card photo for card=%s error=%s",
                drawn.card.slug,
                exc.__class__.__name__,
            )
            await message.answer(f"{caption}\n{image_url}")


NEXT_MENU_TEXT = "\u0417\u0432\u0435\u0437\u0434\u0430 \u0433\u043e\u0442\u043e\u0432\u0430 \u043a \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u043c\u0443 \u0432\u043e\u043f\u0440\u043e\u0441\u0443."
ADMIN_MENU_TEXT = "\u0410\u0434\u043c\u0438\u043d-\u043c\u0435\u043d\u044e \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u043d\u0438\u0436\u0435."


async def _send_followup_menu(message: Message, settings: Settings, user_id: int | None) -> None:
    await message.answer(
        NEXT_MENU_TEXT,
        reply_markup=main_menu(settings.miniapp_url),
    )
    if settings.is_admin(user_id):
        await message.answer(ADMIN_MENU_TEXT, reply_markup=admin_menu())


async def _await_interpretation(
    ai_task: asyncio.Task[str],
    ai_service: AIService,
    spread: Spread,
    question: str,
    drawn_cards: list[DrawnCard],
    user_id: int,
    reading_id: int,
) -> str:
    try:
        return await ai_task
    except Exception as exc:
        logger.warning("AI task failed; using local fallback. Reason: %s", exc.__class__.__name__)
        logger.debug("AI task traceback", exc_info=True)
        return ai_service._fallback_reading(
            spread,
            question,
            drawn_cards,
            user_id=user_id,
            reading_id=reading_id,
        )


async def _send_reading(
    message: Message,
    telegram_user: User | None,
    settings: Settings,
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

    is_admin = settings.is_admin(telegram_user.id)
    await db.upsert_user_from_telegram(telegram_user)
    user = await db.get_user(telegram_user.id)

    is_free = True
    if spread.is_daily:
        if not is_admin and await db.has_daily_usage(telegram_user.id):
            await message.answer(DAILY_ALREADY_USED_TEXT)
            await _send_followup_menu(message, settings, telegram_user.id)
            return
    elif spread.slug in FULL_SPREAD_SLUGS:
        if not is_admin and user and int(user.get("has_used_free_full_spread", 0)) == 1:
            await message.answer(FREE_FULL_SPREAD_USED_TEXT)
            await _send_followup_menu(message, settings, telegram_user.id)
            return

    drawn_cards = create_draw(spread)
    public_base_url = _public_base_url(settings)
    cards_payload = [drawn.to_public_dict(public_base_url) for drawn in drawn_cards]

    if spread.is_daily and not is_admin:
        await db.mark_daily_usage(telegram_user.id)
    elif spread.slug in FULL_SPREAD_SLUGS and not is_admin:
        await db.mark_free_full_spread_used(telegram_user.id)

    reading_id = await db.create_reading(
        telegram_id=telegram_user.id,
        spread_slug=spread.slug,
        spread_title=spread.title,
        question=question,
        cards=cards_payload,
        response_text="",
        is_free=is_free,
    )

    await message.answer(_ritual_message(spread))
    ai_task = asyncio.create_task(
        ai_service.generate_reading(
            spread=spread,
            question=question,
            drawn_cards=drawn_cards,
            user_id=telegram_user.id,
            reading_id=reading_id,
        )
    )

    card_delay_min, card_delay_max = _ritual_delay_range(settings, spread, is_admin)
    card_delay = _random_delay(
        card_delay_min,
        card_delay_max,
        seed=f"cards:{reading_id}:{telegram_user.id}:{spread.slug}",
    )
    if card_delay > 0:
        await _send_chat_action(message, "typing")
        await asyncio.sleep(card_delay)

    await message.answer(f"Карты открыты:\n{_format_cards(drawn_cards)}")
    await _send_card_photos(message, drawn_cards, public_base_url)

    if ai_task.done():
        interpretation_min, interpretation_max = _interpretation_delay_range(settings, is_admin)
        interpretation_delay = _random_delay(
            interpretation_min,
            interpretation_max,
            seed=f"interpretation:{reading_id}:{telegram_user.id}:{spread.slug}",
        )
        if interpretation_delay > 0:
            await _send_chat_action(message, "typing")
            await asyncio.sleep(interpretation_delay)
        response_text = await _await_interpretation(
            ai_task,
            ai_service,
            spread,
            question,
            drawn_cards,
            telegram_user.id,
            reading_id,
        )
    else:
        await message.answer("Толкование складывается...")
        await _send_chat_action(message, "typing")
        response_text = await _await_interpretation(
            ai_task,
            ai_service,
            spread,
            question,
            drawn_cards,
            telegram_user.id,
            reading_id,
        )

    await db.update_reading_response(reading_id, response_text)
    await message.answer(response_text)
    await _send_followup_menu(message, settings, telegram_user.id)


@router.callback_query(F.data.startswith("spread:"))
async def spread_callback(
    callback: CallbackQuery,
    settings: Settings,
    db: Database,
    ai_service: AIService,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    spread_slug = (callback.data or "").split(":", maxsplit=1)[-1]
    await callback.answer()
    await _send_reading(callback.message, callback.from_user, settings, db, ai_service, spread_slug)


@router.message(F.web_app_data)
async def web_app_data_handler(
    message: Message,
    settings: Settings,
    db: Database,
    ai_service: AIService,
) -> None:
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
    await _send_reading(message, message.from_user, settings, db, ai_service, spread_slug, question)
