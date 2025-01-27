from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Каталог', callback_data='catalog')],
    [InlineKeyboardButton(text='Корзина', callback_data='bascket'), InlineKeyboardButton(text='Контакты', callback_data='contacts')]
])

settings = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='YouTube', url='https://www.youtube.com')]])
