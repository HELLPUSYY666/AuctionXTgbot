import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from telethon.errors import RPCError
from fluent.runtime import FluentLocalization
import asyncpg

# Router and logger setup
router = Router()
router.message.filter(F.chat.type == "private")
logger = structlog.get_logger()

# Telethon Client Configuration
API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
SESSION_NAME = 'user_session'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
CHANNEL_USERNAME = 'jolybells'  # Замените на username канала

async def get_db_connection():
    return await asyncpg.connect(
        user='zakariyapolevchishikov',
        password='zakaolga2005',
        database='zakariyapolevchishikov',
        host='localhost'
    )


# Handlers
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("hello-msg"))


@router.message(Command("mnenie"))
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
        async with client:
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
    try:
        if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
            await message.answer(l10n.format_value("donate-input-error"))
            return

        amount = int(command.args)
        kb = InlineKeyboardBuilder()
        kb.button(text=l10n.format_value("donate-button-pay", {"amount": amount}), pay=True)
        kb.button(text=l10n.format_value("donate-button-cancel"), callback_data="donate_cancel")
        kb.adjust(1)

        prices = [LabeledPrice(label="XTR", amount=amount * 100)]  # Сумма в минимальных единицах валюты
        await message.answer_invoice(
            title=l10n.format_value("donate-invoice-title"),
            description=l10n.format_value("donate-invoice-description", {"amount": amount}),
            prices=prices,
            provider_token="your_provider_token",  # Укажите реальный токен платежного провайдера
            payload=f"{amount}_stars",
            currency="XTR",
            reply_markup=kb.as_markup()
        )
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error during donation: {str(e)}")
        await message.answer("Произошла ошибка при создании платежа. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Unexpected error during donation: {str(e)}")
        await message.answer("Произошла неизвестная ошибка. Обратитесь к администратору.")


@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    await message.answer("Пожалуйста, напишите ваш отзыв. Отправьте его в следующем сообщении.")

    @router.message(F.text)
    async def receive_feedback(feedback_message: Message):
        feedback_text = feedback_message.text
        user_id = feedback_message.from_user.id
        username = feedback_message.from_user.username

    try:
        conn = await get_db_connection()
        await conn.execute(
            """
            INSERT INTO feedback (user_id, username, feedback_text) 
            VALUES ($1, $2, $3)
            """,
            user_id, username, feedback_text
        )
        await conn.close()
