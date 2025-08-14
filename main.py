import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка токена
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    logger.error("❌ ОШИБКА: BOT_TOKEN не найден!")
    logger.info("Проверьте файл: /etc/secrets/bot_env")
    exit(1)
else:
    logger.info(f"✅ Токен получен ({len(API_TOKEN)} символов)")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Клавиатуры и обработчики (ваш код остаётся без изменений)
def main_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("🍳 Создать рецепт"),
        KeyboardButton("📜 Публичная оферта"),
        KeyboardButton("📢 Наш канал")
    )

@dp.message_handler(commands=["start"])
async def start(message):
    await message.answer("Привет! Я AI Kitchen Bot!", reply_markup=main_keyboard())

# Важно: добавляем "здоровый" обработчик ошибок
async def on_startup(dp):
    logger.info("🟢 Бот успешно запущен")

async def on_shutdown(dp):
    logger.warning("🔴 Бот остановлен")

if __name__ == "__main__":
    try:
        logger.info("🚀 Запуск бота...")
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=60,
            relax=1
        )
        # Важно: aiogram 3.x автоматически блокирует поток
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
