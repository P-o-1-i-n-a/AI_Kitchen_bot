from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os

# Берем токен из переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Клавиатки ---
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

# --- Обработчики ---
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! Я AI Kitchen Bot!", reply_markup=main_keyboard())

# Пример простого эхо для остальных сообщений
@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(f"Вы написали: {message.text}", reply_markup=main_keyboard())

# --- Запуск бота ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
