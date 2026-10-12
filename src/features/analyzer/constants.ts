// Mirrors the API's free-plan defaults (api/config.py) so bad input fails fast, before upload.
export const LIMITS = {
  archiveBytes: 5 * 1024 * 1024,
  sourceFileBytes: 200 * 1024,
  snippetChars: 200_000,
  // Same bounds as the API's request validation (api/schemas.py).
  taskMinChars: 20,
  explanationMinChars: 30,
  textMaxChars: 10_000,
} as const;

export const ARCHIVE_EXTENSIONS = [".zip"] as const;
export const SOURCE_EXTENSIONS = [".tsx", ".ts", ".jsx", ".js", ".py"] as const;

import type { SourceLanguage } from "@/types/content";

export const SNIPPET_LANGUAGES = [
  { value: "auto", label: "Auto-detect" },
  { value: "tsx", label: "TypeScript + JSX" },
  { value: "typescript", label: "TypeScript" },
  { value: "jsx", label: "JavaScript + JSX" },
  { value: "javascript", label: "JavaScript" },
  { value: "python", label: "Python" },
] as const satisfies readonly { value: "auto" | SourceLanguage; label: string }[];

export type SnippetLanguage = (typeof SNIPPET_LANGUAGES)[number]["value"];
