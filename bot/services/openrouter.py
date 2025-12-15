"""
Асинхронный клиент для работы с OpenRouter API.
Адаптирован под ваши модели: gpt-5.2-chat, gpt-5.2-pro, gpt-5-mini.
"""
import logging
from typing import List, Optional
from openai import AsyncOpenAI, APIError
from bot.config import settings

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Сервис для взаимодействия с OpenRouter API."""

    def __init__(self):
        """Инициализация асинхронного клиента OpenRouter."""
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        self._prepare_headers()

        # Ваши модели в порядке приоритета
        self.all_models = [settings.OPENROUTER_MODEL] + settings.OPENROUTER_FALLBACK_MODELS
        logger.info(f"📋 Загружены модели: {self.all_models}")

    def _prepare_headers(self) -> dict:
        """Подготавливает дополнительные заголовки для OpenRouter."""
        self.extra_headers = {}

        if settings.OPENROUTER_SITE:
            self.extra_headers["HTTP-Referer"] = settings.OPENROUTER_SITE
        if settings.OPENROUTER_TITLE:
            self.extra_headers["X-Title"] = settings.OPENROUTER_TITLE

        return self.extra_headers

    def _get_error_suggestion(self, error_msg: str, model: str) -> str:
        """
        Возвращает понятное описание ошибки и рекомендацию.
        ЭТОТ МЕТОД БЫЛ ОТСУТСТВОВАЛ!
        """
        error_msg = error_msg.lower()

        if "not available" in error_msg:
            return f"Модель {model} недоступна. Проверьте название или доступность региона."
        elif "quota" in error_msg or "limit" in error_msg:
            return f"Закончились токены/квота для {model}. Используйте другую модель."
        elif "not found" in error_msg or "invalid" in error_msg:
            return f"Неправильное имя модели: {model}. Проверьте .env файл."
        elif "timeout" in error_msg:
            return f"Таймаут запроса к {model}. Проверьте интернет-соединение."
        else:
            return f"Неизвестная ошибка. Проверьте API ключ и доступность OpenRouter."

    def format_messages_from_history(
            self,
            history: List[tuple],
            user_message: str,
            system_prompt: str = "Ты полезный ассистент. Отвечай на русском языке."
    ) -> List[dict]:
        """
        Форматирует историю диалога для OpenAI API.
        ЭТОТ МЕТОД БЫЛ ОТСУТСТВОВАЛ — ОН КРИТИЧЕСКИ ВАЖЕН!

        Args:
            history: История из HistoryService [(role, content), ...]
            user_message: Новое сообщение пользователя
            system_prompt: Системный промпт

        Returns:
            Отформатированные сообщения для API
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Добавляем историю из БД
        for role, content in history:
            # Преобразуем 'user'/'assistant' в формат OpenAI
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })

        # Добавляем новое сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        logger.debug(f"Сформировано {len(messages)} сообщений для API")
        return messages

    async def chat_completion(
            self,
            messages: List[dict],
            max_tokens: int = 500,
            temperature: float = 0.7,
    ) -> dict:
        """
        Основной метод для получения ответа от модели.
        """
        last_error = None
        tried_models = []

        for model in self.all_models:
            tried_models.append(model)

            try:
                logger.info(f"🔄 Пробуем модель: {model}")

                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,  # Используем УЖЕ отформатированные messages
                    max_tokens=max_tokens,
                    temperature=temperature,
                    extra_headers=self.extra_headers or None,
                )

                content = response.choices[0].message.content
                usage = response.usage

                logger.info(f"✅ Успех с моделью {model}!")

                return {
                    "success": True,
                    "content": content.strip(),
                    "model_used": model,
                    "tokens_used": usage.total_tokens if usage else None,
                    "fallback_used": model != settings.OPENROUTER_MODEL,
                    "tried_models": tried_models,
                    "is_primary": model == settings.OPENROUTER_MODEL,
                }

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning(f"❌ Ошибка модели {model}: {error_str[:100]}")

                is_critical = any(keyword in error_str for keyword in [
                    "not available", "quota exceeded", "model not found",
                    "invalid model", "403", "429"
                ])

                if not is_critical:
                    break

        logger.error(f"💥 Все модели недоступны. Попробовано: {tried_models}")

        return {
            "success": False,
            "error": str(last_error) if last_error else "Неизвестная ошибка",
            "tried_models": tried_models,
            "content": self._get_friendly_error_message(tried_models, last_error),
        }

    def _get_friendly_error_message(self, tried_models: List[str], error: Exception) -> str:
        """Генерирует понятное сообщение об ошибке для пользователя."""
        error_str = str(error).lower() if error else ""

        if "quota" in error_str or "limit" in error_str:
            return (
                "⚠️ *Достигнут лимит использования моделей!*\n\n"
                f"Попробованы модели: {', '.join(tried_models)}\n"
                "Возможно, закончились бесплатные токены.\n"
                "Попробуйте позже или используйте другую модель."
            )
        else:
            return (
                "😔 *Не удалось получить ответ*\n\n"
                f"Попробовано моделей: {len(tried_models)}\n"
                "Пожалуйста, попробуйте позже."
            )

    async def test_your_models(self) -> dict:
        """
        Тестирует ВАШИ конкретные модели.
        Теперь с исправленным вызовом _get_error_suggestion!
        """
        logger.info("🧪 Тестирование ВАШИХ моделей...")

        test_messages = [{"role": "user", "content": "Привет! Ответь 'Модель работает'."}]
        results = {}

        for model in self.all_models:
            try:
                logger.info(f"Тестируем: {model}")

                response = await self.client.chat.completions.create(
                    model=model,
                    messages=test_messages,
                    max_tokens=20,
                    extra_headers=self.extra_headers or None,
                    timeout=10.0
                )

                results[model] = {
                    "status": "✅ РАБОТАЕТ",
                    "response": response.choices[0].message.content,
                    "tokens": response.usage.total_tokens if response.usage else "N/A",
                }

            except Exception as e:
                error_msg = str(e)
                results[model] = {
                    "status": "❌ ОШИБКА",
                    "error": error_msg[:150],
                    # ТЕПЕРЬ МЕТОД СУЩЕСТВУЕТ:
                    "suggestion": self._get_error_suggestion(error_msg, model),
                }

        return results


# Глобальный экземпляр сервиса
openrouter_service = OpenRouterService()