import structlog
from aiogram import Router, F, Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, CallbackQuery
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
from datetime import datetime
from tgbotbase3.dispatcher import dp

BOT_TOKEN = "7057230300:AAGB9yqp5oi4tY8jAB2ZyW3DnC9WUyfk1cI"
bot = Bot(token=BOT_TOKEN)
router = Router()

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
CHANNEL_USERNAME = 'jolybells'  # Замените на username канала


async def get_db_connection():
    conn = await asyncpg.connect(
        user='zakariyapolevchishikov',
        password='zakaolga2005',
        database='tg_bot',
        host='localhost'
    )
    return conn


# Handlers
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    logger.info("Received /start command")
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


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, напишите ваш отзыв. Отправьте его в следующем сообщении.")
    await state.set_state(FeedbackStates.waiting_for_feedback)

    @router.message(FeedbackStates.waiting_for_feedback)
    async def receive_feedback(feedback_message: Message, state: FSMContext):
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

            await feedback_message.answer("Спасибо за ваш отзыв!")
        except Exception as e:
            await feedback_message.answer("Произошла ошибка при сохранении отзыва. Попробуйте позже.")
            print(f"Ошибка сохранения отзыва: {e}")

        await state.clear()


async def get_weather_open_meteo(city: str) -> str:
    url = "https://api.open-meteo.com/v1/forecast"

    # Координаты для Алматы и Тайланда
    coordinates = {
        "Almaty": {"latitude": 43.2567, "longitude": 76.9286},
        "Thailand": {"latitude": 15.8700, "longitude": 100.9925}
    }

    # Выбираем координаты в зависимости от города
    if city in coordinates:
        lat, lon = coordinates[city]["latitude"], coordinates[city]["longitude"]
    else:
        return "Город не поддерживается."

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    temp = data["current_weather"]["temperature"]
                    wind = data["current_weather"]["windspeed"]
                    return f"Текущая погода в {city}: {temp}°C, скорость ветра: {wind} км/ч"
                else:
                    return "Ошибка при получении данных о погоде."
    except Exception as e:
        return f"Произошла ошибка: {e}"


@router.message(commands=['weather'])
async def weather(message: types.Message):
    city = message.get_args()  # Получаем название города из аргумента команды
    if city:
        weather_info = await get_weather_open_meteo(city)
        await message.reply(weather_info)
    else:
        await message.reply("Пожалуйста, укажите город. Например, /weather Almaty.")


async def send_reminder(chat_id: int, text: str):
    await bot.send_message(chat_id, f"\ud83d\udd14 Напоминание: {text}")


@router.message(commands=['remind'])
async def handle_remind_command(message: Message):
    """Обработка команды /remind HH:MM текст."""
    try:
        # Парсинг команды
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError("Неверный формат команды. Используйте: /remind HH:MM текст.")

        time_str, reminder_text = parts[1], parts[2]
        remind_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now()

        # Вычисление времени для напоминания
        remind_datetime = datetime.combine(now.date(), remind_time)
        if remind_datetime < now:
            remind_datetime += timedelta(days=1)

        # Добавление задачи в планировщик
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=remind_datetime),
            args=(message.chat.id, reminder_text),
        )

        # Сохранение напоминания
        reminders.append({
            "chat_id": message.chat.id,
            "time": remind_datetime,
            "text": reminder_text,
        })

        await message.reply(f"\ud83d\udd14 Напоминание установлено на {remind_datetime.strftime('%H:%M')}.")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /remind: {e}")
        await message.reply("\u274c Неверный формат. Используйте: /remind HH:MM текст.")


@router.message(commands=['list_reminders'])
async def handle_list_reminders(message: Message):
    """Отображение всех напоминаний для пользователя."""
    user_reminders = [r for r in reminders if r['chat_id'] == message.chat.id]

    if not user_reminders:
        await message.reply("\ud83d\udeab У вас нет активных напоминаний.")
    else:
        reply_text = "\ud83d\udd14 Ваши напоминания:\n" + "\n".join(
            [f"\u2022 {r['time'].strftime('%H:%M')} - {r['text']}" for r in user_reminders]
        )
        await message.reply(reply_text)


@router.message(commands=['start'])
async def handle_start_command(message: Message):
    """Приветственное сообщение."""
    await message.reply(
        "Привет! Я бот-напоминалка. \ud83d\udd14\n\n" +
        "Используйте команду /remind HH:MM текст, чтобы установить напоминание.\n" +
        "Например: /remind 15:30 Позвонить маме."
    )
