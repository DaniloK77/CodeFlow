interface ImportMetaEnv {
  /** Base URL of the analysis API. Empty in development, where Vite proxies /api. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
