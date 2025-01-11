import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from telethon.errors import RPCError
from fluent.runtime import FluentLocalization

# Router and logger setup
router = Router()
router.message.filter(F.chat.type == "private")
logger = structlog.get_logger()

# Telethon Client Configuration
API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
CHANNEL_USERNAME = 'jolybells'  # Убедитесь, что это корректное имя канала
SESSION_NAME = 'my_bot_session'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


# Handlers
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("hello-msg"))


@router.message(Command("мое мнение"))
async def cmd_opinion(message: Message):
    try:
        # Убедимся, что клиент подключен
        if not client.is_connected():
            await client.start()

        # Получение последнего сообщения из канала
        last_message = await get_last_message()

        # Отправка ответа
        await message.answer(f"Вот мое мнение! Последнее сообщение из канала: {last_message}")
    except Exception as e:
        # Логирование и отправка ошибки пользователю
        logger.error(f"Failed to fetch last message: {str(e)}")
        await message.answer("Не удалось получить сообщение из канала. Попробуйте позже.")


async def get_last_message():
    try:
        channel = await client.get_entity(CHANNEL_USERNAME)
        messages = await client.get_messages(channel, limit=1)
        return messages[0].text if messages else "Сообщений пока нет."
    except RPCError as e:
        logger.error(f"RPC error while fetching messages: {str(e)}")
        return "Ошибка при подключении к каналу."
    except Exception as e:
        logger.error(f"Unexpected error while fetching messages: {str(e)}")
        return "Произошла неизвестная ошибка."


# DONATE Command Example
@router.message(Command("donate"))
async def cmd_donate(message: Message, command: CommandObject, l10n: FluentLocalization):
    if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
        await message.answer(l10n.format_value("donate-input-error"))
        return

    amount = int(command.args)
    kb = InlineKeyboardBuilder()
    kb.button(text=l10n.format_value("donate-button-pay", {"amount": amount}), pay=True)
    kb.button(text=l10n.format_value("donate-button-cancel"), callback_data="donate_cancel")
    kb.adjust(1)

    prices = [LabeledPrice(label="XTR", amount=amount)]
    await message.answer_invoice(
        title=l10n.format_value("donate-invoice-title"),
        description=l10n.format_value("donate-invoice-description", {"amount": amount}),
        prices=prices,
        provider_token="your_provider_token",
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )
