#!/usr/bin/env python3
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from groq import Groq
from dotenv import load_dotenv

# =======================================
# НАСТРОЙКА ЛОГГИРОВАНИЯ
# =======================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =======================================
# ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# =======================================
load_dotenv('/etc/secrets/bot_env')

# Проверка обязательных переменных
REQUIRED_KEYS = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY', 'WEBHOOK_URL']
for key in REQUIRED_KEYS:
    if not os.getenv(key):
        logger.error(f"Отсутствует обязательная переменная: {key}")
        raise SystemExit(1)

# =======================================
# ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ
# =======================================
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()
app = FastAPI()
client = Groq(api_key=os.getenv('GROQ_API_KEY')) if os.getenv('GROQ_API_KEY') else None

# =======================================
# КЛАВИАТУРЫ
# =======================================
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Поиск рецепта")],
            [KeyboardButton(text="📜 Политика конфиденциальности")],
            [KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True
    )

# =======================================
# ОБРАБОТЧИКИ КОМАНД
# =======================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🍳 Добро пожаловать в AI Kitchen Bot!",
        reply_markup=get_main_menu()
    )

# =======================================
# ВЕБХУК ДЛЯ TELEGRAM
# =======================================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =======================================
# ЗАПУСК СЕРВИСА
# =======================================
@app.on_event("startup")
async def startup():
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    try:
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"Вебхук установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")
        raise

if __name__ == "__main__":
    # Конфигурация UVICORN
    uvicorn_config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=int(os.getenv('WEBHOOK_PORT', 5000)),
        log_level="info",
        reload=False
    )
    
    # Запуск сервера
    server = uvicorn.Server(uvicorn_config)
    
    async def run():
        await startup()
        await server.serve()
    
    asyncio.run(run())
