import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка наличия токена
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    logger.error("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    logger.info("Проверьте файл /etc/secrets/bot_env")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Клавиатуры ---
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Создать рецепт")],
            [
                KeyboardButton(text="📜 Публичная оферта"),
                KeyboardButton(text="📢 Наш канал")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def search_method_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 По названию")],
            [KeyboardButton(text="🥕 По ингредиентам")],
            [KeyboardButton(text="↩️ Назад в меню")]
        ],
        resize_keyboard=True
    )

# --- Обработчики сообщений ---
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    try:
        await message.answer("Привет! Я AI Kitchen Bot!", reply_markup=main_keyboard())
        logger.info(f"Новый пользователь: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")

@dp.message_handler()
async def echo_message(message: types.Message):
    try:
        await message.answer(f"Вы написали: {message.text}", reply_markup=main_keyboard())
        logger.info(f"Сообщение от {message.from_user.id}: {message.text}")
    except Exception as e:
        logger.error(f"Ошибка в echo_message: {e}")

# --- Запуск бота ---
if __name__ == "__main__":
    try:
        logger.info("Запуск бота...")
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.critical(f"Бот остановлен с ошибкой: {e}")
    finally:
        logger.info("Бот завершил работу")
