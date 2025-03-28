import sqlite3
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Union
from config import DB_PATH, DORMS, ADMINS


class Database:
    def __init__(self):
        """Инициализация базы данных"""
        DB_PATH.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._init_dorms_data()
        self._init_admins()

    def _create_tables(self):
        """Создание всех таблиц базы данных"""
        with self.conn:
            # Удаляем старую таблицу users если существует
            self.conn.execute("DROP TABLE IF EXISTS users")

            # Новая таблица пользователей
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    dorm_id INTEGER NOT NULL,
                    room TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    is_registered BOOLEAN DEFAULT FALSE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dorm_id) REFERENCES dorms(id)
                )
            """)

            # Таблица общежитий
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS dorms (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    rules TEXT NOT NULL,
                    events TEXT NOT NULL,
                    contact TEXT NOT NULL
                )
            """)

            # Таблица обращений в поддержку
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    dorm_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Таблица администраторов
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    level TEXT NOT NULL CHECK(level IN ('admin', 'superadmin')),
                    dorms TEXT NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица активностей
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TEXT NOT NULL,
                    place TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES users(id)
                )
            """)

            # В _create_tables():
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    dorm_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dorm_id) REFERENCES dorms(id),
                    FOREIGN KEY (author_id) REFERENCES users(id)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS announcement_receivers (
                    announcement_id INTEGER,
                    user_id INTEGER,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (announcement_id, user_id),
                    FOREIGN KEY (announcement_id) REFERENCES announcements(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

    def _init_dorms_data(self):
        """Инициализация данных об общежитиях"""
        with self.conn:
            self.conn.execute("DELETE FROM dorms")
            for dorm_id, dorm in DORMS.items():
                self.conn.execute(
                    "INSERT INTO dorms VALUES (?, ?, ?, ?, ?)",
                    (
                        dorm_id,
                        dorm["name"],
                        "\n".join(dorm["rules"]),
                        "\n".join(dorm["events"]),
                        dorm["contact"]
                    )
                )

    def _init_admins(self):
        """Инициализация администраторов"""
        with self.conn:
            self.conn.execute("DELETE FROM admins")
            for admin_id, admin_data in ADMINS.items():
                self.register_admin(
                    user_id=admin_id,
                    full_name=admin_data["name"],
                    level=admin_data.get("level", "admin"),
                    dorms=admin_data["dorms"]
                )

    # Методы для работы с пользователями
    def add_temp_user(self, dorm_id: int, room: str, full_name: str) -> int:
        """Добавляет временного пользователя без Telegram ID"""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO users (dorm_id, room, full_name) VALUES (?, ?, ?) RETURNING id",
                (dorm_id, room, full_name)
            )
            return cursor.fetchone()[0]

    def register_user(self, record_id: int, telegram_id: int) -> bool:
        """Привязывает Telegram ID к существующей записи"""
        with self.conn:
            cursor = self.conn.execute(
                """
                UPDATE users 
                SET telegram_id = ?, is_registered = TRUE 
                WHERE id = ? AND telegram_id IS NULL
                """,
                (telegram_id, record_id)
            )
            return cursor.rowcount > 0

    def is_user_registered(self, user_id: int) -> bool:
        """Проверяет, зарегистрирован ли пользователь"""
        cursor = self.conn.execute(
            "SELECT 1 FROM users WHERE telegram_id = ? AND is_registered = TRUE",
            (user_id,)
        )
        return cursor.fetchone() is not None

    def get_user_by_name(self, full_name: str) -> Optional[Dict]:
        """Поиск пользователя по ФИО"""
        cursor = self.conn.execute(
            """SELECT id, dorm_id, room, full_name 
               FROM users 
               WHERE full_name LIKE ? AND is_registered = FALSE 
               LIMIT 1""",
            (f"%{full_name}%",))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает пользователя по ID (совместимость со старым кодом)"""
        cursor = self.conn.execute(
            """
            SELECT 
                u.id,
                COALESCE(u.telegram_id, 0) as user_id,
                u.dorm_id,
                u.room,
                u.full_name,
                u.points,
                d.name as dorm_name
            FROM users u
            JOIN dorms d ON u.dorm_id = d.id
            WHERE u.telegram_id = ? OR u.id = ?
            LIMIT 1
            """,
            (user_id, user_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_user(self, user_id: int, dorm_id: int, room: str, full_name: str) -> None:
        """Добавляет/обновляет пользователя (совместимость со старым кодом)"""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO users (telegram_id, dorm_id, room, full_name, is_registered) 
                VALUES (?, ?, ?, ?, TRUE)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    dorm_id = excluded.dorm_id,
                    room = excluded.room,
                    full_name = excluded.full_name
                """,
                (user_id, dorm_id, room, full_name)
            )

    # Search methods
    def search_users(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск пользователей по имени"""
        cursor = self.conn.execute(
            """SELECT user_id, full_name, room, d.name as dorm_name 
               FROM users JOIN dorms d ON users.dorm_id = d.id 
               WHERE full_name LIKE ? 
               ORDER BY full_name LIMIT ?""",
            (f"%{query}%", limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Campus Connect methods
    def add_points(self, user_id: int, points: int, activity_type: str = "event") -> None:
        """Начисление баллов пользователю"""
        with self.conn:
            # Обновляем общее количество баллов
            self.conn.execute(
                "UPDATE users SET points = points + ? WHERE user_id = ?",
                (points, user_id)
            )
            # Записываем активность в историю
            self.conn.execute(
                "INSERT INTO activities (user_id, activity_type, points) VALUES (?, ?, ?)",
                (user_id, activity_type, points)
            )

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Получение таблицы лидеров"""
        cursor = self.conn.execute(
            "SELECT user_id, full_name, points FROM users ORDER BY points DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_user_rank(self, user_id: int) -> int:
        """Получение позиции пользователя в рейтинге"""
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE points > (SELECT points FROM users WHERE user_id = ?)",
            (user_id,)
        )
        return cursor.fetchone()[0] + 1

    # Admin methods
    def register_admin(self, user_id: int, full_name: str, level: str, dorms: List[int]) -> None:
        """Регистрация администратора"""
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO admins VALUES (?, ?, ?, ?, datetime('now'))",
                (user_id, full_name, level, json.dumps(dorms))
            )

    def is_admin(self, user_id: int) -> bool:
        """Проверка наличия прав администратора"""
        cursor = self.conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone() is not None

    def is_admin(self, user_id: int) -> bool:
        """Проверка наличия прав суперадминистратора"""
        cursor = self.conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ? AND level = 'admin'",
            (user_id,)
        )
        return cursor.fetchone() is not None

    def get_admin_dorms(self, user_id: int) -> List[int]:
        """Получение списка общежитий под управлением администратора"""
        cursor = self.conn.execute(
            "SELECT dorms FROM admins WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else []

    def can_manage_dorm(self, user_id: int, dorm_id: int) -> bool:
        """Проверка прав управления конкретным общежитием"""
        if self.is_admin(user_id):
            return True
        return dorm_id in self.get_admin_dorms(user_id)

    def add_event_to_dorm_schedule(self, event_id: int, dorm_id: int):
        """Добавляет мероприятие в расписание общежития"""
        with self.conn:
            self.conn.execute(
                "INSERT INTO dorm_events (event_id, dorm_id) VALUES (?, ?)",
                (event_id, dorm_id)
            )

    # Support methods
    def add_support_ticket(self, user_id: int, dorm_id: int, message: str) -> int:
        """Добавление обращения в поддержку"""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO support_tickets (user_id, dorm_id, message) VALUES (?, ?, ?)",
                (user_id, dorm_id, message)
            )
            return cursor.lastrowid


# Добавляем в класс Database

    def get_dorm_residents(self, dorm_id: int) -> List[Dict]:
        """Получает всех зарегистрированных жильцов общежития"""
        cursor = self.conn.execute(
            """SELECT id, telegram_id, room, full_name 
               FROM users 
               WHERE dorm_id = ? AND is_registered = TRUE""",
            (dorm_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


    def add_event(self, name: str, description: str, date: datetime,
                  time: str, place: str, creator_id: int) -> int:
        """Создает новое мероприятие"""
        with self.conn:
            cursor = self.conn.execute(
                """INSERT INTO events 
                   (name, description, event_date, event_time, place, creator_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                   RETURNING id""",
                (name, description, date.date(), time, place, creator_id)
            )
            return cursor.fetchone()[0]


    def send_to_dorm(self, dorm_id: int, message: str) -> Dict[str, int]:
        """Рассылает сообщение жильцам общежития и возвращает статистику"""
        residents = self.get_dorm_residents(dorm_id)
        success = 0
        failed = 0

        for user in residents:
            try:
                # В реальной реализации здесь будет отправка через бота
                success += 1
            except:
                failed += 1

        return {
            'total': len(residents),
            'success': success,
            'failed': failed,
            'dorm_name': self.get_dorm_name(dorm_id)
        }

    # Методы объявлений
    def add_announcement(self, text: str, dorm_id: int, author_id: int) -> int:
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO announcements (text, dorm_id, author_id) VALUES (?, ?, ?) RETURNING id",
                (text, dorm_id, author_id)
            )
            return cursor.fetchone()[0]

    def mark_announcement_sent(self, announcement_id: int, user_id: int):
        with self.conn:
            self.conn.execute(
                "INSERT INTO announcement_receivers (announcement_id, user_id) VALUES (?, ?)",
                (announcement_id, user_id)
            )
    # Вспомогательный метод
    def get_dorm_name(self, dorm_id: int) -> str:
        """Возвращает название общежития"""
        cursor = self.conn.execute(
            "SELECT name FROM dorms WHERE id = ?",
            (dorm_id,)
        )
        row = cursor.fetchone()
        return row['name'] if row else "Неизвестное общежитие"

# Инициализация глобального экземпляра базы данных
db = Database()