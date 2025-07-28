__copyright__ = "Конфиденциально. © 2025 Семейкина П.А."

import os
from typing import List


class BotConfig:
    """Конфигурация для TimeWeb Cloud"""

    # Telegram
    TOKEN: str = os.getenv("TELEGRAM_TOKEN")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # Добавлено

    # Настройки
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    REQUEST_DELAY: int = 20  # Для бесплатного тарифа OpenAI

    # Режим отладки
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        required = {
            "TELEGRAM_TOKEN": cls.TOKEN,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY
        }
        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} не задан в .env")


config = BotConfig()
config.validate()
