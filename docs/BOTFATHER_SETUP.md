# BotFather Setup

Mini App URL must be a public HTTPS URL. Local URLs like `http://localhost:5173`
or `http://127.0.0.1:5173` are not valid Telegram Web App URLs.

GitHub Pages URL:

```text
https://zarkonai.github.io/astra-tarot-miniapp/
```

BotFather path:

```text
/mybots
-> Astra Tarot
-> Bot Settings
-> Configure Mini App
-> AstraTaroOracle
-> Edit Web App URL
```

Use the GitHub Pages URL above as the Web App URL. Put the same URL into the
bot `.env` as `MINIAPP_URL`.
