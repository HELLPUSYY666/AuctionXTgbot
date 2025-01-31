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
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from tgbotbase3.keyboards import confirm as kb
from aiogram.fsm.context import FSMContext

# Scheduler and reminders setup
scheduler = AsyncIOScheduler()
reminders = []

router = Router()
router.message.filter(F.chat.type == "private")
logger = structlog.get_logger()

API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
SESSION_NAME = 'user_session'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
CHANNEL_USERNAME = 'jolybells'


async def get_db_connection():
    return await asyncpg.connect(
        user='zakariyapolevchishikov',
        password='zakaolga2005',
        database='tg_bot',
        host='localhost'
    )


class Reg(StatesGroup):
    name = State()
    number = State()


@router.message(Command("start"))
async def handle_start_command(message: Message):
    await message.reply(
        "Привет! Я бот, который может все! 🔔\n\n"
        "Выбирай любые опции на клавиатуре снизу..\n",
        reply_markup=kb.main
    )


@router.message(Command("help"))
async def handle_help_command(message: Message):
    await message.reply(
        'Основные команды которые ты можешь использовать в этом боте такие: \n\n',
        reply_markup=kb.help
    )


@router.message(Command("reg"))
async def reg_one(message: Message, state: FSMContext):
    await state.set_state(Reg.name)
    await message.answer('Введите ваше имя')


@router.message(Reg.name)
async def reg_two(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.number)
    await message.answer('Введите номер телефона')


@router.message(Reg.number)
async def reg_three(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    data = await state.get_data()
    await message.answer(f'Все отлично!\nИмя {data['name']}\nНомер {data["number"]}')
    await state.clear()


@router.message(Command("get_photo"))
async def handle_get_photo(message: Message):
    await message.answer(text='Это масюль', photo='', caption='Это масюль')


@router.callback_query(F.data == 'catalog')
async def catalof(callback: CallbackQuery):
    await callback.answer('Вы выбрали каталог')
    await callback.message.answer('Привет!')


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
