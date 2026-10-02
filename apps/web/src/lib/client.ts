import { invalidateJudgeSession, workspaceRequest } from "./profile-workspace";
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
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
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: request.signal,
    });
    const data = await response.json();
    if (!request.current())
      throw new DOMException("Retired workspace", "AbortError");
    if (
      response.status === 401 &&
      !path.startsWith("auth/") &&
      data.error !== "step_up_required"
    )
      invalidateJudgeSession();
    if (!response.ok)
      throw new ApiError(response.status, data.error ?? "request_failed");
    return data as T;
  } finally {
    request.release();
  }
}
