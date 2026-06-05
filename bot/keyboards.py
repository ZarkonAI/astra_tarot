from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def is_valid_webapp_url(url: str | None) -> bool:
    if not url:
        return False

    url = url.strip()

    if not url:
        return False

    if "your-domain-or-hosting-url" in url:
        return False

    if "127.0.0.1" in url or "localhost" in url:
        return False

    return url.startswith("https://")


def main_menu(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []

    if is_valid_webapp_url(webapp_url):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🌌 Открыть Astra Tarot",
                    web_app=WebAppInfo(url=webapp_url.strip()),
                )
            ]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    text="🃏 Карта дня",
                    callback_data="daily_card",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Быстрый расклад",
                    callback_data="spread_quick",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💜 Сердечный расклад",
                    callback_data="spread_love",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Денежный путь",
                    callback_data="spread_money",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌙 Глубокий расклад",
                    callback_data="spread_deep",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def main_menu_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    return main_menu(webapp_url)