import sqlite3
from config import DB_PATH  # Импортируем путь к БД из config.py


def add_user(id: int, dorm_id: int, room: str, full_name: str):
    """Добавляет пользователя в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO users 
            (id, dorm_id, room, full_name, points, registered_at)
            VALUES (?, ?, ?, ?, 0, datetime('now'))
            """,
            (id, dorm_id, room, full_name)
        )
        conn.commit()
        print(f"✅ Пользователь {full_name} (ID: {id}) добавлен!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


# Пример использования:
if __name__ == "__main__":
    add_user(
        id=778318565,  # ID пользователя в Telegram
        dorm_id=1,  # ID общежития из таблицы dorms
        room="1525",  # Номер комнаты (строка, могут быть буквы)
        full_name="Плескачев Рома"
    )