import pytest
from unittest.mock import AsyncMock, Mock
from bot.middlewares.throttling import ThrottlingMiddleware
from aiogram.types import Message, User


@pytest.mark.asyncio
async def test_throttling_middleware():
    """Тест middleware для ограничения запросов."""
    middleware = ThrottlingMiddleware()

    mock_message = AsyncMock(spec=Message)
    mock_message.text = "Тестовое сообщение"
    mock_message.from_user = User(id=123, first_name="Test", is_bot=False)
    mock_message.answer = AsyncMock()

    # Мок сессии БД
    mock_session = AsyncMock()
    mock_result = Mock()
    mock_result.scalar.return_value = 10
    mock_session.execute = AsyncMock(return_value=mock_result)


    mock_handler = AsyncMock()

    # Тестируем
    data = {"session": mock_session}
    await middleware(mock_handler, mock_message, data)

    # Проверяем, что лимит не превышен и обработчик вызван
    assert mock_handler.called


@pytest.mark.asyncio
async def test_throttling_middleware_limit_exceeded():
    """Тест middleware при превышении лимита."""
    middleware = ThrottlingMiddleware()

    mock_message = AsyncMock(spec=Message)
    mock_message.text = "Тестовое сообщение"
    mock_message.from_user = User(id=456, first_name="Test2", is_bot=False)
    mock_message.answer = AsyncMock()

    # Мок: возвращаем 200 запросов (больше лимита 200)
    mock_session = AsyncMock()
    mock_result = Mock()
    mock_result.scalar.return_value = 201  # Превышает TEXT_DAILY_LIMIT=200
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_handler = AsyncMock()

    data = {"session": mock_session}
    await middleware(mock_handler, mock_message, data)

    # При превышении лимита handler НЕ должен вызываться
    assert not mock_handler.called
    # Проверяем, что отправили сообщение о лимите
    assert mock_message.answer.called