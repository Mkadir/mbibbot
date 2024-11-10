from aiogram import types

from loader import dp


# Echo bot
@dp.message_handler(state=None, chat_type=['private'])
async def bot_echo(message: types.Message):
    await message.answer(message.text)
