from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "open_hint")
async def callback_open_hint(callback: CallbackQuery) -> None:
    await callback.answer("Нажмите кнопку «Открыть Astra Taro» в главном меню ✨", show_alert=True)
