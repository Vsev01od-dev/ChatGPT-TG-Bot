import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import asyncio

# Создаем директорию для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level=logging.INFO):
    """Настройка логирования для приложения."""

    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(level)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик (ротация по размеру)
    file_handler = RotatingFileHandler(
        LOG_DIR / "bot.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Отдельный логгер для ошибок
    error_handler = RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=5_242_880,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    # Логирование SQL запросов
    sql_logger = logging.getLogger("sqlalchemy.engine")
    sql_logger.setLevel(logging.WARNING)

    return logger


# Декоратор для логирования функций
def log_execution(func):

    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Вызов функции {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Функция {func.__name__} выполнена успешно")
            return result
        except Exception as e:
            logger.error(f"Ошибка в функции {func.__name__}: {e}", exc_info=True)
            raise

    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Вызов функции {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Функция {func.__name__} выполнена успешно")
            return result
        except Exception as e:
            logger.error(f"Ошибка в функции {func.__name__}: {e}", exc_info=True)
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper