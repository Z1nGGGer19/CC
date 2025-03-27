from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from bot.database import db
from config import DORMS

router = Router()


def generate_calendar(dorm_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Генерация календаря мероприятий для конкретного общежития"""
    events = DORMS[dorm_id]["events"]
    current_date = datetime.now()

    # Формируем текст с мероприятиями на ближайшие 2 недели
    text = f"📅 <b>Календарь мероприятий {DORMS[dorm_id]['name']}</b>\n\n"

    for event in events:
        event_date = current_date + timedelta(days=events.index(event) * 3)  # Примерные даты
        text += f"🗓 <u>{event_date.strftime('%d.%m')}</u> - {event}\n"

    # Создаем интерактивные кнопки
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Записаться на мероприятие",
            callback_data="events_register"
        ),
        InlineKeyboardButton(
            text="ℹ️ Подробнее",
            callback_data="events_more_info"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📢 Предложить мероприятие",
            callback_data="events_suggest"
        )
    )

    return text, builder.as_markup()


@router.message(F.text == "📅 Календарь мероприятий")
async def events_handler(message: types.Message):
    """Обработчик главного меню мероприятий"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    dorm_id = user["dorm_id"]
    text, keyboard = generate_calendar(dorm_id)

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "events_more_info")
async def events_more_info(callback: types.CallbackQuery):
    """Детальная информация о мероприятиях"""
    user = db.get_user(callback.from_user.id)
    dorm_info = DORMS[user["dorm_id"]]

    text = (
        f"ℹ️ <b>Детали мероприятий в {dorm_info['name']}</b>\n\n"
        "📍 Место проведения: холл 1 этажа\n"
        "⏰ Время: 18:00-20:00\n"
        "📌 Контакт для справок: @event_manager\n\n"
        "Для записи нажмите кнопку ниже👇"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✍️ Записаться",
            callback_data="events_register"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="events_back"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "events_register")
async def register_for_event(callback: types.CallbackQuery):
    """Регистрация на мероприятие"""
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Вы записаны на ближайшее мероприятие в {DORMS[user['dorm_id']]['name']}!\n\n"
        "Мы пришлем вам напоминание за день до события.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Назад", callback_data="events_back")
        ]])
    )
    await callback.answer()


@router.callback_query(F.data == "events_suggest")
async def suggest_event(callback: types.CallbackQuery):
    """Предложение нового мероприятия"""
    await callback.message.edit_text(
        "✏️ <b>Предложите свое мероприятие</b>\n\n"
        "Напишите название и описание вашего предложения в одном сообщении.\n"
        "Пример:\n"
        "<i>\"Киновечер: Просмотр и обсуждение фильма 'Интерстеллар' с попкорном\"</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "events_back")
async def events_back(callback: types.CallbackQuery):
    """Возврат в главное меню мероприятий"""
    user = db.get_user(callback.from_user.id)
    text, keyboard = generate_calendar(user["dorm_id"])
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()