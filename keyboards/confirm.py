from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Каталог')],
    [KeyboardButton(text='Корзина'), KeyboardButton(text='Конатакты')]
], resize_keyboard=True)

settings = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='YouTube', url='https://www.youtube.com')]])

cars = ['Tesla', 'Mercedes', 'BMW', 'Venus']


async def inline_cars():
    keyboard = ReplyKeyboardBuilder
    for car in cars:
        keyboard.add(KeyboardButton(text=car))
    return keyboard.adjust(2)
