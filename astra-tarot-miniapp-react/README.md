# Astra Tarot Mini App

React/Vite/TypeScript frontend for the Astra Tarot Telegram Mini App. The app is mobile-first and uses real visual assets from `public/assets` with GitHub Pages-safe paths.

## Run Locally

```bash
npm install
npm run dev
```

Open the Vite URL in a browser. Outside Telegram the app shows a small `Browser preview` badge and works in mock mode.

## Build And Preview

```bash
npm run typecheck
npm run build
npm run preview
```

## Assets

Runtime images must live in:

```text
public/assets/
  background/
  cards/
  covers/
  guide/
  logo/
```

The current source images were copied from the root `assets/` folder into `public/assets/`. React uses only `public/assets` so Vite can serve them locally, in preview, and on GitHub Pages.

Important files:

- `public/assets/guide/hero_guide_banner.webp`
- `public/assets/guide/guide_avatar.webp`
- `public/assets/guide/guide_card.webp`
- `public/assets/logo/guide_round.webp`
- `public/assets/background/card_back_minimal.webp`
- `public/assets/background/card_back_ornate.webp`
- `public/assets/covers/cover_daily.webp`
- `public/assets/covers/cover_quick.webp`
- `public/assets/covers/cover_love.webp`
- `public/assets/covers/cover_money.webp`
- `public/assets/covers/cover_deep.webp`
- `public/assets/cards/card_*.webp`

All image URLs in React should go through:

```ts
import { assetUrl } from "./src/services/assets";

assetUrl("assets/guide/guide_avatar.webp");
```

Do not use hard-coded absolute paths like `/assets/...` in React components.

## Screens

The Mini App keeps a five-screen flow:

- `WelcomeScreen` uses `hero_guide_banner.webp` and the Star Guide.
- `HomeScreen` uses `guide_avatar.webp`, `cover_daily.webp`, and the four spread cover cards.
- `SpreadScreen` shows the selected spread cover, details, question textarea, and sticky CTA.
- `RitualScreen` uses `guide_card.webp` plus `card_back_ornate.webp` with light animation-ready classes.
- `ResultScreen` renders the result inside the Mini App with card images, Star Guide advice, and safe fallback visuals.

## Missing Images

If a card image is missing, the UI falls back to:

- `assets/background/card_back_minimal.webp` for result and arcana cards;
- `assets/background/card_back_ornate.webp` for ritual and spread cover fallback;
- CSS fallback if even the fallback image is unavailable.

If an image does not display:

1. Check that it is under `public/assets`, not only under root `assets`.
2. Check spelling and case in `src/data/arcana.ts` or `src/data/spreads.ts`.
3. Check `VITE_BASE_PATH` for GitHub Pages deployments.
4. Run `npm run build` to catch path or TypeScript regressions.

Mock readings prefer cards that already have real `public/assets/cards/*.webp` images. Arcana without images still remain valid data and fall back safely in UI.

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
