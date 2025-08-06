from bot.states import DIET_RULES


def check_diet_conflicts(ingredients: str, diet_type: str, allergies: str = "") -> tuple[list, str]:
    """
    Проверяет ингредиенты на соответствие диете
    :param ingredients: Строка с ингредиентами
    :param diet_type: Выбранный тип диеты
    :param allergies: Строка с аллергенами (если есть)
    :return: (список конфликтов, строка с заменами)
    """
    if diet_type not in DIET_RULES:
        return [], ""

    ingredients_list = [i.strip().lower() for i in ingredients.split(',')]
    forbidden = DIET_RULES[diet_type].get("forbidden", [])

    if diet_type == "⚠️ Аллергии":
        forbidden.extend(a.strip().lower() for a in allergies.split(',') if a.strip())

    conflicts = []
    for ingredient in ingredients_list:
        for forbidden_item in forbidden:
            if forbidden_item and forbidden_item in ingredient:
                conflicts.append(ingredient)
                break

    replacement_note = ""
    if conflicts and DIET_RULES[diet_type].get("replacements"):
        replacement_note = "\n\n🔁 Возможные замены:\n"
        for original, replacement in DIET_RULES[diet_type]["replacements"].items():
            if any(original in conflict for conflict in conflicts):
                replacement_note += f"- {original} → {replacement}\n"

    return conflicts, replacement_note