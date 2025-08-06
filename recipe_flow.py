from aiogram import types, F
from aiogram.fsm.context import FSMContext
from bot.keyboards.recipe import (
    meal_time_keyboard,
    cuisine_keyboard,
    diet_keyboard
)
from bot.states import user_states, DIET_RULES


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