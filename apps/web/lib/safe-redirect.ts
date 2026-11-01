/** Only allow same-site relative paths, to prevent open redirects via ?next=. */
export function safeNextPath(value: string | null | undefined, fallback = "/dashboard"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return fallback;
  }
  if (value.startsWith("/login")) return fallback;
  return value;
}
