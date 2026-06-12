from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import is_valid_telegram_webapp_url


SPREAD_BUTTONS = [
    ("🃏 Карта дня", "spread:daily_card"),
    ("⚡ Быстрый расклад", "spread:quick"),
    ("💜 Сердечный расклад", "spread:love"),
    ("🪙 Денежный путь", "spread:money"),
    ("🌙 Глубокий расклад", "spread:deep"),
]


def main_menu(webapp_url: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if is_valid_telegram_webapp_url(webapp_url):
        rows.append(
            [
                InlineKeyboardButton(
                    text="🌌 Открыть Astra Tarot",
                    web_app=WebAppInfo(url=webapp_url.strip()),
                )
            ]
        )

    rows.extend([[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in SPREAD_BUTTONS])
    return InlineKeyboardMarkup(inline_keyboard=rows)
