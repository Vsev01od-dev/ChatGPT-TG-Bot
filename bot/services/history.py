"""
Сервис для работы с историей диалогов: сохранение, получение, очистка.
"""
from typing import List, Tuple
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models import DialogHistory
from bot.config import settings


class HistoryService:
    """Сервис для управления историей диалогов пользователя."""

    @staticmethod
    async def add_message(
            session: AsyncSession,
            user_id: int,
            role: str,
            content: str,
    ) -> DialogHistory:
        """
        Сохраняет одно сообщение в истории диалога.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя Telegram
            role: Роль отправителя ('user' или 'assistant')
            content: Текст сообщения

        Returns:
            Созданная запись в истории
        """
        # Проверяем валидность роли
        if role not in ("user", "assistant"):
            raise ValueError("Роль должна быть 'user' или 'assistant'")

        # Создаем новую запись
        message = DialogHistory(
            user_id=user_id,
            role=role,
            content=content,
        )

        # Сохраняем в БД
        session.add(message)
        await session.commit()
        await session.refresh(message)

        return message

    @staticmethod
    async def get_recent_history(
            session: AsyncSession,
            user_id: int,
            limit: int = None,
    ) -> List[Tuple[str, str]]:
        """
        Получает последние сообщения пользователя для формирования контекста.
        Возвращает список кортежей (role, content).

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя Telegram
            limit: Максимальное количество возвращаемых сообщений
                   (по умолчанию из настроек)

        Returns:
            Список последних сообщений в формате для OpenAI API
        """
        # Используем лимит из настроек, если не указан явно
        if limit is None:
            limit = settings.CHAT_WINDOW_LIMIT

        # Запрос последних сообщений пользователя
        stmt = (
            select(DialogHistory.role, DialogHistory.content)
            .where(DialogHistory.user_id == user_id)
            .order_by(desc(DialogHistory.timestamp))
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        # Переворачиваем порядок (от старых к новым) для корректного контекста
        history = [(row.role, row.content) for row in rows[::-1]]
        return history

    @staticmethod
    async def clear_user_history(
            session: AsyncSession,
            user_id: int,
    ) -> int:
        """
        Полностью очищает историю диалогов для указанного пользователя.
        Используется по команде /start и кнопке "Новый запрос".

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя Telegram

        Returns:
            Количество удаленных записей
        """
        stmt = (
            delete(DialogHistory)
            .where(DialogHistory.user_id == user_id)
        )

        result = await session.execute(stmt)
        await session.commit()

        deleted_count = result.rowcount
        return deleted_count

    @staticmethod
    async def get_message_count(
            session: AsyncSession,
            user_id: int,
            role: str = None,
    ) -> int:
        """
        Подсчитывает количество сообщений пользователя.
        Может использоваться для проверки лимитов.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя Telegram
            role: Фильтр по роли ('user', 'assistant' или None)

        Returns:
            Количество сообщений
        """
        stmt = select(DialogHistory).where(DialogHistory.user_id == user_id)

        if role:
            stmt = stmt.where(DialogHistory.role == role)

        result = await session.execute(stmt)
        return len(result.fetchall())