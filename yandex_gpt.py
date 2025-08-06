import json
import httpx
import logging
from bot.states import DIET_RULES
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

logger = logging.getLogger(__name__)

EXAMPLE_RECIPE = """🍲 Куриный суп с киноа (Халяль)

Кухня: Ближневосточная
Диета: ☪️ Халяль (без свинины и алкоголя)
Время приготовления: 40 мин
Порций: 4

📋 Ингредиенты:
- Куриное филе (халяль) - 500 г
- Киноа - 150 г
- Морковь - 2 шт (200 г)
- Сельдерей - 2 стебля (100 г)
- Лук репчатый - 1 шт (100 г)
- Оливковое масло - 2 ст.л.
- Куркума - 1 ч.л.
- Вода - 1.5 л

🔪 Приготовление:
1. Нарежьте курицу кубиками, овощи соломкой.
2. Обжарьте лук и морковь на оливковом масле 5 мин.
3. Добавьте курицу, обжаривайте 7 мин.
4. Залейте водой, добавьте киноа и специи.
5. Варите на медленном огне 25 мин.

📊 КБЖУ на порцию:
- Калории: 320 ккал
- Белки: 28 г
- Жиры: 10 г
- Углеводы: 30 г

💡 Советы:
- Подавайте с зеленью и лимоном
- Хорошо сочетается с лепешками
- Можно заменить киноа на булгур"""

async def generate_recipe(user_data: dict) -> str:
    """
    Генерирует рецепт с учетом всех ограничений
    """
    try:
        prompt = build_prompt(user_data)
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-pro/latest",  # Используем pro-версию
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,  # Меньше креативности
                "maxTokens": 3000,
                "top_p": 0.7
            },
            "messages": [
                {
                    "role": "system",
                    "text": (
                        "Ты шеф-повар в элитном ресторане. Строго соблюдай правила:\n"
                        "1. Никогда не предлагай поискать в интернете\n"
                        "2. Учитывай все диетические ограничения\n"
                        "3. Формат вывода должен быть идентичен примеру\n"
                        "4. Запрещенные продукты должны быть заменены\n"
                        "5. Обязательно укажи точные количества ингредиентов"
                    )
                },
                {
                    "role": "user",
                    "text": prompt
                },
                {
                    "role": "assistant",
                    "text": EXAMPLE_RECIPE
                }
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            result = response.json()
            return validate_recipe(result['result']['alternatives'][0]['message']['text'], user_data)

    except Exception as e:
        logger.error(f"Yandex GPT error: {str(e)}")
        return "⚠️ Ошибка генерации. Пожалуйста, попробуйте изменить параметры."

def build_prompt(user_data: dict) -> str:
    """Строит строгий промпт с учетом всех ограничений"""
    diet_rules = DIET_RULES.get(user_data['diet_type'], {})
    
    prompt = [
        "Сгенерируй рецепт по следующим параметрам:",
        f"Тип блюда: {user_data.get('meal_time', 'Обед')}",
        f"Кухня: {user_data['cuisine']}",
        f"Диета: {user_data['diet_type']} ({diet_rules.get('description', '')})",
        "",
        "Диетические ограничения:",
        f"Запрещенные продукты: {', '.join(diet_rules.get('forbidden', [])) or 'нет'}",
        f"Рекомендуемые замены: {json.dumps(diet_rules.get('replacements', {}), ensure_ascii=False}",
        "",
        "Технические требования:",
        "- Формат должен быть идентичен примеру",
        "- Указать точные количества в граммах/мл",
        "- Рассчитать КБЖУ для 1 порции",
        "- Предложить 2-3 совета по приготовлению",
        "- Если блюдо невозможно - честно сообщить об этом"
    ]

    if user_data['search_method'] == "by_name":
        prompt.insert(1, f"Название блюда: {user_data['dish_name']}")
    else:
        prompt.insert(1, f"Основные ингредиенты: {user_data['ingredients']}")
        prompt.append("- Адаптировать рецепт под указанные ингредиенты")

    if user_data.get('allergies'):
        prompt.append(f"Дополнительные аллергены: {user_data['allergies']}")

    return "\n".join(prompt)

def validate_recipe(text: str, user_data: dict) -> str:
    """Проверяет и корректирует рецепт"""
    # Удаляем ссылки и предложения поискать
    forbidden_phrases = [
        "поищите в интернете", "можно найти", "я могу поискать",
        "вот что нашлось", "рекомендую посмотреть"
    ]
    for phrase in forbidden_phrases:
        text = text.lower().replace(phrase, "")
    
    # Проверка на запрещенные продукты
    diet_rules = DIET_RULES.get(user_data['diet_type'], {})
    for forbidden in diet_rules.get('forbidden', []):
        if forbidden.lower() in text.lower():
            text = f"⚠️ Внимание: рецепт содержит {forbidden}, который исключен в вашей диете.\n\n" + text
    
    # Проверка структуры
    required_sections = ["📋 Ингредиенты", "🔪 Приготовление", "📊 КБЖУ"]
    if not all(section in text for section in required_sections):
        text = "🍽 " + text  # Добавляем эмодзи если нет
    
    return text.strip()

def clean_recipe_text(text: str) -> str:
    """Дополнительная очистка текста"""
    return text.replace("```", "").replace("**", "").strip()
