import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ===== Настройка логирования =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Получение токена =====
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.critical("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# ===== Инициализация бота и диспетчера =====
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ===== Клавиатура =====
def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")],
            [
                KeyboardButton(text="📜 Публичная оферта"),
                KeyboardButton(text="📢 Наш канал")
            ]
        ],
        resize_keyboard=True
    )

# ===== Обработчик команды /start =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я AI Kitchen Bot!", reply_markup=get_keyboard())

# ===== Главная функция =====
async def main():
    logger.info("🚀 Бот запускается...")
    try:
        # start_polling теперь с диспетчером и ботом
        await dp.start_polling(bot, skip_updates=True)
    finally:
        # закрываем сессию бота при завершении
        await bot.session.close()

# ===== Точка входа =====
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен вручную")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
