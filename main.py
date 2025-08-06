from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Главное меню с тремя кнопками"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")], 
            [
                KeyboardButton(text="📜 Публичная оферта"),
                KeyboardButton(text="📢 Наш канал") 
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def search_method_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 По названию")],
            [KeyboardButton(text="🥕 По ингредиентам")],
            [KeyboardButton(text="↩️ Назад в меню")]
        ],
        resize_keyboard=True
    )
