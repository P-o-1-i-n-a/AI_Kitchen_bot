from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def search_method_keyboard():
    """Клавиатура выбора способа поиска"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 По названию блюда")],
            [KeyboardButton(text="🥕 По ингредиентам")],
            [KeyboardButton(text="↩️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
def meal_time_keyboard():
    """Клавиатура выбора времени приёма пищи"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌅 Завтрак"), KeyboardButton(text="🌇 Обед")],
            [KeyboardButton(text="🌃 Ужин"), KeyboardButton(text="☕ Перекус")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def cuisine_keyboard():
    """Клавиатура выбора кухни"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русская"), KeyboardButton(text="🇮🇹 Итальянская")],
            [KeyboardButton(text="🇯🇵 Японская"), KeyboardButton(text="🇬🇪 Кавказская")],
            [KeyboardButton(text="🇺🇸 Американская"), KeyboardButton(text="🇫🇷 Французская")],
            [KeyboardButton(text="🇹🇷 Турецкая"), KeyboardButton(text="🇨🇳 Китайская")],
            [KeyboardButton(text="🇲🇽 Мексиканская"), KeyboardButton(text="🇮🇳 Индийская")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def diet_keyboard():
    """Клавиатура выбора диеты"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚫 Нет ограничений"), KeyboardButton(text="⚠️ Аллергии")],
            [KeyboardButton(text="⚖️ Низкокалорийные"), KeyboardButton(text="💪 Высокобелковые")],
            [KeyboardButton(text="☪️ Халяль"), KeyboardButton(text="☦️ Постная")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True

    )
