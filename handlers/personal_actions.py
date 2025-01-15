import structlog
from aiogram import Router, F, Bot, types
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
    """Establish a connection to the database."""
    return await asyncpg.connect(
        user='zakariyapolevchishikov',
        password='zakaolga2005',
        database='tg_bot',
        host='localhost'
    )


@router.message(Command("start"))
async def handle_start_command(message: Message):
    await message.reply(
        "Welcome! I'm your reminder bot. \ud83d\udd14\n\n"
        "Use /remind HH:MM text to set a reminder.\n"
        "Example: /remind 15:30 Call mom."
    )


@router.message(Command("mnenie"))
async def cmd_opinion(message: Message):
    """Fetch the last message from the specified channel."""
    try:
        if not client.is_connected():
            await client.start()

        last_message = await get_last_message()
        await message.reply(f"Here's my opinion! Last message from the channel: {last_message}")
    except Exception as e:
        logger.error(f"Failed to fetch last message: {e}")
        await message.reply("Unable to retrieve the channel message. Try again later.")


async def get_last_message():
    """Retrieve the latest message from the channel."""
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
        feedback_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

        if not feedback_text:
            await message.reply("Please provide your feedback after the command, like: /feedback Your feedback here.")
            return

        conn = await get_db_connection()

        await conn.execute(
            "INSERT INTO feedback (feedback) VALUES ($1, $2)",
            message.chat.id,
            feedback_text
        )

        await conn.close()

        await message.reply("Thank you for your feedback! Your opinion is important to us. \U0001F60A")
    except Exception as e:
        logger.error(f"Error handling /feedback command: {e}")
        await message.reply("There was an error saving your feedback. Please try again later.")
