from __future__ import annotations

import asyncio
import contextlib
import json
import logging

import uvicorn
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

from backend.app import create_app
from bot.config import Settings, load_settings
from bot.routers import admin, payments, start, webapp
from database.db import Database
from services.ai.base import AIService


SPREAD_TITLES = {
    "daily_card": "Карта дня",
    "quick": "Быстрый расклад",
    "love": "Сердечный расклад",
    "money": "Денежный путь",
    "deep": "Глубокий расклад",
}


def create_bot(settings: Settings) -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))


def create_web_app_data_router() -> Router:
    router = Router(name="web_app_data")

    @router.message(F.web_app_data)
    async def handle_web_app_data(message: Message) -> None:
        raw_data = message.web_app_data.data if message.web_app_data else ""

        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            await message.answer(
                "Не удалось прочитать выбор расклада. Попробуйте еще раз."
            )
            return

        action = data.get("action")
        spread = data.get("spread")

        if action != "select_spread" or spread not in SPREAD_TITLES:
            await message.answer(
                "Не удалось определить расклад. Попробуйте выбрать его еще раз."
            )
            return

        spread_title = SPREAD_TITLES[spread]
        await message.answer(
            f"✨ Вы выбрали: <b>{spread_title}</b>\n\n"
            "Звезда-проводник уже настраивается на ваш вопрос."
        )

    return router


def create_dispatcher(settings: Settings, db: Database, ai_service: AIService) -> Dispatcher:
    dp = Dispatcher()
    dp["db"] = db
    dp["settings"] = settings
    dp["ai_service"] = ai_service

    dp.include_router(start.router)
    dp.include_router(create_web_app_data_router())
    dp.include_router(webapp.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)

    return dp


async def run_backend(app, host: str, port: int) -> None:
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    db = Database(settings.database_path)
    await db.init()

    ai_service = AIService(settings=settings, db=db)
    bot = create_bot(settings)
    dp = create_dispatcher(settings=settings, db=db, ai_service=ai_service)
    app = create_app(settings=settings, db=db, ai_service=ai_service, bot=bot)

    backend_task = asyncio.create_task(run_backend(app, settings.host, settings.port))

    try:
        await start_bot(bot, dp)
    finally:
        backend_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await backend_task
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
