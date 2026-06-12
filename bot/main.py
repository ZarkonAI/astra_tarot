from __future__ import annotations

from aiogram import Dispatcher

from bot.routers import admin, payments, readings, start


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(start.router)
    dispatcher.include_router(readings.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(payments.router)
    return dispatcher
