from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bot.config import Settings
from bot.texts import FREE_FULL_SPREAD_USED_TEXT, DAILY_ALREADY_USED_TEXT, READING_DISCLAIMER
from database.db import Database
from services.ai.service import AIService
from services.readings.engine import create_draw
from services.tarot.spreads import FULL_SPREAD_SLUGS, Spread, get_spread


logger = logging.getLogger(__name__)
FRIENDLY_READING_ERROR = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0440\u0430\u0441\u043a\u043b\u0430\u0434. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437."


class TelegramUserPayload(BaseModel):
    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class CreateReadingRequest(BaseModel):
    spread: str
    question: str = ""
    initData: str = ""
    telegramUser: TelegramUserPayload | None = None


class _TelegramUserAdapter:
    def __init__(self, user: TelegramUserPayload) -> None:
        self.id = int(user.id or 0)
        self.username = user.username
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.language_code = user.language_code


def _public_base_url(settings: Settings) -> str:
    return settings.public_base_url or settings.miniapp_url


def _response_source(settings: Settings) -> str:
    if settings.ai_provider == "local":
        return "local"
    if settings.ai_provider == "openrouter" and settings.openrouter_api_key:
        return "openrouter"
    return "fallback"


def _telegram_id(payload: CreateReadingRequest) -> int | None:
    if payload.telegramUser is None or payload.telegramUser.id is None:
        return None
    try:
        user_id = int(payload.telegramUser.id)
    except (TypeError, ValueError):
        return None
    return user_id if user_id > 0 else None


async def _limit_response_if_needed(
    settings: Settings,
    db: Database,
    spread: Spread,
    telegram_user: TelegramUserPayload | None,
) -> dict[str, object] | None:
    if telegram_user is None or telegram_user.id is None:
        return None

    user_id = _TelegramUserAdapter(telegram_user).id
    if user_id <= 0:
        return None

    is_admin = settings.is_admin(user_id)
    await db.upsert_user_from_telegram(_TelegramUserAdapter(telegram_user))
    user = await db.get_user(user_id)

    if spread.is_daily:
        if not is_admin and await db.has_daily_usage(user_id):
            return {"ok": False, "error": "limit_reached", "message": DAILY_ALREADY_USED_TEXT}
        if not is_admin:
            await db.mark_daily_usage(user_id)
    elif spread.slug in FULL_SPREAD_SLUGS:
        if not is_admin and user and int(user.get("has_used_free_full_spread", 0)) == 1:
            return {"ok": False, "error": "limit_reached", "message": FREE_FULL_SPREAD_USED_TEXT}
        if not is_admin:
            await db.mark_free_full_spread_used(user_id)

    return None


def _card_payload(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "position": card.get("position", ""),
        "title": card.get("title", ""),
        "slug": card.get("slug", ""),
        "symbol": card.get("symbol", ""),
        "archetype": card.get("archetype", ""),
        "light": card.get("meaning", ""),
        "shadow": card.get("shadow", ""),
        "meaning": card.get("meaning", ""),
        "image": card.get("image", ""),
    }


def create_app(settings: Settings, db: Database, ai_service: AIService) -> FastAPI:
    app = FastAPI(title="Astra Tarot Backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, object]:
        return {"ok": True, "service": "astra-tarot-backend"}

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"ok": True, "service": "astra-tarot-backend"}

    @app.post("/api/readings/create")
    async def create_reading(payload: CreateReadingRequest) -> JSONResponse:
        # TODO: validate Telegram initData before production. Do not log full initData.
        spread = get_spread(payload.spread)
        if spread is None:
            return JSONResponse(
                status_code=200,
                content={"ok": False, "error": "unknown_spread", "message": FRIENDLY_READING_ERROR},
            )

        try:
            limit_response = await _limit_response_if_needed(settings, db, spread, payload.telegramUser)
            if limit_response is not None:
                return JSONResponse(status_code=200, content=limit_response)

            drawn_cards = create_draw(spread)
            public_base_url = _public_base_url(settings)
            cards = [drawn.to_public_dict(public_base_url) for drawn in drawn_cards]
            telegram_id = _telegram_id(payload)
            reading_id = await db.create_reading(
                telegram_id=telegram_id,
                spread_slug=spread.slug,
                spread_title=spread.title,
                question=payload.question,
                cards=cards,
                response_text="",
                is_free=True,
            )
            interpretation = await ai_service.generate_reading(
                spread,
                payload.question,
                drawn_cards,
                user_id=telegram_id or 0,
                reading_id=reading_id,
            )
            await db.update_reading_response(reading_id, interpretation)

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "source": _response_source(settings),
                    "spread": spread.slug,
                    "spreadTitle": spread.title,
                    "question": payload.question,
                    "cards": [_card_payload(card) for card in cards],
                    "interpretation": interpretation,
                    "guideAdvice": "\u0421\u0434\u0435\u043b\u0430\u0439\u0442\u0435 \u043e\u0434\u0438\u043d \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u044b\u0439 \u0448\u0430\u0433, \u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0435\u0442 \u044f\u0441\u043d\u043e\u0441\u0442\u044c.",
                    "disclaimer": READING_DISCLAIMER,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as exc:
            logger.warning("Mini App reading failed: %s", exc.__class__.__name__)
            logger.debug("Mini App reading traceback", exc_info=True)
            return JSONResponse(
                status_code=200,
                content={"ok": False, "error": "reading_failed", "message": FRIENDLY_READING_ERROR},
            )

    return app
