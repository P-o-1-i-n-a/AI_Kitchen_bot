from aiogram import types
from bot.states import user_states
from bot.services.diet_checker import check_diet_conflicts
from bot.keyboards.main import main_keyboard


async def process_diet_choice(message: types.Message):
    """Обрабатывает выбор диеты"""
    diet_type = message.text
    user_states[message.chat.id]["diet_type"] = diet_type

    if diet_type == "⚠️ Аллергии":
        user_states[message.chat.id]["step"] = "waiting_allergies"
        await message.answer(
            "📝 Укажите продукты, которые нужно исключить (через запятую):",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        user_states[message.chat.id]["step"] = "waiting_ingredients"
        await message.answer(
            "📝 Введите ингредиенты через запятую:\nПример: 2 яйца, 100г муки, 1 ст.л. масла",
            reply_markup=types.ReplyKeyboardRemove()
        )


async def process_allergies(message: types.Message):
    """Обрабатывает ввод аллергенов"""
    user_states[message.chat.id]["allergies"] = message.text
    user_states[message.chat.id]["step"] = "waiting_ingredients"
    await message.answer(
        "📝 Теперь введите ингредиенты через запятую:",
        reply_markup=types.ReplyKeyboardRemove()
    )


async def process_ingredients(message: types.Message):
    """Обрабатывает ввод ингредиентов"""
    user_data = user_states[message.chat.id]
    user_data["ingredients"] = message.text

    conflicts, replacements = check_diet_conflicts(
        message.text,
        user_data["diet_type"],
        user_data.get("allergies", "")
    )

    if conflicts:
        warning = "⚠️ Конфликты с диетой:\n" + "\n".join(f"- {c}" for c in conflicts)
        if replacements:
            warning += "\n\n" + replacements
        await message.answer(warning)

    await message.answer("🧑‍🍳 Генерирую рецепт...", reply_markup=main_keyboard())
    # Здесь будет вызов генерации рецепта


def register_handlers(dp):
    """Регистрирует обработчики кнопок"""
    dp.message.register(process_diet_choice,
                        lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_diet")
    dp.message.register(process_allergies,
                        lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_allergies")
    dp.message.register(process_ingredients,
                        lambda msg: user_states.get(msg.chat.id, {}).get("step") == "waiting_ingredients")