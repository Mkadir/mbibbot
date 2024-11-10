from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def test_menu_returner(tests: list):
    test_menu = InlineKeyboardMarkup(row_width=1)
    for i in tests:
        test_menu.add(
            InlineKeyboardButton(
                text=f"{i.title} ...",
                callback_data=i.id
            )
        )

    test_menu.add(
        InlineKeyboardButton(
            text="Test qo'shish",
            callback_data="add_test"
        )
    )
    return test_menu


def regions_keyboard():
    from data.config import regions
    ikb = InlineKeyboardMarkup(
        row_width=2
    )
    for i, j in regions.items():
        ikb.insert(
            InlineKeyboardButton(
                text=f"{j}",
                callback_data=f"region_{i}"
            )
        )

    return ikb
