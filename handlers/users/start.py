from typing import List, Optional
from dataclasses import dataclass
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import PollOption
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.utils.callback_data import CallbackData
import math
import ast
from sqlalchemy.orm import Session
from database.models import TestQuestions, Tests
from keyboards.default.simple import home
from loader import dp, bot
from database.crud import get_tests, add_test, add_test_question, get_test_by_id, delete_test, get_questions_by_id, update_question
from data.config import ADMINS, GROUP_ID
from typing import List, Optional
import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import TelegramAPIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Callback factories
test_cb = CallbackData('test', 'action', 'page', 'test_id')


class QuizStates:
    """State constants for the quiz flow"""
    TEST_MENU = "test_menu"
    GET_TEST_TITLE = "get_test_title"
    COLLECTING_QUESTIONS = "collecting_questions"
    TEST_MANAGEMENT = "test_management"


@dataclass
class QuizQuestion:
    """Represents a single quiz question"""
    question: str
    options: List[PollOption]
    correct_option: int
    media_content: Optional[str] = None
    media_type: Optional[str] = None


class QuizCache:
    """Handles temporary storage of quiz data"""

    def __init__(self):
        self.questions: List[QuizQuestion] = []
        self.current_question: Optional[QuizQuestion] = None
        self.title: Optional[str] = None

    def add_question(self, question: QuizQuestion):
        self.questions.append(question)
        self.current_question = None

    def clear_current_question(self):
        self.questions.pop()

    def clear_all(self):
        self.questions = []
        self.current_question = None
        self.title = None

    def get_len(self):
        return len(self.questions)


# Initialize cache
quiz_cache = QuizCache()


@dp.message_handler(user_id=ADMINS, commands=['start'], state="*", chat_type=['private'])
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        text="<b>Bosh menu</b>",
        reply_markup=home
    )
    await state.finish()
    quiz_cache.clear_all()


def get_tests_keyboard(tests: List, page: int = 1, items_per_page: int = 5) -> types.InlineKeyboardMarkup:
    """Create paginated keyboard for tests"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    # Calculate pagination
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    total_pages = math.ceil(len(tests) / items_per_page)
    tests = list(reversed(tests))
    # Add test buttons
    for test in tests[start_idx:end_idx]:
        keyboard.add(
            types.InlineKeyboardButton(
                text=test.title,
                callback_data=test_cb.new(action='view', page=page, test_id=test.id)
            )
        )

    # Add navigation row
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️ Prev",
                callback_data=test_cb.new(action='page', page=page - 1, test_id=0)
            )
        )

    # Add button
    nav_buttons.append(
        types.InlineKeyboardButton(
            text="➕ Qo'shish",
            callback_data=test_cb.new(action='add', page=0, test_id=0)
        )
    )

    if page < total_pages:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="Next ➡️",
                callback_data=test_cb.new(action='page', page=page + 1, test_id=0)
            )
        )

    keyboard.row(*nav_buttons)
    return keyboard


@dp.message_handler(user_id=ADMINS, text="📊 Testlar", state="*")
async def show_tests_menu(message: types.Message, state: FSMContext):
    """Handle the tests menu button"""
    await state.finish()
    try:
        db = message.bot.get('db')
        tests = get_tests(db)

        if not tests:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text="➕ Qo'shish",
                    callback_data=test_cb.new(action='add', page=0, test_id=0)
                )
            )
            await message.answer("Quzilar mavjud emas!", reply_markup=keyboard)
        else:
            await message.answer(
                text="Available Tests:",
                reply_markup=get_tests_keyboard(tests)
            )

        await state.set_state(QuizStates.TEST_MENU)

    except Exception as e:
        await message.answer(f"Error loading tests: {str(e)}")


@dp.message_handler(user_id=ADMINS, commands=['yakunlash'], state=QuizStates.COLLECTING_QUESTIONS)
async def finish_test(message: types.Message, state: FSMContext):
    """Finish test creation"""
    if len(quiz_cache.questions) < 1:
        await message.answer("Savollar birdan ortiq bo'lishi kerak")
        return

    try:
        # Save test
        db = message.bot.get('db')
        test = add_test(db=db, title=quiz_cache.title)

        # Save questions
        for question in quiz_cache.questions:
            options = [option.text for option in question.options]
            add_test_question(
                db=db,
                test_id=test.id,
                question=question.question,
                options=str(options),
                correct_option=question.correct_option,
                media_content=question.media_content if question.media_content else None,
                media_type=question.media_type
            )

        await message.answer(
            f"'{quiz_cache.title}'<b> Quiz {len(quiz_cache.questions)} ta savol bilan yaratildi ✅</b>",
            reply_markup=home
        )
        quiz_cache.clear_all()

        # Show tests menu
        tests = get_tests(db)
        await message.answer(
            text="Available Tests:",
            reply_markup=get_tests_keyboard(tests)
        )
        await state.set_state(QuizStates.TEST_MENU)

    except Exception as e:
        await message.answer(f"Error saving test: {str(e)}")


@dp.callback_query_handler(test_cb.filter(action='page'), state=QuizStates.TEST_MENU)
async def handle_page_navigation(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """Handle pagination navigation"""
    page = int(callback_data['page'])
    db = callback.bot.get('db')
    tests = get_tests(db)

    await callback.message.edit_reply_markup(
        reply_markup=get_tests_keyboard(tests, page)
    )


@dp.callback_query_handler(test_cb.filter(action='add'), state=QuizStates.TEST_MENU)
async def start_test_creation(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    """Start test creation process"""
    quiz_cache.clear_all()
    text = """
<b>Test uchun sarlavha kiriting</b>
<i>Misol uchun: T2024.11.31 yoki TEST11.31</i>
"""
    await callback.message.answer(
        text,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(QuizStates.GET_TEST_TITLE)


@dp.message_handler(user_id=ADMINS, state=QuizStates.GET_TEST_TITLE)
async def process_test_title(message: types.Message, state: FSMContext):
    """Handle test title input"""
    title = message.text.strip()
    if 3 > len(title) or len(title) > 12:
        await message.answer(
            "<b>Maximal 4-12 belgidan iborat bo'lishi kerak</b>\n<i>Misol uchun: T2024.11.31 yoki TEST11.31</i>")
        return

    quiz_cache.title = title
    await state.update_data(title=title)
    text = """
Yaxshi. 
Endi menga birinchi savolingizni yuboring. 
Shu bilan bir qatorda, siz menga ushbu savoldan <b>oldin</b> ko'rsatiladigan <b>matn</b> yoki <b>media</b> xabar yuborishingiz mumkin.


<b>Ogohlantirish: bu bot anonim so‘rovlar yarata olmaydi. Guruhdagi foydalanuvchilar boshqa a'zolarning ovozlarini ko'radi.</b>
"""
    await message.answer(
        text=text,
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="Quiz yaratish",
                                         request_poll=types.KeyboardButtonPollType(type=types.PollType.QUIZ))
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
    await state.set_state(QuizStates.COLLECTING_QUESTIONS)


@dp.message_handler(user_id=ADMINS, state=QuizStates.COLLECTING_QUESTIONS, content_types=['poll'])
async def get_poll(message: types.Message, state: FSMContext):
    data = await state.get_data()
    media_type = data.get('media_type')
    media_content = data.get('media_content')
    poll = message.poll
    poll_id = poll.id
    question = poll.question
    options = poll.options
    correct_option = poll.correct_option_id
    quiz_cache.add_question(
        question=QuizQuestion(
            question=question,
            options=options,
            correct_option=correct_option,
            media_content=media_content,
            media_type=media_type
        )
    )
    q_count = quiz_cache.get_len()
    await state.update_data(media_type=None)
    text = f"""
<b>Aboyib, {q_count}ta test qo'shildi.</b>

Keyingi savolingizni yuboring. 
Shu bilan bir qatorda, siz menga ushbu savoldan <b>oldin</b> ko'rsatiladigan <b>matn</b> yoki <b>media</b> xabar yuborishingiz mumkin.

<i>Agar xatolik bo'lsa, </i>/bekor <i>yuboring.</i>
<i>Yakunlash uchun /yakunlash yuboring</i>
    """
    await message.answer(
        text=text
    )


@dp.message_handler(user_id=ADMINS, state=QuizStates.COLLECTING_QUESTIONS, commands=['bekor'])
async def cancel_question(message: types.Message, state: FSMContext):
    if quiz_cache.get_len() == 0:
        await message.answer(
            text="Bosh menu",
            reply_markup=home
        )
        quiz_cache.clear_all()
        await state.finish()
        return
    quiz_cache.clear_current_question()
    await message.answer(
        text=f"<b>Sizda {quiz_cache.get_len()} ta test bor, qo'shishda davom etishingiz mumkin</b>"
    )


@dp.message_handler(user_id=ADMINS, state=QuizStates.COLLECTING_QUESTIONS, content_types=['text', 'photo', 'video'])
async def process_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    media = data.get('media_type', 0)
    """Handle question input"""
    if media:
        await message.answer("<b>Avval yuborilgan media uchun testlarni yuboring</b>\nBekor qilish uchun /bekor")
        return

    media_content = None
    media_type = None

    if message.photo:
        media_content = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        media_content = message.video.file_id
        media_type = 'video'
    if message.audio:
        media_content = message.audio.file_id
        media_type = 'audio'
    if message.voice:
        media_content = message.voice.file_id
        media_type = 'voice'
    if message.document:
        media_content = message.document.file_id
        media_type = 'document'

    await state.update_data(
        media_content=media_content,
        media_type=media_type
    )

    await message.reply(
        text="<b>Ajoyib, endi quyidagi tugma orqali savolni yuboring</b>",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="Quiz yaratish",
                                         request_poll=types.KeyboardButtonPollType(type=types.PollType.QUIZ))
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


@dp.callback_query_handler(test_cb.filter(action='view'), state=QuizStates.TEST_MENU)
async def view_test(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """View test details and management options"""
    test_id = int(callback_data['test_id'])
    db = callback.bot.get('db')
    test = get_test_by_id(db=db, test_id=test_id)

    if not test:
        await callback.answer("Test topilmadi!")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📤 Guruhga yuborish", callback_data=f"send_group_{test_id}"),
        types.InlineKeyboardButton(text="📊 Hisobot", callback_data=f"stats_{test_id}"),
        types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_{test_id}"),
        types.InlineKeyboardButton(text="📤 Xabar yuborish", callback_data=f"send_message_{test_id}"),
        types.InlineKeyboardButton("⬅️ Ortga", callback_data=test_cb.new(action='page', page=1, test_id=0))
    )

    await callback.message.edit_text(
        f"Test: {test.title}\n"
        f"Savollar soni: {len(test.questions)} ta\n"
        "Amalni tanlang:",
        reply_markup=keyboard
    )


@dp.callback_query_handler(user_id=ADMINS, text_contains="delete_", state="*")
async def delete_test_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    test_id = call.data.split("_")[1]
    db = call.bot.get('db')
    test = get_test_by_id(db=db, test_id=int(test_id))
    if not test:
        await call.message.answer(
            text="<b>Test topilmadi</b>"
        )
        return

    await call.message.edit_reply_markup()
    delete_test(db, test_id)
    await call.message.answer(
        text="<b>Muvaffaqiyatli o'chirildi</b>"
    )
    try:

        tests = get_tests(db)

        if not tests:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text="➕ Qo'shish",
                    callback_data=test_cb.new(action='add', page=0, test_id=0)
                )
            )
            await call.message.answer("Quzilar mavjud emas!", reply_markup=keyboard)
        else:
            await call.message.answer(
                text="<b>Mavjud testlar</b>",
                reply_markup=get_tests_keyboard(tests)
            )

        await state.set_state(QuizStates.TEST_MENU)

    except Exception as e:
        await call.message.answer(f"Error loading tests: {str(e)}")


async def send_media_message(bot, chat_id: int, media_type: str, media_content: str) -> bool:
    """Helper function to send different types of media messages."""
    try:
        if media_type == 'video':
            await bot.send_video(chat_id=chat_id, video=media_content)
        elif media_type == 'photo':
            await bot.send_photo(chat_id=chat_id, photo=media_content)
        elif media_type == 'audio':
            await bot.send_audio(chat_id=chat_id, audio=media_content)
        elif media_type == 'voice':
            await bot.send_voice(chat_id=chat_id, voice=media_content)
        elif media_type == 'document':
            await bot.send_document(chat_id=chat_id, document=media_content)
        elif media_type == 'text':
            await bot.send_message(chat_id=chat_id, text=media_content)
        else:
            logger.warning(f"Unsupported media type: {media_type}")
            return False
        return True
    except TelegramAPIError as e:
        logger.error(f"Failed to send {media_type}: {str(e)} (file_id: {media_content})")
        return False


async def send_poll_message(bot, db: Session, chat_id: int, question: str,
                            options: str, correct_option: int, question_id: int= None,) -> bool:
    """Helper function to send poll messages."""
    options = ast.literal_eval(options)
    try:
        # print(options)
        message = await bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            correct_option_id=correct_option,
            is_anonymous=False,
            type='quiz'
        )
        poll_id = message.poll.id
        update_question(db=db, question_id=question_id, poll_id=poll_id)
        return True
    except TelegramAPIError as e:
        logger.error(f"Failed to send poll: {str(e)}")
        return False


@dp.callback_query_handler(user_id=ADMINS, state="*", text_contains="send_group_")
async def send_to_group(call: types.CallbackQuery, state: FSMContext):
    """Handler for sending test questions to a group."""
    try:
        # Extract test ID and get database connection
        test_id = call.data.split("_")[2]
        # print(test_id)
        db = call.bot.get('db')

        # Validate GROUP_ID
        if not GROUP_ID:
            await call.message.answer("Error: GROUP_ID is not configured")
            logger.error("GROUP_ID is not configured")
            return

        # Get test questions
        tests: List[TestQuestions] = get_questions_by_id(db=db, test_id=test_id)
        # print(tests)
        if not tests:
            await call.message.answer("No questions found for this test")
            return

        success_count = 0
        total_items = len(tests)

        # Process each test item
        for item in tests:
            # Send media content if present
            if hasattr(item, 'media_type') and hasattr(item, 'media_content'):
                media_success = await send_media_message(
                    call.bot,
                    GROUP_ID,
                    item.media_type,
                    item.media_content,
                    
                )
            # Send poll if present
            if all(hasattr(item, attr) for attr in ['question', 'options', 'correct_option']):
                if item.question and item.options and isinstance(item.correct_option, int):
                    poll_success = await send_poll_message(
                        bot=call.bot,
                        db=db,
                        chat_id=GROUP_ID,
                        question=item.question,
                        options=item.options,
                        correct_option=item.correct_option,
                        question_id=item.id
                    )
                    if poll_success:
                        success_count += 1

        # Send completion message with status
        status_message = (
            f"<b>Yuborish yakunlandi ✅</b>\n"
            f"Yuborilgan: {success_count}/{total_items}"
        )
        await call.message.answer(text=status_message)

        # Answer the callback query to remove loading state
        await call.answer()

    except Exception as e:
        error_msg = f"Error processing test {test_id}: {str(e)}"
        logger.error(error_msg)
        await call.message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await call.answer()
