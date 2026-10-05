import { selectLoginPersona } from "./helpers/login-persona";
import { test, expect, type Page } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import { chmod, mkdir } from "node:fs/promises";
import path from "node:path";
import { offerFixture, multiReasonPacket } from "./fixtures/conversation-ui";
import { stageCosts, callTotals, type TraceEvent } from "../src/lib/trace";

// Authored UI fixtures only. Never load held-out suites or organizer records.
const phase = process.env.FRONTEND_DESIGN_CAPTURE_PHASE;
async function review(page: Page, name: string) {
  const scroll = await page.evaluate(() => ({ x: scrollX, y: scrollY }));
  expect(await page.pageErrors()).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.locator(".skip-link")).toHaveCSS("position", "absolute");
  if (page.viewportSize()!.width === 1440) {
    const rail = await page.locator(".sidebar").boundingBox();
    expect(rail?.y).toBe(0);
    expect(rail?.height).toBe(page.viewportSize()!.height);
  }
  if (phase !== "before") {
    const sizes = await page.evaluate(() =>
      [
        ...new Set(
          [...document.querySelectorAll<HTMLElement>("body *")]
            .filter(
              (element) =>
                element.getClientRects().length &&
                !element.matches(".demo-disclosure") &&
                [...element.childNodes].some(
                  (node) =>
                    node.nodeType === Node.TEXT_NODE &&
                    node.textContent?.trim(),
                ),
            )
            .map((element) => getComputedStyle(element).fontSize),
        ),
      ].sort(),
    );
    expect(
      sizes.every((size) => ["14px", "16px", "24px"].includes(size)),
      `Unexpected type scale: ${sizes}`,
    ).toBe(true);
  }
  await expect(page.locator(".demo-disclosure")).toHaveCount(1);
  await expect(page.locator(".synthetic-banner, .clock")).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.evaluate(({ x, y }) => window.scrollTo(x, y), scroll);
  if (phase) {
    if (!["before", "after"].includes(phase))
      throw new Error("Invalid design capture phase");
    const directory = path.resolve(
      process.cwd(),
      "../../artifacts/ux-audit/minimal-design",
      phase,
    );
    await mkdir(directory, { recursive: true, mode: 0o700 });
    await chmod(directory, 0o700);
    for (const fullPage of [false, true]) {
      const file = path.join(
        directory,
        `${name}-${fullPage ? "full" : "viewport"}.png`,
      );
      await page.screenshot({
        path: file,
        fullPage,
        mask: [
          page.locator(
            "input[type=password], input[autocomplete=username], input[autocomplete=one-time-code], [data-testid=sms-code]",
          ),
        ],
      });
      await chmod(file, 0o600);
    }
  }
}
async function login(
  page: Page,
  pt: boolean,
  role: "customer" | "agent" | "ops",
) {
  await page.goto("/");
  if (role !== "customer")
    await page
      .locator(".sidebar nav button")
      .nth(role === "agent" ? 1 : 2)
      .click();
  await selectLoginPersona(
    page,
    role === "customer" ? (pt ? "demo.pt.br" : "demo.es.mx") : `demo.${role}`,
  );
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
  await page
    .locator("input[autocomplete=one-time-code]")
    .fill((await page.getByTestId("sms-code").textContent())!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(
    page.locator(
      role === "customer"
        ? ".chat-panel"
        : role === "agent"
          ? ".desk-grid"
          : ".trace-panel",
    ),
  ).toBeVisible();
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
}
const costEvents: TraceEvent[] = [
  {
    id: "ui-cost-language",
    stage: "Understand",
    state: "ui_language",
    tool: null,
    rules: [],
    verified: false,
    llm: {
      provider: "mock",
      model: "authored-ui",
      prompt_version: "none",
      input_tokens: 0,
      output_tokens: 0,
      cost_usd: 0.002,
      latency_ms: 0,
    },
  },
  {
    id: "ui-cost-decision",
    stage: "Decide",
    state: "ui_decision",
    tool: null,
    rules: [],
    verified: false,
    llm: {
      provider: "mock",
      model: "authored-ui",
      prompt_version: "none",
      input_tokens: 0,
      output_tokens: 0,
      cost_usd: 0.001,
      latency_ms: 0,
    },
  },
  {
    id: "ui-cost-unknown",
    stage: "Understand",
    state: "ui_unknown",
    tool: null,
    rules: [],
    verified: false,
    llm: {
      provider: "mock",
      model: "authored-ui",
      prompt_version: "none",
      input_tokens: 0,
      output_tokens: 0,
      cost_usd: null,
      latency_ms: 0,
    },
  },
];
test("costs keep unknown calls out of measured bars and deduplicate execution references", () => {
  const events = [...costEvents, costEvents[0]];
  expect(callTotals(events)).toMatchObject({
    count: 3,
    unknown: 1,
    known: 0.003,
  });
  expect(stageCosts(events)).toEqual([
    { stage: "Understand", count: 2, knownCount: 1, cost: 0.002 },
    { stage: "Decide", count: 1, knownCount: 1, cost: 0.001 },
  ]);
});
for (const pt of [false, true])
  test(`${pt ? "PT" : "ES"}: Ops cost chart labels known/total calls and never charts an unknown cost as zero`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/ops/overview", (route) =>
      route.fulfill({
        json: {
          dataset_version: "authored-ui-cost",
          source_kind: "authored_fixture",
          bank_clock: "2026-06-18T06:00:00Z",
          quality: [],
          freshness: {
            built_at: "2026-06-18T06:00:00Z",
            source_as_of: "2026-06-18T06:00:00Z",
            status: "unknown",
          },
          conversations: [{ id: "CONV-UI-COST", events: costEvents }],
          daily_cost: [],
          results: null,
        },
      }),
    );
    await login(page, pt, "ops");
    const chart = page.locator(".conversation-cost .evidence-chart");
    await expect(chart).toHaveAttribute("data-zero-based", "true");
    await expect(chart).toHaveAttribute("data-axis-max", "0.002");
    await expect(chart).toContainText("USD");
    await expect(chart).toContainText("1/2");
    await expect(chart).toContainText("1/1");
    await expect(chart.locator("rect")).toHaveCount(2);
    expect(
      await chart
        .locator("rect")
        .evaluateAll((elements) =>
          elements.map((element) => element.getAttribute("width")),
        ),
    ).toEqual(["100", "50"]);
    await expect(page.locator(".conversation-cost")).toContainText("2/3");
    await review(page, `${pt ? "pt" : "es"}-390-ops-cost`);
    await page.route("**/ops/overview", (route) =>
      route.fulfill({
        json: {
          dataset_version: "authored-ui-cost",
          source_kind: "authored_fixture",
          bank_clock: "2026-06-18T06:00:00Z",
          quality: [],
          freshness: {
            built_at: "2026-06-18T06:00:00Z",
            source_as_of: "2026-06-18T06:00:00Z",
            status: "unknown",
          },
          conversations: [{ id: "CONV-UI-COST", events: [costEvents[2]] }],
          daily_cost: [],
          results: null,
        },
      }),
    );
    await page.reload();
    await page.locator(".sidebar nav button").nth(2).click();
    await expect(page.locator(".trace-panel")).toBeVisible();
    await page
      .locator(".locale-select select")
      .selectOption(pt ? "pt-BR" : "es-MX");
    await expect(page.locator(".conversation-cost > strong")).toHaveText(
      pt ? "Custo não registrado" : "Costo no registrado",
    );
    await expect(
      page.locator(".conversation-cost .evidence-chart"),
    ).toHaveCount(0);
  });
for (const pt of [false, true])
  for (const width of [1440, 390]) {
    const name = `${pt ? "pt" : "es"}-${width}`;
    test(`${name}: minimal chat, desk, operations and sourced evidence are accessible`, async ({
      page,
    }) => {
      test.setTimeout(90000);
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.route("**/chat/sessions/*/messages", (route) =>
        route.fulfill({ json: offerFixture(pt) }),
      );
      await login(page, pt, "customer");
      await page
        .locator(".composer textarea")
        .fill(
          pt
            ? "Quero revisar esta compra de teste."
            : "Quiero revisar esta compra de prueba.",
        );
      await page.locator(".composer button[type=submit]").click();
      await expect(page.locator(".recognition-actions")).toBeVisible();
      if (phase !== "before") {
        const log = await page.locator(".conversation-log").boundingBox();
        const merchant = await page
          .locator(".conversation-log .transaction-top h3")
          .boundingBox();
        expect(merchant!.y).toBeGreaterThanOrEqual(log!.y);
        expect(merchant!.y + merchant!.height).toBeLessThanOrEqual(
          log!.y + log!.height,
        );
      }
      await review(page, `${name}-chat`);
      await page
        .getByRole("button", {
          name: pt ? "Sair" : "Cerrar sesión",
          exact: true,
        })
        .click();
      await page.route("**/agent/handoffs", (route) =>
        route.fulfill({
          json: [
            {
              ...multiReasonPacket,
              verified_facts: [offerFixture(pt).transaction],
              customer_display: pt
                ? "Pessoa de teste UI"
                : "Persona de prueba UI",
              open_questions: [
                pt
                  ? "Confirmar qual ajuda a pessoa precisa."
                  : "Confirmar qué ayuda necesita la persona.",
              ],
              route: { ...multiReasonPacket.route, language: pt ? "pt" : "es" },
            },
          ],
        }),
      );
      await login(page, pt, "agent");
      await page.locator(".queue-item").click();
      await review(page, `${name}-desk`);
      await page
        .getByRole("button", {
          name: pt ? "Sair" : "Cerrar sesión",
          exact: true,
        })
        .click();
      await login(page, pt, "ops");
      await review(page, `${name}-ops`);
      await page.locator(".sidebar nav button").nth(3).click();
      await expect(page.locator(".insights-hero")).toBeVisible();
      await review(page, `${name}-insights`);
      await page.getByTestId("insights-comparison").scrollIntoViewIfNeeded();
      await review(page, `${name}-evidence`);
      if (phase !== "before") {
        await expect(page.getByTestId("insights-languages")).toContainText(
          "43 / 48",
        );
        await expect(page.getByTestId("insights-languages")).toContainText(
          "41 / 48",
        );
        const escalation = page.getByTestId("insights-escalation");
        for (const value of [
          "49 / 53",
          "38 / 53",
          "15 / 53",
          "4 / 53",
          "11 / 47",
          "2 / 47",
          "7 / 98",
          "0 / 100",
        ])
          await expect(escalation).toContainText(value);
        await expect(page.locator(".insights-safety")).toContainText("4 / 100");
        await expect(page.locator(".insights-safety")).toContainText("0 / 30");
        await expect(page.locator(".insights-page")).toContainText(
          pt ? "0,0023" : "0.0023",
        );
        await expect(page.getByTestId("insights-progression")).toContainText(
          "65 / 200",
        );
        await expect(page.getByTestId("insights-progression")).toContainText(
          "77 / 100",
        );
        await expect(page.getByTestId("insights-progression")).toContainText(
          "88 / 100",
        );
        const bars = page.locator(".insights-page .evidence-chart");
        expect(await bars.count()).toBeGreaterThan(10);
        for (const bar of await bars.all()) {
          await expect(bar).toHaveAttribute("data-zero-based", "true");
          await expect(bar).toHaveAttribute("data-axis-max", "1");
          const values = await bar.locator("rect").evaluateAll((elements) =>
            elements.map((element) => ({
              x: Number(element.getAttribute("x")),
              width: Number(element.getAttribute("width")),
              value: Number(element.getAttribute("data-value")),
            })),
          );
          for (const mark of values) {
            expect(mark.x).toBe(0);
            expect(mark.width).toBeCloseTo(mark.value * 100);
          }
          for (let i = 1; i < values.length; i++)
            expect(values[i - 1].value).toBeGreaterThanOrEqual(values[i].value);
        }
        await page.getByTestId("insights-languages").scrollIntoViewIfNeeded();
        await review(page, `${name}-languages`);
      }
    });
  }
