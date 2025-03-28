from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base import main_menu_kb  # Убедитесь, что импорт правильный
from bot.database import db
from bot.utils.states import Registration
from config import DORMS

router = Router()

async def show_main_menu(message: types.Message):
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
    for btn in buttons:
        builder.add(KeyboardButton(text=btn))
    builder.adjust(2, 2, 2, 1)
    await message.answer(
        "Главное меню:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    if db.get_user(message.from_user.id):
        await show_main_menu(message)
    else:
        await message.answer(
            "👋 Добро пожаловать! Для регистрации введите ваше полное имя (Фамилия Имя):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Registration.full_name)


@router.message(Registration.full_name, F.text)
async def process_full_name(message: types.Message, state: FSMContext):
    if len(message.text.split()) < 2:
        await message.answer("❌ Пожалуйста, введите и фамилию, и имя")
        return

    await state.update_data(full_name=message.text.strip())

    # Создаем inline-клавиатуру с общежитиями
    builder = InlineKeyboardBuilder()
    for dorm_id, dorm in DORMS.items():
        builder.add(InlineKeyboardButton(
            text=dorm["name"],
            callback_data=f"select_dorm_{dorm_id}"
        ))
    builder.adjust(2)

    await message.answer(
        "🏠 Теперь выберите ваше общежитие:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(Registration.dorm)


@router.callback_query(F.data.startswith("select_dorm_"))
async def process_dorm_selection(callback: types.CallbackQuery, state: FSMContext):
    dorm_id = int(callback.data.split("_")[2])
    await state.update_data(dorm_id=dorm_id)

    await callback.message.edit_text(
        f"Вы выбрали: {DORMS[dorm_id]['name']}\n\n"
        "Теперь введите номер вашей комнаты:",
        reply_markup=None  # Убираем inline-клавиатуру
    )
    await callback.answer()
    await state.set_state(Registration.room)


@router.message(Registration.room, F.text)
async def process_room(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Номер комнаты должен содержать только цифры")
        return

    data = await state.get_data()
    db.add_user(
        user_id=message.from_user.id,
        dorm_id=data["dorm_id"],
        room=message.text.strip(),
        full_name=data["full_name"]
    )

    await message.answer(
        "✅ Регистрация завершена!",
        reply_markup=main_menu_kb()
    )
    await state.clear()


@router.message(Command("register"))
async def register_handler(message: types.Message):
    """Регистрация для предварительно добавленных пользователей"""
    user = db.get_user_by_name(message.from_user.full_name)

    if not user:
        await message.answer("❌ Ваших данных нет в системе. Обратитесь к администратору.")
        return

    if user['is_registered']:
        await message.answer("ℹ️ Вы уже зарегистрированы!")
        return

    db.register_user(user['id'], message.from_user.id)
    await message.answer(
        f"✅ Регистрация завершена!\n"
        f"Ваши данные:\n"
        f"Общежитие: {user['dorm_name']}\n"
        f"Комната: {user['room']}",
        reply_markup=main_menu_kb()
    )
@router.message(Registration.room, F.text)
async def process_room(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Номер комнаты должен содержать только цифры")
        return

    data = await state.get_data()
    try:
        db.add_user(
            user_id=message.from_user.id,
            dorm_id=data["dorm_id"],
            room=message.text.strip(),
            full_name=data["full_name"]
        )
        await message.answer(
            "✅ Регистрация завершена!",
            reply_markup=main_menu_kb()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка регистрации: {str(e)}")
    finally:
        await state.clear()