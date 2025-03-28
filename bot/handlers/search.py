from aiogram import Router, types, F
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict

from bot.database import db
from bot.keyboards.base import main_menu_kb

router = Router()


@router.message(F.text == "🔍 Поиск жильцов")
async def search_start(message: types.Message):
    """Обработчик начала поиска"""
    if not db.get_user(message.from_user.id):
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    await message.answer(
        "🔍 <b>Поиск жильцов</b>\n\n"
        "Введите ФИО или часть имени для поиска (минимум 3 символа)\n"
        "Примеры:\n"
        "- <i>Иванов</i>\n"
        "- <i>Анна</i>\n"
        "- <i>Сергеевич</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )


@router.message(F.text.func(lambda text: 3 <= len(text) <= 50))
async def process_search(message: types.Message):
    """Обработка поискового запроса"""
    search_query = message.text.strip()
    results: List[Dict] = db.search_users(search_query)

    if not results:
        await message.answer(
            "🔍 Никого не найдено. Попробуйте изменить запрос.",
            reply_markup=main_menu_kb()
        )
        return

    # Группируем результаты по общежитиям
    results_by_dorm = {}
    for user in results:
        if user['dorm_name'] not in results_by_dorm:
            results_by_dorm[user['dorm_name']] = []
        results_by_dorm[user['dorm_name']].append(user)

    # Формируем текст ответа
    response = []
    for dorm_name, users in results_by_dorm.items():
        dorm_users = "\n".join(
            f"  {i + 1}. {user['full_name']} (комн. {user['room']})"
            for i, user in enumerate(users)
        )
        response.append(f"🏠 <b>{dorm_name}</b>\n{dorm_users}")

    text = "🔍 <b>Результаты поиска:</b>\n\n" + "\n\n".join(response)[:4000]

    # Создаем интерактивные кнопки
    builder = InlineKeyboardBuilder()
    for user in results[:5]:  # Ограничиваем 5 кнопками
        builder.add(InlineKeyboardButton(
            text=f"{user['full_name']} ({user['dorm_name']})",
            callback_data=f"user_detail_{user['user_id']}"
        ))
    builder.adjust(1)

    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("user_detail_"))
async def show_user_detail(callback: types.CallbackQuery):
    """Показ детальной информации о пользователе"""
    user_id = int(callback.data.split("_")[2])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    text = (
        "👤 <b>Информация о жильце:</b>\n\n"
        f"🏠 Общежитие: {user['dorm_name']}\n"
        f"🚪 Комната: {user['room']}\n"
        f"📅 Дата регистрации: {user['registered_at'][:10]}\n\n"
        f"🏆 Баллов в Кампус Коннект: {user.get('points', 0)}"
    )

    # Кнопки действий
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📨 Написать",
            url=f"tg://user?id={user_id}"
        ),
        InlineKeyboardButton(
            text="🔙 Назад к результатам",
            callback_data="search_back"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "search_back")
async def back_to_search_results(callback: types.CallbackQuery):
    """Возврат к результатам поиска"""
    # Здесь можно реализовать сохранение предыдущего поиска
    await callback.message.edit_text(
        "Введите новый поисковый запрос или используйте предыдущие результаты",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="↩️ Вернуться в меню",
                callback_data="search_to_menu"
            )
        ]])
    )
    await callback.answer()


@router.callback_query(F.data == "search_to_menu")
async def return_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()