#!/usr/bin/env python3
import os
import re
import logging
import asyncio
import httpx
import uvloop
from aiogram import Bot, Dispatcher, types, F
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

# Проверка обязательных переменных
REQUIRED_KEYS = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY']
for key in REQUIRED_KEYS:
    if not os.getenv(key):
        logger.error(f"Отсутствует обязательная переменная: {key}")
        raise SystemExit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ
# ======================
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()
app = web.Application()

# Исправленная инициализация Groq клиента
groq_client = Groq(
    api_key=os.getenv('GROQ_API_KEY'),
    http_client=httpx.AsyncClient(proxies=None)
) if os.getenv('GROQ_API_KEY') else None

MODEL_NAME = "llama3-70b-8192"
CHANNEL_LINK = "https://t.me/ai_kitchen_channel"

# ======================
# СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ
# ======================
user_states = {}

# [Остальной код остается без изменений до функции generate_recipe]

async def generate_recipe(chat_id: int):
    try:
        data = user_states[chat_id]
        await bot.send_chat_action(chat_id, 'typing')

        # Формируем промпт с учетом диеты
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

        if data['ingredients'].lower() == 'что есть в холодильнике?':
            prompt = f"""Придумай рецепт для {data['meal_time']} в стиле {data['cuisine']} кухни.{diet_prompt}
            Используй распространённые ингредиенты, которые обычно есть дома у россиян. Говори только на русском языке!"""
        else:
            prompt = f"""Составь рецепт для {data['meal_time']} в стиле {data['cuisine']} кухни, используя: {data['ingredients']}.{diet_prompt}
            Говори только на русском языке!"""

        prompt += """
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

        response = await groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Ты профессиональный шеф-повар. Говори только на русском языке! "
                               "Всегда указывай вес порции в граммах при расчёте КБЖУ."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        recipe = ensure_russian(response.choices[0].message.content)
        
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

    except Exception as e:
        await bot.send_message(
            chat_id,
            f"⚠️ Ошибка генерации рецепта: {str(e)}\n\n"
            "Попробуйте еще раз или нажмите /start",
            reply_markup=main_keyboard()
        )
    finally:
        user_states[chat_id]["step"] = "done"

# [Остальной код без изменений]

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
