__copyright__ = "Конфиденциально. © 2025 Семейкина П.А."

import os
from typing import List

class BotConfig:
    """Конфигурация для Beget VPS (переменные окружения задаются в панели Beget)"""

    # --- Telegram ---
    TOKEN: str = os.getenv("TELEGRAM_TOKEN")  # Берётся из переменных окружения сервера
    
    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama3-70b-8192"
    
    # --- Настройки ---
    ADMIN_IDS: List[int] = [
        int(id) for id in os.getenv("ADMIN_IDS", "1081610697").split(",") 
        if id.strip()
    ]
    
    # --- Режимы работы ---
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        if not cls.TOKEN:
            raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения Beget")
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY не задан в переменных окружения Beget")

# Проверка при импорте
config = BotConfig()
config.validate()
