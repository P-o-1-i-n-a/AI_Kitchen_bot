from aiogram import types, F
from aiogram.filters import Command
from bot.keyboards.main import main_keyboard
from bot.keyboards.inline import channel_markup
from bot.states import user_states

async def cmd_start(message: types.Message):
    """Обработчик команд /start и /help"""
    user_states[message.chat.id] = {}
    await message.answer(
        "👨‍🍳 Привет! Я - кулинарный бот с генерацией рецептов.\n"
        "⚠️ Рецепты создаются ИИ и могут содержать неточности.\n\n"
        "Нажмите кнопку ниже, чтобы создать рецепт ↓",
        reply_markup=main_keyboard()
    )

async def show_offer(message: types.Message):
    """Показывает публичную оферту"""
    await message.answer(
        "📄 Публичная оферта:\n\n"
        "1. Все рецепты генерируются искусственным интеллектом.\n"
        "2. Проверяйте ингредиенты на аллергены и свежесть.",
        disable_web_page_preview=True
    )

async def show_channel(message: types.Message):
    """Показывает ссылку на канал"""
    await message.answer(
        "🔔 Подпишитесь на наш кулинарный канал:",
        reply_markup=channel_markup()
    )

def register_handlers(dp):
    """Регистрирует обработчики команд"""
    dp.message.register(cmd_start, Command("start", "help"))
    dp.message.register(show_offer, F.text == "📜 Публичная оферта")
    dp.message.register(show_channel, F.text == "📢 Наш кулинарный канал")