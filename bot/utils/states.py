from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    full_name = State()  # Шаг 1: Ввод ФИО
    dorm = State()       # Шаг 2: Выбор общежития (inline)
    room = State()       # Шаг 3: Ввод комнаты

class Support(StatesGroup):
    message = State()

class Settings(StatesGroup):
    dorm = State()
    room = State()
    full_name = State()

class AdminRegistration(StatesGroup):
    user_id = State()
    level = State()
    dorms = State()

class AdminPanel(StatesGroup):
    menu = State()
    create_event = State()
    add_admin = State()
    add_user = State()
    send_announcement = State()
    search_residents = State()
    select_dorm = State()  # Для выбора целевого общежития

