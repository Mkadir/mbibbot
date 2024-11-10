from aiogram.dispatcher import FSMContext
import os
from database.crud import export_users_to_excel
from loader import dp
from aiogram import types


@dp.message_handler(text="👥 Users", state="*")
async def users_stats(message: types.Message, state: FSMContext):
    await state.finish()
    db = message.bot.get('db')
    file = export_users_to_excel(db=db)

    await message.answer_document(
        document=open(file=file, mode='rb')
    )
    os.remove(file)
