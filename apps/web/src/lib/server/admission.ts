import { createHmac, randomBytes } from "node:crypto";
import { isIP } from "node:net";

type Window = { limit: number; ms: number };
type Bucket = { events: number[]; expires: number };
const minute = 60_000;
const day = 24 * 60 * minute;
export const chatWindows = [
  { limit: 20, ms: minute },
  { limit: 300, ms: day },
];
export const loginWindows = [
  { limit: 10, ms: minute },
  { limit: 100, ms: day },
];
export const otpWindows = [
  { limit: 20, ms: minute },
  { limit: 200, ms: day },
];

// Synchronous reservation: parallel requests cannot pass a check before counting.
// No bodies or raw capabilities/IPs are stored, persisted or logged.
export class AdmissionLimiter {
  private buckets = new Map<string, Bucket>();
  private prunedAt = 0;
  constructor(private readonly capacity = 4096) {}

  consume(key: string, windows: Window[], now = Date.now()): number | null {
    if (now - this.prunedAt >= minute || this.buckets.size >= this.capacity) {
      for (const [id, bucket] of this.buckets)
        if (bucket.expires <= now) this.buckets.delete(id);
      this.prunedAt = now;
    }
    let bucket = this.buckets.get(key);
    // Never evict active counters to admit a flood of new keys.
    if (!bucket && this.buckets.size >= this.capacity) return 60;
    const longest = Math.max(...windows.map((window) => window.ms));
    bucket ??= { events: [], expires: now + longest };
    bucket.events = bucket.events.filter((time) => time > now - longest);
    let wait = 0;
    for (const window of windows) {
      const recent = bucket.events.filter((time) => time > now - window.ms);
      if (recent.length >= window.limit)
        wait = Math.max(
          wait,
          recent[recent.length - window.limit] + window.ms - now,
        );
    }
    if (wait > 0) return Math.max(1, Math.ceil(wait / 1000));
    bucket.events.push(now);
    bucket.expires = now + longest;
    this.buckets.set(key, bucket);
    return null;
  }

  rotate(previous: string, next: string) {
    const bucket = this.buckets.get(previous);
    if (!bucket || previous === next) return;
    this.buckets.set(next, bucket);
    this.buckets.delete(previous);
  }
}

export function clientAddress(headers: Headers, azureIngress: boolean): string {
  // ACA appends the observed peer; caller-supplied prefix and x-real-ip are untrusted.
  const value = azureIngress
    ? (headers.get("x-forwarded-for")?.split(",").at(-1)?.trim() ?? "")
    : "";
  if (!isIP(value) || value.includes("%")) return "unresolved-peer";
  if (isIP(value) === 4) return value;
  const canonical = new URL(`http://[${value}]`).hostname.slice(1, -1);
  // IPv4-mapped IPv6 must share the IPv4 bucket.
  const mapped = /^::ffff:([\da-f]+):([\da-f]+)$/.exec(canonical);
  if (!mapped) return canonical;
  return mapped
    .slice(1)
    .flatMap((part) => {
      const n = Number.parseInt(part, 16);
      return [n >> 8, n & 255];
    })
    .join(".");
}

const globalAdmission = globalThis as typeof globalThis & {
  aclaraAdmission?: { limiter: AdmissionLimiter; salt: Buffer };
};
const state = (globalAdmission.aclaraAdmission ??= {
  limiter: new AdmissionLimiter(),
  salt: randomBytes(32),
});
function key(kind: string, value: string) {
  return createHmac("sha256", state.salt)
    .update(`${kind}:${value}`)
    .digest("hex");
}
export function admit(
  path: string,
  token: string,
  headers: Headers,
): number | null {
  if (path === "auth/login")
    return state.limiter.consume(
      key("login", clientAddress(headers, !!process.env.CONTAINER_APP_NAME)),
      loginWindows,
    );
  if (["auth/otp/verify", "auth/step-up", "auth/step-up/verify"].includes(path))
    return state.limiter.consume(
      key("otp", clientAddress(headers, !!process.env.CONTAINER_APP_NAME)),
      otpWindows,
    );
  if (token && /^chat\/sessions\/[\w-]{1,80}\/(messages|confirm)$/.test(path))
    return state.limiter.consume(key("chat", token), chatWindows);
  return null;
}
export function carryAdmission(previous: string, next: string) {
  state.limiter.rotate(key("chat", previous), key("chat", next));
}
export function admissionMessage(language: string | null, seconds: number) {
  return language?.toLowerCase().startsWith("pt")
    ? `Muitas tentativas. Tente novamente em ${seconds} s.`
    : `Demasiados intentos. Vuelve a intentarlo en ${seconds} s.`;
}
