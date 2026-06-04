from __future__ import annotations

from pathlib import Path
from aiogram import Bot
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from bot.config import Settings
from database.db import Database
from services.ai.base import AIService
from backend.api import health, users
from backend.api.readings import create_router as create_readings_router


def create_app(settings: Settings, db: Database, ai_service: AIService, bot: Bot) -> FastAPI:
    app = FastAPI(title="Astra Taro Backend")
    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(create_readings_router(settings, db, ai_service, bot))
    miniapp_path = Path(__file__).resolve().parents[1] / "miniapp"
    app.mount("/", StaticFiles(directory=miniapp_path, html=True), name="miniapp")
    return app
