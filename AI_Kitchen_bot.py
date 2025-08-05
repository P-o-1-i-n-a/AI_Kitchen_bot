#!/usr/bin/env python3
import os
import re
import json
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
from dotenv import load_dotenv

uvloop.install()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv('/etc/secrets/bot_env')

REQUIRED_KEYS = ['TELEGRAM_BOT_TOKEN', 'YANDEX_API_KEY', 'YANDEX_FOLDER_ID', 'WEBHOOK_URL']
for key in REQUIRED_KEYS:
    if not os.getenv(key):
        logger.error(f"Отсутствует обязательная переменная: {key}")
        raise SystemExit(1)

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAINTENANCE = os.getenv('MAINTENANCE', 'False').lower() == 'true'
logger.info(f"Режимы работы: DEBUG={DEBUG}, MAINTENANCE={MAINTENANCE}")

bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()
app = web.Application()

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
CHANNEL_LINK = os.getenv('CHANNEL_LINK', "https://t.me/ai_kitchen_channel")

MAX_RETRIES = 3
REQUEST_DELAY = 1

user_states = {}

# --- Клавиатуры ---
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

# --- Вспомогательные функции ---
def ensure_russian(text):
    return re.sub(r'[a-zA-Z]', '', text).strip()

async def safe_api_call(call, *args, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            return await call(*args, **kwargs)
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(REQUEST_DELAY * (attempt + 1))
        except Exception as e:
            logger.error(f"API call error: {str(e)}")
            raise

# --- Команды ---
@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👨‍🍳 Привет! Я - кулинарный бот с генерацией рецептов. Мой профиль: {}\n"
        "⚠️ Рецепты создаются искусственным интеллектом и могут содержать неточности.\n\n"
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
    await message.answer("🔔 Подпишитесь на наш кулинарный канал с рецептами и кулинарными лайфхаками!", reply_markup=markup)

@dp.message(F.text == "🍳 Создать рецепт")
async def ask_meal_time(message: types.Message):
    user_states[message.chat.id] = {"step": "waiting_meal_time"}
    await message.answer("🕒 Для какого приёма пищи нужен рецепт?", reply_markup=meal_time_keyboard())

@dp.message(lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_meal_time")
async def ask_cuisine(message: types.Message):
    if message.text not in ["🌅 Завтрак", "🌇 Обед", "🌃 Ужин", "☕ Перекус"]:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓", reply_markup=meal_time_keyboard())
        return
    user_states[message.chat.id] = {"step": "waiting_cuisine", "meal_time": message.text}
    await message.answer("🌍 Выберите кухню:", reply_markup=cuisine_keyboard())

@dp.message(lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_cuisine")
async def ask_diet(message: types.Message):
    if message.text not in [btn.text for row in cuisine_keyboard().keyboard for btn in row]:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓", reply_markup=cuisine_keyboard())
        return
    user_states[message.chat.id]["cuisine"] = message.text
    user_states[message.chat.id]["step"] = "waiting_diet"
    await message.answer("🥗 Есть ли диетические ограничения?", reply_markup=diet_keyboard())

@dp.message(lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_diet")
async def process_diet_choice(message: types.Message):
    user_states[message.chat.id]["diet_type"] = message.text
    if message.text == "⚠️ Аллергии":
        user_states[message.chat.id]["step"] = "waiting_allergies"
        await message.answer("📝 Укажите продукты, которые нужно исключить (через запятую):", reply_markup=types.ReplyKeyboardRemove())
    else:
        user_states[message.chat.id]["step"] = "waiting_ingredients"
        await ask_for_ingredients(message.chat.id)

@dp.message(lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_allergies")
async def process_allergies(message: types.Message):
    user_states[message.chat.id]["allergies"] = message.text
    user_states[message.chat.id]["step"] = "waiting_ingredients"
    await ask_for_ingredients(message.chat.id)

async def ask_for_ingredients(chat_id: int):
    await bot.send_message(chat_id, "📝 Введите ингредиенты через запятую:\nПример: 2 яйца, 100г муки, 1 ст.л. масла", reply_markup=types.ReplyKeyboardRemove())

@dp.message(lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_ingredients")
async def process_ingredients(message: types.Message):
    user_states[message.chat.id]["ingredients"] = message.text
    await message.answer("🔄 Генерирую рецепт... Пожалуйста, подождите.")
    await generate_recipe(message.chat.id)

# --- ГЕНЕРАЦИЯ С ЯНДЕКС GPT ---
async def generate_recipe(chat_id: int):
    try:
        data = user_states[chat_id]
        await bot.send_chat_action(chat_id, 'typing')

        diet_prompt = ""
        if data['diet_type'] == "⚠️ Аллергии":
            diet_prompt = f" Исключи: {data.get('allergies', '')}.отправь небольшое сообщение с предупреждением если пользователь ввелингридиенты-аллергены. и не бери в рецепт ингридиенты-аллергены"
        elif data['diet_type'] == "⚖️ Низкокалорийные":
            diet_prompt = " Сделай рецепт низкокалорийным (менее 300 ккал на порцию)."
        elif data['diet_type'] == "💪 Высокобелковые":
            diet_prompt = " Сделай рецепт с высоким содержанием белка (не менее 20г на порцию)."
        elif data['diet_type'] == "☪️ Халяль":
            diet_prompt = " Учитывай правила халяль. отправь небольшое сообщение с предупреждением если пользователь ввел ингридиенты, не подходящие под эту диету. и не бери в рецепт неподходящие для диеты ингридиенты"
        elif data['diet_type'] == "☦️ Постная":
            diet_prompt = " Учитывай постные правила (без мяса, молока, яиц). отправь небольшое сообщение с предупреждением если пользователь ввел ингридиенты, не подходящие под эту диету. и не бери в рецепт неподходящие для диеты ингридиенты"

        prompt = f"""Ты - профессиональный шеф-повар. Создай подробный рецепт блюда по следующим параметрам:
- Прием пищи: {data['meal_time']}
- Кухня: {data['cuisine']}
- Диетические ограничения: {data['diet_type']}{f" (исключить: {data.get('allergies', '')})" if data['diet_type'] == "⚠️ Аллергии" else ""}
- Основные ингредиенты: {data['ingredients']}

Требования к формату ответа (строго соблюдай структуру):
1. 🍽 Название блюда (должно отражать кухню и тип блюда)
2. 🌍 Кухня: {data['cuisine']}
3. 🥗 Тип диеты: {data['diet_type']}
4. ⏱ Время приготовления (общее и по этапам)
5. 👨‍🍳 Количество порций (укажи точное число)
6. 📋 Ингредиенты (в граммах/мл на 1 порцию):
   - Перечисли все ингредиенты с точным количеством на 1 порцию
   - Укажи общее количество для всех порций в скобках
7. 🔪 Пошаговый рецепт (подробные шаги с временем на каждый этап)
8. 📊 Пищевая ценность на порцию (точно рассчитай):
   - Калории (ккал)
   - Белки (г)
   - Жиры (г)
   - Углеводы (г)
9. 💡 Полезные советы (по замене ингредиентов, хранению и подаче)

Пример правильного ответа:
🍽 Спагетти Карбонара по-римски
🌍 Кухня: Итальянская
🥗 Тип диеты: 🚫 Нет ограничений
⏱ Время приготовления: 25 мин (10 мин подготовка, 15 мин готовка)
👨‍🍳 Количество порций: 2

📋 Ингредиенты (на 1 порцию):
- Спагетти: 100г (200г всего)
- Гуанчиале: 50г (100г всего)
- Яйцо: 1 шт (2 шт всего)
- Пармезан: 30г (60г всего)
- Черный перец: по вкусу
- Соль: щепотка

🔪 Приготовление:
1. Отварите спагетти в подсоленной воде...
2. Обжарьте гуанчиале до хрустящей корочки...
3. Взбейте яйца с пармезаном...
4. Смешайте все ингредиенты...

📊 Пищевая ценность на порцию:
- Калории: 550 ккал
- Белки: 25г
- Жиры: 30г
- Углеводы: 45г

💡 Советы:
- Для более легкой версии используйте сливки вместо яиц
- Подавайте сразу после приготовления
- Хранить не рекомендуется"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 2048},
            "messages": [
                {"role": "system", "text": "Ты профессиональный шеф-повар с 20-летним опытом. Говори только на русском языке!"},
                {"role": "user", "text": prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            yandex_response = await safe_api_call(
                client.post,
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                data=json.dumps(body)
            )

            result = yandex_response.json()
            recipe = ensure_russian(result['result']['alternatives'][0]['message']['text'])

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Наш кулинарный канал", url=CHANNEL_LINK)]
        ])

        await bot.send_message(chat_id, recipe, reply_markup=markup)
        await bot.send_message(chat_id, "Что будем делать дальше?", reply_markup=main_keyboard())

    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        await bot.send_message(chat_id, "⚠️ Ошибка генерации. Попробуйте ещё раз.", reply_markup=main_keyboard())

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Используйте кнопку «🍳 Создать рецепт» или /start", reply_markup=main_keyboard())

# --- Webhook ---
async def handle_webhook(request):
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(text="Error", status=500)

async def on_startup(bot: Bot):
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        await bot.set_webhook(url=f"{webhook_url}/webhook", drop_pending_updates=True)
        logger.info(f"Вебхук установлен: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL не указан!")

async def main():
    app.router.add_post('/webhook', handle_webhook)
    setup_application(app, dp, bot=bot)
    await on_startup(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('WEBHOOK_PORT', 8000))
    site = web.TCPSite(runner, host='127.0.0.1', port=port, reuse_port=True)
    await site.start()
    logger.info(f"Сервер запущен на порту {port}")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Остановка бота")
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")

