import { expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { chmodSync, closeSync, existsSync, fsyncSync, mkdirSync, openSync, readFileSync, rmSync, rmdirSync, writeFileSync } from "node:fs";
import path from "node:path";

export const live = process.env.JUDGE_TOUR_MODE === "live";
export const locale = (info: TestInfo) => ((process.env.JUDGE_TOUR_LANGUAGE ?? info.project.name.split("-")[0]) === "pt" ? "pt-BR" : "es-MX");
export const directory = (info: TestInfo) => path.resolve("../../artifacts/ux-audit/go-live", live ? "live" : "demo", info.project.name);
export async function visible(locator: Locator) {
  // Boolean assertions keep private text out of Playwright assertion diagnostics.
  await expect.poll(() => locator.isVisible(), { timeout: 30000 }).toBe(true);
}
export async function language(page: Page, info: TestInfo) {
  const select = page.locator(".locale-select select");
  if (await select.count()) await select.selectOption(locale(info));
  await expect.poll(() => page.locator("html").getAttribute("lang")).toBe(locale(info));
}
export function paid(info: TestInfo) {
  return (
    !live ||
    (process.env.JUDGE_TOUR_PAID === "1" && Number(process.env.JUDGE_TOUR_MAX_TURNS ?? 0) > 0 && info.project.name === (process.env.JUDGE_TOUR_PAID_PROJECT ?? "es-desktop"))
  );
}
export function reserveTurn() {
  if (!live) return;
  reserveLiveTurn();
}
export function reserveLiveTurn() {
  const maximum = Number(process.env.JUDGE_TOUR_MAX_TURNS ?? 0);
  if (process.env.JUDGE_TOUR_PAID !== "1" || !Number.isInteger(maximum) || maximum < 1 || maximum > 40)
    throw new Error("Live model turns require explicit opt-in and a cap from 1 to 40.");
  const file = path.resolve(process.env.JUDGE_TOUR_TURN_LEDGER ?? `../../artifacts/ux-audit/go-live/live/turn-reservations-${new Date().toISOString().slice(0, 10)}.json`);
  const root = path.resolve("../../artifacts");
  if (!file.startsWith(`${root}${path.sep}`)) throw new Error("Turn ledger must remain under ignored artifacts.");
  mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const lock = `${file}.lock`;
  // Atomic lock fails closed, including after a crash. Reservations are never refunded.
  try {
    mkdirSync(lock, { mode: 0o700 });
  } catch {
    throw new Error("Turn ledger locked; inspect before continuing.");
  }
  try {
    const prior = existsSync(file)
      ? (JSON.parse(readFileSync(file, "utf8")) as {
          attempts: number;
          maximum: number;
        })
      : { attempts: 0, maximum };
    if (!Number.isInteger(prior.attempts) || prior.attempts < 0 || !Number.isInteger(prior.maximum) || prior.maximum < 1 || prior.maximum > 40)
      throw new Error("Invalid durable turn ledger.");
    const cap = Math.min(maximum, prior.maximum);
    if (prior.attempts >= cap) throw new Error("Live tour turn reservation exhausted.");
    const descriptor = openSync(file, "w", 0o600);
    try {
      writeFileSync(descriptor, JSON.stringify({ attempts: prior.attempts + 1, maximum: cap }));
      fsyncSync(descriptor);
    } finally {
      closeSync(descriptor);
    }
    chmodSync(file, 0o600);
  } finally {
    rmdirSync(lock);
  }
}
export async function logout(page: Page) {
  if (page.isClosed()) return;
  const button = page.getByRole("button", { name: /^(Cerrar sesión|Sair)$/ });
  if (await button.isVisible()) {
    await button.click();
    await visible(page.locator(".login-panel input[autocomplete=current-password]"));
    expect((await page.context().cookies()).some((cookie) => cookie.name === "aclara_access")).toBe(false);
  }
}
async function paceLogin() {
  const file = path.resolve("../../artifacts/ux-audit/go-live", live ? "live" : "demo", "last-login.json");
  mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const previous = existsSync(file) ? Number(JSON.parse(readFileSync(file, "utf8")).at) : 0;
  if (!Number.isFinite(previous)) throw new Error("Invalid login pacing record.");
  await new Promise((resolve) => setTimeout(resolve, Math.max(0, 7000 - (Date.now() - previous))));
  writeFileSync(file, JSON.stringify({ at: Date.now() }), { mode: 0o600 });
}
export async function login(page: Page, info: TestInfo, staff = false) {
  const username = process.env[staff ? "JUDGE_TOUR_STAFF_USERNAME" : "JUDGE_TOUR_USERNAME"];
  const password = process.env[staff ? "JUDGE_TOUR_STAFF_PASSWORD" : "JUDGE_TOUR_PASSWORD"];
  if (!username || !password) throw new Error("Required runtime tour credentials are unavailable.");
  try {
    await page.goto("/");
    await visible(page.locator(".login-panel input[autocomplete=current-password]"));
    await language(page, info);
    if (staff) await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
    const input = page.locator(".login-panel input[autocomplete=username]");
    if (await input.count()) await input.fill(username);
    else await page.locator(".login-panel select").selectOption(username);
    await page.locator(".login-panel input[autocomplete=current-password]").fill(password);
    await paceLogin();
    await page.locator(".login-panel button[type=submit]").click();
    await expect.poll(async () => /^\d{6}$/.test((await page.getByTestId("sms-code").textContent()) ?? "")).toBe(true);
    await capture(page, info, staff ? "staff-login-otp" : "login-otp");
    await page.locator(".login-panel input[autocomplete=one-time-code]").fill((await page.getByTestId("sms-code").textContent())!.trim());
    await page.locator(".login-panel button[type=submit]").click();
    await visible(page.getByRole("button", { name: /^(Cerrar sesión|Sair)$/ }));
    await language(page, info);
  } catch {
    // An expired/failed OTP attempt must not leave challenge captures behind.
    for (const suffix of ["full.png", "viewport.png", "checks.json"])
      rmSync(path.join(directory(info), `${staff ? "staff-login-otp" : "login-otp"}-${suffix}`), { force: true });
    throw new Error("Authentication failed; credential diagnostics suppressed.");
  }
}
export async function profile(page: Page, info: TestInfo) {
  if (live) {
    await visible(page.getByTestId("profile-mx-es"));
    await page.getByTestId(locale(info) === "pt-BR" ? "profile-pt" : "profile-mx-es").click();
  }
  await visible(page.locator(".composer textarea"));
  await language(page, info);
}
export async function capture(page: Page, info: TestInfo, name: string) {
  await expect.poll(() => page.locator("html").getAttribute("lang")).toBe(locale(info));
  const folder = directory(info);
  mkdirSync(folder, { recursive: true, mode: 0o700 });
  const masks = [page.locator("input[type=password], input[autocomplete=one-time-code], input[autocomplete=username], .login-panel select, .sms-code")];
  if (live)
    masks.push(
      page.locator(
        ".bubble > p, .transaction-card h3, .transaction-top p, .transaction-money, .transaction-card time, .transaction-bottom .badge, .case-reference strong, .receipt > div > p, .receipt > div > strong, .composer textarea, .queue-item, .packet-section :is(p,ul,ol), .packet-section dl, .technical-reference, .execution-list, .metadata-list, .why-explanation, .packet-heading > div, .packet-section .transaction-card, .action-timeline, .action-references, .trace-panel select, .clock, [role=dialog] > p",
      ),
    );
  const scroll = await page.evaluate(() => ({ x: scrollX, y: scrollY }));
  for (const fullPage of [false, true]) {
    if (fullPage) await page.evaluate(() => window.scrollTo(0, 0));
    const file = path.join(folder, `${name}-${fullPage ? "full" : "viewport"}.png`);
    await page.screenshot({ path: file, fullPage, mask: masks });
    chmodSync(file, 0o600);
  }
  await page.evaluate(({ x, y }) => window.scrollTo(x, y), scroll);
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const file = path.join(folder, `${name}-checks.json`);
  const checks = {
    axe_violations: results.violations.length,
    horizontal_overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
  };
  writeFileSync(file, JSON.stringify(checks), { mode: 0o600 });
  expect(checks.axe_violations).toBe(0);
  expect(checks.horizontal_overflow).toBe(false);
}
export function aggregates(page: Page, info: TestInfo, suffix = "") {
  const counts = {
    console_errors: 0,
    application_console_errors: 0,
    page_errors: 0,
    failed_requests: 0,
    responses_429: 0,
  };
  page.on("console", (message) => {
    if (message.type() === "error") {
      counts.console_errors++;
      if (!message.text().startsWith("Failed to load resource:")) counts.application_console_errors++;
    }
  });
  page.on("pageerror", () => counts.page_errors++);
  page.on("requestfailed", () => counts.failed_requests++);
  page.on("response", (response) => {
    if (response.status() === 429) counts.responses_429++;
  });
  return () => {
    mkdirSync(directory(info), { recursive: true, mode: 0o700 });
    writeFileSync(path.join(directory(info), `test-${info.testId.replace(/[^a-zA-Z0-9-]/g, "")}${suffix}-metrics.json`), JSON.stringify({ ...counts, status: info.status }), {
      mode: 0o600,
    });
    expect(counts.page_errors).toBe(0);
    expect(counts.application_console_errors).toBe(0);
  };
}
