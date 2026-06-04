from __future__ import annotations

import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import load_settings
from bot.routers import start, admin, webapp, payments
from database.db import Database
from services.ai.base import AIService
from backend.app import create_app


async def run_backend(app, host: str, port: int) -> None:
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()

    db = Database(settings.database_path)
    await db.init()
    ai_service = AIService(settings=settings, db=db)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp["db"] = db
    dp["settings"] = settings
    dp["ai_service"] = ai_service

    dp.include_router(start.router)
    dp.include_router(webapp.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)

    app = create_app(settings=settings, db=db, ai_service=ai_service, bot=bot)
    backend_task = asyncio.create_task(run_backend(app, settings.host, settings.port))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        backend_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
