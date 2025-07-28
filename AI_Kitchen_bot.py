import os
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.middlewares import BaseMiddleware
from pip install aiogram==3.0.0b7 import CancelHandler
import openai
from collections import deque
import logging
from typing import Deque, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация для бесплатного тарифа OpenAI (3 RPM)
OPENAI_RATE_LIMIT = 3  # 3 запроса в минуту
REQUEST_DELAY = 20  # 20 секунд между запросами (60/3=20)
MAX_CONCURRENT_REQUESTS = 1  # Только 1 одновременный запрос

# Очередь запросов и система rate limiting
REQUEST_QUEUE: Deque[types.Message] = deque()
ACTIVE_REQUESTS: Dict[int, bool] = {}

# Инициализация бота
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher(bot)
openai.api_key = os.getenv('OPENAI_API_KEY')

# Клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по названию блюда")],
        [KeyboardButton(text="🧅 Поиск по ингредиентам")],
        [KeyboardButton(text="🛑 Отменить запрос")]
    ],
    resize_keyboard=True
)

# Кэш состояний пользователей
user_state: Dict[int, Dict] = {}


class RateLimitMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        if user_id in ACTIVE_REQUESTS and ACTIVE_REQUESTS[user_id]:
            await message.answer("⏳ Ваш предыдущий запрос еще обрабатывается. Пожалуйста, подождите...")
            raise CancelHandler()


async def process_queue():
    """Асинхронная обработка очереди запросов с учетом лимитов"""
    while True:
        if REQUEST_QUEUE and len([v for v in ACTIVE_REQUESTS.values() if v]) < MAX_CONCURRENT_REQUESTS:
            message = REQUEST_QUEUE.popleft()
            user_id = message.from_user.id

            ACTIVE_REQUESTS[user_id] = True
            try:
                await process_user_request(message)
            except Exception as e:
                logger.error(f"Ошибка обработки запроса: {e}")
                await message.answer("⚠ Произошла ошибка. Попробуйте позже.")
            finally:
                ACTIVE_REQUESTS[user_id] = False
                await asyncio.sleep(REQUEST_DELAY)
        await asyncio.sleep(0.1)


async def generate_recipe(prompt: str) -> str:
    """Генерация рецепта с учетом лимитов"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты профессиональный шеф-повар. Создай подробный рецепт:"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            request_timeout=30
        )
        return response.choices[0].message.content
    except openai.error.RateLimitError:
        logger.warning("Достигнут лимит запросов к OpenAI")
        return "⚠ Слишком много запросов. Подождите 20 секунд."
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "⚠ Ошибка сервера. Попробуйте позже."


async def process_user_request(message: types.Message):
    """Обработка запроса пользователя"""
    user_id = message.from_user.id
    user_data = user_state.get(user_id, {})

    if not user_data:
        await message.answer("Сначала выберите тип поиска рецепта.")
        return

    prompt = user_data.get('prompt')
    if not prompt:
        await message.answer("Не удалось сформировать запрос.")
        return

    await message.answer("🍳 Генерирую рецепт...")
    recipe = await generate_recipe(prompt)
    await message.answer(recipe, reply_markup=main_keyboard)


# Обработчики команд
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    user_state[message.from_user.id] = {}
    await message.reply(
        "🍳 Привет! Я кулинарный бот с AI. Выберите способ поиска:",
        reply_markup=main_keyboard
    )


@dp.message_handler(Text(equals="🔍 Поиск по названию блюда"))
async def search_by_dish(message: types.Message):
    user_state[message.from_user.id] = {'mode': 'dish'}
    await message.answer("Введите название блюда:")


@dp.message_handler(Text(equals="🧅 Поиск по ингредиентам"))
async def search_by_ingredients(message: types.Message):
    user_state[message.from_user.id] = {'mode': 'ingredients'}
    await message.answer("Введите ингредиенты (через запятую):")


@dp.message_handler(Text(equals="🛑 Отменить запрос"))
async def cancel_request(message: types.Message):
    user_id = message.from_user.id
    if user_id in ACTIVE_REQUESTS and ACTIVE_REQUESTS[user_id]:
        ACTIVE_REQUESTS[user_id] = False
        await message.answer("✅ Запрос отменен.", reply_markup=main_keyboard)
    else:
        await message.answer("Нет активных запросов для отмены.", reply_markup=main_keyboard)


# Обработка ввода пользователя
@dp.message_handler()
async def handle_user_input(message: types.Message):
    user_id = message.from_user.id
    user_data = user_state.get(user_id, {})

    if not user_data:
        await message.answer("Сначала выберите тип поиска рецепта.", reply_markup=main_keyboard)
        return

    if 'mode' in user_data and 'prompt' not in user_data:
        if user_data['mode'] == 'dish':
            user_data['dish'] = message.text
            await message.answer("Укажите дополнительные предпочтения (кухня, диета и т.д.) или /skip:")
            user_data['waiting_for_prefs'] = True
        elif user_data['mode'] == 'ingredients':
            user_data['ingredients'] = message.text
            await message.answer("Укажите дополнительные предпочтения или /skip:")
            user_data['waiting_for_prefs'] = True

    elif user_data.get('waiting_for_prefs', False):
        preferences = "" if message.text == "/skip" else message.text

        if user_data['mode'] == 'dish':
            prompt = f"Создай рецепт для блюда: {user_data['dish']}. "
        else:
            prompt = f"Создай рецепт используя: {user_data['ingredients']}. "

        if preferences:
            prompt += f"Учти: {preferences}. "

        prompt += "Включи: 1) ингредиенты, 2) инструкцию, 3) время, 4) КБЖУ."

        user_data['prompt'] = prompt
        user_data['waiting_for_prefs'] = False

        await message.answer("⏳ Запрос добавлен в очередь. Ожидайте...")
        REQUEST_QUEUE.append(message)


async def on_startup(dp):
    """Запуск обработки очереди при старте"""
    asyncio.create_task(process_queue())
    dp.middleware.setup(RateLimitMiddleware())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
