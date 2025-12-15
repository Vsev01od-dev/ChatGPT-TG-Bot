import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, User
from bot.handlers.commands import cmd_start, cmd_help


@pytest.mark.asyncio
async def test_start_command():
    """Тест команды /start."""
    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(id=123, first_name="Test", is_bot=False)
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    await cmd_start(mock_message, mock_session)

    # Проверяем, что ответ был отправлен
    assert mock_message.answer.called
    call_args = mock_message.answer.call_args
    assert "Привет" in call_args[0][0]


@pytest.mark.asyncio
async def test_help_command():
    """Тест команды /help."""
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    await cmd_help(mock_message)

    assert mock_message.answer.called
    call_args = mock_message.answer.call_args
    assert "/start" in call_args[0][0]
    assert "/help" in call_args[0][0]