from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK

def channel_markup():
    """Inline-кнопка для подписки на канал"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🍳 AI Kitchen Channel",
                url=CHANNEL_LINK
            )]
        ]
    )

def recipe_actions_markup():
    """Кнопки действий с рецептом"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♻️ Сгенерировать снова", callback_data="regenerate"),
                InlineKeyboardButton(text="📷 Прикрепить фото", callback_data="add_photo")
            ],
            [
                InlineKeyboardButton(text="📢 Поделиться", switch_inline_query="")
            ]
        ]
    )