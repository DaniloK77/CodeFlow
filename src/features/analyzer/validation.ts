import { formatBytes } from "@/lib/format";

interface FileRules {
  maxBytes: number;
  extensions: readonly string[];
}

/** A user-facing reason the file can't be analysed, or `null` if it's fine to upload. */
export function validateFile(file: File, { maxBytes, extensions }: FileRules): string | null {
  const name = file.name.toLowerCase();
  if (!extensions.some((extension) => name.endsWith(extension))) {
    return `“${file.name}” isn't supported. Choose a ${extensions.join(", ")} file.`;
  }
  if (file.size === 0) {
    return `“${file.name}” is empty.`;
  }
  if (file.size > maxBytes) {
    return `“${file.name}” is ${formatBytes(file.size)}; the free plan accepts up to ${formatBytes(maxBytes)}.`;
  }
  return null;
}
