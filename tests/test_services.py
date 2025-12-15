import pytest
from unittest.mock import AsyncMock, patch
from bot.services.openrouter import OpenRouterService


@pytest.mark.asyncio
async def test_format_messages():
    """Тест форматирования сообщений для API."""
    service = OpenRouterService()

    history = [
        ("user", "Привет"),
        ("assistant", "Привет! Как дела?"),
        ("user", "Хорошо, а ты?")
    ]

    messages = service.format_messages_from_history(
        history=history,
        user_message="Что такое ИИ?"
    )

    assert len(messages) == 5  # system + 3 истории + новый запрос
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "Что такое ИИ?"


@pytest.mark.asyncio
@patch('bot.services.openrouter.AsyncOpenAI')
async def test_chat_completion(mock_openai):
    """Тест запроса к OpenRouter"""

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "Тестовый ответ"
    mock_response.usage = AsyncMock()
    mock_response.usage.total_tokens = 50

    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # Создаем сервис
    service = OpenRouterService()
    service.client = mock_client

    # Выполняем запрос
    result = await service.chat_completion(
        messages=[{"role": "user", "content": "Тест"}]
    )

    assert result["success"] == True
    assert "Тестовый ответ" in result["content"]