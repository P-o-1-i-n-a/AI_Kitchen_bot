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
    base_prompt = [
        "Ты профессиональный шеф-повар. Сгенерируй рецепт по параметрам:",
        f"Кухня: {user_data['cuisine']}",
        f"Диета: {user_data['diet_type']}",
        "",
        "Требования:",
        "- Учет диетических ограничений",
        "- Точный расчет КБЖУ на порцию",
        "- Четкая пошаговая инструкция"
    ]
    
    if user_data['search_method'] == "by_name":
        base_prompt.insert(1, f"Название блюда: {user_data['dish_name']}")
    else:
        base_prompt.insert(1, f"Ингредиенты: {user_data['ingredients']}")
    
    return "\n".join(base_prompt)


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
