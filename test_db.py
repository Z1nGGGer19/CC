from config import DB_PATH
from bot.database import Database

print(f"База данных будет создана в: {DB_PATH}")
db = Database()
print("База данных успешно инициализирована!")