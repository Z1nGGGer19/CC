import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from bot.handlers import (
    base, campus, dorm,
    events, rules, search,
    settings, support, admins
)
import bot.database as db


# В main.py
# async def on_startup():
#     db._create_tables()  # Пересоздаст таблицы с новой структурой

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Принудительная инициализация БД
    from bot.database import db
    db._create_tables()
    db._init_dorms_data()
    db._init_admins()  # Добавляем суперадминов


    bot = None  # Инициализируем переменную заранее
    try:
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()

        # Подключение роутеров
        routers = [
            base.router,
            campus.router,
            dorm.router,
            events.router,
            rules.router,
            search.router,
            settings.router,
            support.router,
            admins.router
        ]

        for router in routers:
            dp.include_router(router)

        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}", exc_info=True)
    finally:
        if bot:  # Закрываем сессию только если бот был создан
            await bot.session.close()
    dp.include_router(base.router)
    dp.include_router(admins.router)


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")