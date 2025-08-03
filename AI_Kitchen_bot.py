#!/usr/bin/env python3
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from groq import Groq
from dotenv import load_dotenv

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
# ИНИЦИАЛИЗАЦИЯ БОТА
# ======================
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()
app = FastAPI()
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY')) if os.getenv('GROQ_API_KEY') else None

# ======================
# КЛАВИАТУРЫ
# ======================
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Поиск рецепта")],
            [KeyboardButton(text="📜 Политика конфиденциальности")],
            [KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True
    )

# ======================
# ОБРАБОТЧИКИ КОМАНД
# ======================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🍳 Добро пожаловать в AI Kitchen Bot!",
        reply_markup=get_main_menu()
    )

# Пример обработки текста (заменили Text() на F.text)
@dp.message(F.text == "🍳 Поиск рецепта")
async def handle_recipe_request(message: types.Message):
    await message.answer("Введите ингредиенты для поиска рецепта:")

# ======================
# ВЕБХУКИ
# ======================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ======================
# ЗАПУСК СЕРВИСА
# ======================
@app.on_event("startup")
async def startup():
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        await bot.set_webhook(
            url=f"{webhook_url}/webhook",
            drop_pending_updates=True
        )
        logger.info(f"Вебхук установлен: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL не указан, используем polling")
        asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('WEBHOOK_PORT', 5000)),
        log_level="info"
    )
