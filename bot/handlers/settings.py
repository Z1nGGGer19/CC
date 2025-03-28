from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import db
from bot.utils.states import Settings
from config import DORMS
from bot.keyboards.base import dorms_kb, main_menu_kb

router = Router()


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: types.Message):
    """Главное меню настроек"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    # Получаем текущие настройки
    current_dorm = DORMS.get(user['dorm_id'], {}).get('name', 'не указано')

    text = (
        "⚙️ <b>Ваши текущие настройки:</b>\n\n"
        f"🏠 Общежитие: <b>{current_dorm}</b>\n"
        f"🚪 Комната: <b>{user['room']}</b>\n"
        f"👤 Имя: <b>{user['full_name']}</b>\n\n"
        "Выберите параметр для изменения:"
    )

    # Создаем клавиатуру настроек
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🏠 Изменить общежитие", "change_dorm"),
        ("🚪 Изменить комнату", "change_room"),
        ("👤 Изменить имя", "change_name"),
        ("🔙 В главное меню", "settings_back")
    ]
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(1)

    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("change_"))
async def change_settings(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик изменения настроек"""
    setting_type = callback.data.split("_")[1]

    if setting_type == "dorm":
        await callback.message.edit_text(
            "Выберите новое общежитие:",
            reply_markup=dorms_kb()
        )
        await state.set_state(Settings.dorm)

    elif setting_type == "room":
        await callback.message.edit_text(
            "Введите новый номер комнаты:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Settings.room)

    elif setting_type == "name":
        await callback.message.edit_text(
            "Введите ваше новое полное имя (Фамилия Имя):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Settings.full_name)

    await callback.answer()


@router.message(Settings.dorm, F.text)
async def process_new_dorm(message: types.Message, state: FSMContext):
    """Обработка нового общежития"""
    dorm_name = message.text
    dorm_id = next((id for id, dorm in DORMS.items() if dorm["name"] == dorm_name), None)

    if not dorm_id:
        await message.answer("❌ Пожалуйста, выберите общежитие из списка")
        return

    db.update_user_dorm(message.from_user.id, dorm_id)
    await state.clear()
    await message.answer(
        f"✅ Общежитие изменено на: <b>{dorm_name}</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(Settings.room, F.text)
async def process_new_room(message: types.Message, state: FSMContext):
    """Обработка нового номера комнаты"""
    room = message.text.strip()
    if not room.isdigit():
        await message.answer("❌ Номер комнаты должен содержать только цифры")
        return

    db.update_user_room(message.from_user.id, room)
    await state.clear()
    await message.answer(
        f"✅ Номер комнаты изменен на: <b>{room}</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(Settings.full_name, F.text)
async def process_new_name(message: types.Message, state: FSMContext):
    """Обработка нового имени"""
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("❌ Пожалуйста, введите и фамилию, и имя")
        return

    db.update_user_full_name(message.from_user.id, full_name)
    await state.clear()
    await message.answer(
        f"✅ Имя изменено на: <b>{full_name}</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "settings_back")
async def settings_back(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()