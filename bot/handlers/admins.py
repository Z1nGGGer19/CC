from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.admins import (
    admin_panel_kb,
    dorms_selection_kb,
    back_to_admin_kb,
    confirm_action_kb
)
from bot.utils.states import AdminPanel
from config import DORMS
from bot.database import db
from datetime import datetime

router = Router()


# Главное меню админки
@router.message(F.text == "👑 Управление")
async def admin_panel(message: types.Message, state: FSMContext):
    if not db.is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer(
        "Панель администратора:",
        reply_markup=admin_panel_kb()
    )
    await state.set_state(AdminPanel.menu)


# Создание мероприятий
@router.callback_query(F.data == "admin_create_event")
async def create_event_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите данные мероприятия в формате:\n"
        "Название|Описание|Дата (ДД.ММ.ГГГГ)|Время|Место\n\n"
        "Пример:\n"
        "Киновечер|Просмотр фильма|15.06.2024|19:00|Холл 1 этажа",
        reply_markup=back_to_admin_kb()
    )
    await state.set_state(AdminPanel.create_event)


@router.message(AdminPanel.create_event, F.text)
async def process_event_creation(message: types.Message, state: FSMContext):
    try:
        name, desc, date, time, place = message.text.split("|")
        db.add_event(
            name=name.strip(),
            description=desc.strip(),
            date=datetime.strptime(date.strip(), "%d.%m.%Y"),
            time=time.strip(),
            place=place.strip(),
            creator_id=message.from_user.id
        )
        await message.answer("✅ Мероприятие создано и добавлено в расписание!")
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {e}\nПроверьте формат данных")
    await state.clear()


# Управление объявлениями
@router.callback_query(F.data == "admin_send_announce")
async def announce_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите общежитие для объявления:",
        reply_markup=dorms_selection_kb(DORMS.values())
    )
    await state.set_state(AdminPanel.select_dorm)


@router.callback_query(F.data.startswith("admin_select_dorm_"))
async def process_dorm_selection(callback: types.CallbackQuery, state: FSMContext):
    dorm_id = int(callback.data.split("_")[-1])
    await state.update_data(dorm_id=dorm_id)
    await callback.message.edit_text(
        f"Введите текст объявления для {DORMS[dorm_id]['name']}:",
        reply_markup=back_to_admin_kb()
    )
    await state.set_state(AdminPanel.send_announcement)


@router.message(AdminPanel.send_announcement, F.text)
async def send_announcement(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dorm_id = data["dorm_id"]
    residents = db.get_dorm_residents(dorm_id)

    for user in residents:
        try:
            await message.bot.send_message(
                chat_id=user['telegram_id'],
                text=f"📢 Объявление для {DORMS[dorm_id]['name']}:\n\n{message.text}"
            )
        except:
            continue

    await message.answer(f"📢 Объявление отправлено {len(residents)} жильцам!")
    await state.clear()


# Управление пользователями (новый функционал)
@router.callback_query(F.data == "admin_manage_users")
async def manage_users_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="admin_add_user")],
            [InlineKeyboardButton(text="🔍 Поиск пользователей", callback_data="admin_search_users")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]]
        )
    )
    await state.set_state(AdminPanel.manage_users)

    # Добавление пользователей без Telegram ID
@ router.callback_query(F.data == "admin_add_user")
async def add_user_start(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Введите данные пользователя в формате:\n"
            "Общежитие|Комната|ФИО\n\n"
            "Пример:\n"
            "1|305|Иванов Иван Иванович",
            reply_markup=back_to_admin_kb()
        )
        await state.set_state(AdminPanel.add_user)

@router.message(AdminPanel.add_user, F.text)
async def process_add_user(message: types.Message, state: FSMContext):
        try:
            dorm_id, room, full_name = message.text.split("|")
            db.add_temp_user(
                dorm_id=int(dorm_id),
                room=room.strip(),
                full_name=full_name.strip()
            )
            await message.answer("✅ Пользователь добавлен! Он сможет зарегистрироваться через /register")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@router.message(AdminPanel.create_event, F.text)
async def process_event_creation(message: types.Message, state: FSMContext):
        try:
            name, desc, date_str, time, place = map(str.strip, message.text.split("|"))
            event_date = datetime.strptime(date_str, "%d.%m.%Y").date()

            event_id = db.add_event(
                name=name,
                description=desc,
                date=event_date,
                time=time,
                place=place,
                creator_id=message.from_user.id
            )

            # Добавляем мероприятие в расписание для всех жильцов
            dorm_id = (await state.get_data()).get('dorm_id')
            if dorm_id:
                db.add_event_to_dorm_schedule(event_id, dorm_id)

            await message.answer(
                f"✅ Мероприятие #{event_id} создано!\n"
                f"Название: {name}\n"
                f"Дата: {date_str} {time}\n"
                f"Место: {place}",
                reply_markup=admin_panel_kb()
            )
        except ValueError as e:
            await message.answer(
                f"❌ Ошибка формата: {e}\n"
                "Правильный формат:\n"
                "Название|Описание|ДД.ММ.ГГГГ|Время|Место"
            )
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {str(e)}")
        finally:
            await state.clear()

@router.message(AdminPanel.send_announcement, F.text)
async def send_announcement(message: types.Message, state: FSMContext):
        data = await state.get_data()
        dorm_id = data["dorm_id"]

        try:
            # Сохраняем объявление в БД
            announcement_id = db.add_announcement(
                text=message.text,
                dorm_id=dorm_id,
                author_id=message.from_user.id
            )

            # Рассылка жильцам
            stats = {"success": 0, "failed": 0}
            residents = db.get_dorm_residents(dorm_id)

            for user in residents:
                try:
                    await message.bot.send_message(
                        chat_id=user['telegram_id'],
                        text=f"📢 {DORMS[dorm_id]['name']}\n\n{message.text}"
                    )
                    db.mark_announcement_sent(announcement_id, user['id'])
                    stats["success"] += 1
                except:
                    stats["failed"] += 1
                    continue

            await message.answer(
                f"📊 Статистика рассылки:\n"
                f"• Всего получателей: {len(residents)}\n"
                f"• Успешно: {stats['success']}\n"
                f"• Не удалось: {stats['failed']}\n\n"
                f"ID объявления: #{announcement_id}",
                reply_markup=admin_panel_kb()
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка рассылки: {str(e)}")
        finally:
            await state.clear()


@router.message(AdminPanel.add_user, F.text)
async def process_add_user(message: types.Message, state: FSMContext):
    try:
        parts = list(map(str.strip, message.text.split("|")))
        if len(parts) != 3:
            raise ValueError("Неверное количество параметров")

        dorm_id, room, full_name = parts
        user_id = db.add_temp_user(
            dorm_id=int(dorm_id),
            room=room,
            full_name=full_name
        )

        await message.answer(
            f"✅ Пользователь добавлен!\n"
            f"ID: {user_id}\n"
            f"Общежитие: {db.get_dorm_name(dorm_id)}\n"
            f"Комната: {room}\n"
            f"ФИО: {full_name}\n\n"
            f"Для регистрации нужно выполнить команду /register",
            reply_markup=admin_panel_kb()
        )
    except ValueError as e:
        await message.answer(f"❌ Ошибка формата: {e}")
    except Exception as e:
        await message.answer(f"⚠️ Системная ошибка: {str(e)}")
    finally:
        await state.clear()


@router.message(AdminPanel.create_event, F.text)
async def process_event_creation(message: types.Message, state: FSMContext):
    try:
        name, desc, date, time, place = map(str.strip, message.text.split("|"))
        # Сохраняем данные в состоянии
        await state.update_data(
            event_name=name,
            event_desc=desc,
            event_date=date,
            event_time=time,
            event_place=place
        )

        await message.answer(
            f"Подтвердите создание мероприятия:\n\n"
            f"🏷 Название: {name}\n"
            f"📝 Описание: {desc}\n"
            f"📅 Дата: {date} {time}\n"
            f"📍 Место: {place}",
            reply_markup=confirm_action_kb("create_event")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(AdminPanel.send_announcement, F.text)
async def send_announcement(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dorm_id = data["dorm_id"]

    await state.update_data(announce_text=message.text)
    await message.answer(
        f"Подтвердите рассылку в {DORMS[dorm_id]['name']}:\n\n"
        f"📢 Текст:\n{message.text}\n\n"
        f"Количество получателей: {len(db.get_dorm_residents(dorm_id))}",
        reply_markup=confirm_action_kb("send_announce", dorm_id)
    )


@router.callback_query(F.data.startswith("confirm_"))
async def process_confirmation(callback: types.CallbackQuery, state: FSMContext):
    action_type = callback.data.split("_")[1]
    data = await state.get_data()

    if action_type == "create_event":
        event_id = db.add_event(
            name=data["event_name"],
            description=data["event_desc"],
            date=datetime.strptime(data["event_date"], "%d.%m.%Y"),
            time=data["event_time"],
            place=data["event_place"],
            creator_id=callback.from_user.id
        )
        await callback.message.edit_text(f"✅ Мероприятие #{event_id} создано!")

    elif action_type == "send_announce":
        dorm_id = int(callback.data.split("_")[2])
        stats = {"success": 0, "failed": 0}

        for user in db.get_dorm_residents(dorm_id):
            try:
                await callback.message.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=f"📢 {DORMS[dorm_id]['name']}\n\n{data['announce_text']}"
                )
                stats["success"] += 1
            except:
                stats["failed"] += 1

        await callback.message.edit_text(
            f"📊 Рассылка завершена:\n"
            f"• Успешно: {stats['success']}\n"
            f"• Не удалось: {stats['failed']}"
        )

    await state.clear()


@router.callback_query(F.data == "admin_cancel")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено")