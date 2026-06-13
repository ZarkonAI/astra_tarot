# Deploy to GitHub Pages

## Local Build

```bash
npm install
npm run typecheck
npm run build
```

The static build appears in `dist/`.

## Assets

GitHub Pages serves images from the built `public/assets` folder. Keep runtime images here:

```text
public/assets/background/
public/assets/cards/
public/assets/covers/
public/assets/guide/
public/assets/logo/
```

React components should resolve image URLs through `src/services/assets.ts`:

```ts
assetUrl("assets/covers/cover_daily.webp");
```

This keeps paths working when the app is deployed under `/astra_tarot/`.

## GitHub Pages With Actions

1. Create or use the repository `astra_tarot`.
2. Push this project to GitHub.
3. In GitHub, open `Settings -> Pages`.
4. Set `Build and deployment` to `GitHub Actions`.
5. Keep `.github/workflows/deploy.yml` in the repository root, not only inside
   `astra-tarot-miniapp-react`.
6. Push to `main` or run the workflow manually.

The expected URL is:

```text
https://zarkonai.github.io/astra_tarot/
```

## Base Path

For GitHub Pages the build uses:

```env
VITE_APP_MODE=mock
VITE_API_BASE_URL=
VITE_BASE_PATH=/astra_tarot/
VITE_GITHUB_PAGES_BASE=/astra_tarot/
```

If the repository name changes, update `VITE_BASE_PATH` and the workflow.

Local and preview builds can keep the fallback base path:

```env
VITE_BASE_PATH=/
```

Do not reference images as `/assets/...` from React. Use `assetUrl("assets/...")` so Vite prefixes the current base path.

## BotFather

Insert the deployed HTTPS URL into the Mini App/Web App settings:

```text
https://zarkonai.github.io/astra_tarot/
```

Use it for both Main App URL and Menu Button URL.

## Bot Environment

In the Python bot `.env`, use:

```env
MINIAPP_URL=https://zarkonai.github.io/astra_tarot/
PUBLIC_BASE_URL=https://zarkonai.github.io/astra_tarot/
```

Do not add bot or Gemini secrets to the frontend `.env`.

## If Images Do Not Display

Check that the files exist under `public/assets`, that paths in `src/data/spreads.ts` and `src/data/arcana.ts` do not start with `/`, and that `VITE_BASE_PATH` matches the GitHub Pages repository path.

Quick checks:

```bash
npm run typecheck
npm run build
npm run preview
```

Then open:

```text
http://127.0.0.1:4173/
http://127.0.0.1:4173/astra_tarot/
http://127.0.0.1:4173/astra_tarot/assets/guide/hero_guide_banner.webp
http://127.0.0.1:4173/astra_tarot/assets/cards/card_star.webp
```
