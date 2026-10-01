import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { chmod, mkdir } from "node:fs/promises";
import { resolve, sep } from "node:path";
import type { Config } from "../src/lib/contracts";
import { planSchema } from "../src/lib/contracts";
import { opsSchema, traceSchema } from "../src/lib/staff-contracts";
import { multiReasonPacket, offerFixture } from "./fixtures/conversation-ui";

// Project-authored presentation fixtures only. No bank/evaluation rows or models.
function config(ptHint = false): Config {
  return {
    fixtures: false,
    bankClock: "2026-06-18T06:00:00Z",
    resetEnabled: false,
    personas: [
      {
        username: "demo.es.mx",
        label: "Authored ES",
        locale: "es-MX",
        role: "ops",
        demo_stories: ["explain", "fraud"],
      },
      {
        username: "demo.pt.br",
        label: "Authored PT",
        locale: "pt-BR",
        role: "ops",
        demo_stories: ptHint ? ["ambiguous"] : [],
      },
    ],
  };
}
async function bootstrap(
  page: Page,
  pt: boolean,
  signedIn: boolean,
  ptHint = false,
) {
  await page.route("**/api/bff/config", (r) =>
    r.fulfill({ json: config(ptHint) }),
  );
  await page.route("**/api/bff/me", (r) =>
    r.fulfill(
      signedIn
        ? {
            json: {
              username: pt ? "demo.pt.br" : "demo.es.mx",
              role: "ops",
              locale: pt ? "pt-BR" : "es-MX",
              bank_clock: "2026-06-18T06:00:00Z",
            },
          }
        : { status: 401, json: { error: "session_or_credentials_invalid" } },
    ),
  );
  await page.route("**/api/bff/chat/sessions", (r) =>
    r.fulfill({ json: { conversation_id: "CONV-UI-VIDEO" } }),
  );
  await page.goto("/?grabar=1");
  await expect(
    page.locator(signedIn ? ".composer" : ".login-panel"),
  ).toBeVisible();
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
  await expect(page.locator("html")).toHaveAttribute(
    "lang",
    pt ? "pt-BR" : "es-MX",
  );
}
async function audit(page: Page) {
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}
async function capture(page: Page, name: string) {
  const configured = process.env.FRONTEND_VIDEO_CAPTURE_DIR;
  if (!configured) return; // No screenshot artifacts in CI.
  const directory = resolve(configured);
  if (!directory.startsWith(resolve(process.cwd(), "../../artifacts") + sep))
    throw new Error("Capture path must be under ignored artifacts");
  await mkdir(directory, { recursive: true, mode: 0o700 });
  for (const fullPage of [false, true]) {
    const path = resolve(directory, name + (fullPage ? "-full" : "") + ".png");
    await page.screenshot({
      path,
      fullPage,
      mask: [
        page.locator("input[type=password]"),
        page.locator("input[autocomplete=username]"),
        page.locator("[data-testid=sms-code]"),
        page.locator("input[autocomplete=one-time-code]"),
      ],
    });
    await chmod(path, 0o600);
  }
}
for (const pt of [false, true]) {
  for (const width of [1440, 390]) {
    const prefix = `${pt ? "pt" : "es"}-${width}`;
    test(`${prefix}: Ops hints enable ES shortcuts, require authentication, and leave unbound PT disabled`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      let posts = 0;
      page.on("request", (r) => {
        if (r.method() === "POST") posts++;
      });
      await bootstrap(page, pt, false);
      await expect(page.getByTestId("quickstart-explain")).toBeEnabled();
      await expect(page.getByTestId("quickstart-fraud")).toBeEnabled();
      await expect(page.getByTestId("quickstart-ambiguous")).toBeDisabled();
      const shortcut = page.getByRole("button", {
        name: pt
          ? "Abrir ferramentas de gravação"
          : "Abrir herramientas de grabación",
        exact: true,
      });
      await expect(shortcut).toBeInViewport();
      await shortcut.click();
      const helper = page.locator(".recording-helper");
      await expect(helper).toHaveAttribute("open", "");
      await expect(helper.locator("summary")).toBeFocused();
      const explain = helper.getByRole("button", {
        name: pt ? "Entender cobrança · ES" : "Entender un cargo · ES",
        exact: true,
      });
      await expect(explain).toBeEnabled();
      await expect(
        helper.getByRole("button", {
          name: pt ? "Escolher compra · PT" : "Elegir una compra · PT",
          exact: true,
        }),
      ).toBeDisabled();
      await capture(page, prefix + "-helper");
      await explain.click();
      await expect(page.locator(".login-panel select")).toHaveValue(
        "demo.es.mx",
      );
      await expect(page.locator("input[type=password]")).toBeVisible();
      await expect(page.locator(".composer")).toHaveCount(0);
      expect(posts).toBe(0); // No login, OTP, message, confirmation or reset.
      await audit(page);
    });
    test(`${prefix}: authenticated hinted Ops persona only prepares a neutral draft`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      const mutations: string[] = [];
      page.on("request", (r) => {
        if (r.method() === "POST" && !r.url().endsWith("/chat/sessions"))
          mutations.push(r.url());
      });
      await bootstrap(page, pt, true, true);
      await page
        .getByTestId(pt ? "quickstart-ambiguous" : "quickstart-explain")
        .click();
      await expect(page.locator(".composer textarea")).toHaveValue(
        pt
          ? "Quero entender uma cobrança no meu cartão. Quais compras posso revisar?"
          : "Quiero entender un cargo en mi tarjeta.",
      );
      await expect(page.locator("input[type=password]")).toHaveCount(0);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      expect(mutations).toEqual([]);
      await capture(page, prefix + "-draft");
      await audit(page);
    });
    test(`${prefix}: live Desk uses wall deadlines and labels risk and missing packet details`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.clock.install({ time: new Date("2026-10-01T12:00:00Z") });
      await page.route("**/api/bff/agent/handoffs", (r) =>
        r.fulfill({
          json: [
            {
              ...multiReasonPacket,
              created_at: "2026-10-01T12:00:00Z",
              sla_due_at: "2026-10-16T12:00:00Z",
              actions: [],
              actions_taken: [],
              open_questions: [],
              risk_flags: ["fraud_review", "authored_unknown_flag"],
            },
          ],
        }),
      );
      await bootstrap(page, pt, true);
      await page.locator(".sidebar nav button").nth(1).click();
      const countdown = page.locator(".sla-countdown");
      await expect(countdown).toContainText("15d 0h 0m");
      await expect(page.locator(".packet-empty")).toHaveCount(3);
      await expect(page.locator(".packet-empty").nth(1)).toContainText(
        pt
          ? "O pacote não inclui ações verificadas"
          : "El paquete no incluye acciones verificadas",
      );
      await expect(page.locator(".timeline-check")).toHaveCount(0);
      await expect(page.locator(".packet-risks p")).toHaveText(
        pt
          ? "Análise de fraude · Outro indicador de análise"
          : "Revisión por fraude · Otro indicador de revisión",
      );
      await expect(
        page.getByText("fraud_review", { exact: true }),
      ).not.toBeVisible();
      await capture(page, prefix + "-desk");
      await page.locator(".packet-risks summary").click();
      await expect(
        page.getByText("fraud_review", { exact: true }),
      ).toBeVisible();
      await page.clock.fastForward(61000);
      await expect(countdown).toContainText("14d 23h 59m");
      await audit(page);
    });
    test(`${prefix}: zero-call traces disclose absence of a model-cost measurement`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      const trace = traceSchema.parse({
        conversation_id: "CONV-UI-VIDEO",
        policy_version: "ui-policy",
        scope: "current_workspace",
        events: [
          {
            id: "UI-HANDOFF:0",
            stage: "Escalate",
            state: "create_handoff",
            tool: null,
            rules: ["FRD-01"],
            verified: false,
            llm: null,
          },
          {
            id: "UI-READBACK:0",
            stage: "Verify",
            state: "verify_readback",
            tool: "verify_readback",
            rules: [],
            verified: true,
            llm: null,
          },
        ],
      });
      const snapshot = opsSchema.parse({
        dataset_version: "authored-ui-video",
        bank_clock: "2026-06-18T06:00:00Z",
        loaded_at: "2026-06-18T06:00:00Z",
        source_as_of: "2026-06-18T06:00:00Z",
        source_kind: "authored_fixture",
        scope: "current_workspace",
        quality: [],
        metrics: {
          source: "current_workspace_operations",
          cases: 0,
          handoffs: 1,
          conversations: 1,
          execution_records: 2,
          observed_model_cost_usd: 0,
          sar: null,
          unsafe_rate: null,
          note: "Authored UI metadata",
        },
        conversation_ids: [trace.conversation_id],
      });
      await page.route("**/api/bff/ops/snapshot", (r) =>
        r.fulfill({ json: snapshot }),
      );
      await page.route("**/api/bff/chat/sessions/*/trace", (r) =>
        r.fulfill({ json: trace }),
      );
      await bootstrap(page, pt, true);
      await page.locator(".sidebar nav button").nth(2).click();
      const cost = page.locator(".conversation-cost");
      await expect(cost.locator("strong")).toHaveText(
        pt
          ? "Sem chamadas ao modelo registradas"
          : "Sin llamadas al modelo registradas",
      );
      await expect(cost).toContainText(
        pt
          ? "Este registro não mede um custo de modelo"
          : "Esta traza no mide un costo de modelo",
      );
      await expect(cost).toContainText(
        pt
          ? "Este registro não inclui julgamentos de risco do modelo"
          : "Esta traza no incluye juicios de riesgo del modelo",
      );
      await expect(cost).not.toContainText("USD");
      await expect(page.locator(".execution-list .badge")).toContainText(
        "Verificado",
      );
      await capture(page, prefix + "-ops");
      await audit(page);
    });
  }
  test(`${pt ? "PT" : "ES"}: missing and numeric merchants stay honest; numbered choices only send text`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const transactions = [null, "—", "123"].map((merchant, i) => ({
      ...offerFixture(pt).transaction!,
      handle: `txn_ui_video_${i}`,
      merchant,
    }));
    const requests: string[] = [];
    let confirms = 0;
    page.on("request", (r) => {
      if (r.url().endsWith("/confirm")) confirms++;
    });
    await page.route("**/api/bff/chat/sessions/*/messages", (r) => {
      requests.push(r.request().postDataJSON().message);
      return r.fulfill({
        json: planSchema.parse(
          requests.length === 1
            ? {
                response_type: "choose_transaction",
                outcome: "choose_transaction",
                reply: pt ? "Escolha um movimento." : "Elige un movimiento.",
                candidates: transactions,
              }
            : {
                response_type: "explain_status",
                outcome: "explained",
                reply: pt
                  ? "Confira o status registrado."
                  : "Revisa el estado registrado.",
                transaction: transactions[0],
              },
        ),
      });
    });
    await bootstrap(page, pt, true);
    await page
      .locator(".composer textarea")
      .fill(
        pt
          ? "Quero revisar um movimento de teste."
          : "Quiero revisar un movimiento de prueba.",
      );
    await page.locator(".composer button[type=submit]").click();
    const cards = page.locator(".candidate-grid article");
    await expect(cards.locator(".choice-number")).toHaveText(
      pt
        ? ["Movimento 1", "Movimento 2", "Movimento 3"]
        : ["Movimiento 1", "Movimiento 2", "Movimiento 3"],
    );
    await expect(cards.locator("h3")).toHaveText([
      pt ? "Estabelecimento não informado" : "Comercio no informado",
      pt ? "Estabelecimento não informado" : "Comercio no informado",
      "123",
    ]);
    await expect(page.locator(".candidate-grid")).not.toContainText(
      "txn_ui_video",
    );
    await capture(page, `${pt ? "pt" : "es"}-390-choices`);
    await cards.first().getByRole("button").click();
    await expect(page.locator(".chooser")).toHaveCount(0);
    expect(requests).toHaveLength(2);
    expect(requests[1]).toBe(pt ? "o primeiro" : "el primero");
    expect(confirms).toBe(0);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await audit(page);
  });
}
