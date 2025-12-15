import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import settings
from bot.database import init_db, close_db
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.database import get_session
from aiogram import BaseMiddleware
from bot.logging_config import setup_logging
from bot.handlers import commands, messages
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Настройка логирования
    setup_logging(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("🚀 Запуск инициализации бота...")
    logger.info("=" * 50)

    # 1. Инициализация базы данных
    try:
        await init_db()
        logger.info("✅ База данных готова")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return

    # 2. Создание объектов бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()  # Для простоты используем память
    dp = Dispatcher(storage=storage)

    # 3. Настройка middleware
    # Middleware для внедрения сессии БД
    class DBSessionMiddleware(BaseMiddleware):
        async def __call__(self, handler, event, data):
            async for session in get_session():
                data["session"] = session
                return await handler(event, data)

    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())

    # Middleware для ограничения запросов
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    # 4. Регистрация роутеров
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    # dp.include_router(buttons.router)

    # 5. Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"🤖 Бот @{bot_info.username} готов к работе!")

    # 6. Запуск поллинга
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=True,  # Обработка сигналов завершения
        )
    finally:
        # 7. Корректное завершение работы
        await bot.close()
        await close_db()
        logger.info("✅ Бот завершил работу")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")