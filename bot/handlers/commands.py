from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.history import HistoryService
from bot.handlers.buttons import get_main_reply_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, session: AsyncSession) -> None:
    user_id = message.from_user.id
    deleted_count = await HistoryService.clear_user_history(session, user_id)

    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я — интеллектуальный бот с поддержкой ChatGPT через OpenRouter.\n"
        "Просто напиши мне сообщение, и я постараюсь помочь!\n\n"
        f"✅ История диалога очищена (удалено сообщений: {deleted_count})\n"
        "Теперь мы начинаем новый разговор."
    )

    await message.answer(welcome_text, reply_markup=get_main_reply_keyboard())


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    help_text = (
        "📚 *Справка по командам бота:*\n\n"
        "*/start* — Начать новый диалог (очищает историю)\n"
        "*/help* — Показать эту справку\n"
        "*/new* — Начать новый запрос (аналогично кнопке)\n\n"
        "Нажмите кнопку '🔄 Новый запрос' внизу экрана, "
        "чтобы сбросить контекст нашего разговора.\n\n"
        "*Как использовать:*\n" 
        "1. Просто напишите мне сообщение\n" 
        "2. Я запомню контекст нашего разговора\n" 
        "3. Для сбоса контекста используйте /start или кнопку 'Новый запрос'\n\n" 
        "*Ограничения:*\n" f"• Сохраняю последние {10} сообщений для контекста\n" 
        "• Использую бесплатные модели OpenRouter\n" 
        "• При ошибках автоматически переключаюсь на резервные модели"
    )

    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard())


@router.message(Command("new"))
async def cmd_new(message: types.Message, session: AsyncSession) -> None:
    user_id = message.from_user.id
    deleted_count = await HistoryService.clear_user_history(session, user_id)

    response_text = (
        f"🔄 Контекст диалога сброшен.\n"
        f"Удалено сообщений: {deleted_count}\n\n"
        "Можете задать новый вопрос!"
    )

    await message.answer(response_text, reply_markup=get_main_reply_keyboard())