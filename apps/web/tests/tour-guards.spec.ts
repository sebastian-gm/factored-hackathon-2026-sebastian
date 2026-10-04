import { test, expect, type Page } from "@playwright/test";
import { mkdtempSync, readFileSync, mkdirSync, writeFileSync, rmSync, appendFileSync } from "node:fs";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import path from "node:path";
import { reserveLiveTurn } from "./helpers/judge-tour";
import { installPaidBudgetGuard } from "./helpers/tour-budget";

const keys = ["JUDGE_TOUR_PAID", "JUDGE_TOUR_MAX_TURNS", "JUDGE_TOUR_TURN_LEDGER", "JUDGE_TOUR_BUDGET_ADAPTER", "JUDGE_TOUR_BUDGET_SCOPE", "JUDGE_TOUR_RESERVE_ALL_HTTP", "JUDGE_TOUR_URL"] as const;
let original: (string | undefined)[];
let folder: string;
let server: Server | undefined;
test.beforeEach(() => {
  original = keys.map((key) => process.env[key]);
  const root = path.resolve("../../artifacts/ux-audit/go-live/guard-tests");
  mkdirSync(root, { recursive: true, mode: 0o700 });
  folder = mkdtempSync(path.join(root, "run-"));
  process.env.JUDGE_TOUR_TURN_LEDGER = path.join(folder, "turns.json");
  process.env.JUDGE_TOUR_PAID = "1";
  process.env.JUDGE_TOUR_MAX_TURNS = "2";
  process.env.JUDGE_TOUR_BUDGET_SCOPE = `authored.${path.basename(folder)}`;
  delete process.env.JUDGE_TOUR_RESERVE_ALL_HTTP;
  delete process.env.JUDGE_TOUR_URL;
});
test.afterEach(async () => {
  if (server) await new Promise<void>((resolve) => server!.close(() => resolve()));
  server = undefined;
  keys.forEach((key, i) => {
    if (original[i] === undefined) delete process.env[key];
    else process.env[key] = original[i];
  });
  rmSync(folder, { recursive: true, force: true });
});
test("live turn guard requires opt-in and a finite bounded cap", () => {
  process.env.JUDGE_TOUR_PAID = "0";
  expect(() => reserveLiveTurn()).toThrow();
  process.env.JUDGE_TOUR_PAID = "1";
  for (const value of ["0", "113", "NaN", "Infinity", "1.5"]) {
    process.env.JUDGE_TOUR_MAX_TURNS = value;
    expect(() => reserveLiveTurn()).toThrow();
  }
});
test("live turn guard persists attempted sends and cannot raise a previous cap", () => {
  reserveLiveTurn();
  process.env.JUDGE_TOUR_MAX_TURNS = "40";
  reserveLiveTurn();
  expect(() => reserveLiveTurn()).toThrow();
  expect(JSON.parse(readFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "utf8"))).toEqual({ attempts: 2, maximum: 2 });
});
test("live turn guard fails closed on crashed locks and invalid accounting", () => {
  mkdirSync(process.env.JUDGE_TOUR_TURN_LEDGER! + ".lock");
  expect(() => reserveLiveTurn()).toThrow();
  rmSync(process.env.JUDGE_TOUR_TURN_LEDGER! + ".lock", { recursive: true });
  writeFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "{}");
  expect(() => reserveLiveTurn()).toThrow();
});
test("live turn guard refuses paths outside ignored artifacts", () => {
  process.env.JUDGE_TOUR_TURN_LEDGER = path.resolve("tour-ledger-forbidden.json");
  expect(() => reserveLiveTurn()).toThrow();
});

function operatorAdapter(unknown = false) {
  const file = path.join(folder, "operator.mjs");
  const calls = path.join(folder, "operations.txt");
  writeFileSync(file, `import { appendFileSync } from "node:fs";
export const scope = ${JSON.stringify(process.env.JUDGE_TOUR_BUDGET_SCOPE)}, capUsd = 0.2;
const record = name => appendFileSync(${JSON.stringify(calls)}, name + "\\n", {mode: 0o600});
export async function reserve(request) { if (!request.accessToken) throw Error(); record("reserve"); return {token:"authored-reservation",maximumUsd:0.01}; }
export async function settle() { record("settle"); return {verified:true,costUsd:${unknown ? "NaN" : "0"}}; }
export async function halt() { record("halt"); }
`, { mode: 0o600 });
  process.env.JUDGE_TOUR_BUDGET_ADAPTER = file;
  return calls;
}
async function operatorPage(page: Page, calls: string) {
  server = createServer((request, response) => {
    if (request.method === "POST") appendFileSync(calls, "sent\n", { mode: 0o600 });
    response.writeHead(request.method === "POST" ? 201 : 200, { "Content-Type": "text/plain" });
    response.end("Authored operator test");
  });
  await new Promise<void>((resolve) => server!.listen(0, "127.0.0.1", resolve));
  await page.goto(`http://127.0.0.1:${(server.address() as AddressInfo).port}`);
  await page.context().addCookies([{ name: "aclara_access", value: "authored-budget-session", url: page.url() }]);
}
test("operator guard reserves messages and confirmations before returning a verified response", async ({ page }) => {
  const calls = operatorAdapter();
  await operatorPage(page, calls);
  const healthy = await installPaidBudgetGuard(page);
  for (const action of ["messages", "confirm"])
    expect(await page.evaluate(async (action) => (await fetch(`/api/bff/chat/sessions/authored-budget-session/${action}`, { method: "POST", body: "{}" })).status, action)).toBe(201);
  healthy();
  expect(readFileSync(calls, "utf8")).toBe("reserve\nsent\nsettle\nreserve\nsent\nsettle\n");
  expect(JSON.parse(readFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "utf8")).attempts).toBe(2);
});
test("unknown operator receipts retain reserves and stop later paid requests", async ({ page }) => {
  const calls = operatorAdapter(true);
  await operatorPage(page, calls);
  const healthy = await installPaidBudgetGuard(page);
  for (let request = 0; request < 2; request++)
    expect(await page.evaluate(() => fetch("/api/bff/chat/sessions/authored-budget-session/messages", { method: "POST", body: "{}" }).then(() => false, () => true))).toBe(true);
  expect(() => healthy()).toThrow();
  expect(readFileSync(calls, "utf8")).toBe("reserve\nsent\nsettle\nhalt\n");
  await expect(installPaidBudgetGuard(page)).rejects.toThrow();
});

test("all-HTTP guard reserves deterministic reads without consuming paid turn attempts", async ({ page }) => {
  const calls = operatorAdapter();
  await operatorPage(page, calls);
  process.env.JUDGE_TOUR_RESERVE_ALL_HTTP = "1";
  const healthy = await installPaidBudgetGuard(page);
  expect(await page.evaluate(() => fetch("/authored-read").then((r) => r.status))).toBe(200);
  healthy();
  expect(readFileSync(calls, "utf8")).toBe("reserve\nsettle\n");
  expect(() => readFileSync(process.env.JUDGE_TOUR_TURN_LEDGER!, "utf8")).toThrow();
});
