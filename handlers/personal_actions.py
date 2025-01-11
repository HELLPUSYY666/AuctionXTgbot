import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from fluent.runtime import FluentLocalization
import asyncio

# Declare router
router = Router()
router.message.filter(F.chat.type == "private")

# Declare logger
logger = structlog.get_logger()

# Telethon Client Configuration
API_ID = '26212615'
API_HASH = '9782dd94b8d3fe6fbe1d8a01bb760af6'
CHANNEL_USERNAME = 'https://t.me/jolybells'
client = TelegramClient('session_name', API_ID, API_HASH)


# Handlers
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("hello-msg"))


@router.message(Command("donate", "donat", "донат"))
async def cmd_donate(message: Message, command: CommandObject, l10n: FluentLocalization):
    if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
        await message.answer(l10n.format_value("donate-input-error"))
        return

    amount = int(command.args)

    # Keyboard setup
    kb = InlineKeyboardBuilder()
    kb.button(text=l10n.format_value("donate-button-pay", {"amount": amount}), pay=True)
    kb.button(text=l10n.format_value("donate-button-cancel"), callback_data="donate_cancel")
    kb.adjust(1)

    # Invoice creation
    prices = [LabeledPrice(label="XTR", amount=amount)]

    await message.answer_invoice(
        title=l10n.format_value("donate-invoice-title"),
        description=l10n.format_value("donate-invoice-description", {"amount": amount}),
        prices=prices,
        provider_token="",
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery, l10n: FluentLocalization):
    await callback.answer(l10n.format_value("donate-cancel-payment"))
    await callback.message.delete()


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("donate-paysupport-message"))


@router.message(Command("refund"))
async def cmd_refund(message: Message, bot: Bot, command: CommandObject, l10n: FluentLocalization):
    transaction_id = command.args
    if transaction_id is None:
        await message.answer(l10n.format_value("donate-refund-input-error"))
        return

    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        )
        await message.answer(l10n.format_value("donate-refund-success"))
    except TelegramBadRequest as e:
        error_message = l10n.format_value("donate-refund-code-not-found")
        if "CHARGE_ALREADY_REFUNDED" in e.message:
            error_message = l10n.format_value("donate-refund-already-refunded")
        await message.answer(error_message)


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery, l10n: FluentLocalization):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, l10n: FluentLocalization):
    await message.answer(
        l10n.format_value(
            "donate-successful-payment",
            {"t_id": message.successful_payment.telegram_payment_charge_id}
        ),
        message_effect_id="5159385139981059251",
    )


@router.message(Command("мое мнение"))
async def cmd_opinion(message: Message, l10n: FluentLocalization):
    try:
        await client.start()
        last_message = await get_last_message()
        await message.answer(f"Вот мое мнение! Последнее сообщение из канала: {last_message}")
    except Exception as e:
        logger.error("Failed to fetch last message", error=str(e))
        await message.answer("Не удалось получить сообщение из канала. Попробуйте позже.")


async def get_last_message():
    async with client:
        try:
            channel = await client.get_entity(CHANNEL_USERNAME)
            messages = await client.get_messages(channel, limit=1)
            return messages[0].text if messages else "Сообщений пока нет."
        except Exception as e:
            logger.error("Error fetching last message", error=str(e))
            return "Ошибка при получении сообщения."
