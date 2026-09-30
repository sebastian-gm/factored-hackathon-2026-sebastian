// The clock is part of /me. BFF /config reads /personas upstream.
const startupReads = new Set([
  "me",
  "clock",
  "transactions",
  "config",
  "personas",
]);
const transientStatuses = new Set([502, 503, 504]);

export async function upstreamFetch(
  base: string,
  path: string,
  init: RequestInit,
): Promise<Response> {
  const readOnly = init.method === "GET";
  const timeout =
    readOnly && startupReads.has(path)
      ? 75000
      : path.endsWith("/messages")
        ? 180000
        : 10000;
  // At most one retry for idempotent reads. Never replay authentication,
  // messages, confirmations, or any other POST, even after a timeout.
  for (let attempt = 0; ; attempt++) {
    try {
      const result = await fetch(`${base.replace(/\/$/, "")}/${path}`, {
        ...init,
        signal: AbortSignal.timeout(timeout),
      });
      if (readOnly && attempt === 0 && transientStatuses.has(result.status)) {
        await result.body?.cancel();
        continue;
      }
      return result;
    } catch (error) {
      if (!readOnly || attempt === 1) throw error;
    }
  }
}
