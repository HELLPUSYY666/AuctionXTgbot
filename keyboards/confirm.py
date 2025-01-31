from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Каталог', callback_data='catalog')],
    [InlineKeyboardButton(text='Корзина', callback_data='bascket'), InlineKeyboardButton(text='Контакты', callback_data='contacts')]
])

settings = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='YouTube', url='https://www.youtube.com')]])

help = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='/start')], [KeyboardButton(text='/help')],
    [KeyboardButton(text='/info')], [KeyboardButton(text='/settings')],
    [KeyboardButton(text='/reg')], [KeyboardButton(text='/feedback')], [KeyboardButton(text='/remind')]
])