#!/usr/bin/env python3
import os
import re
import logging
import asyncio
import httpx
import uvloop
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from groq import Groq
from dotenv import load_dotenv

# Устанавливаем uvloop как event loop для asyncio
uvloop.install()

# ======================
# НАСТРОЙКА ЛОГГИРОВАНИЯ
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================
# ЗАГРУЗКА ПЕРЕМЕННЫХ
# ======================
load_dotenv('/etc/secrets/bot_env')
print("DEBUG: TELEGRAM_BOT_TOKEN =", os.getenv("TELEGRAM_BOT_TOKEN"))


# Проверка обязательных переменных
REQUIRED_KEYS = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY', 'WEBHOOK_URL']
for key in REQUIRED_KEYS:
    if not os.getenv(key):
        logger.error(f"Отсутствует обязательная переменная: {key}")
        raise SystemExit(1)

# Загрузка режимов работы
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAINTENANCE = os.getenv('MAINTENANCE', 'False').lower() == 'true'
logger.info(f"Режимы работы: DEBUG={DEBUG}, MAINTENANCE={MAINTENANCE}")

# ======================
# ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ
# ======================
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()
app = web.Application()

# Режим обслуживания
if MAINTENANCE:
    maintenance_router = Router()
    
    @maintenance_router.message()
    async def maintenance_mode(message: types.Message):
        await message.answer("🔧 Бот на техническом обслуживании. Попробуйте позже.")
    
    dp.include_router(maintenance_router)
    logger.warning("Бот запущен в режиме обслуживания!")

# Конфигурация клиента Groq с увеличенными таймаутами и правильным доменом
groq_client = Groq(
    api_key=os.getenv('GROQ_API_KEY'),
    base_url="https://api.groq.com/v1"  # ← Убрать /openai!
)

MODEL_NAME = "llama3-70b-8192"
CHANNEL_LINK = os.getenv('CHANNEL_LINK', "https://t.me/ai_kitchen_channel")

# ======================
# КОНСТАНТЫ И НАСТРОЙКИ
# ======================
MAX_RETRIES = 3  # Максимальное количество попыток запроса к API
REQUEST_DELAY = 1  # Задержка между попытками в секундах

# ======================
# СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ
# ======================
user_states = {}

# ======================
# КЛАВИАТУРЫ
# ======================
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")],
            [KeyboardButton(text="📜 Публичная оферта")],
            [KeyboardButton(text="📢 Наш кулинарный канал")]
        ],
        resize_keyboard=True
    )

def meal_time_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌅 Завтрак"), KeyboardButton(text="🌇 Обед")],
            [KeyboardButton(text="🌃 Ужин"), KeyboardButton(text="☕ Перекус")]
        ],
        resize_keyboard=True
    )

def cuisine_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русская"), KeyboardButton(text="🇮🇹 Итальянская"), KeyboardButton(text="🇯🇵 Японская")],
            [KeyboardButton(text="🇬🇪 Кавказская"), KeyboardButton(text="🇺🇸 Американская"), KeyboardButton(text="🇫🇷 Французская")],
            [KeyboardButton(text="🇹🇷 Турецкая"), KeyboardButton(text="🇨🇳 Китайская"), KeyboardButton(text="🇲🇽 Мексиканская")],
            [KeyboardButton(text="🇮🇳 Индийская")]
        ],
        resize_keyboard=True
    )

def diet_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚫 Нет ограничений"), KeyboardButton(text="⚠️ Аллергии")],
            [KeyboardButton(text="⚖️ Низкокалорийные"), KeyboardButton(text="💪 Высокобелковые")],
            [KeyboardButton(text="☪️ Халяль"), KeyboardButton(text="☦️ Постная")]
        ],
        resize_keyboard=True
    )

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================
def ensure_russian(text):
    """Удаляет английские фразы из текста"""
    return re.sub(r'[a-zA-Z]', '', text).strip()

async def safe_api_call(call, *args, **kwargs):
    """Безопасный вызов API с повторными попытками"""
    for attempt in range(MAX_RETRIES):
        try:
            return await call(*args, **kwargs)
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(REQUEST_DELAY * (attempt + 1))
        except Exception as e:
            logger.error(f"API call error: {str(e)}")
            raise

# ======================
# ОБРАБОТЧИКИ КОМАНД
# ======================
@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    if DEBUG:
        logger.debug(f"Start command from {message.from_user.id}")
    
    await message.answer(
    "👨‍🍳 Привет! Я - кулинарный бот с генерацией рецептов. Мой профиль: {}\n"
    "⚠️ Рецепты создаются искусственным интеллектом (AI) и могут содержать неточности.\n\n"
    "Нажмите кнопку ниже, чтобы создать рецепт ↓".format(os.getenv('BOT_LINK')),
    reply_markup=main_keyboard()
)

@dp.message(F.text == "📜 Публичная оферта")
async def show_offer(message: types.Message):
    await message.answer(
        "📄 Публичная оферта:\n\n"
        "1. Все рецепты генерируются искусственным интеллектом и не являются профессиональной рекомендацией.\n"
        "2. Вы несете ответственность за проверку ингредиентов на аллергены и свежесть.\n"
        "3. Запрещено использовать бот для создания вредоносного контента.",
        disable_web_page_preview=True
    )

@dp.message(F.text == "📢 Наш кулинарный канал")
async def show_channel(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍳 AI Kitchen Channel", url=CHANNEL_LINK)]
    ])
    await message.answer(
        "🔔 Подпишитесь на наш кулинарный канал с рецептами и кулинарными лайфхаками!",
        reply_markup=markup
    )

@dp.message(F.text == "🍳 Создать рецепт")
async def ask_meal_time(message: types.Message):
    if MAINTENANCE:
        return
    
    user_states[message.chat.id] = {"step": "waiting_meal_time"}
    await message.answer(
        "🕒 Для какого приёма пищи нужен рецепт?",
        reply_markup=meal_time_keyboard()
    )

@dp.message(
    lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_meal_time"
)
async def ask_cuisine(message: types.Message):
    if MAINTENANCE:
        return
        
    if message.text not in ["🌅 Завтрак", "🌇 Обед", "🌃 Ужин", "☕ Перекус"]:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓", 
                           reply_markup=meal_time_keyboard())
        return

    user_states[message.chat.id] = {
        "step": "waiting_cuisine",
        "meal_time": message.text
    }
    await message.answer("🌍 Выберите кухню:", reply_markup=cuisine_keyboard())

@dp.message(
    lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_cuisine"
)
async def ask_diet(message: types.Message):
    if MAINTENANCE:
        return
        
    valid_cuisines = ["🇷🇺 Русская", "🇮🇹 Итальянская", "🇯🇵 Японская", "🇬🇪 Кавказская",
                     "🇺🇸 Американская", "🇫🇷 Французская", "🇹🇷 Турецкая", "🇨🇳 Китайская",
                     "🇲🇽 Мексиканская", "🇮🇳 Индийская"]

    if message.text not in valid_cuisines:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓", 
                           reply_markup=cuisine_keyboard())
        return

    user_states[message.chat.id]["cuisine"] = message.text
    user_states[message.chat.id]["step"] = "waiting_diet"
    await message.answer("🥗 Есть ли диетические ограничения?", reply_markup=diet_keyboard())

@dp.message(
    lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_diet"
)
async def process_diet_choice(message: types.Message):
    if MAINTENANCE:
        return
        
    valid_diets = ["🚫 Нет ограничений", "⚠️ Аллергии", "⚖️ Низкокалорийные",
                  "💪 Высокобелковые", "☪️ Халяль", "☦️ Постная"]

    if message.text not in valid_diets:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓", 
                           reply_markup=diet_keyboard())
        return

    user_states[message.chat.id]["diet_type"] = message.text

    if message.text == "⚠️ Аллергии":
        user_states[message.chat.id]["step"] = "waiting_allergies"
        await message.answer(
            "📝 Укажите продукты, которые нужно исключить (через запятую):\n"
            "Пример: орехи, молоко, морепродукты",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        user_states[message.chat.id]["step"] = "waiting_ingredients"
        await ask_for_ingredients(message.chat.id)

async def ask_for_ingredients(chat_id: int):
    if MAINTENANCE:
        return
        
    await bot.send_message(
        chat_id,
        "📝 Введите ингредиенты через запятую:\n"
        "Пример: 2 яйца, 100г муки, 1 ст.л. масла",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(
    lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_allergies"
)
async def process_allergies(message: types.Message):
    if MAINTENANCE:
        return
        
    user_states[message.chat.id]["allergies"] = message.text
    user_states[message.chat.id]["step"] = "waiting_ingredients"
    await ask_for_ingredients(message.chat.id)

@dp.message(
    lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_ingredients"
)
async def process_ingredients(message: types.Message):
    if MAINTENANCE:
        return
        
    user_states[message.chat.id]["ingredients"] = message.text
    await message.answer(
        "🔄 Генерирую рецепт... Пожалуйста, подождите.\n"
        "Это может занять до 30 секунд.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await generate_recipe(message.chat.id)

async def generate_recipe(chat_id: int):
    try:
        if MAINTENANCE:
            await bot.send_message(chat_id, "🔧 Бот на техническом обслуживании. Попробуйте позже.")
            return

        data = user_states[chat_id]
        await bot.send_chat_action(chat_id, 'typing')

        if DEBUG:
            logger.debug(f"Generating recipe for {chat_id} with data: {data}")

        # Формируем промпт
        diet_prompt = ""
        if data.get('diet_type') == "⚠️ Аллергии":
            diet_prompt = f" Исключи: {data.get('allergies', '')}."
        elif data['diet_type'] == "⚖️ Низкокалорийные":
            diet_prompt = " Сделай рецепт низкокалорийным (менее 300 ккал на порцию)."
        elif data['diet_type'] == "💪 Высокобелковые":
            diet_prompt = " Сделай рецепт с высоким содержанием белка (не менее 20г на порцию)."
        elif data['diet_type'] == "☪️ Халяль":
            diet_prompt = " Учитывай правила халяль (без свинины, алкоголя и т.д.)."
        elif data['diet_type'] == "☦️ Постная":
            diet_prompt = " Учитывай православные постные правила (без мяса, молока, яиц)."

        prompt = f"""Составь рецепт для {data['meal_time']} в стиле {data['cuisine']} кухни, используя: {data['ingredients']}.{diet_prompt}
        Формат (всегда на русском):
        🍽 Название (только на русском)
        🌍 Кухня: [тип кухни]
        🥗 Диета: [тип диеты]
        ⏱ Время приготовления: [время]
        📋 Ингредиенты (точные количества в граммах/мл):
        - Ингредиент 1: количество
        - Ингредиент 2: количество
        🔪 Пошаговое приготовление:
        1. Шаг 1
        2. Шаг 2
        📊 КБЖУ на порцию (указать вес порции в граммах):
        - Калории: [ккал]
        - Белки: [г]
        - Жиры: [г]
        - Углеводы: [г]
        💡 Полезные советы:"""

        response = await safe_api_call(
            groq_client.chat.completions.create,
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Ты профессиональный шеф-повар. Говори только на русском языке!"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        recipe = ensure_russian(response.choices[0].message.content)
        
        if DEBUG:
            logger.debug(f"Generated recipe: {recipe[:200]}...")
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Наш кулинарный канал", url=CHANNEL_LINK)]
        ])
        
        await bot.send_message(
            chat_id,
            recipe,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        await bot.send_message(
            chat_id,
            "Что будем делать дальше?",
            reply_markup=main_keyboard()
        )

    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        await bot.send_message(
            chat_id,
            "⏳ Превышено время ожидания ответа от сервиса генерации. Попробуйте позже.",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка генерации: {str(e)}", exc_info=True)
        await bot.send_message(
            chat_id,
            "⚠️ Произошла ошибка при генерации рецепта. Попробуйте ещё раз.",
            reply_markup=main_keyboard()
        )
    finally:
        if chat_id in user_states:
            user_states[chat_id]["step"] = "done"

@dp.message()
async def handle_other(message: types.Message):
    if MAINTENANCE:
        return
        
    await message.answer(
        "Используйте кнопку «🍳 Создать рецепт» или /start",
        reply_markup=main_keyboard()
    )

# ======================
# ОБРАБОТЧИК ВЕБХУКА
# ======================
async def handle_webhook(request):
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(text="Error", status=500)

# ======================
# ЗАПУСК СЕРВЕРА
# ======================
async def on_startup(bot: Bot):
    if DEBUG:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logger.info("Режим DEBUG активирован")

    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        try:
            await bot.set_webhook(
                url=f"{webhook_url}/webhook",
                drop_pending_updates=True
            )
            logger.info(f"Вебхук установлен: {webhook_url}")
        except Exception as e:
            logger.error(f"Ошибка установки вебхука: {e}")
            raise
    else:
        logger.warning("WEBHOOK_URL не указан, используем polling")

async def main():
    # Регистрируем обработчик вебхука
    app.router.add_post('/webhook', handle_webhook)
    
    # Настраиваем приложение aiogram
    setup_application(app, dp, bot=bot)
    
    # Выполняем startup действия
    await on_startup(bot)
    
    # Настраиваем и запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Используем порт из переменной окружения (8000 по умолчанию)
    port = int(os.getenv('WEBHOOK_PORT', 8000))  # ← Основное изменение!
    
    site = web.TCPSite(
        runner, 
        host='127.0.0.1',  # Слушаем только локально ← Важно!
        port=port,
        reuse_port=True
    )
    
    logger.info(f"Сервер запущен на порту {port}")
    
    try:
        await site.start()
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка сервера: {e}")
    finally:
        await runner.cleanup()
        await bot.session.close()
        logger.info("Сервер остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")





