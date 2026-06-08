# Deploy to GitHub Pages

## Local Build

```bash
npm install
npm run build
```

The static build appears in `dist/`.

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
