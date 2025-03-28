from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def settings_kb():
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🏠 Изменить общежитие", "change_dorm"),
        ("🚪 Изменить комнату", "change_room"),
        ("👤 Изменить имя", "change_name"),
        ("🔙 Назад", "settings_back")
    ]
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(1)
    return builder.as_markup()