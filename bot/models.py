from datetime import datetime
from sqlalchemy import String, Text, BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


class DialogHistory(Base):
    """
    Модель для хранения истории диалогов с пользователем.
    Каждая запись - одно сообщение от пользователя или ассистента.
    """

    __tablename__ = "dialog_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' или 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DialogHistory(user_id={self.user_id}, role={self.role}, timestamp={self.timestamp})>"