import { type Page } from "@playwright/test";
import { realpathSync, statSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { reserveLiveTurn } from "./judge-tour";

type RequestScope = { method: string; path: string; accessToken: string; body?: string };
type Reservation = { token: string; maximumUsd: number };
type Adapter = {
  scope: string;
  capUsd: number;
  reserve: (request: RequestScope) => Promise<Reservation>;
  settle: (token: string, request: RequestScope & { status: number; responseType?: string; outcome?: string; error?: string }) => Promise<{ verified: boolean; costUsd: number }>;
  halt: (token: string) => Promise<void>;
};
const stoppedScopes = new Set<string>();
export async function installPaidBudgetGuard(page: Page) {
  const file = path.resolve(process.env.JUDGE_TOUR_BUDGET_ADAPTER ?? "");
  const root = path.resolve("../../artifacts");
  if (!file.startsWith(root + path.sep) || !file.endsWith(".mjs") || realpathSync(file) !== file || (statSync(file).mode & 0o777) !== 0o600)
    throw new Error("A private operator budget adapter is required.");
  const adapter = (await import(pathToFileURL(file).href)) as Adapter;
  if (adapter.scope !== process.env.JUDGE_TOUR_BUDGET_SCOPE || adapter.capUsd !== 0.2 || [adapter.reserve, adapter.settle, adapter.halt].some((method) => typeof method !== "function"))
    throw new Error("Operator adapter must enforce the approved frontend purse.");
  if (stoppedScopes.has(adapter.scope)) throw new Error("Paid tour scope already stopped.");
  let stopped = false;
  const allHttp = process.env.JUDGE_TOUR_RESERVE_ALL_HTTP === "1";
  const origin = new URL(process.env.JUDGE_TOUR_URL ?? page.url()).origin;
  const pattern = allHttp ? `${origin}/**` : "**/api/bff/chat/sessions/*/*";
  const handler: Parameters<Page["route"]>[1] = async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    const turn = request.method() === "POST" && /^\/api\/bff\/chat\/sessions\/[\w-]{1,80}\/(messages|confirm)$/.test(pathname);
    if (!allHttp && !turn) return route.continue();
    if (stopped) return route.abort();
    let token = "";
    try {
      if (turn) reserveLiveTurn();
      const cookie = await request.headerValue("cookie") ?? "";
      const accessToken = cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("aclara_access="))?.slice("aclara_access=".length) ?? "";
      if (turn && !accessToken) throw new Error();
      // Private in-memory credential lets the operator resolve the exact trusted
      // customer/run/session scope before taking an execution-ID baseline.
      const scope = { method: request.method(), path: pathname, accessToken, ...(turn && pathname.endsWith("/messages") ? { body: request.postData() ?? "{}" } : {}) };
      const reservation = await adapter.reserve(scope);
      token = reservation.token;
      if (typeof token !== "string" || !/^[\w.-]{1,200}$/.test(token) || !Number.isFinite(reservation.maximumUsd) || reservation.maximumUsd <= 0 || reservation.maximumUsd > 0.2) throw new Error();
      const response = await route.fetch({ maxRetries: 0, maxRedirects: 0, timeout: 65000 });
      try {
        let plan: { response_type?: string; outcome?: string; error?: string } = {};
        if (turn) try { plan = await response.json(); } catch { /* The adapter rejects unverified live receipts. */ }
        const receipt = await adapter.settle(token, { ...scope, status: response.status(), responseType: plan.response_type, outcome: plan.outcome, error: plan.error });
        if (receipt.verified !== true || !Number.isFinite(receipt.costUsd) || receipt.costUsd < 0 || receipt.costUsd > reservation.maximumUsd) throw new Error();
        await route.fulfill({ response });
      } finally {
        await response.dispose();
      }
    } catch {
      stopped = true;
      stoppedScopes.add(adapter.scope);
      // The operator retains unknown reserves and halts the shared durable scope.
      await adapter.halt(token).catch(() => undefined);
      await route.abort().catch(() => undefined);
    }
  };
  if (allHttp) await page.context().route(pattern, handler);
  else await page.route(pattern, handler);
  return () => {
    if (stopped) throw new Error("Paid tour stopped; operator reservation/receipt could not be verified.");
  };
}
