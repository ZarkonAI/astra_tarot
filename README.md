# Astra Tarot Mini App

React/Vite/TypeScript frontend for the Astra Tarot Telegram Mini App. It is built as a mobile-first in-app experience with welcome, home, spread selection, ritual loading, and result screens.

## Run Locally

```bash
npm install
npm run dev
```

Open the Vite URL in a browser. Outside Telegram the app shows a small `Browser preview` badge and works in mock mode.

## Build

```bash
npm run typecheck
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Environment

Create `.env.local` only for public frontend settings:

```env
VITE_APP_MODE=mock
VITE_API_BASE_URL=
VITE_BASE_PATH=/
```

For GitHub Pages, set:

```env
VITE_BASE_PATH=/astra-tarot-miniapp/
```

Do not put `BOT_TOKEN`, `GEMINI_API_KEY`, or any private backend secrets in this frontend project.

## Telegram

The Telegram wrapper lives in `src/services/telegram.ts`. It safely reads `window.Telegram.WebApp`, calls `ready()`, expands the Mini App, sets colors, reads `initData`, and exposes haptic feedback.

When the bot is ready, set the Mini App URL in BotFather to the deployed HTTPS URL, for example:

```text
https://username.github.io/astra-tarot-miniapp/
```

## API Mode

If `VITE_API_BASE_URL` is empty or `VITE_APP_MODE=mock`, the app uses `src/services/mockApi.ts`.

When `VITE_API_BASE_URL` is set and `VITE_APP_MODE` is not `mock`, the app sends:

```http
POST ${VITE_API_BASE_URL}/api/readings/create
```

Request body:

```json
{
  "spread": "love",
  "question": "текст вопроса",
  "initData": "telegram init data"
}
```

The backend should validate Telegram `initData`, call Gemini server-side, and return a `ReadingResult` JSON object.

## Assets

Expected optional files:

- `public/assets/guide/guide_main.webp`
- `public/assets/cards/card_back.webp`
- `public/assets/covers/cover_daily.webp`
- `public/assets/covers/cover_quick.webp`
- `public/assets/covers/cover_love.webp`
- `public/assets/covers/cover_money.webp`
- `public/assets/covers/cover_deep.webp`

The interface has CSS fallbacks and does not break if these files are missing.
