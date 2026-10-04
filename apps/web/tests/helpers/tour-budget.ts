import { type Page } from "@playwright/test";
import { realpathSync, statSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { reserveLiveTurn } from "./judge-tour";

type RequestScope = { method: string; path: string; accessToken: string };
type Reservation = { token: string; maximumUsd: number };
type Adapter = {
  scope: string;
  capUsd: number;
  reserve: (request: RequestScope) => Promise<Reservation>;
  settle: (token: string, request: RequestScope & { status: number }) => Promise<{ verified: boolean; costUsd: number }>;
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
  await page.route("**/api/bff/chat/sessions/*/*", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() !== "POST" || !/^\/api\/bff\/chat\/sessions\/[\w-]{1,80}\/(messages|confirm)$/.test(pathname)) return route.continue();
    let token = "";
    try {
      if (stopped) throw new Error();
      reserveLiveTurn();
      const accessToken = (await page.context().cookies()).find((cookie) => cookie.name === "aclara_access")?.value ?? "";
      if (!accessToken) throw new Error();
      // Private in-memory credential lets the operator resolve the exact trusted
      // customer/run/session scope before taking an execution-ID baseline.
      const scope = { method: request.method(), path: pathname, accessToken };
      const reservation = await adapter.reserve(scope);
      token = reservation.token;
      if (typeof token !== "string" || !/^[\w.-]{1,200}$/.test(token) || !Number.isFinite(reservation.maximumUsd) || reservation.maximumUsd <= 0 || reservation.maximumUsd > 0.2) throw new Error();
      const response = await route.fetch({ maxRetries: 0, maxRedirects: 0, timeout: 65000 });
      try {
        const receipt = await adapter.settle(token, { ...scope, status: response.status() });
        if (receipt.verified !== true || !Number.isFinite(receipt.costUsd) || receipt.costUsd < 0 || receipt.costUsd > reservation.maximumUsd) throw new Error();
        await route.fulfill({ response });
      } finally {
        await response.dispose();
      }
    } catch {
      stopped = true;
      stoppedScopes.add(adapter.scope);
      // The operator retains unknown reserves and halts the shared durable scope.
      if (token) await adapter.halt(token).catch(() => undefined);
      await route.abort().catch(() => undefined);
    }
  });
  return () => {
    if (stopped) throw new Error("Paid tour stopped; operator reservation/receipt could not be verified.");
  };
}
