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

This keeps paths working when the app is deployed under `/astra-tarot-miniapp/`.

## GitHub Pages With Actions

1. Create or use the repository `astra-tarot-miniapp`.
2. Push this project to GitHub.
3. In GitHub, open `Settings -> Pages`.
4. Set `Build and deployment` to `GitHub Actions`.
5. Keep `.github/workflows/deploy.yml` in the repo.
6. Push to `main` or run the workflow manually.

The expected URL is:

```text
https://username.github.io/astra-tarot-miniapp/
```

## Base Path

For GitHub Pages the build uses:

```env
VITE_BASE_PATH=/astra-tarot-miniapp/
```

If the repository name changes, update `VITE_BASE_PATH` and the workflow.

## BotFather

Insert the deployed HTTPS URL into the Mini App/Web App settings:

```text
https://username.github.io/astra-tarot-miniapp/
```

## Bot Environment

In the Python bot `.env`, use:

```env
MINIAPP_URL=https://username.github.io/astra-tarot-miniapp/
```

Do not add bot or Gemini secrets to the frontend `.env`.

## If Images Do Not Display

Check that the files exist under `public/assets`, that paths in `src/data/spreads.ts` and `src/data/arcana.ts` do not start with `/`, and that `VITE_BASE_PATH` matches the GitHub Pages repository path.
