from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Основная reply-клавиатура бота.
def get_main_reply_keyboard() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Новый запрос")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Напишите сообщение или нажмите кнопку"
    )
