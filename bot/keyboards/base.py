from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton

def main_menu_kb(is_admin=False):
    builder = ReplyKeyboardBuilder()
    buttons = [
        "📅 Календарь мероприятий",
        "📜 Правила проживания",
        "🆘 Поддержка",
        "🏆 Кампус Коннект",
        "👥 Общажное дело",
        "🔍 Поиск жильцов",
        "⚙️ Настройки"
    ]
    if is_admin:  # Только для админов
        buttons.append("👑 Управление")
    for btn in buttons:
        builder.add(KeyboardButton(text=btn))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

def dorms_kb():
    builder = ReplyKeyboardBuilder()
    from config import DORMS
    for dorm in DORMS.values():
        builder.add(KeyboardButton(text=dorm["name"]))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)