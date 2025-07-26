from flask import Flask, request
import telebot
from telebot import types
import requests
from io import BytesIO
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
from config import TOKEN, GROQ_API_KEY, HF_API_KEY, WEBHOOK_URL

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MODEL_NAME = "llama3-70b-8192"

app = Flask(__name__)

# --- Состояния пользователей ---
user_states = {}

# --- Генерация изображений ---
def generate_food_image(prompt):
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": f"реалистичное фото блюда: {prompt}, профессиональная фотография, высокое качество, 4K"}
        )
        if response.status_code == 403:
            raise Exception("Доступ запрещён. Проверьте API-ключ")
        elif response.status_code == 429:
            raise Exception("Лимит запросов исчерпан")
        elif response.status_code != 200:
            raise Exception(f"Ошибка API: {response.text}")
        return BytesIO(response.content)
    except Exception as e:
        raise Exception(f"Ошибка генерации: {str(e)}")

# --- Клавиатуры ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🍳 Создать рецепт"))
    return markup

def meal_time_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🌅 Завтрак"),
        types.KeyboardButton("🌇 Обед"),
        types.KeyboardButton("🌃 Ужин"),
        types.KeyboardButton("☕ Перекус")
    ]
    markup.add(*buttons)
    return markup

def cuisine_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        types.KeyboardButton("🇷🇺 Русская"),
        types.KeyboardButton("🇮🇹 Итальянская"),
        types.KeyboardButton("🇯🇵 Японская"),
        types.KeyboardButton("🇬🇪 Кавказская"),
        types.KeyboardButton("🇺🇸 Американская"),
        types.KeyboardButton("🇫🇷 Французская"),
        types.KeyboardButton("🇹🇷 Турецкая"),
        types.KeyboardButton("🇨🇳 Китайская"),
        types.KeyboardButton("🇲🇽 Мексиканская"),
        types.KeyboardButton("🇮🇳 Индийская"),
        types.KeyboardButton("🌍 Другая")
    ]
    markup.add(*buttons)
    return markup

def diet_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🥩 Обычная"),
        types.KeyboardButton("🌱 Вегетарианская"),
        types.KeyboardButton("🐄 Без молочных"),
        types.KeyboardButton("🌾 Без глютена"),
        types.KeyboardButton("🍯 Кето"),
        types.KeyboardButton("☦️ Постная"),
        types.KeyboardButton("⚡ Нет ограничений")
    ]
    markup.add(*buttons)
    return markup

def image_request_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🖼 Показать изображение", callback_data="generate_image"))
    return markup

# --- Обработчики сообщений ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👨‍🍳 Привет! Я - кулинарный бот с генерацией изображений.\n"
        "Нажмите кнопку ниже, чтобы создать рецепт ↓",
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "🍳 Создать рецепт")
def ask_meal_time(message):
    user_states[message.chat.id] = {"step": "waiting_meal_time"}
    bot.send_message(
        message.chat.id,
        "🕒 Для какого приёма пищи нужен рецепт?",
        reply_markup=meal_time_keyboard()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_meal_time")
def ask_cuisine(message):
    if message.text not in ["🌅 Завтрак", "🌇 Обед", "🌃 Ужин", "☕ Перекус"]:
        bot.send_message(message.chat.id, "Пожалуйста, выберите вариант из кнопок ↓", reply_markup=meal_time_keyboard())
        return

    user_states[message.chat.id] = {
        "step": "waiting_cuisine",
        "meal_time": message.text
    }
    bot.send_message(
        message.chat.id,
        "🌍 Выберите кухню (топ-10 для России):",
        reply_markup=cuisine_keyboard()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_cuisine")
def ask_diet(message):
    valid_cuisines = ["🇷🇺 Русская", "🇮🇹 Итальянская", "🇯🇵 Японская", "🇬🇪 Кавказская",
                      "🇺🇸 Американская", "🇫🇷 Французская", "🇹🇷 Турецкая", "🇨🇳 Китайская",
                      "🇲🇽 Мексиканская", "🇮🇳 Индийская", "🌍 Другая"]

    if message.text not in valid_cuisines:
        bot.send_message(message.chat.id, "Пожалуйста, выберите вариант из кнопок ↓", reply_markup=cuisine_keyboard())
        return

    user_states[message.chat.id]["cuisine"] = message.text
    user_states[message.chat.id]["step"] = "waiting_diet"
    bot.send_message(
        message.chat.id,
        "🥗 Есть ли диетические ограничения?\n"
        "☦️ Постная - вариант для православных постов",
        reply_markup=diet_keyboard()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_diet")
def ask_ingredients(message):
    valid_diets = ["🥩 Обычная", "🌱 Вегетарианская", "🐄 Без молочных",
                   "🌾 Без глютена", "🍯 Кето", "☦️ Постная", "⚡ Нет ограничений"]

    if message.text not in valid_diets:
        bot.send_message(message.chat.id, "Пожалуйста, выберите вариант из кнопок ↓", reply_markup=diet_keyboard())
        return

    user_states[message.chat.id]["diet"] = message.text
    user_states[message.chat.id]["step"] = "waiting_ingredients"
    bot.send_message(
        message.chat.id,
        "📝 Введите ингредиенты через запятую:\n"
        "Пример: 2 яйца, 100г муки, 1 ст.л. масла\n"
        "Или напишите 'что есть в холодильнике?' для генерации по списку",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_ingredients")
def process_ingredients(message):
    user_states[message.chat.id]["ingredients"] = message.text
    generate_recipe(message.chat.id)

def ensure_russian(text):
    """Удаляет английские фразы из текста"""
    return re.sub(r'[a-zA-Z]', '', text).strip()

def generate_recipe(chat_id):
    try:
        data = user_states[chat_id]
        bot.send_chat_action(chat_id, 'typing')

        if data['ingredients'].lower() == 'что есть в холодильнике?':
            prompt = f"""Придумай рецепт для {data['meal_time']} в стиле {data['cuisine']} кухни, 
            соответствующий {data['diet']} диете. Используй распространённые ингредиенты, которые 
            обычно есть дома у россиян. Говори только на русском языке!"""
        else:
            prompt = f"""Составь рецепт для {data['meal_time']} в стиле {data['cuisine']} кухни, 
            соответствующий {data['diet']} диете, используя: {data['ingredients']}. 
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

        response = client.chat.completions.create(
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
        user_states[chat_id]["recipe_title"] = recipe.split('\n')[0].replace('🍽', '').strip()
        user_states[chat_id]["full_recipe"] = recipe

        bot.send_message(
            chat_id,
            recipe,
            reply_markup=image_request_keyboard(),
            parse_mode='Markdown'
        )

    except Exception as e:
        bot.send_message(
            chat_id,
            f"⚠️ Ошибка генерации рецепта: {str(e)}",
            reply_markup=main_keyboard()
        )
    finally:
        user_states[chat_id]["step"] = "recipe_ready"

@bot.callback_query_handler(func=lambda call: call.data == "generate_image")
def handle_image_request(call):
    try:
        chat_id = call.message.chat.id
        recipe_title = user_states.get(chat_id, {}).get("recipe_title")
        if not recipe_title:
            raise Exception("Название рецепта не найдено")

        bot.send_message(chat_id, "🖌 Генерирую аппетитное изображение... Это займет 10-20 секунд")
        image_bytes = generate_food_image(f"{recipe_title}, {user_states[chat_id]['cuisine']} кухня")

        bot.send_photo(
            chat_id,
            image_bytes,
            caption=f"🍽 {recipe_title}\n🌍 {user_states[chat_id]['cuisine']} кухня",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        bot.send_message(
            chat_id,
            f"⚠️ Не удалось сгенерировать изображение: {str(e)}",
            reply_markup=main_keyboard()
        )

@bot.message_handler(func=lambda m: True)
def handle_other(message):
    bot.send_message(
        message.chat.id,
        "Используйте кнопку «🍳 Создать рецепт» или /start",
        reply_markup=main_keyboard()
    )

# --- Flask Webhook ---
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
