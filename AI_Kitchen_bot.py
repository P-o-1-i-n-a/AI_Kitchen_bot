import os
import asyncio
import logging
from collections import deque
from typing import Deque, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from groq import Groq

# Настройки логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama3-70b-8192"
CHANNEL_LINK = "https://t.me/ai_kitchen_channel"
SUPPORT_EMAIL = "ai_kitchen_help@outlook.com"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Ограничения запросов
REQUEST_DELAY = 20
MAX_CONCURRENT_REQUESTS = 1
REQUEST_QUEUE: Deque[types.Message] = deque()
ACTIVE_REQUESTS: Dict[int, bool] = {}

# Клавиатуры
def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Поиск рецепта")],
            [KeyboardButton(text="📜 Политика конфиденциальности")],
            [KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True
    )

def get_recipe_search_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 По названию блюда")],
            [KeyboardButton(text="🧅 По ингредиентам")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_after_recipe_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")],
            [KeyboardButton(text="🍳 Создать следующий рецепт")]
        ],
        resize_keyboard=True
    )

# Состояния пользователей
user_states: Dict[int, Dict] = {}

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            if user_id in ACTIVE_REQUESTS and ACTIVE_REQUESTS[user_id]:
                await event.answer("⏳ Ваш предыдущий запрос еще обрабатывается. Пожалуйста, подождите...")
                return
        return await handler(event, data)

dp.message.middleware(RateLimitMiddleware())

async def process_queue():
    """Асинхронная обработка очереди запросов"""
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
    """Генерация рецепта через Groq"""
    try:
        system_prompt = (
            "Ты профессиональный шеф-повар. Создай подробный рецепт на русском языке. "
            "Укажи: 1) точное название блюда, 2) ингредиенты с количествами, "
            "3) пошаговый процесс приготовления, 4) время приготовления, "
            "5) примерную калорийность на порцию. Будь точным и креативным!"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        recipe_text = response.choices[0].message.content
        disclaimer = (
            "\n\nℹ️ Рецепт сгенерирован искусственным интеллектом и может содержать неточности. "
            "Проверяйте ингредиенты перед приготовлением!\n"
            f"Подпишись на наш кулинарный канал: {CHANNEL_LINK}"
        )
        return recipe_text + disclaimer
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "⚠ Ошибка сервера. Попробуйте позже."

async def process_user_request(message: types.Message):
    """Обработка запроса пользователя"""
    user_id = message.from_user.id
    user_data = user_states.get(user_id, {})

    if not user_data:
        await message.answer("Сначала выберите тип поиска рецепта.", reply_markup=get_main_menu())
        return

    prompt = user_data.get('prompt')
    if not prompt:
        await message.answer("Не удалось сформировать запрос.", reply_markup=get_main_menu())
        return

    await message.answer("🍳 Генерирую рецепт...")
    recipe = await generate_recipe(prompt)
    await message.answer(recipe, reply_markup=get_after_recipe_menu())

# Обработчики команд
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_states[message.from_user.id] = {}
    await message.answer(
        "🍳 Добро пожаловать в AI Kitchen Bot!\n"
        "Я помогу вам найти идеальный рецепт с учетом ваших предпочтений.",
        reply_markup=get_main_menu()
    )

@dp.message(Text("🍳 Поиск рецепта"))
async def search_recipe(message: types.Message):
    user_states[message.from_user.id] = {"action": "recipe_search"}
    await message.answer("Выберите тип поиска:", reply_markup=get_recipe_search_menu())

@dp.message(Text("📜 Политика конфиденциальности"))
async def show_privacy_policy(message: types.Message):
    policy_text = (
        "🔒 Политика конфиденциальности\n\n"
        "1. Все рецепты генерируются искусственным интеллектом (ИИ) и могут содержать неточности.\n"
        "2. Мы не храним ваши персональные данные.\n"
        "3. Бот предназначен только для информационных целей.\n"
        "4. Разработчик не несет ответственности за последствия использования рецептов.\n\n"
        "Используя этого бота, вы соглашаетесь с этими условиями."
    )
    await message.answer(policy_text, reply_markup=get_main_menu())

@dp.message(Text("🆘 Помощь"))
async def show_help(message: types.Message):
    help_text = (
        "🆘 Помощь\n\n"
        "Если у вас есть вопросы или предложения, пишите нам на почту:\n"
        f"✉️ {SUPPORT_EMAIL}\n\n"
        "Мы постараемся ответить как можно скорее!"
    )
    await message.answer(help_text, reply_markup=get_main_menu())

@dp.message(Text("🔍 По названию блюда"))
async def search_by_name(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "by_name", "action": "recipe_search"}
    await message.answer("Введите название блюда (например: 'паста карбонара'):", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Text("🧅 По ингредиентам"))
async def search_by_ingredients(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "by_ingredients", "action": "recipe_search"}
    await message.answer("Введите ингредиенты через запятую (например: 'курица, рис, овощи'):", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Text("🔙 Назад"))
async def back_to_main_menu(message: types.Message):
    await message.answer("Возвращаемся в главное меню", reply_markup=get_main_menu())

@dp.message(Text("🏠 Главное меню"))
async def return_to_main_menu(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_menu())

@dp.message(Text("🍳 Создать следующий рецепт"))
async def create_next_recipe(message: types.Message):
    await search_recipe(message)

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    user_data = user_states.get(user_id, {})

    if not user_data:
        await message.answer("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu())
        return

    if user_data.get("action") != "recipe_search":
        await message.answer("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu())
        return

    mode = user_data.get("mode")
    text = message.text.strip()

    if mode == "by_name":
        prompt = (
            f"Создай подробный рецепт для блюда: '{text}'. "
            "Укажи: 1) точное название, 2) ингредиенты с количествами, "
            "3) пошаговый процесс приготовления, 4) время приготовления, "
            "5) калорийность на порцию. Будь креативным!"
        )
    elif mode == "by_ingredients":
        prompt = (
            f"Придумай рецепт используя эти ингредиенты: {text}. "
            "Укажи: 1) название блюда, 2) полный список ингредиентов с количествами, "
            "3) пошаговый процесс приготовления, 4) время приготовления, "
            "5) калорийность на порцию. Будь креативным!"
        )
    else:
        await message.answer("Неизвестный режим поиска.", reply_markup=get_main_menu())
        return

    user_states[user_id]["prompt"] = prompt
    REQUEST_QUEUE.append(message)
    await message.answer("Ваш запрос добавлен в очередь. Подождите немного...")

async def main():
    asyncio.create_task(process_queue())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
