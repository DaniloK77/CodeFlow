import type { CodeLanguage } from "@/types/content";

const LANGUAGE_BY_EXTENSION: Record<string, CodeLanguage> = {
  ".py": "python",
  ".ts": "typescript",
  ".tsx": "tsx",
  ".jsx": "jsx",
  ".js": "javascript",
};

/** Syntax-highlighting language for a file name; unknown extensions fall back to JavaScript. */
export function languageForPath(path: string): CodeLanguage {
  const extension = path.slice(path.lastIndexOf(".")).toLowerCase();
  return LANGUAGE_BY_EXTENSION[extension] ?? "javascript";
}
