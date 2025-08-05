__copyright__ = "Конфиденциально. © 2025 Семейкина П.А."

import os
from typing import List


class BotConfig:
    """Конфигурация для TimeWeb Cloud"""

    # Telegram
    TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")

    # Yandex GPT
    YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_MODEL: str = os.getenv("YANDEX_MODEL", "yandexgpt-lite")  # можно указать "yandexgpt" или "yandexgpt-lite"

    # Админы
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    REQUEST_DELAY: int = 20

    # Режим отладки
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        required = {
            "TELEGRAM_BOT_TOKEN": cls.TOKEN,
            "YANDEX_API_KEY": cls.YANDEX_API_KEY,
            "YANDEX_FOLDER_ID": cls.YANDEX_FOLDER_ID,
        }
        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} не задан в .env")


config = BotConfig()
config.validate()
