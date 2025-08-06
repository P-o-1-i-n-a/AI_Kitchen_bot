from aiogram import types, F
from aiogram.fsm.context import FSMContext
from bot.keyboards.recipe import (
    meal_time_keyboard,
    cuisine_keyboard,
    diet_keyboard
)
from bot.states import user_states, DIET_RULES

async def ask_search_method(message: types.Message):
    """Запрос способа поиска рецепта"""
    user_states[message.chat.id] = {"step": "waiting_search_method"}
    await message.answer(
        "Выберите способ поиска рецепта:",
        reply_markup=search_method_keyboard()
    )

async def handle_by_name(message: types.Message):
    """Обработка выбора 'По названию'"""
    user_states[message.chat.id].update({
        "search_method": "by_name",
        "step": "waiting_dish_name"
    })
    await message.answer("Введите название блюда:", reply_markup=types.ReplyKeyboardRemove())

async def handle_by_ingredients(message: types.Message):
    """Обработка выбора 'По ингредиентам'"""
    user_states[message.chat.id].update({
        "search_method": "by_ingredients",
        "step": "waiting_ingredients"
    })
    await message.answer(
        "📝 Введите ингредиенты через запятую:\nПример: яйца, мука, молоко",
        reply_markup=types.ReplyKeyboardRemove()
    )

def register_handlers(dp):
    dp.message.register(ask_search_method, F.text == "🍳 Создать рецепт")
    dp.message.register(handle_by_name, F.text == "🔍 По названию блюда")
    dp.message.register(handle_by_ingredients, F.text == "🥕 По ингредиентам")
    
async def ask_meal_time(message: types.Message):
    """Запрашивает время приёма пищи"""
    user_states[message.chat.id] = {"step": "waiting_meal_time"}
    await message.answer(
        "🕒 Для какого приёма пищи нужен рецепт?",
        reply_markup=meal_time_keyboard()
    )


async def ask_cuisine(message: types.Message):
    """Запрашивает кухню"""
    if message.text not in ["🌅 Завтрак", "🌇 Обед", "🌃 Ужин", "☕ Перекус"]:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓")
        return

    user_states[message.chat.id] = {
        "step": "waiting_cuisine",
        "meal_time": message.text
    }
    await message.answer("🌍 Выберите кухню:", reply_markup=cuisine_keyboard())


async def ask_diet(message: types.Message):
    """Запрашивает диетические ограничения"""
    if message.text not in [btn.text for row in cuisine_keyboard().keyboard for btn in row]:
        await message.answer("Пожалуйста, выберите вариант из кнопок ↓")
        return

    user_states[message.chat.id].update({
        "cuisine": message.text,
        "step": "waiting_diet"
    })
    await message.answer("🥗 Есть ли диетические ограничения?", reply_markup=diet_keyboard())


def register_handlers(dp):
    """Регистрирует обработчики потока создания рецепта"""
    dp.message.register(ask_meal_time, F.text == "🍳 Создать рецепт")
    dp.message.register(ask_cuisine, lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_meal_time")

    dp.message.register(ask_diet, lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_cuisine")
