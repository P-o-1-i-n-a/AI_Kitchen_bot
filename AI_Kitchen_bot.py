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

# --- Диетические правила ---
DIET_RULES = {
    "🚫 Нет ограничений": {
        "description": "",
        "forbidden": [],
        "replacements": {}
    },
    "⚠️ Аллергии": {
        "description": "Исключены аллергены: {allergies}",
        "forbidden": [],
        "replacements": {}
    },
    "⚖️ Низкокалорийные": {
        "description": "Рецепт содержит менее 300 ккал на порцию",
        "forbidden": ["масло сливочное", "майонез", "сало", "сливки"],
        "replacements": {
            "масло сливочное": "масло оливковое (вдвое меньше)",
            "сливки": "молоко обезжиренное",
            "майонез": "йогурт греческий"
        }
    },
    "💪 Высокобелковые": {
        "description": "Содержит не менее 20г белка на порцию",
        "forbidden": [],
        "replacements": {
            "макароны": "макароны из нута",
            "рис": "киноа"
        }
    },
    "☪️ Халяль": {
        "description": "Соответствует исламским пищевым нормам",
        "forbidden": ["свинина", "бекон", "сало", "алкоголь", "желатин"],
        "replacements": {
            "свинина": "говядина/баранина",
            "бекон": "индейка халяль",
            "алкоголь": "лимонный сок/уксус"
        }
    },
    "☦️ Постная": {
        "description": "Без продуктов животного происхождения",
        "forbidden": ["мясо", "курица", "рыба", "молоко", "сыр", "яйца", "сливочное масло"],
        "replacements": {
            "мясо": "грибы/баклажаны",
            "молоко": "растительное молоко",
            "яйца": "льняная смесь (1 ст.л. льна + 3 ст.л. воды = 1 яйцо)",
            "сливочное масло": "растительное масло"
        }
    }
}

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

def check_diet_conflicts(ingredients: str, diet_type: str, allergies: str = "") -> tuple:
    """Проверяет ингредиенты на соответствие диете"""
    if diet_type not in DIET_RULES:
        return [], ""
    
    ingredients_list = [i.strip().lower() for i in ingredients.split(',')]
    forbidden = DIET_RULES[diet_type]["forbidden"]
    
    if diet_type == "⚠️ Аллергии":
        forbidden = [a.strip().lower() for a in allergies.split(',') if a.strip()]
    
    conflicts = []
    for ingredient in ingredients_list:
        for forbidden_item in forbidden:
            if forbidden_item and forbidden_item in ingredient:
                conflicts.append(ingredient)
                break
    
    replacement_note = ""
    if conflicts and diet_type in DIET_RULES and DIET_RULES[diet_type]["replacements"]:
        replacement_note = "\nВозможные замены:\n"
        for conflict in conflicts:
            for original, replacement in DIET_RULES[diet_type]["replacements"].items():
                if original in conflict:
                    replacement_note += f"- {conflict} → {replacement}\n"
    
    return conflicts, replacement_note

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
    await message.answer("🔄 Проверяю ингредиенты...")
    
    # Проверка на конфликты с диетой
    diet_type = user_states[message.chat.id]["diet_type"]
    allergies = user_states[message.chat.id].get("allergies", "")
    
    conflicts, replacements = check_diet_conflicts(
        message.text, 
        diet_type,
        allergies
    )
    
    if conflicts:
        warning_msg = f"⚠️ Внимание: эти ингредиенты не соответствуют выбранной диете ({diet_type}):\n"
        warning_msg += "\n".join(f"- {c}" for c in conflicts)
        if replacements:
            warning_msg += replacements
        await message.answer(warning_msg)
    
    await message.answer("🔄 Генерирую рецепт с учетом диетических ограничений...")
    await generate_recipe(message.chat.id)

async def generate_recipe(chat_id: int):
    try:
        data = user_states[chat_id]
        await bot.send_chat_action(chat_id, 'typing')

        # Формируем промпт с учетом диеты
        diet_info = DIET_RULES.get(data['diet_type'], DIET_RULES["🚫 Нет ограничений"])
        diet_description = diet_info["description"]
        
        if data['diet_type'] == "⚠️ Аллергии":
            diet_description = diet_description.format(allergies=data.get('allergies', ''))
        
        replacements_note = ""
        if diet_info["replacements"]:
            replacements_note = "\nВозможные замены:\n" + "\n".join(
                f"- {k} → {v}" for k, v in diet_info["replacements"].items()
            )

        # Формируем промпт частями
        prompt_lines = [
            "Ты - профессиональный шеф-повар. Создай рецепт строго по следующим требованиям:",
            "",
            "1. Основные параметры:",
            f"- Прием пищи: {data['meal_time']}",
            f"- Кухня: {data['cuisine']}",
            f"- Диета: {data['diet_type']} ({diet_description})",
            f"- Исходные ингредиенты: {data['ingredients']}",
            "",
            "2. Строгие правила:"
        ]
        
        if data['diet_type'] == "⚠️ Аллергии":
            prompt_lines.append(f"- Исключи следующие аллергены: {data['allergies']}")
        elif diet_info["forbidden"]:
            prompt_lines.extend([f"- Исключи {i}" for i in diet_info["forbidden"]])
        
        if diet_info["replacements"]:
            prompt_lines.extend([f"- Замени {k} на {v}" for k, v in diet_info["replacements"].items()])
        
        prompt_lines.extend([
            "",
            "3. Требования к формату:",
            "🍽 Название блюда (укажи тип диеты, если не стандартный)",
            f"🌍 Кухня: {data['cuisine']}",
            f"🥗 Диета: {data['diet_type']} ({diet_description})",
            f"⚠️ Изменения: {'Нет' if not diet_info['forbidden'] else 'Исключено: ' + ', '.join(diet_info['forbidden'])}",
            "",
            "⏱ Время приготовления (разбивка по этапам)",
            "👨‍🍳 Порций: [число]",
            "",
            "📋 Ингредиенты (на 1 порцию):",
            "- [ингредиент] [кол-во] (замена если была)",
            "[общее кол-во для всех порций в скобках]",
            "",
            "🔪 Пошаговый рецепт (адаптированный под диету):",
            "1. [шаг с учетом изменений]",
            "...",
            "",
            "📊 КБЖУ на порцию (точно рассчитанные):",
            "- Калории: [значение] ккал",
            "- Белки: [значение] г",
            "- Жиры: [значение] г",
            "- Углеводы: [значение] г",
            "",
            "💡 Советы:",
            "- По адаптации рецепта",
            "- По заменам ингредиентов",
            "- По подаче и хранению"
        ])

        prompt = "\n".join(prompt_lines)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.5,
                "maxTokens": 2500
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты профессиональный диетолог и шеф-повар. Строго соблюдай диетические ограничения. Говори только на русском. Форматируй ответ четко по структуре."
                },
                {
                    "role": "user", 
                    "text": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
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

        # Отправляем рецепт частями, если он слишком длинный
        if len(recipe) > 4000:
            parts = [recipe[i:i+4000] for i in range(0, len(recipe), 4000)]
            for part in parts:
                await bot.send_message(chat_id, part, reply_markup=markup)
                await asyncio.sleep(0.5)
        else:
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
