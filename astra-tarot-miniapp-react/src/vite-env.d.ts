/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_MODE?: "mock" | "api" | string;
  readonly VITE_BASE_PATH?: string;
  readonly VITE_GITHUB_PAGES_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
