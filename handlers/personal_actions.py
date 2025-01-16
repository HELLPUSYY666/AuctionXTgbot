import structlog
from aiogram import Router, F, Bot, types, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from telethon.errors import RPCError
from fluent.runtime import FluentLocalization
import asyncpg
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from tgbotbase3 import bot
from tgbotbase3.dispatcher import dp

# Scheduler and reminders setup
scheduler = AsyncIOScheduler()
reminders = []

# Router and logger setup
router = Router()
router.message.filter(F.chat.type == "private")
logger = structlog.get_logger()

# Telethon Client Configuration
API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
SESSION_NAME = 'user_session'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
CHANNEL_USERNAME = 'jolybells'  # Replace with the actual channel username


async def get_db_connection():
    return await asyncpg.connect(
        user='zakariyapolevchishikov',
        password='zakaolga2005',
        database='tg_bot',
        host='localhost'
    )


@router.message(Command("start"))
async def handle_start_command(message: Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Button 1"), KeyboardButton(text="Button 2")],
            [KeyboardButton(text="Button 3")]
        ]
    )
    await message.reply(
        "Привет! Я бот, который может все! 🔔\n\n"
        "Выбирай любые опции на клавиатуре снизу..\n",
        reply_markup=keyboard
    )


@dp.message_handler(lambda message: message.text == "Button 2")
async def button2_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Option X", callback_data="option_X"),
             InlineKeyboardButton(text="Option Y", callback_data="option_Y")]
        ]
    )
    await message.reply("Вы выбрали Button 2, выберите одну из опций:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Button 3")
async def button3_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Option M", callback_data="option_M"),
             InlineKeyboardButton(text="Option N", callback_data="option_N")]
        ]
    )
    await message.reply("Вы выбрали Button 3, выберите одну из опций:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data in ["option_X", "option_Y", "option_M", "option_N"])
async def process_callback(callback_query: types.CallbackQuery):
    # Обрабатываем выбор пользователя из inline кнопок
    selected_option = callback_query.data
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали: {selected_option}")


@router.message(Command("mnenie"))
async def cmd_opinion(message: Message):
    try:
        if not client.is_connected():
            await client.start()

        last_message = await get_last_message()
        await message.reply(f"Here's my opinion! Last message from the channel: {last_message}")
    except Exception as e:
        logger.error(f"Failed to fetch last message: {e}")
        await message.reply("Unable to retrieve the channel message. Try again later.")


async def get_last_message():
    try:
        async with client:
            channel = await client.get_entity(CHANNEL_USERNAME)
            messages = await client.get_messages(channel, limit=1)
            return messages[0].text if messages else "No messages yet."
    except RPCError as e:
        logger.error(f"RPC error while fetching messages: {e}")
        return "Error connecting to the channel."
    except Exception as e:
        logger.error(f"Unexpected error while fetching messages: {e}")
        return "An unknown error occurred."


@router.message(Command("remind"))
async def handle_remind_command(message: Message):
    try:
        parts = message.text.split(maxsplit=2)

        if len(parts) < 3:
            raise ValueError("Invalid format. Use: /remind HH:MM text.")

        time_str, reminder_text = parts[1], parts[2]

        try:
            remind_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM.")

        now = datetime.now()
        remind_datetime = datetime.combine(now.date(), remind_time)

        if remind_datetime < now:
            remind_datetime += timedelta(days=1)

        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=remind_datetime),
            args=(message.chat.id, reminder_text),
        )

        reminders.append({
            "chat_id": message.chat.id,
            "time": remind_datetime,
            "text": reminder_text,
        })

        await message.reply(f"\U0001F514 Reminder set for {remind_datetime.strftime('%H:%M')}.")
    except Exception as e:
        logger.error(f"Error handling /remind command: {e}")
        await message.reply(f"\u274c Error: {str(e)}")


@router.message(Command("list_reminders"))
async def handle_list_reminders(message: Message):
    """Display all reminders for the user."""
    user_reminders = [r for r in reminders if r['chat_id'] == message.chat.id]

    if not user_reminders:
        await message.reply("\U0001F6AB You have no active reminders.")
    else:
        reply_text = "\U0001F514 Your reminders:\n" + "\n".join(
            [f"\u2022 {r['time'].strftime('%H:%M')} - {r['text']}" for r in user_reminders]
        )
        await message.reply(reply_text)


async def send_reminder(chat_id: int, text: str):
    try:
        await Bot.get_current().send_message(chat_id, f"\U0001F514 Reminder: {text}")
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")


@router.message(Command("feedback"))
async def handle_feedback_command(message: Message):
    try:
        # Проверяем текст отзыва
        feedback_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

        if not feedback_text:
            await message.reply("Please provide your feedback after the command, like: /feedback Your feedback here.")
            return

        # Логируем входящие данные
        logger.info(f"Chat ID: {message.chat.id}, Username: {message.from_user.username}, Feedback: {feedback_text}")

        # Установление соединения с БД
        conn = await get_db_connection()

        # Выполняем запрос
        await conn.execute(
            """
            INSERT INTO feedback (user_id, username, feedback_text) 
            VALUES ($1, $2, $3)
            """,
            message.chat.id,  # user_id
            message.from_user.username,  # username
            feedback_text  # feedback_text
        )

        # Закрываем соединение
        await conn.close()

        # Уведомление об успешной записи
        await message.reply("Thank you for your feedback! Your opinion is important to us. 😊")
    except Exception as e:
        logger.error(f"Error handling /feedback command: {e}")
        await message.reply("There was an error saving your feedback. Please try again later.")
