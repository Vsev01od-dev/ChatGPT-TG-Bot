import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from bot.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для тестов на уровне сессии."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Создаем тестовый движок БД на уровне сессии."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA foreign_keys=ON"))

    yield engine

    # Закрываем движок в конце сессии
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    Создаем изолированную сессию БД для каждого теста.
    """
    # Начинаем транзакцию
    async with engine.connect() as connection:
        await connection.begin()

        AsyncTestSession = async_sessionmaker(
            connection,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        session = AsyncTestSession()

        try:
            yield session
        finally:
            # Откатываем транзакцию и закрываем сессию
            await session.close()
            await connection.rollback()