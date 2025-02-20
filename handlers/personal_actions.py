import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluent.runtime import FluentLocalization

router = Router()
router.message.filter(F.chat.type == "private")

logger = structlog.get_logger()


@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    logger.info("Command /start received", user_id=message.from_user.id)
    try:
        await message.answer(l10n.format_value("hello-msg"))
    except Exception as e:
        logger.error("Error in /start command", error=str(e))


@router.message(F.content_type.in_({'photo', 'video'}))
async def cmd_media_react_bot(message: Message, l10n: FluentLocalization):
    await message.reply(l10n.format_value("media-msg"))
