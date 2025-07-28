# 🍳 AI Kitchen Bot *(Приватный репозиторий)*

> ⚠️ **КОНФИДЕНЦИАЛЬНО**  
> Этот код является интеллектуальной собственностью.  
> Любое копирование или использование без письменного разрешения запрещено.  
> © Семейкина П.А., 2025

---

## 🛠 Технические требования
- **Python 3.11.9** (указано в runtime.txt)
- **Память**: минимум 1 ГБ RAM
- **Хранилище**: 20+ ГБ SSD

## 📦 Зависимости
В .env:

TELEGRAM_TOKEN="ваш_bot_token"

OPENAI_API_KEY="ваш_openai_key"

DEBUG="False"

Запуск:

python AI_Kitchen_bot.py

🌐 Деплой на TimeWeb Cloud
Минимум: 1 CPU / 1 ГБ RAM / 20 ГБ SSD


ssh root@your-server-ip

sudo apt update && sudo apt install python3-venv redis

git clone https://your-repo.git && cd AI_Kitchen_bot

python3 -m venv venv && source venv/bin/activate

pip install --upgrade pip && pip install -r requirements.txt

sudo systemctl enable redis && sudo systemctl start redis

screen -S bot

python AI_Kitchen_bot.py

⚙️ Конфигурация


class BotConfig:

    OPENAI_MODEL = "gpt-3.5-turbo"

    REQUEST_DELAY = 20

    MAX_CONCURRENT_REQUESTS = 1

📊 Логирование

logs/bot.log — события

logs/errors.log — ошибки


[2025-01-15 12:00:00] INFO: User 12345 requested recipe

[2025-01-15 12:00:05] ERROR: OpenAI API timeout

🔒 Безопасность

Чувствительные данные — в .env

Ограниченный доступ

Регулярные обновления зависимостей

📞 Контакты

Email: psemeykina@gmail.com

Telegram: @Simlinaa

```bash
pip install -r requirements.txt
