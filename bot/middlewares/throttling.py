import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from bot.config import settings
from bot.models import DialogHistory

logger = logging.getLogger(__name__)

# Middleware для ограничения количества запросов пользователя.
class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit_period_hours: int = 24) -> None:
        self.limit_period_hours = limit_period_hours
        # Кэш для быстрой проверки (user_id -> [count, last_check])
        self._cache: Dict[int, Dict[str, Any]] = {}

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Проверяем только текстовые сообщения (не команды)
        if not event.text or event.text.startswith('/'):
            return await handler(event, data)

        user_id = event.from_user.id
        session: AsyncSession = data.get("session")

        if not session:
            logger.warning(f"Сессия БД не найдена для пользователя {user_id}")
            return await handler(event, data)

        # Проверяем лимит
        can_proceed, count = await self._check_limit(user_id, session)

        if not can_proceed:
            await self._send_limit_message(event, count)
            return

        # Если лимит не превышен, продолжаем обработку
        return await handler(event, data)

    async def _check_limit(self, user_id: int, session: AsyncSession) -> tuple[bool, int]:
        """Проверяет, не превысил ли пользователь лимит запросов."""

        # Проверяем кэш (обновляем каждые 5 минут)
        cache_key = user_id
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if (datetime.now() - cache_data["timestamp"]).seconds < 300:  # 5 минут
                return cache_data["can_proceed"], cache_data["count"]

        # Рассчитываем период
        period_start = datetime.utcnow() - timedelta(hours=self.limit_period_hours)

        # Считаем запросы пользователя за период
        stmt = select(func.count(DialogHistory.id)).where(
            and_(
                DialogHistory.user_id == user_id,
                DialogHistory.role == "user",
                DialogHistory.timestamp >= period_start
            )
        )

        result = await session.execute(stmt)
        request_count = result.scalar() or 0

        can_proceed = request_count < settings.TEXT_DAILY_LIMIT

        # Обновляем кэш
        self._cache[cache_key] = {
            "can_proceed": can_proceed,
            "count": request_count,
            "timestamp": datetime.now()
        }

        logger.debug(f"Пользователь {user_id}: {request_count}/{settings.TEXT_DAILY_LIMIT} запросов")
        return can_proceed, request_count

    async def _send_limit_message(self, event: Message, count: int) -> None:
        """Отправляет сообщение о превышении лимита."""
        from datetime import datetime, timedelta

        # Примерное время сброса (через 24 часа после первого запроса)
        reset_time = datetime.now() + timedelta(hours=24)
        reset_str = reset_time.strftime("%H:%M %d.%m.%Y")

        message = (
            f"⚠️ *Достигнут дневной лимит запросов!*\n\n"
            f"Вы использовали {count} из {settings.TEXT_DAILY_LIMIT} доступных запросов.\n"
            f"Лимит обновится примерно в {reset_str}\n\n"
            f"Чтобы увеличить лимит, обратитесь к администратору."
        )

        await event.answer(message, parse_mode="Markdown")