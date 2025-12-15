import pytest
from bot.services.history import HistoryService


@pytest.mark.asyncio
async def test_add_message(db_session):
    """Тест добавления сообщения в историю."""
    message = await HistoryService.add_message(
        db_session, user_id=123, role="user", content="Тестовое сообщение"
    )

    assert message.id is not None
    assert message.user_id == 123
    assert message.content == "Тестовое сообщение"

    # Сохраняем изменения и проверяем
    await db_session.commit()

    # Проверяем, что сообщение действительно сохранилось
    history = await HistoryService.get_recent_history(db_session, 123)
    assert len(history) == 1
    assert history[0][0] == "user"
    assert history[0][1] == "Тестовое сообщение"


@pytest.mark.asyncio
async def test_get_history(db_session):
    """Тест получения истории."""

    # Добавляем два сообщения
    await HistoryService.add_message(db_session, 123, "user", "Привет")
    await HistoryService.add_message(db_session, 123, "assistant", "Привет! Как дела?")

    # Сохраняем
    await db_session.commit()

    history = await HistoryService.get_recent_history(db_session, 123)

    assert len(history) == 2
    assert history[0][0] == "user"
    assert history[0][1] == "Привет"
    assert history[1][0] == "assistant"
    assert history[1][1] == "Привет! Как дела?"


@pytest.mark.asyncio
async def test_clear_history(db_session):
    """Тест очистки истории."""

    # Добавляем одно тестовое сообщение
    await HistoryService.add_message(db_session, 123, "user", "Тест")
    await db_session.commit()

    # Проверяем, что оно есть
    before_clear = await HistoryService.get_recent_history(db_session, 123)
    assert len(before_clear) == 1

    # Очищаем
    deleted = await HistoryService.clear_user_history(db_session, 123)
    assert deleted == 1  # Должно удалить 1 сообщение
    await db_session.commit()

    # Проверяем, что база пуста
    after_clear = await HistoryService.get_recent_history(db_session, 123)
    assert len(after_clear) == 0