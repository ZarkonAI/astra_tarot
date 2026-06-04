# Деплой на Bothost

## Что подготовить

1. Репозиторий GitHub.
2. Файл `requirements.txt`.
3. Главный файл запуска: `bot/main.py` или `run.py`.
4. Переменные окружения в панели Bothost.
5. HTTPS-домен для Mini App.

## Переменные окружения

```env
BOT_TOKEN=...
ADMIN_ID=...
AI_PROVIDER=gemini
GEMINI_API_KEY=...
DATABASE_PATH=database/astra_taro.db
WEBAPP_URL=https://ваш-домен
DEV_ALLOW_UNVERIFIED_WEBAPP=false
HOST=0.0.0.0
PORT=8000
```

## Важное

- `.env` не должен попадать в GitHub.
- `.env.example` должен содержать только заглушки.
- Если Mini App не открывается в Telegram, проверьте HTTPS.
- Если бот падает, смотрите логи работы и логи сборки.
