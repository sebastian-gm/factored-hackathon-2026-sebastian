import type { Locale } from "./contracts";
export function money(
  amount: number,
  currency: string,
  locale: Locale,
): string {
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      currencyDisplay: "code",
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}
export function date(value: string, locale: Locale, time = false): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    ...(time ? { timeStyle: "short" as const } : {}),
    timeZone: "UTC",
  }).format(parsed);
}
export function remaining(due: string, clock: string): string {
  const minutes = Math.max(
    0,
    Math.ceil((Date.parse(due) - Date.parse(clock)) / 60000),
  );
  if (!Number.isFinite(minutes)) return "—";
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  return `${days ? `${days}d ` : ""}${hours}h ${minutes % 60}m`;
}
