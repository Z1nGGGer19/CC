from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

def admin_panel_kb():
    builder = InlineKeyboardBuilder()
    buttons = [
        ("📅 Создать мероприятие", "admin_create_event"),
        ("👑 Назначить админа", "admin_add_admin"),
        ("📢 Сделать объявление", "admin_send_announce"),
        ("🔍 Поиск жильцов", "admin_search_residents"),
        ("⬅️ В меню", "admin_back_to_menu")
    ]
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(1)
    return builder.as_markup()

def dorms_selection_kb(dorms):
    builder = InlineKeyboardBuilder()
    for dorm in dorms:
        builder.add(InlineKeyboardButton(
            text=dorm["name"],
            callback_data=f"admin_select_dorm_{dorm['id']}"
        ))
    builder.adjust(2)
    return builder.as_markup()
def back_to_admin_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Назад в админку"))
    return keyboard


from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def confirm_action_kb(action_type: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()

    callback_data = f"confirm_{action_type}"
    if item_id:
        callback_data += f"_{item_id}"

    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=callback_data),
        InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel")
    )
    return builder.as_markup()