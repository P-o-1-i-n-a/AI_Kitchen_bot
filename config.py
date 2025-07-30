__copyright__ = "Конфиденциально. © 2025 Семейкина П.А."

import os
from typing import List


class BotConfig:
    """Конфигурация для TimeWeb Cloud"""

    # Telegram
    TOKEN: str = os.getenv("TELEGRAM_TOKEN")

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama3-8b-8192"  # можно менять на другой при необходимости

    # Настройки
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    REQUEST_DELAY: int = 20  # задержка для бесплатного тарифа

    # Режим отладки
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        required = {
            "TELEGRAM_TOKEN": cls.TOKEN,
            "GROQ_API_KEY": cls.GROQ_API_KEY,
        }
        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} не задан в .env")


config = BotConfig()
config.validate()
