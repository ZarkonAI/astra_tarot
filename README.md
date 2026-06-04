# Astra Taro v0.1

**Astra Taro** — первая рабочая заготовка Telegram-бота и Telegram Mini App для мистических развлекательных Таро-раскладов.

## Что есть в версии v0.1

- Telegram-бот на `aiogram 3`.
- Mini App на обычных `HTML/CSS/JS`.
- Backend на `FastAPI`.
- SQLite-база.
- 22 старших аркана.
- Расклады: Карта дня, Быстрый расклад, Сердечный расклад, Денежный путь, Глубокий расклад.
- Gemini как основной ИИ-провайдер.
- Заготовки под Groq, OpenRouter и Ollama.
- Мягкий фильтр опасных тем.
- Уведомления админу об ошибках ИИ.
- `.env.example` без реальных ключей.

## Важно про ключи

Никогда не загружайте `.env` в GitHub.

Файл `.env.example` должен содержать только заглушки, не реальные токены.

## Быстрый запуск локально

```bash
cd astra_taro_v0_1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m bot.main
```

Откройте `.env` и вставьте свои значения:

```env
BOT_TOKEN=...
ADMIN_ID=...
GEMINI_API_KEY=...
WEBAPP_URL=http://localhost:8000
DEV_ALLOW_UNVERIFIED_WEBAPP=true
```

Проверка backend:

```text
http://localhost:8000/api/health
```
