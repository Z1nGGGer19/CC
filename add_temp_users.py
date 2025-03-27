from bot.database import db

def add_temp_user():
    print("Добавление нового пользователя:")
    dorm_id = int(input("ID общежития: "))
    room = input("Номер комнаты: ")
    full_name = input("ФИО: ")

    user_id = db.add_temp_user(dorm_id, room, full_name)
    print(f"✅ Пользователь добавлен! ID записи: {user_id}")

if __name__ == "__main__":
    while True:
        add_temp_user()
        if input("Добавить еще? (y/n): ").lower() != 'y':
            break