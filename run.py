from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

import uvicorn
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from backend.app import create_app
from bot.config import load_settings
from bot.main import create_dispatcher
from database.db import Database
from services.ai.service import AIService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _serve_backend(app, host: str, port: int) -> None:
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    settings = load_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is required. Copy .env.example to .env and fill BOT_TOKEN.")

    db = Database(settings.database_path)
    await db.init()
    ai_service = AIService(settings)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher()

    backend_task: asyncio.Task | None = None
    try:
        if settings.start_backend:
            app = create_app(settings, db, ai_service)
            backend_task = asyncio.create_task(_serve_backend(app, settings.host, settings.port))
            logger.info("FastAPI backend is starting on %s:%s", settings.host, settings.port)

        await dispatcher.start_polling(
            bot,
            settings=settings,
            db=db,
            ai_service=ai_service,
        )
    finally:
        if backend_task is not None:
            backend_task.cancel()
            with suppress(asyncio.CancelledError):
                await backend_task
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
