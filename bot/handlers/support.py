from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime

from bot.database import db
from bot.utils.states import Support
from bot.keyboards.base import main_menu_kb

router = Router()

@router.message(F.text == "🆘 Поддержка")
async def support_handler(message: types.Message, state: FSMContext):
    """Обработчик входа в раздел поддержки"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    # Создаем клавиатуру с вариантами проблем
    builder = ReplyKeyboardBuilder()
    common_issues = [
        "Поломка в комнате",
        "Проблемы с соседями",
        "Вопрос по оплате",
        "Другая проблема"
    ]
    for issue in common_issues:
        builder.add(types.KeyboardButton(text=issue))
    builder.adjust(1)

    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Выберите тип проблемы или опишите ее в одном сообщении:\n"
        "(Максимум 500 символов)\n\n"
        "Пример:\n"
        "<i>\"В комнате 305 не работает розетка, прошу устранить неисправность\"</i>",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="HTML"
    )
    await state.set_state(Support.message)

@router.message(Support.message, F.text.func(len) <= 500)
async def process_support_message(message: types.Message, state: FSMContext):
    """Обработка обращения в поддержку"""
    user = db.get_user(message.from_user.id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Сохраняем обращение в базу данных
    db.add_support_ticket(
        user_id=user['user_id'],
        dorm_id=user['dorm_id'],
        message=message.text,
        timestamp=timestamp
    )

    # Формируем текст подтверждения
    confirmation_text = (
        "✅ <b>Ваше обращение принято!</b>\n\n"
        f"📝 <b>Текст:</b> {message.text[:100]}...\n"
        f"🏠 <b>Общежитие:</b> {user['dorm_name']}\n"
        f"🚪 <b>Комната:</b> {user['room']}\n\n"
        "Мы ответим вам в течение 24 часов.\n"
        "Номер вашего обращения: #{ticket_id}"
    )

    await message.answer(
        confirmation_text,
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
    await state.clear()

    # Отправляем уведомление админу (заглушка)
    admin_notification = (
        "🆘 <b>Новое обращение в поддержку</b>\n\n"
        f"От: {user['full_name']}\n"
        f"Комната: {user['room']}\n"
        f"Общежитие: {user['dorm_name']}\n\n"
        f"Текст: {message.text}"
    )
    # Здесь должен быть код отправки сообщения админу

@router.message(Support.message, F.text.func(len) > 500)
async def process_long_support_message(message: types.Message):
    """Обработка слишком длинного сообщения"""
    await message.answer(
        "❌ Сообщение слишком длинное (максимум 500 символов).\n"
        "Пожалуйста, опишите проблему короче.",
        reply_markup=ReplyKeyboardRemove()
    )