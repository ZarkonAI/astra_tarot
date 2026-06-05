import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def _miniapp_url() -> str:
    public_base_url = os.getenv("PUBLIC_BASE_URL", os.getenv("WEBAPP_URL", "http://127.0.0.1:8000")).rstrip("/")
    return os.getenv("MINIAPP_URL", f"{public_base_url}/miniapp/").strip()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Astra Tarot",
                    web_app=WebAppInfo(url=_miniapp_url()),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Карта дня",
                    callback_data="daily_card",
                )
            ],
        ]
    )
