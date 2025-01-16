import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tgbotbase3 import bot
from fluent.runtime import FluentLocalization
from tgbotbase3.dispatcher import dp
from telethon import TelegramClient

router = Router()
router.message.filter(F.chat.type == "chat")
logger = structlog.get_logger()
API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
SESSION_NAME = 'user_session'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
CHANNEL_USERNAME = 'jolybells'


@dp.message(F.text == 'Как дела?')
async def how_are_you(message: Message):
    await message.answer('Все ЗБС!!!')
