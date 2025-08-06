Вот улучшенная версия файла `README.md` с более чёткой структурой и актуальной информацией:

```markdown
# 🍳 AI Kitchen Bot *(Приватный репозиторий)*

> ⚠️ **КОНФИДЕНЦИАЛЬНО**  
> Этот код является интеллектуальной собственностью.  
> Любое копирование или использование без письменного разрешения запрещено.  
> © Семейкина П.А., 2025

---

## 🌟 Особенности бота
- Генерация рецептов с учётом диетических ограничений (халяль, постное, низкокалорийное и др.)
- Интеграция с Yandex GPT (ранее Groq)
- Умная проверка ингредиентов на соответствие диете
- Развёртывание на TimeWeb Cloud

## 🛠 Технические требования
| Компонент       | Минимальные требования |
|-----------------|------------------------|
| Python          | 3.11+                 |
| Память (RAM)    | 1 ГБ                  |
| Хранилище       | 20 ГБ SSD             |
| Сеть            | Стабильный интернет   |

## ⚙️ Настройка окружения

### 📋 Переменные окружения (`.env`)
```ini
TELEGRAM_BOT_TOKEN="ваш_токен"
YANDEX_API_KEY="ваш_api_key"
YANDEX_FOLDER_ID="идентификатор_каталога"
WEBHOOK_URL="https://ваш_домен/webhook"
DEBUG="False"  # True для разработки
```

### 📦 Установка зависимостей
```bash
pip install -r requirements.txt
```

## 🚀 Запуск бота

### Локальный запуск
```bash
python3 AI_Kitchen_bot.py
```

### Деплой на TimeWeb Cloud
```bash
# 1. Подключение к серверу
ssh root@your-server-ip

# 2. Установка зависимостей
sudo apt update && sudo apt install -y python3-venv

# 3. Клонирование репозитория
git clone https://github.com/ваш-логин/AI_Kitchen_bot.git
cd AI_Kitchen_bot

# 4. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 5. Установка Python-зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# 6. Запуск через screen
screen -S bot
python AI_Kitchen_bot.py
# Ctrl+A, затем D для детача
```

## ⚠️ Важные настройки
`AI_Kitchen_bot.py` содержит критически важные параметры:
```python
class BotConfig:
    YANDEX_MODEL = "yandexgpt-lite"  # Используемая модель
    REQUEST_DELAY = 1.5              # Задержка между запросами (сек)
    MAX_RETRIES = 3                  # Попытки при ошибках API
```

## 📊 Логирование
Система логирования сохраняет:
- Основные события: `logs/bot.log`
- Ошибки: `logs/errors.log`

Пример записи:
```
[2025-08-06 14:30:45] INFO: User 12345 запросил рецепт (кухня: 🇷🇺 Русская)
[2025-08-06 14:30:50] ERROR: Yandex API timeout, попытка 1/3
```

## 🔒 Меры безопасности
1. Все секретные данные хранятся только в `.env`
2. Git-репозиторий приватный
3. Регулярное обновление зависимостей:
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

## 📞 Контакты
По вопросам доступа и сотрудничества:
- 📧 Email: [psemeykina@gmail.com](mailto:psemeykina@gmail.com)
- ✉️ Telegram: [@Simlinaa](https://t.me/Simlinaa)

---

> **Важно**: Для работы с Yandex Cloud API требуется активный платежный аккаунт.
``` 
