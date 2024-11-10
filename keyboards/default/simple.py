from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppData, WebAppInfo

home = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📊 Testlar"
            ),
            KeyboardButton(
                text="👥 Users"
            )
        ]
    ],
    resize_keyboard=True
)
