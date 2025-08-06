from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Главная клавиатура меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")],
            [KeyboardButton(text="📜 Публичная оферта")],
            [KeyboardButton(text="📢 Наш кулинарный канал")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )