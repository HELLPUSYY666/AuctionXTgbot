from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == 'Как дела?')
async def how_are_you(message: Message):
    await message.answer('Все ЗБС!!!')
