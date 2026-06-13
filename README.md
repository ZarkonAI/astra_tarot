# Astra Tarot Bot

Python Telegram bot and backend for the Astra Tarot Mini App.

Frontend GitHub Pages URL:

```text
https://zarkonai.github.io/astra_tarot/
```

Use the same URL in BotFather as Main App URL and Menu Button URL.

Python `.env`:

```env
MINIAPP_URL=https://zarkonai.github.io/astra_tarot/
PUBLIC_BASE_URL=https://zarkonai.github.io/astra_tarot/
```

## Run Bot

```powershell
cd Z:\job\02_tarot_bot
.\.venv\Scripts\Activate.ps1
python run.py
```

`BOT_TOKEN` is required. `GEMINI_API_KEY` is optional; without it the bot uses a
safe local fallback reading.

## Check /start

1. Start the bot with `python run.py`.
2. Open the bot in Telegram.
3. Send `/start`.
4. Confirm the menu contains `🌌 Открыть Astra Tarot` and all spread buttons.

If `MINIAPP_URL` is empty or invalid, the bot must still show spread buttons
without creating a WebApp button.

## Check Card Images

1. Send `/start`.
2. Choose `🃏 Карта дня` or another spread.
3. The bot should send the opened card list, card photo messages from GitHub
   Pages, and then the full interpretation.

Card images are loaded from:

```text
https://zarkonai.github.io/astra_tarot/assets/cards/
```

Missing major arcana images use:

```text
https://zarkonai.github.io/astra_tarot/assets/background/card_back_ornate.webp
```

## Checks

```powershell
python -m compileall .
python tools\smoke_test.py
```
