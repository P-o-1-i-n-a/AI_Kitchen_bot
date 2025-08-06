from aiogram import types, F
from aiogram.filters import Command
from bot.keyboards.main import main_keyboard, search_method_keyboard
from bot.keyboards.inline import channel_markup, recipe_actions_markup
from bot.states import user_states, reset_user_state
from bot.services.diet_checker import check_diet_conflicts

async def cmd_start(message: types.Message):
    """Обработчик команд /start и /help"""
    reset_user_state(message.chat.id)
    await message.answer(
        "👨‍🍳 Привет! Я - умный кулинарный бот.\n"
        "Я могу:\n"
        "• Создать рецепт по названию блюда\n"
        "• Придумать рецепт из ваших ингредиентов\n"
        "• Учитывать диетические ограничения\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

async def show_offer(message: types.Message):
    """Показывает публичную оферту с улучшенным форматированием"""
    offer_text = (
        "<b>📄 Публичная оферта</b>\n\n"
        "1. Все рецепты генерируются нейросетью\n"
        "2. Обязательно проверяйте:\n"
        "   • Аллергены\n"
        "   • Сроки годности\n"
        "   • Индивидуальную переносимость\n\n"
        "3. Бот не заменяет консультацию диетолога"
    )
    await message.answer(offer_text, parse_mode="HTML")

async def show_channel(message: types.Message):
    """Показывает канал с интерактивной клавиатурой"""
    await message.answer(
        "🎁 Подпишитесь на канал и получите:\n"
        "• Эксклюзивные рецепты\n"
        "• Кулинарные лайфхаки\n"
        "• Сезонные подборки",
        reply_markup=channel_markup()
    )

async def handle_back_to_menu(message: types.Message):
    """Обработчик возврата в главное меню"""
    await cmd_start(message)

async def show_recipe_help(message: types.Message):
    """Помощь по работе с рецептами"""
    help_text = (
        "<b>🧭 Как работать с ботом:</b>\n\n"
        "<u>По названию блюда:</u>\n"
        "1. Выберите кухню\n"
        "2. Укажите диету\n"
        "3. Получите рецепт с КБЖУ\n\n"
        "<u>По ингредиентам:</u>\n"
        "1. Введите продукты через запятую\n"
        "2. Выберите кухню\n"
        "3. Укажите диету"
    )
    await message.answer(help_text, parse_mode="HTML")

def register_handlers(dp):
    """Регистрация всех обработчиков команд"""
    # Основные команды
    dp.message.register(cmd_start, Command("start", "help"))
    dp.message.register(show_recipe_help, Command("help"))
    
    # Обработчики кнопок
    dp.message.register(show_offer, F.text == "📜 Публичная оферта")
    dp.message.register(show_channel, F.text == "📢 Наш кулинарный канал")
    dp.message.register(handle_back_to_menu, F.text == "↩️ Назад в меню")
    
    # Добавьте это в конец файла
    from bot.handlers import recipe_flow, buttons
    recipe_flow.register_handlers(dp)
    buttons.register_handlers(dp)
