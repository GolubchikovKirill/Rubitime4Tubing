from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def user_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Встать в очередь (Трасса 1)", callback_data="u:enq:1")
    kb.button(text="Встать в очередь (Трасса 2)", callback_data="u:enq:2")
    kb.button(text="Моё место", callback_data="u:pos")
    kb.button(text="Выйти из очереди", callback_data="u:leave")
    kb.adjust(1)
    return kb.as_markup()


def operator_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Трасса 1: Следующий", callback_data="op:next:1")
    kb.button(text="Трасса 2: Следующий", callback_data="op:next:2")
    kb.button(text="Трасса 1: Список (30)", callback_data="op:list:1")
    kb.button(text="Трасса 2: Список (30)", callback_data="op:list:2")
    kb.button(text="Трасса 1: Не явился", callback_data="op:noshow:1")
    kb.button(text="Трасса 2: Не явился", callback_data="op:noshow:2")
    kb.button(text="Трасса 1: Завершить (SERVED)", callback_data="op:serve:1")
    kb.button(text="Трасса 2: Завершить (SERVED)", callback_data="op:serve:2")

    kb.row(
        InlineKeyboardButton(
            text="Сканер QR (WebApp)",
            web_app=WebAppInfo(url=settings.webapp_scanner_url),
        )
    )
    kb.adjust(1)
    return kb.as_markup()
