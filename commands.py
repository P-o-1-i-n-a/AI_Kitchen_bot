from aiogram import types, F
from aiogram.filters import Command
from bot.keyboards.main import main_keyboard, search_method_keyboard
from bot.keyboards.inline import channel_markup
from bot.states import user_states, reset_user_state
import logging

logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message):
    """Главная команда с принудительным сбросом клавиатуры"""
    try:
        # Сначала убираем все кнопки
        await message.answer("Загружаем меню...", reply_markup=types.ReplyKeyboardRemove())
        
        # Полный сброс состояния
        reset_user_state(message.chat.id)
        
        # Задержка для гарантированного обновления
        await asyncio.sleep(0.3)
        
        # Отправляем новое меню
        await message.answer(
            "👨‍🍳 <b>AI Kitchen Bot</b>\n"
            "Я помогу вам:\n"
            "- Найти рецепт по названию\n"
            "- Придумать блюдо из ваших продуктов\n\n"
            "Выберите действие:",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"New session for user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("⚠️ Ошибка загрузки. Попробуйте позже.")

async def show_offer(message: types.Message):
    """Обновленная оферта с HTML-форматированием"""
    await message.answer(
        "<b>📄 Публичная оферта</b>\n\n"
        "1. Все рецепты генерируются нейросетью YandexGPT\n"
        "2. Обязательно проверяйте:\n"
        "   • Аллергены\n"
        "   • Сроки годности\n"
        "   • Индивидуальную переносимость",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def show_channel(message: types.Message):
    """Кнопка канала с улучшенным описанием"""
    await message.answer(
        "🎁 <b>Наш кулинарный канал</b>\n"
        "Подпишитесь для получения:\n"
        "- Эксклюзивных рецептов\n"
        "- Сезонных подборок\n"
        "- Кулинарных лайфхаков",
        reply_markup=channel_markup(),
        parse_mode="HTML"
    )

async def handle_create_recipe(message: types.Message):
    """Обработчик создания рецепта с проверкой состояния"""
    try:
        reset_user_state(message.chat.id)
        user_states[message.chat.id] = {"step": "waiting_method"}
        
        await message.answer(
            "🔍 <b>Выберите способ поиска:</b>\n\n"
            "1. <i>По названию</i> - если знаете конкретное блюдо\n"
            "2. <i>По ингредиентам</i> - если хотите использовать определенные продукты",
            reply_markup=search_method_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in handle_create_recipe: {e}")
        await cmd_start(message)

async def handle_back_to_menu(message: types.Message):
    """Улучшенный обработчик возврата"""
    await message.answer(
        "Возвращаемся в главное меню...",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await asyncio.sleep(0.3)
    await cmd_start(message)

async def debug_command(message: types.Message):
    """Команда для отладки"""
    current_state = user_states.get(message.chat.id, {})
    await message.answer(
        f"DEBUG INFO:\n"
        f"User ID: {message.from_user.id}\n"
        f"Current state: {current_state}\n"
        f"Last message: {message.text}",
        parse_mode="HTML"
    )

def register_handlers(dp):
    """Полная регистрация обработчиков с приоритетами"""
    # Команды
    dp.message.register(cmd_start, Command("start", "help"))
    dp.message.register(debug_command, Command("debug"))
    
    # Главное меню
    dp.message.register(handle_create_recipe, F.text == "🍳 Создать рецепт")
    dp.message.register(show_offer, F.text == "📜 Публичная оферта")
    dp.message.register(show_channel, F.text == "📢 Наш кулинарный канал")
    
    # Навигация
    dp.message.register(handle_back_to_menu, F.text == "↩️ Назад в меню")
    
    # Регистрация дополнительных обработчиков
    from bot.handlers import recipe_handlers, button_handlers
    recipe_handlers.register_handlers(dp)
    button_handlers.register_handlers(dp)
