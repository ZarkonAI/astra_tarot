# GitHub Pages Frontend

The Telegram Mini App frontend lives in:

```text
Z:\job\02_tarot_bot\astra-tarot-miniapp-react
```

Local development:

```powershell
cd Z:\job\02_tarot_bot\astra-tarot-miniapp-react
npm install
npm run dev
```

Production build:

```powershell
npm run build
```

The public GitHub Pages URL should be placed in the bot root `.env`:

```text
MINIAPP_URL=https://zarkonai.github.io/astra_tarot/
PUBLIC_BASE_URL=https://zarkonai.github.io/astra_tarot/
```

Do not put `BOT_TOKEN` or `GEMINI_API_KEY` into frontend env files.
