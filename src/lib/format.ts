const eurFormatter = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });

const wholeEurFormatter = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

/** "€20", or "€19.99" when the amount has cents. */
export function formatPrice(amount: number): string {
  return (Number.isInteger(amount) ? wholeEurFormatter : eurFormatter).format(amount);
}

const BYTE_UNITS = ["B", "KB", "MB", "GB"] as const;

/** 1536 → "1.5 KB". */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const digits = unit === 0 || value >= 10 ? 0 : 1;
  return `${value.toFixed(digits)} ${BYTE_UNITS[unit] ?? "B"}`;
}

/** "Sarah Chen" → "SC". Used for avatar fallbacks. */
export function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}
