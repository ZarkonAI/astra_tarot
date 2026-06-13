# Local Run

## Python bot

```powershell
cd Z:\job\02_tarot_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m compileall .
python tools\smoke_test.py
python run.py
```

Fill `BOT_TOKEN` in `Z:\job\02_tarot_bot\.env` before running the bot.
`GEMINI_API_KEY` is optional: without it the bot uses the local fallback interpretation.

The bot `.env` should contain the production Mini App URL:

```env
MINIAPP_URL=https://zarkonai.github.io/astra_tarot/
PUBLIC_BASE_URL=https://zarkonai.github.io/astra_tarot/
```

## Telegram checks

1. Run `python run.py`.
2. Open the bot in Telegram and send `/start`.
3. Check that the `🌌 Открыть Astra Tarot` button appears when `MINIAPP_URL` is
   `https://zarkonai.github.io/astra_tarot/`.
4. Click a spread button and confirm that the bot sends card photos, then the
   interpretation text.
5. Temporarily clear `MINIAPP_URL` locally if you need to verify that the bot
   still starts without creating a WebApp button.

## React Mini App

```powershell
cd Z:\job\02_tarot_bot\astra-tarot-miniapp-react
npm install
npm run dev
npm run build
```

React-specific local variables should stay in `astra-tarot-miniapp-react\.env.local`.
Backend secrets must not be copied there.
