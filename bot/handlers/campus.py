from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import db
from config import CAMPUS_CONNECT

router = Router()


def get_campus_main_kb() -> InlineKeyboardMarkup:
    """Клавиатура основного меню Кампус Коннект"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏆 Мой рейтинг", callback_data="campus_my_rating"),
        InlineKeyboardButton(text="📊 Топ участников", callback_data="campus_top")
    )
    builder.row(
        InlineKeyboardButton(text="📜 Правила", callback_data="campus_rules"),
        InlineKeyboardButton(text="🎁 Призы", callback_data="campus_rewards")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить активность", callback_data="campus_add_activity")
    )
    return builder.as_markup()


@router.message(Command("campus"))
@router.message(F.text == "🏆 Кампус Коннект")
async def campus_menu(message: types.Message):
    """Обработчик главного меню Кампус Коннект"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    await message.answer(
        f"🏆 <b>Кампус Коннект</b>\n\n"
        f"Ваши баллы: <b>{user['points']}</b>\n"
        f"Место в рейтинге: <b>{db.get_user_rank(message.from_user.id)}</b>\n\n"
        "Выберите действие:",
        reply_markup=get_campus_main_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("campus_"))
async def campus_actions(callback: types.CallbackQuery):
    """Обработчик всех действий Кампус Коннект"""
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = db.get_user(user_id)

    if action == "my_rating":
        text = (
            f"📊 <b>Ваш рейтинг</b>\n\n"
            f"Баллы: <b>{user['points']}</b>\n"
            f"Место в топе: <b>{db.get_user_rank(user_id)}</b>\n\n"
            f"Активности за последний месяц: <b>5</b>"
        )

    elif action == "top":
        top_users = db.get_top_users(limit=10)
        text = "🏆 <b>Топ 10 участников</b>\n\n"
        text += "\n".join(
            f"{i + 1}. {u['full_name']} - {u['points']} баллов"
            for i, u in enumerate(top_users)
        )

    elif action == "rules":
        text = "📜 <b>Правила программы</b>\n\n"
        text += "\n".join(
            f"• {act}: {points} баллов"
            for act, points in CAMPUS_CONNECT["point_rules"].items()
        )

    elif action == "rewards":
        text = "🎁 <b>Доступные призы</b>\n\n"
        text += "\n".join(
            f"{i + 1}. {reward}"
            for i, reward in enumerate(CAMPUS_CONNECT["rewards"])
        )

    elif action == "add_activity":
        text = "Выберите тип активности:"
        kb = get_activities_kb()
        await callback.message.edit_text(text, reply_markup=kb)
        return

    else:
        await callback.answer("Неизвестное действие")
        return

    # Кнопка "Назад" для всех действий
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="campus_back"
    ))

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


def get_activities_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора активностей"""
    builder = InlineKeyboardBuilder()
    activities = [
        ("Участие в мероприятии", "activity_event"),
        ("Организация мероприятия", "activity_org"),
        ("Волонтерство", "activity_volunteer"),
        ("Спортивное достижение", "activity_sport")
    ]
    for text, callback_data in activities:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"campus_confirm_{callback_data}"
        ))
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data.startswith("campus_confirm_"))
async def confirm_activity(callback: types.CallbackQuery):
    """Подтверждение добавления активности"""
    activity_type = callback.data.split("_")[2]
    points = {
        "activity_event": 10,
        "activity_org": 20,
        "activity_volunteer": 15,
        "activity_sport": 25
    }.get(activity_type, 0)

    db.add_points(callback.from_user.id, points)

    await callback.message.edit_text(
        f"✅ Начислено {points} баллов за {activity_type.replace('_', ' ')}!\n"
        f"Новый баланс: {db.get_user(callback.from_user.id)['points']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="В меню", callback_data="campus_back")
        ]])
    )
    await callback.answer()