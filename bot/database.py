from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from bot.models import Base

# Создаем асинхронный движок для SQLite
# Используем aiosqlite в качестве асинхронного драйвера
engine: AsyncEngine = create_async_engine(
    f"sqlite+aiosqlite:///data/db.sqlite",
    echo=False,  # Включить для отладки SQL-запросов
    future=True,
)

# Создаем фабрику для асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение асинхронной сессии БД. Используется в обработчиках для доступа к базе данных."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных: создание всех таблиц."""

    async with engine.begin() as conn:
        # Создаем все таблицы, определенные в моделях
        await conn.run_sync(Base.metadata.create_all)
        # Проверяем соединение
        await conn.execute(text("SELECT 1"))
    print("✅ База данных успешно инициализирована")


async def close_db() -> None:
    """Корректное закрытие соединений с БД при завершении работы."""
    await engine.dispose()
    print("✅ Соединения с базой данных закрыты")