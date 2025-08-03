import os
import asyncio
import logging
import hmac
import hashlib
from collections import deque
from typing import Deque, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, Text
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from groq import Groq

# Настройки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")  # Добавьте этот секрет в .env
MODEL_NAME = "llama3-70b-8192"
CHANNEL_LINK = "https://t.me/ai_kitchen_channel"
SUPPORT_EMAIL = "ai_kitchen_help@outlook.com"
WEBHOOK_PORT = 5000
WEBHOOK_URL = "https://ваш-домен.ру/webhook"  # Ваш основной вебхук для Telegram
GITHUB_WEBHOOK_PATH = "/github-webhook"  # Путь для GitHub вебхуков

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
app = FastAPI()
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

# Middleware для ограничения запросов
class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            if user_id in ACTIVE_REQUESTS and ACTIVE_REQUESTS[user_id]:
                await event.answer("⏳ Ваш предыдущий запрос еще обрабатывается. Пожалуйста, подождите...")
                return
        return await handler(event, data)

dp.message.middleware(RateLimitMiddleware())

# Обработка очереди запросов
async def process_queue():
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

# Генерация рецепта
async def generate_recipe(prompt: str) -> str:
    try:
        system_prompt = "Ты профессиональный шеф-повар..."
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7
        )
        recipe_text = response.choices[0].message.content
        disclaimer = f"\n\nℹ️ Рецепт сгенерирован ИИ. Подпишись: {CHANNEL_LINK}"
        return recipe_text + disclaimer
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "⚠ Ошибка сервера. Попробуйте позже."

# Обработчики команд
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("🍳 Добро пожаловать в AI Kitchen Bot!", reply_markup=get_main_menu())

# ... (другие обработчики сообщений остаются без изменений)

# Вебхук для Telegram
@app.post("/webhook")
async def handle_telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return JSONResponse({"status": "error"}, status_code=500)

# Вебхук для GitHub
@app.post(GITHUB_WEBHOOK_PATH)
async def handle_github_webhook(request: Request):
    try:
        # Проверка подписи
        body = await request.body()
        signature = request.headers.get("x-hub-signature-256")
        
        if not GITHUB_WEBHOOK_SECRET:
            logger.warning("GitHub webhook secret not configured")
            raise HTTPException(status_code=403, detail="Webhook secret not configured")
        
        if not signature:
            logger.warning("Missing GitHub signature")
            raise HTTPException(status_code=403, detail="Missing signature")
        
        computed_signature = 'sha256=' + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            logger.warning("Invalid GitHub signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Обработка событий GitHub
        event = request.headers.get("x-github-event")
        payload = await request.json()
        
        logger.info(f"GitHub webhook received: {event}")
        logger.debug(f"Payload: {payload}")
        
        # Здесь можно добавить логику обработки разных событий
        if event == "push":
            logger.info(f"Push event received for repo: {payload['repository']['full_name']}")
            # Например, можно автоматически обновлять бота при пуше в репозиторий
            # await bot.send_message(ADMIN_CHAT_ID, "Получен push в репозиторий")
        
        return JSONResponse({"status": "success"})
    
    except Exception as e:
        logger.error(f"GitHub webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Запуск бота и веб-сервера
async def start_bot():
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(process_queue())
    logger.info(f"Бот запущен. Telegram вебхук: {WEBHOOK_URL}")
    logger.info(f"GitHub вебхук доступен по: {WEBHOOK_URL}{GITHUB_WEBHOOK_PATH}")

if __name__ == "__main__":
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    async def run():
        await start_bot()
        await server.serve()
    
    asyncio.run(run())
