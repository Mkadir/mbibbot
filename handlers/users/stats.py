import asyncio
from sqlalchemy import func
from datetime import datetime
from aiogram import types
from sqlalchemy.orm import Session
from aiogram.dispatcher import FSMContext
import os
from data.config import ADMINS
from database.crud import get_test_results, export_results_to_excel
from database.models import Tests, TestQuestions, Results, Users
from loader import dp, bot
from aiogram import types


@dp.callback_query_handler(state="*", user_id=ADMINS, text_contains="stats_")
async def statistics_test_(call: types.CallbackQuery, state: FSMContext):
    test_id = call.data.split("_")[1]
    db = call.bot.get('db')
    await call.answer(text="Hisobot tayyorlanmoqda ⏳", show_alert=True)
    test_results = export_results_to_excel(db, int(test_id))
    await call.message.answer_document(
        document=open(test_results, 'rb'),
    )
    os.remove(test_results)


async def send_test_results_message(call: types.CallbackQuery, test_id: int, db: Session):
    # Get total questions count for this test
    total_questions = db.query(TestQuestions).filter(TestQuestions.test_id == test_id).count()

    # Get all participants for this test
    participants = db.query(Users).join(
        Results, Results.user_id == Users.id
    ).filter(
        Results.test_id == test_id
    ).distinct().all()
    sent = 0
    for participant in participants:
        # Count correct answers for this participant
        correct_answers = db.query(Results).filter(
            Results.test_id == test_id,
            Results.user_id == participant.id,
            Results.is_correct == True
        ).count()

        # Check if participant answered any questions
        answered_questions = db.query(Results).filter(
            Results.test_id == test_id,
            Results.user_id == participant.id
        ).count()

        if answered_questions == 0:
            message = "⚠️ Hurmatli {}, testlarda faol ishtirok eting, ogohlantirish!".format(
                participant.full_name
            )
        else:
            if correct_answers >= 5:
                message = "Hurmatli {}, bugun a'lo darajada javob berdingiz. {} ta to'g'ri javob.".format(
                    participant.full_name, correct_answers
                )
            elif correct_answers == 4:
                message = "Hurmatli {}, bugun yaxshi darajada javob berdingiz. {} ta to'g'ri javob.".format(
                    participant.full_name, correct_answers
                )
            elif correct_answers == 3:
                message = "Hurmatli {}, bugun qoniqarli darajada javob berdingiz. {} ta to'g'ri javob.".format(
                    participant.full_name, correct_answers
                )
            else:
                message = "Hurmatli {}, bugun qoniqarsiz darajada javob berdingiz. {} ta to'g'ri javob.".format(
                    participant.full_name, correct_answers
                )

        # Send message to participant
        if sent % 10 == 0:
            await asyncio.sleep(1)
        try:
            await call.bot.send_message(participant.tg_id, message)
        except Exception as e:
            for admin in ADMINS:
                await bot.send_message(
                    chat_id=admin,
                    text=f"<b>Xabar yuborishda xatolik, foydalanuvchi </b><a href='tg://user?id={participant.tg_id}'>{participant.full_name}</a>\n"
                         f"Xolat: {e}"
                )
                await asyncio.sleep(0.5)
                print(f"Error sending message to user {participant.tg_id}: {e}")
        sent += 1


@dp.callback_query_handler(state="*", user_id=ADMINS, text_contains='send_message_')
async def send_message_for_test(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    try:
        test_id = int(call.data.split("_")[2])
        db = call.bot.get("db")

        # Send results messages
        await send_test_results_message(call, test_id, db)

        # Confirm to admin
        await call.answer("Natijalar bo'yicha xabarlar barcha ishtirokchilarga yuborildi!", show_alert=True)

    except Exception as e:
        await call.answer(f"Xatolik yuz berdi: {str(e)}", show_alert=True)
    finally:
        await state.finish()
