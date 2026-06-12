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

## React Mini App

```powershell
cd Z:\job\02_tarot_bot\astra-tarot-miniapp-react
npm install
npm run dev
npm run build
```

React-specific local variables should stay in `astra-tarot-miniapp-react\.env.local`.
Backend secrets must not be copied there.
