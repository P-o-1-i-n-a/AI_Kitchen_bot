from flask import Flask, request
import telebot
from telebot import types
from groq import Groq
import os
import re

# --- Импорт клиента Groq с защитой ---
try:
    from groq import Groq
except ImportError as e:
    raise ImportError(
        "Не удалось импортировать класс Groq. "
        "Проверь, что библиотека groq установлена (pip install groq)."
    ) from e

# --- Конфигурация ---
from config import TOKEN, GROQ_API_KEY  # Убрал WEBHOOK_URL, так как на Beget будем использовать polling

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MODEL_NAME = "llama3-70b-8192"
CHANNEL_LINK = "https://t.me/ai_kitchen_channel"

app = Flask(__name__)

# --- Состояния пользователей ---
user_states = {}


# --- Клавиатуры (остаются без изменений) ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🍳 Создать рецепт"))
    markup.add(types.KeyboardButton("📜 Публичная оферта"))
    markup.add(types.KeyboardButton("📢 Наш кулинарный канал"))
    return markup


# ... (остальные функции клавиатур остаются без изменений) ...

# --- Обработчики сообщений (остаются без изменений) ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):


# ... (код без изменений) ...

@bot.message_handler(func=lambda m: m.text == "📜 Публичная оферта")
def show_offer(message):


# ... (код без изменений) ...

# ... (все остальные обработчики остаются без изменений) ...

# --- Webhook-часть закомментирована для Beget ---
"""
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Unsupported Media Type", 415

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    bot.remove_webhook()
    success = bot.set_webhook(url=WEBHOOK_URL)
    return ("Webhook установлен" if success else "Ошибка установки webhook"), 200
"""

if __name__ == "__main__":
    # Упрощенный запуск для Beget VPS
    print("Бот запущен в режиме polling...")
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=1)

    # Альтернативный вариант с Flask (если нужно):
    # app.run(host="0.0.0.0", port=5000)
