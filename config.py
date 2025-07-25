__copyright__ = "Конфиденциально. © 2025 Семейкина П.А."

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# --- Telegram ---
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Groq ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"

# --- Hugging Face ---
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# --- Webhook ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Прочее ---
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
