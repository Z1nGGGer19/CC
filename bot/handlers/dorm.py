from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import db
from config import DORMS

router = Router()


@router.message(F.text == "👥 Общажное дело")
async def dorm_affairs_handler(message: types.Message):
    # Получаем данные пользователя
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return

    # Получаем информацию об общежитии пользователя
    dorm_id = user['dorm_id']
    dorm_info = DORMS.get(dorm_id)

    if not dorm_info:
        await message.answer("Информация по вашему общежитию не найдена")
        return

    # Формируем текст сообщения
    council = dorm_info.get('student_council', {})
    text = (
        f"🏠 <b>{dorm_info['name']}</b>\n\n"
        "👥 <u>Студенческий совет:</u>\n"
        f"• Председатель: {council.get('head', 'не указан')}\n"
        f"• Заместитель: {council.get('deputy', 'не указан')}\n"
        f"• Контакт: {council.get('contact', 'не указан')}\n\n"
        f"📅 Ближайшее собрание: <b>15.04 в 19:00</b> (холл 1 этажа)\n\n"
        f"📌 Особые правила вашего общежития:\n"
        f"{dorm_info['rules'][0]}"  # Первое правило из списка
    )

    # Создаем инлайн-кнопку для связи
    builder = InlineKeyboardBuilder()
    if council.get('contact'):
        builder.add(InlineKeyboardButton(
            text="📨 Написать в студсовет",
            url=f"tg://resolve?domain={council['contact'].lstrip('@')}"
        ))

    builder.add(InlineKeyboardButton(
        text="📋 Все правила",
        callback_data=f"dorm_rules_{dorm_id}"
    ))

    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("dorm_rules_"))
async def show_full_rules(callback: types.CallbackQuery):
    dorm_id = int(callback.data.split("_")[2])
    dorm_info = DORMS.get(dorm_id)

    if dorm_info:
        rules_text = "\n".join(f"• {rule}" for rule in dorm_info['rules'])
        await callback.message.answer(
            f"📜 <b>Полные правила {dorm_info['name']}:</b>\n\n{rules_text}",
            parse_mode="HTML"
        )
    else:
        await callback.answer("Информация не найдена", show_alert=True)

    await callback.answer()