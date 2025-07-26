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
from config import TOKEN, GROQ_API_KEY, WEBHOOK_URL

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MODEL_NAME = "llama3-70b-8192"

app = Flask(__name__)

# --- Состояния пользователей ---
user_states = {}

# --- Клавиатуры ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🍳 Создать рецепт"))
    markup.add(types.KeyboardButton("📜 Публичная оферта"))
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
        types.KeyboardButton("🇮🇳 Индийская")
    ]
    markup.add(*buttons)
    return markup

def diet_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🚫 Нет ограничений"),
        types.KeyboardButton("⚠️ Аллергии"),
        types.KeyboardButton("⚖️ Низкокалорийные"),
        types.KeyboardButton("💪 Высокобелковые"),
        types.KeyboardButton("☪️ Халяль"),
        types.KeyboardButton("☦️ Постная")
    ]
    markup.add(*buttons)
    return markup

# --- Обработчики сообщений ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👨‍🍳 Привет! Я - кулинарный бот с генерацией рецептов.\n"
        "⚠️ Рецепты создаются искусственным интеллектом (AI) и могут содержать неточности.\n\n"
        "Нажмите кнопку ниже, чтобы создать рецепт ↓",
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "📜 Публичная оферта")
def show_offer(message):
    bot.send_message(
        message.chat.id,
        "📄 Публичная оферта:\n\n"
        "1. Все рецепты генерируются искусственным интеллектом и не являются профессиональной рекомендацией.\n"
        "2. Вы несете ответственность за проверку ингредиентов на аллергены и свежесть.\n"
        "3. Запрещено использовать бота для создания вредоносного контента.\n\n"
        "Полная версия: https://example.com/offer",
        disable_web_page_preview=True
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
        "🌍 Выберите кухню:",
        reply_markup=cuisine_keyboard()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_cuisine")
def ask_diet(message):
    valid_cuisines = ["🇷🇺 Русская", "🇮🇹 Итальянская", "🇯🇵 Японская", "🇬🇪 Кавказская",
                     "🇺🇸 Американская", "🇫🇷 Французская", "🇹🇷 Турецкая", "🇨🇳 Китайская",
                     "🇲🇽 Мексиканская", "🇮🇳 Индийская"]

    if message.text not in valid_cuisines:
        bot.send_message(message.chat.id, "Пожалуйста, выберите вариант из кнопок ↓", reply_markup=cuisine_keyboard())
        return

    user_states[message.chat.id]["cuisine"] = message.text
    user_states[message.chat.id]["step"] = "waiting_diet"
    bot.send_message(
        message.chat.id,
        "🥗 Есть ли диетические ограничения?",
        reply_markup=diet_keyboard()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_diet")
def process_diet_choice(message):
    valid_diets = ["🚫 Нет ограничений", "⚠️ Аллергии", "⚖️ Низкокалорийные", 
                  "💪 Высокобелковые", "☪️ Халяль", "☦️ Постная"]

    if message.text not in valid_diets:
        bot.send_message(message.chat.id, "Пожалуйста, выберите вариант из кнопок ↓", reply_markup=diet_keyboard())
        return

    user_states[message.chat.id]["diet_type"] = message.text
    
    if message.text == "⚠️ Аллергии":
        user_states[message.chat.id]["step"] = "waiting_allergies"
        bot.send_message(
            message.chat.id,
            "📝 Укажите продукты, которые нужно исключить (через запятую):\n"
            "Пример: орехи, молоко, морепродукты",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        user_states[message.chat.id]["step"] = "waiting_ingredients"
        ask_for_ingredients(message.chat.id)

def ask_for_ingredients(chat_id):
    bot.send_message(
        chat_id,
        "📝 Введите ингредиенты через запятую:\n"
        "Пример: 2 яйца, 100г муки, 1 ст.л. масла\n"
        "Или напишите 'что есть в холодильнике?' для генерации по списку",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "waiting_allergies")
def process_allergies(message):
    user_states[message.chat.id]["allergies"] = message.text
    user_states[message.chat.id]["step"] = "waiting_ingredients"
    ask_for_ingredients(message.chat.id)

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
        bot.send_message(
            chat_id,
            recipe,
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )

    except Exception as e:
        bot.send_message(
            chat_id,
            f"⚠️ Ошибка генерации рецепта: {str(e)}",
            reply_markup=main_keyboard()
        )
    finally:
        user_states[chat_id]["step"] = "done"

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
