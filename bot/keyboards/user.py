from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def main_menu(webapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Открыть Astra Taro", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton(text="🌙 Карта дня", callback_data="daily_card")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="❔ Помощь", callback_data="help")],
        ]
    )
