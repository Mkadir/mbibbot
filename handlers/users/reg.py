from aiogram.dispatcher import FSMContext

from database.crud import update_user, get_user_by_tg_id
from keyboards.inline.simplein import regions_keyboard
from loader import bot, dp
from aiogram import types
from data.config import regions


@dp.message_handler(commands=['start'], state="*", chat_type=['private'])
async def registration_start(message: types.Message, state: FSMContext):
    db = message.bot.get('db')
    user_in_db = get_user_by_tg_id(db=db, tg_id=message.from_user.id)
    if not user_in_db or (not user_in_db.verified):
        await message.answer(
            text="<b>Iltimos F.I.SH va ish joyingizni kiriting\n</b>Misol uchun <i>Алимов Али Саидович Фарғона ИИБ МГ</i>"
        )
        await state.set_state("get_name")


@dp.message_handler(state="get_name", chat_type=['private'])
async def get_name_func(message: types.Message, state: FSMContext):
    name = message.text
    db = message.bot.get('db')
    await message.answer(
        text="<b>Viloyatingizni tanlang</b>", reply_markup=regions_keyboard()
    )
    # await state.update_data(name=name)
    update_user(db=db, user_id=message.from_user.id, data={'full_name': name})
    await state.set_state("get_region")


@dp.callback_query_handler(state="get_region", chat_type=['private'])
async def get_region(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    db = call.bot.get('db')
    c_data = call.data.split("_")[1]
    region = regions.get(int(c_data))
    update_user(db=db, user_id=call.from_user.id, data={'region': region, 'verified': True})
    await message.answer(
        text="<b>E'tiboringiz uchun tashakkur ! \nGuruhdagi testlarda ishtirok etishingiz mumkin🫡</b>",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()


@dp.message_handler(state="get_number", content_types=['contact'], chat_type=['private'])
async def get_contact_(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number[1:] if message.contact.phone_number[0] == "+" \
        else message.contact.phone_number
    await message.delete()
    db = message.bot.get('db')

    update_user(db=db, user_id=message.from_user.id, data={'phone_number': phone_number, 'verified': True})
    await message.answer(
        text="<b>E'tiboringiz uchun tashakkur ! \nGuruhdagi testlarda ishtirok etishingiz mumkin🫡</b>",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()