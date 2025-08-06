from aiogram import types, F
from aiogram.filters import Command
from bot.keyboards.main import main_keyboard, search_method_keyboard
from bot.keyboards.inline import channel_markup
from bot.states import user_states, reset_user_state

async def cmd_start(message: types.Message):
    """Обработчик /start и /help с новым интерфейсом"""
    reset_user_state(message.chat.id)
    await message.answer(
        "👨‍🍳 <b>AI Kitchen Bot</b>\n"
        "Выберите действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

async def show_offer(message: types.Message):
    """Публичная оферта)"""
    await message.answer(
        "📄 Публичная оферта:\n\n"
        "1. Рецепты создаются ИИ\n"
        "2. Проверяйте ингредиенты",
        disable_web_page_preview=True
    )

async def show_channel(message: types.Message):
    """Кнопка канала (без изменений)"""
    await message.answer(
        "📢 Наш кулинарный канал:",
        reply_markup=channel_markup()
    )

async def handle_create_recipe(message: types.Message):
    """Новый обработчик для кнопки создания рецепта"""
    reset_user_state(message.chat.id)
    await message.answer(
        "🔍 <b>Выберите способ поиска рецепта:</b>",
        reply_markup=search_method_keyboard(),
        parse_mode="HTML"
    )

async def handle_back_to_menu(message: types.Message):
    """Обработчик кнопки возврата"""
    await cmd_start(message)

def register_handlers(dp):
    """Обновленная регистрация с новыми кнопками"""
    # Основные команды
    dp.message.register(cmd_start, Command("start", "help"))
    
    # Главное меню
    dp.message.register(handle_create_recipe, F.text == "🍳 Создать рецепт")
    dp.message.register(show_offer, F.text == "📜 Публичная оферта")
    dp.message.register(show_channel, F.text == "📢 Наш кулинарный канал")
    
    # Навигация
    dp.message.register(handle_back_to_menu, F.text == "↩️ Назад в меню")
