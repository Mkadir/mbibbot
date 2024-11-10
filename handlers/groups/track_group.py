from aiogram import types
from aiogram.dispatcher.filters import ChatTypeFilter

from data.config import ADMINS
from loader import dp, bot
from database.crud import add_result_question, get_user_by_tg_id, get_existing_answer
from data.config import GROUP_ID


@dp.poll_answer_handler()
async def some_poll_answer_handler(poll_answer: types.PollAnswer):
    db = poll_answer.bot.get('db')

    user_id = poll_answer.user.id
    user_in_db = get_user_by_tg_id(db=db, tg_id=user_id)
    user_first_name = poll_answer.user.full_name
    user_username = poll_answer.user.username
    poll_id = poll_answer.poll_id
    selected_option = poll_answer.option_ids[0]

    # Check if the user is an admin or not
    if str(user_id) not in ADMINS:
        # If the user is not verified, prompt for registration
        if not user_in_db.verified:
            # Format the mention
            if user_username:
                mention = f"@{user_username}"
            else:
                mention = f"<a href='tg://user?id={user_id}'>{user_first_name}</a>"

            # Send the message mentioning the user
            await bot.send_message(
                chat_id=GROUP_ID,  # Replace with your group chat ID
                text=f"<b>🫡 Hurmatli {mention}, iltimos ro'yxatdan o'ting 👇</b>",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Ro'yxatdan o'tish",
                                url="https://t.me/MBIB_vote_bot?start=reg"
                            )
                        ]
                    ]
                )
            )

    # Check if there's an existing answer for this user and poll
    existing_answer = get_existing_answer(db=db, poll_id=poll_id, user_id=user_in_db.id)

    if existing_answer:
        # Update the existing answer
        existing_answer.selected_option = selected_option
        existing_answer.is_correct = selected_option == int(existing_answer.question.correct_option)
        db.commit()
    else:
        # Add a new answer
        add_result_question(
            db=db,
            poll_id=poll_id,
            selected_option=selected_option,
            user_id=user_id
        )
