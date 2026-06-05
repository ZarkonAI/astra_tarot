from __future__ import annotations

from pathlib import Path

from aiogram import Bot
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api import health, users
from backend.api.readings import create_router as create_readings_router
from bot.config import Settings
from database.db import Database
from services.ai.base import AIService


def create_app(settings: Settings, db: Database, ai_service: AIService, bot: Bot) -> FastAPI:
    app = FastAPI(title="Astra Tarot Backend")

    @app.get("/")
    async def root() -> dict[str, str | bool]:
        return {
            "ok": True,
            "project": "Astra Tarot",
            "miniapp": "/miniapp/",
            "health": "/health",
        }

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "astra_tarot"}

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(create_readings_router(settings, db, ai_service, bot))

    miniapp_path = Path(__file__).resolve().parents[1] / "miniapp"
    app.mount("/miniapp", StaticFiles(directory=miniapp_path, html=True), name="miniapp")

    return app
