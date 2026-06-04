from __future__ import annotations

from typing import Any
from aiogram import Bot
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from bot.config import Settings
from database.db import Database
from services.ai.base import AIService
from services.safety.content_filter import is_dangerous_question, safe_refusal_text
from services.tarot.deck import draw_cards
from services.tarot.prompt_builder import build_prompt
from services.tarot.spreads import SPREADS
from backend.security.telegram_auth import validate_telegram_init_data


class ReadingRequest(BaseModel):
    spread_type: str = Field(..., examples=["quick_reading"])
    question: str = Field("", max_length=1000)
    init_data: str = ""
    telegram_id: int | None = None


def create_router(settings: Settings, db: Database, ai_service: AIService, bot: Bot) -> APIRouter:
    router = APIRouter()

    @router.get("/api/readings/spreads")
    async def list_spreads():
        return {"spreads": [{"id": sid, "title": data["title"], "cards_count": data["cards_count"], "positions": data["positions"]} for sid, data in SPREADS.items()]}

    @router.post("/api/readings/generate")
    async def generate_reading(payload: ReadingRequest) -> dict[str, Any]:
        if payload.spread_type not in SPREADS:
            raise HTTPException(status_code=400, detail="Unknown spread_type")

        if settings.dev_allow_unverified_webapp:
            telegram_id = payload.telegram_id or 0
        else:
            if not validate_telegram_init_data(payload.init_data, settings.bot_token):
                raise HTTPException(status_code=403, detail="Invalid Telegram initData")
            telegram_id = payload.telegram_id or 0

        question = payload.question.strip() or "Без конкретного вопроса"

        if is_dangerous_question(question):
            return {"ok": False, "safe_refusal": True, "message": safe_refusal_text()}

        spread = SPREADS[payload.spread_type]
        cards = draw_cards(spread["cards_count"])
        prompt = build_prompt(payload.spread_type, question, cards)

        try:
            ai_response = await ai_service.generate(prompt)
        except Exception as exc:
            if settings.admin_id:
                try:
                    await bot.send_message(settings.admin_id, f"⚠️ Ошибка ИИ в Mini App: {exc}")
                except Exception:
                    pass
            return {"ok": False, "message": "Звезда временно скрылась за облаками. Попробуйте немного позже."}

        is_free = False
        user = None
        if telegram_id:
            user = await db.get_user(telegram_id)
        if payload.spread_type != "daily_card" and user and not user.get("free_reading_used"):
            is_free = True
            await db.mark_free_reading_used(telegram_id)
        if telegram_id:
            await db.save_reading(telegram_id, payload.spread_type, question, cards, ai_response, is_free)

        return {"ok": True, "spread": {"id": payload.spread_type, "title": spread["title"]}, "question": question, "cards": cards, "answer": ai_response, "is_free": is_free}

    return router
