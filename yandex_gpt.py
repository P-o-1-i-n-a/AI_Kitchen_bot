import json
import httpx
import logging
from bot.states import DIET_RULES
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

logger = logging.getLogger(__name__)


async def generate_recipe(user_data: dict) -> str:
    """
    Генерирует рецепт через Yandex GPT API
    :param user_data: Данные пользователя из user_states
    :return: Строка с рецептом
    """
    try:
        prompt = build_prompt(user_data)
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.5,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты профессиональный шеф-повар. Генерируй рецепты по запросу."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            result = response.json()
            return clean_recipe_text(result['result']['alternatives'][0]['message']['text'])

    except Exception as e:
        logger.error(f"Yandex GPT error: {str(e)}")
        return "⚠️ Ошибка генерации рецепта. Пожалуйста, попробуйте позже."


def build_prompt(user_data: dict) -> str:
    """Формирует промт для GPT на основе выбора пользователя"""
    diet_info = DIET_RULES.get(user_data['diet_type'], {})
    prompt = [
        "Сгенерируй рецепт по следующим параметрам:",
        f"Тип блюда: {user_data['meal_time']}",
        f"Кухня: {user_data['cuisine']}",
        f"Диета: {user_data['diet_type']}",
        f"Ингредиенты: {user_data['ingredients']}",
        "",
        "Требования:",
        "- Строгий формат: Название, Кухня, Диета, Время приготовления, Ингредиенты, Пошаговый рецепт, КБЖУ",
        "- Учитывай диетические ограничения",
        "- Предлагай замены для несоответствующих ингредиентов",
        "- Никогда не предлагай поискать в интернете"
    ]

    if user_data['diet_type'] == "⚠️ Аллергии":
        prompt.append(f"Исключить аллергены: {user_data.get('allergies', '')}")

    return "\n".join(prompt)


def clean_recipe_text(text: str) -> str:
    """Очищает текст рецепта от ненужных фраз"""
    unwanted_phrases = [
        "Вы можете найти рецепты в интернете",
        "Я могу поискать рецепты",
        "Посмотрите в поиске"
    ]
    for phrase in unwanted_phrases:
        text = text.replace(phrase, "")
    return text.strip()