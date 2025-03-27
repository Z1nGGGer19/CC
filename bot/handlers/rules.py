from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from bot.database import db
from config import DORMS

router = Router()


@router.message(F.text == "📜 Правила проживания")
async def rules_handler(message: types.Message):
    """Обработчик правил проживания с интерактивным меню"""
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пожалуйста, сначала зарегистрируйтесь через /start")
        return

    dorm_id = user["dorm_id"]
    dorm = DORMS.get(dorm_id)

    if not dorm:
        await message.answer("⚠️ Информация по вашему общежитию не найдена")
        return

    # Формируем текст с основными правилами
    rules_text = "\n".join(f"▪️ {rule}" for rule in dorm["rules"][:3])  # Показываем первые 3 правила

    text = (
        f"🏠 <b>Правила проживания в {dorm['name']}</b>\n\n"
        f"{rules_text}\n\n"
        f"📌 Контакт администратора: {dorm['contact']}"
    )

    # Создаем интерактивную клавиатуру
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Все правила",
            callback_data=f"rules_full_{dorm_id}"
        ),
        InlineKeyboardButton(
            text="❓ Частые вопросы",
            callback_data=f"rules_faq_{dorm_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚠️ Чрезвычайные ситуации",
            callback_data=f"rules_emergency_{dorm_id}"
        )
    )

    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("rules_full_"))
async def show_full_rules(callback: types.CallbackQuery):
    """Показ всех правил"""
    dorm_id = int(callback.data.split("_")[2])
    dorm = DORMS.get(dorm_id)

    if not dorm:
        await callback.answer("Информация не найдена")
        return

    full_rules = "\n\n".join(f"▫️ {rule}" for rule in dorm["rules"])

    await callback.message.edit_text(
        f"📜 <b>Полные правила {dorm['name']}:</b>\n\n{full_rules}",
        reply_markup=back_to_rules_kb(dorm_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rules_faq_"))
async def show_faq(callback: types.CallbackQuery):
    """Показ частых вопросов"""
    dorm_id = int(callback.data.split("_")[2])
    dorm = DORMS.get(dorm_id)

    faq = {
        "Можно ли гостей?": "Да, с 9:00 до 23:00, не более 3 человек одновременно",
        "Стирка белья": "Стиральные машины на 1 этаже, график: пн-ср-пт",
        "Уборка комнат": "Обязательная еженедельная уборка по четвергам"
    }

    faq_text = "\n\n".join(f"❓ <b>{q}</b>\n💡 {a}" for q, a in faq.items())

    await callback.message.edit_text(
        f"❓ <b>Частые вопросы ({dorm['name']}):</b>\n\n{faq_text}",
        reply_markup=back_to_rules_kb(dorm_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rules_emergency_"))
async def show_emergency(callback: types.CallbackQuery):
    """Информация по ЧС"""
    contacts = {
        "Охрана": "+7 (XXX) XXX-XX-XX",
        "Дежурный администратор": "+7 (XXX) XXX-XX-XX",
        "МЧС": "112 (экстренный номер)"
    }

    emergency_text = "\n".join(f"🚨 <b>{service}:</b> {number}" for service, number in contacts.items())

    await callback.message.edit_text(
        f"🚨 <b>Контакты для экстренных случаев:</b>\n\n{emergency_text}\n\n"
        "При пожаре немедленно сообщите охране и покиньте здание!",
        reply_markup=back_to_rules_kb(callback.data.split("_")[2]),
        parse_mode="HTML"
    )
    await callback.answer()


def back_to_rules_kb(dorm_id: int) -> InlineKeyboardMarkup:
    """Кнопка возврата к правилам"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔙 Назад к правилам",
        callback_data=f"rules_back_{dorm_id}"
    ))
    return builder.as_markup()


@router.callback_query(F.data.startswith("rules_back_"))
async def back_to_rules(callback: types.CallbackQuery):
    """Возврат к основным правилам"""
    dorm_id = int(callback.data.split("_")[2])
    dorm = DORMS.get(dorm_id)

    rules_text = "\n".join(f"▪️ {rule}" for rule in dorm["rules"][:3])

    await callback.message.edit_text(
        f"🏠 <b>Правила проживания в {dorm['name']}</b>\n\n"
        f"{rules_text}\n\n"
        f"📌 Контакт администратора: {dorm['contact']}",
        reply_markup=main_rules_kb(dorm_id),
        parse_mode="HTML"
    )
    await callback.answer()


def main_rules_kb(dorm_id: int) -> InlineKeyboardMarkup:
    """Основная клавиатура правил"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Все правила",
            callback_data=f"rules_full_{dorm_id}"
        ),
        InlineKeyboardButton(
            text="❓ Частые вопросы",
            callback_data=f"rules_faq_{dorm_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚠️ Чрезвычайные ситуации",
            callback_data=f"rules_emergency_{dorm_id}"
        )
    )
    return builder.as_markup()