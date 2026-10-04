import type { Locale } from "./contracts";
let conversationLocale: Locale = "es-MX";
export function setConversationLocale(locale: Locale) {
  conversationLocale = locale;
}
import { invalidateSession, workspaceRequest } from "./profile-workspace";
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public retryAfter = 60,
  ) {
    super(code);
  }
}
export async function api<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const request = workspaceRequest(path, signal);
  try {
    const response = await fetch(`/api/bff/${path}`, {
      method: body === undefined ? "GET" : "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "Accept-Language": conversationLocale,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: request.signal,
    });
    const data = await response.json();
    if (!request.current())
      throw new DOMException("Retired workspace", "AbortError");
    const actionAuth =
      path === "auth/step-up" || path === "auth/step-up/verify";
    if (
      response.status === 401 &&
      (!path.startsWith("auth/") || actionAuth) &&
      !["step_up_required", "invalid_otp_code", "challenge_expired"].includes(
        data.error,
      )
    )
      invalidateSession();
    if (response.ok && data.session_ended === true) invalidateSession();
    if (!response.ok)
      throw new ApiError(
        response.status,
        data.error ?? "request_failed",
        Math.max(
          1,
          Math.min(86400, Number(response.headers.get("Retry-After")) || 60),
        ),
      );
    return data as T;
  } finally {
    request.release();
  }
}
