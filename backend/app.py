from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot.config import Settings
from bot.texts import READING_DISCLAIMER
from database.db import Database
from services.ai.service import AIService
from services.readings.engine import create_draw
from services.tarot.spreads import get_spread


class CreateReadingRequest(BaseModel):
    spread: str
    question: str = ""
    initData: str = ""


def create_app(settings: Settings, db: Database, ai_service: AIService) -> FastAPI:
    app = FastAPI(title="Astra Tarot Backend")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": "Astra Tarot Backend", "status": "ok"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/readings/create")
    async def create_reading(payload: CreateReadingRequest) -> dict[str, object]:
        # TODO: validate Telegram initData before production.
        spread = get_spread(payload.spread)
        if spread is None:
            raise HTTPException(status_code=400, detail="Unknown spread")

        drawn_cards = create_draw(spread)
        interpretation = await ai_service.generate_reading(spread, payload.question, drawn_cards)
        cards = [drawn.to_public_dict() for drawn in drawn_cards]

        await db.create_reading(
            telegram_id=None,
            spread_slug=spread.slug,
            spread_title=spread.title,
            question=payload.question,
            cards=cards,
            response_text=interpretation,
            is_free=True,
        )

        return {
            "spread": spread.slug,
            "spreadTitle": spread.title,
            "question": payload.question,
            "cards": [
                {
                    "position": card["position"],
                    "title": card["title"],
                    "meaning": card["meaning"],
                }
                for card in cards
            ],
            "interpretation": interpretation,
            "guideAdvice": "Сделайте один спокойный шаг, который возвращает ясность.",
            "disclaimer": READING_DISCLAIMER,
        }

    return app
