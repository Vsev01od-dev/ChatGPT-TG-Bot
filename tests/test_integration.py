import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.asyncio
async def test_openrouter_service():
    """Интеграционный тест OpenRouter сервиса."""
    from bot.services.openrouter import openrouter_service

    messages = openrouter_service.format_messages_from_history(
        history=[("user", "Привет")],
        user_message="Как дела?",
        system_prompt="Ты тестовый ассистент."
    )

    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Как дела?"


@pytest.mark.asyncio
async def test_model_fallback_logic():
    """Тест логики переключения моделей."""
    from bot.services.openrouter import openrouter_service

    # Тест 1: Проверяем публичные свойства
    assert hasattr(openrouter_service, 'all_models')
    assert isinstance(openrouter_service.all_models, list)
    assert len(openrouter_service.all_models) > 0

    # Тест 2: Проверяем форматирование сообщений с разной историей
    test_cases = [
        {
            "history": [],
            "user_message": "Тест",
            "expected_count": 2  # system + user
        },
        {
            "history": [("user", "Привет"), ("assistant", "Привет!")],
            "user_message": "Пока",
            "expected_count": 4  # system + 2 истории + user
        }
    ]

    for case in test_cases:
        messages = openrouter_service.format_messages_from_history(
            history=case["history"],
            user_message=case["user_message"]
        )
        assert len(messages) == case["expected_count"]

    # Тест 3: Проверяем обработку ошибок
    from unittest.mock import patch

    with patch.object(openrouter_service.client.chat.completions, 'create') as mock_create:
        mock_create.side_effect = Exception("Test error")

        # Не должно падать, должен вернуть словарь с ошибкой
        result = await openrouter_service.chat_completion(
            messages=[{"role": "user", "content": "Тест"}],
            max_tokens=10
        )

        assert "success" in result
        assert result["success"] is False
        assert "error" in result