from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Главное меню с тремя кнопками"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")],  # Запускает выбор метода поиска
            [
                KeyboardButton(text="📜 Публичная оферта"),
                KeyboardButton(text="📢 Наш канал")  # Сохраняем кнопку канала
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
