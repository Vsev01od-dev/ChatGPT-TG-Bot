from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.history import HistoryService
from bot.services.openrouter import openrouter_service
from bot.handlers.buttons import get_main_reply_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "🔄 Новый запрос")
async def handle_new_request(
    message: types.Message,
    session: AsyncSession,
):

    # Обработка кнопки 'Новый запрос'.

    user_id = message.from_user.id

    deleted_count = await HistoryService.clear_user_history(session, user_id)

    await message.answer(
        f"✅ Контекст диалога сброшен.\n"
        f"Удалено сообщений: {deleted_count}\n\n"
        "Можешь задать новый вопрос 🙂",
        reply_markup=get_main_reply_keyboard()
    )

@router.message(F.text)
async def handle_text_message(
        message: types.Message,
        session: AsyncSession,
) -> None:

    # Обрабатывает все текстовые сообщения пользователя

    user_id = message.from_user.id
    user_message = message.text

    logger.info(f"Новое сообщение от {user_id}: {user_message[:50]}...")

    # Показываем индикатор "печатает"
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # 1. Получаем историю диалога
        history = await HistoryService.get_recent_history(session, user_id)
        logger.debug(f"История для {user_id}: {len(history)} сообщений")

        # 2. Сохраняем сообщение пользователя в историю
        await HistoryService.add_message(
            session, user_id, "user", user_message
        )

        # 3. Форматируем сообщения для API (теперь метод существует!)
        formatted_messages = openrouter_service.format_messages_from_history(
            history=history,
            user_message=user_message,
            system_prompt=(
                "Ты полезный, вежливый и информативный ассистент. "
                "Отвечай на русском языке. Будь краток, но содержателен. "
                "Учитывай контекст предыдущих сообщений."
            )
        )

        # Логируем, что отправляем в API (для отладки)
        logger.debug(f"Отправляем в API {len(formatted_messages)} сообщений:")
        for msg in formatted_messages[-3:]:  # Логируем последние 3 сообщения
            role = msg["role"]
            content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            logger.debug(f"  {role}: {content_preview}")

        # 4. Получаем ответ от OpenRouter
        response = await openrouter_service.chat_completion(
            messages=formatted_messages,
            max_tokens=600,
            temperature=0.8,
        )

        # 5. Обрабатываем ответ
        if response["success"]:
            bot_response = response["content"]

            # Сохраняем ответ ассистента в историю
            await HistoryService.add_message(
                session, user_id, "assistant", bot_response
            )

            # Добавляем информацию о модели, если использовалась резервная
            if response.get("fallback_used"):
                bot_response += f"\n\n🔁 *Примечание:* использована резервная модель ({response['model_used']})"

            # Отправляем ответ пользователю
            await message.answer(
                bot_response,
                parse_mode="Markdown" if response.get("fallback_used") else None,
                reply_markup=get_main_reply_keyboard()
            )

            logger.info(f"✅ Ответ пользователю {user_id} от модели {response['model_used']}")

        else:
            # Обработка ошибки API
            error_msg = (
                "❌ Произошла ошибка при обработке вашего запроса.\n"
                "Попробуйте повторить позже или переформулировать вопрос."
            )
            await message.answer(error_msg)
            logger.error(f"Ошибка OpenRouter для {user_id}: {response['error']}")

    except Exception as e:
        logger.exception(f"Критическая ошибка при обработке сообщения от {user_id}")

        error_msg = (
            "⚠️ Произошла внутренняя ошибка. "
            "Разработчики уже уведомлены. Попробуйте позже."
        )
        await message.answer(error_msg)