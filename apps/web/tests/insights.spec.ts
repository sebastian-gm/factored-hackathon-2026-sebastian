import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import snapshot from "../src/data/insights.json";
import { insightsResultsSchema } from "../src/lib/insights-results";
import { proposalFixture } from "./fixtures/conversation-ui";

// Presentation-only aggregates invented for publication-state tests. This is
// neither a held-out scenario nor a result from a system run.
const publicationFixture = {
  schema_version: 1,
  version: "v4",
  status: "partial",
  source: {
    path: "docs/evaluation/example-aggregate.json",
    commit: "b".repeat(40),
    sha256: "c".repeat(64),
  },
  systems: {
    B1: {
      pass: { count: 5, denominator: 10 },
      sar: { count: 2, denominator: 10 },
    },
    P: {
      pass: { count: 7, denominator: 10 },
      sar: { count: 4, denominator: 10 },
    },
  },
  sar_difference_pp: { estimate: 20, ci95: [-10, 40] },
  unauthorized_actions: { count: 0, denominator: 10 },
  safety_gate: "failed",
};
const auditDir = path.resolve(
  process.cwd(),
  "../../artifacts/ux-audit/insights",
);
async function capture(page: Page, name: string) {
  await mkdir(auditDir, { recursive: true });
  await page.screenshot({
    path: path.join(auditDir, `${name}-full.png`),
    fullPage: true,
  });
  await page.screenshot({ path: path.join(auditDir, `${name}-viewport.png`) });
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
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
}
async function open(page: Page, pt = false) {
  await page.goto("/insights");
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
  await expect(page.locator(".insights-hero")).toBeVisible();
}
async function login(page: Page) {
  await page.goto("/");
  await page.locator(".login-panel select").selectOption("demo.es.mx");
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
  await page
    .locator("input[autocomplete=one-time-code]")
    .fill((await page.getByTestId("sms-code").textContent())!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.locator(".composer textarea")).toBeVisible();
}

test("snapshot regenerates from committed aggregate sources without reading rows or running a system", () => {
  execFileSync(
    process.execPath,
    ["scripts/build-insights-snapshot.mjs", "--check"],
    { stdio: "pipe" },
  );
  expect(snapshot.sources).toHaveLength(11);
});
test("future results require aggregate denominators and provenance; row fields, invalid intervals and fake pending metrics fail closed", () => {
  expect(insightsResultsSchema.safeParse(publicationFixture).success).toBe(
    true,
  );
  for (const data of [
    { ...publicationFixture, rows: [] },
    {
      ...publicationFixture,
      source: { ...publicationFixture.source, path: "artifacts/private.json" },
    },
    { ...publicationFixture, unauthorized_actions: { count: 0 } },
    {
      ...publicationFixture,
      unauthorized_actions: { count: 11, denominator: 10 },
    },
    {
      ...publicationFixture,
      sar_difference_pp: { estimate: 20, ci95: [30, 40] },
    },
    {
      schema_version: 1,
      version: "v4",
      status: "pending",
      systems: publicationFixture.systems,
    },
  ])
    expect(insightsResultsSchema.safeParse(data).success).toBe(false);
});
for (const pt of [false, true])
  for (const width of [1440, 390]) {
    const name = `${pt ? "pt" : "es"}-${width}`;
    test(`${name}: read-only story, rounded data, citations, honest v3 safety and pending v4; accessible screenshots`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      const writes: string[] = [],
        errors: string[] = [];
      page.on("request", (r) => {
        if (!["GET", "HEAD"].includes(r.method())) writes.push(r.url());
      });
      page.on("pageerror", (e) => errors.push(e.message));
      await open(page, pt);
      await expect(page.locator(".insights-hero-stat strong")).toHaveText(
        pt ? "43,6%" : "43.6%",
      );
      await expect(page.locator(".insights-problem-grid")).toContainText(
        pt ? "17,1%" : "17.1%",
      );
      await expect(page.locator(".insights-problem-grid")).toContainText(
        pt ? "23,1%" : "23.1%",
      );
      await expect(page.locator(".insights-problem-grid")).toContainText(
        pt ? "12.297" : "12,297",
      );
      const comparison = page.getByTestId("insights-comparison");
      await expect(comparison).toContainText("77 / 100");
      await expect(comparison).toContainText("52 / 100");
      await expect(comparison).toContainText("+11 pp");
      await expect(comparison).toContainText("+5 → +17 pp");
      await expect(page.locator(".insights-safety")).toContainText("0 / 100");
      await expect(page.locator(".insights-safety")).toContainText("· v3");
      await expect(page.locator(".insights-safety")).toContainText("0 / 30");
      await expect(
        page.locator(".insights-safety .insights-caution"),
      ).toContainText(pt ? "não passou" : "no pasó");
      await expect(page.getByTestId("insights-v4")).toContainText(
        pt ? "Pendente" : "Pendiente",
      );
      await expect(page.getByTestId("insights-v4")).not.toContainText("0%");
      await expect(page.locator(".insights-sources li")).toHaveCount(
        snapshot.sources.length,
      );
      for (const source of snapshot.sources) {
        const link = page.locator(`#insights-source-${source.id} > a`);
        await expect(link).toHaveAttribute(
          "href",
          `https://github.com/sebastian-gm/bank-agent-lab/blob/${source.commit}/${source.path}`,
        );
      }
      await expect(page.locator(".recording-helper")).toHaveCount(0);
      await capture(page, `${name}-overview`);
      await page.getByRole("button", { name: /v2 ·/ }).click();
      await expect(comparison).toContainText(pt ? "32,5%" : "32.5%");
      await expect(comparison).toContainText(pt ? "31,5%" : "31.5%");
      await expect(comparison).toContainText(pt ? "-1,04 pp" : "-1.04 pp");
      await capture(page, `${name}-v2`);
      await page.getByRole("tab", { name: /Entender/ }).focus();
      await page.keyboard.press("ArrowRight");
      await page.keyboard.press("ArrowRight");
      await expect(
        page.getByRole("tab", { name: pt ? "Agir Act" : "Actuar Act" }),
      ).toBeFocused();
      await expect(page.getByRole("tabpanel")).toContainText(
        pt ? "confirmação" : "confirmación",
      );
      await page
        .getByRole("button", {
          name: pt ? "Consultas originais" : "Consultas originales",
          exact: true,
        })
        .click();
      await expect(page.getByTestId("insights-matcher")).toContainText("13 / ");
      await capture(page, `${name}-matcher-original`);
      await page
        .locator(".insights-ref[href='#insights-source-demand']")
        .first()
        .click();
      await page.locator("#insights-source-demand summary").click();
      await expect(
        page.locator("#insights-source-demand code").first(),
      ).toHaveText(snapshot.sources[0].sha256);
      await capture(page, `${name}-sources`);
      await page.locator(".insights-lineage summary").click();
      const lineage = page.locator(".insights-lineage img");
      await expect(lineage).toBeVisible();
      await expect
        .poll(() =>
          lineage.evaluate(
            (element: HTMLImageElement) =>
              element.complete && element.naturalWidth > 0,
          ),
        )
        .toBe(true);
      await capture(page, `${name}-lineage`);
      expect(writes).toEqual([]);
      expect(errors).toEqual([]);
    });
    test(`${name}: future aggregate publication and errors stay separate from historical evidence`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      let state: "error" | "invalid" | "published" = "error";
      await page.route("**/insights-results.json", (r) =>
        state === "error"
          ? r.fulfill({ status: 503, body: "Unavailable" })
          : r.fulfill({
              json:
                state === "invalid"
                  ? { ...publicationFixture, rows: [] }
                  : publicationFixture,
            }),
      );
      await open(page, pt);
      const v4 = page.getByTestId("insights-v4");
      await expect(v4.getByRole("alert")).toBeVisible();
      await expect(v4).not.toContainText("7 / 10");
      await expect(page.getByTestId("insights-comparison")).toContainText(
        "77 / 100",
      );
      await capture(page, `${name}-publication-error`);
      state = "invalid";
      await v4.getByRole("button").click();
      await expect(v4.getByRole("alert")).toBeVisible();
      state = "published";
      await v4.getByRole("button").click();
      await expect(v4).toContainText("7 / 10");
      await expect(v4).toContainText("5 / 10");
      await expect(v4).toContainText(
        pt ? "Publicação parcial" : "Publicación parcial",
      );
      await expect(v4).toContainText(pt ? "não aprovada" : "no aprobada");
      await capture(page, `${name}-publication-example`);
    });
  }
test("Insights keeps a pending proposal and draft, and history navigation never confirms a write or changes identity", async ({
  page,
}) => {
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({ json: proposalFixture(false) }),
  );
  await login(page);
  await page.locator(".composer textarea").fill("Mi borrador sin enviar");
  await page.locator(".sidebar nav button").last().click();
  await expect(page.locator(".insights-hero")).toBeVisible();
  await page
    .getByRole("button", { name: "Probar Aclara", exact: true })
    .click();
  await expect(page.locator(".composer textarea")).toHaveValue(
    "Mi borrador sin enviar",
  );
  await page
    .locator(".composer textarea")
    .fill("Revisar una compra de ejemplo.");
  await page.locator(".composer button[type=submit]").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") writes.push(r.url());
  });
  await page.locator(".sidebar nav button").last().click();
  await expect(page).toHaveURL(/\/insights$/);
  await expect(page.locator(".insights-hero")).toBeVisible();
  await page.goBack();
  await expect(page.locator(".composer textarea")).toBeDisabled();
  await expect(page.locator(".proposal-bar")).toBeVisible();
  await page.goForward();
  await expect(page.locator(".insights-hero")).toBeVisible();
  await page
    .getByRole("button", { name: "Probar Aclara", exact: true })
    .click();
  await expect(page.locator(".proposal-bar")).toBeVisible();
  await expect(page.locator(".composer textarea")).toBeDisabled();
  expect(writes).toEqual([]);
});
test("quickstart opens Insights; direct authenticated Insights does not create a conversation", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Conoce los datos/ }).click();
  await expect(page).toHaveURL(/\/insights$/);
  await login(page);
  let created = 0;
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/chat/sessions")) created++;
  });
  await open(page);
  await expect(page.getByTestId("insights-v4")).toContainText("Pendiente");
  await expect(page.locator(".chat-panel")).toHaveCount(0);
  expect(created).toBe(0);
});
test("aggregate Insights remains available during bank cold start and failure; publication loading is explicit", async ({
  page,
}) => {
  let release!: () => void;
  const wait = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/config", async (r) => {
    await wait;
    await r.fulfill({ status: 503, body: "Unavailable" });
  });
  await page.route("**/insights-results.json", async (r) => {
    await wait;
    await r.fulfill({
      json: { schema_version: 1, version: "v4", status: "pending" },
    });
  });
  await open(page);
  await expect(page.getByTestId("insights-v4").getByRole("status")).toHaveText(
    "Consultando la publicación de v4…",
  );
  await expect(page.locator(".insights-hero-stat")).toContainText("43.6%");
  release();
  await expect(page.getByTestId("insights-v4")).toContainText("Pendiente");
  await expect(page.locator(".insights-hero-stat")).toContainText("43.6%");
  await page
    .getByRole("button", { name: "Probar Aclara", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "El servicio aún no está disponible. Vuelve a intentarlo.",
    }),
  ).toBeVisible();
});
