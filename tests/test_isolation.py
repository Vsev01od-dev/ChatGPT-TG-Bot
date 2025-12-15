import pytest
from bot.services.history import HistoryService


@pytest.mark.asyncio
async def test_database_isolation(db_session):
    """
    Тест изоляции баз данных между тестами.
    """
    # Добавляем данные
    await HistoryService.add_message(db_session, 999, "user", "Изоляция тест 1")
    await db_session.commit()

    count1 = len(await HistoryService.get_recent_history(db_session, 999))
    assert count1 == 1


@pytest.mark.asyncio
async def test_database_isolation_second(db_session):
    """
    Второй тест - должен начать с чистой БД.
    """
    # Проверяем, что данные от предыдущего теста не видны
    count2 = len(await HistoryService.get_recent_history(db_session, 999))
    assert count2 == 0, f"Нарушена изоляция тестов! Найдено сообщений: {count2}"

    # Добавляем свои данные
    await HistoryService.add_message(db_session, 999, "user", "Изоляция тест 2")
    await db_session.commit()

    count2_after = len(await HistoryService.get_recent_history(db_session, 999))
    assert count2_after == 1