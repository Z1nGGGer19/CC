from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def campus_kb():
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🏆 Рейтинг", "campus_leaderboard"),
        ("📜 Правила", "campus_rules"),
        ("🎁 Призы", "campus_rewards"),
        ("➕ Добавить баллы", "campus_add_points")
    ]
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(2)
    return builder.as_markup()

def campus_actions_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Назад в меню",
        callback_data="campus_back"
    ))
    return builder.as_markup()