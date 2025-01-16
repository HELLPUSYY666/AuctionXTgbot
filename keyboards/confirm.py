from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# main = ReplyKeyboardMarkup(keyboard=[
#     [KeyboardButton(text='Каталог')],
#     [KeyboardButton(text='Корзина'), KeyboardButton(text='Контакты')]
# ])
#

def get_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Confirm", callback_data="confirm")
    return kb.as_markup()
