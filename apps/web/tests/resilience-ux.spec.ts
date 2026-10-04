import { test, expect, type Page } from "./helpers/test";
import { selectLoginPersona } from "./helpers/login-persona";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, chmod } from "node:fs/promises";
import { offerFixture, multiReasonPacket } from "./fixtures/conversation-ui";
import { planSchema } from "../src/lib/contracts";

async function login(page: Page, pt: boolean, agent = false) {
  await page.goto("/");
  if (agent)
    await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  if (agent) await selectLoginPersona(page, "demo.agent");
  if (pt) {
    if (!agent) await selectLoginPersona(page, "demo.pt.br");
    await page
      .getByLabel(/Idioma y región|Idioma e região/)
      .selectOption("pt-BR");
  }
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  const sms = page.getByTestId("sms-code");
  await expect(sms).toHaveText(/^\d{6}$/);
  await page
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await sms.textContent())!);
  await page
    .getByRole("button", {
      name: pt ? "Verificar e entrar" : "Verificar y entrar",
    })
    .click();
  if (!agent) await expect(page.locator("#message")).toBeVisible();
}
async function send(page: Page, pt: boolean, text = "Consulta de interfaz") {
  await page.locator("#message").fill(text);
  await page
    .getByRole("button", { name: pt ? "Enviar mensagem" : "Enviar mensaje" })
    .click();
}
async function capture(page: Page, name: string) {
  if (process.env.FRONTEND_RESILIENCE_CAPTURE !== "1") return;
  const directory = "../../artifacts/ux-audit/web-resilience";
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const path = `${directory}/${name}.png`;
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path,
    fullPage: true,
    mask: [page.locator("input[type=password]"), page.getByTestId("sms-code")],
  });
  await chmod(path, 0o600);
}
async function audit(page: Page) {
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}

test("only an explicit boolean degraded flag is projected; no failure details or inferred text", () => {
  const plan = planSchema.parse({
    ...offerFixture(false),
    degraded: true,
    failure_detail: "private diagnostic",
  });
  expect(plan.degraded).toBe(true);
  expect(plan).not.toHaveProperty("failure_detail");
  expect(
    planSchema.parse({ ...offerFixture(false), degraded: false }).degraded,
  ).toBe(false);
  expect(planSchema.parse(offerFixture(false)).degraded).toBeUndefined();
  expect(
    planSchema.safeParse({ ...offerFixture(false), degraded: "true" }).success,
  ).toBe(false);
});

for (const pt of [false, true]) {
  for (const width of [1440, 390]) {
    test(`${pt ? "PT" : "ES"} ${width}: healthy and basic modes preserve the offer and inline verified receipt`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 900 });
      await login(page, pt);
      await page.route("**/api/bff/config", async (route) => {
        const config = await (await route.fetch()).json();
        await route.fulfill({ json: { ...config, fixtures: false } });
      });
      await page.reload();
      await expect(page.locator("#message")).toBeVisible();
      if (pt)
        await page
          .getByLabel(/Idioma y región|Idioma e região/)
          .selectOption("pt-BR");
      let turn = 0;
      await page.route("**/chat/sessions/*/messages", (route) => {
        const current = turn++;
        return route.fulfill({
          json:
            current === 3
              ? {
                  response_type: "report_case",
                  outcome: "dispute_filed",
                  reply: pt ? "Pedido registrado." : "Solicitud registrada.",
                  verified: true,
                  case: {
                    case_id: "CASE-UI-RESILIENCE",
                    transaction_handle: offerFixture(pt).transaction!.handle,
                    status: "received",
                    created_at: "2026-06-18T06:00:00Z",
                    policy_rules: ["DSP-01"],
                  },
                }
              : {
                  ...offerFixture(pt),
                  ...(current === 0
                    ? { degraded: false, reply: "Modo básico" }
                    : current === 1
                      ? { degraded: true }
                      : {}),
                },
        });
      });
      await send(page, pt);
      const notice = page.getByTestId("basic-mode");
      await expect(page.locator(".chat-line.aclara")).toHaveCount(1);
      await expect(page.getByRole("log")).toContainText("Modo básico");
      await expect(notice).toHaveCount(0);
      await expect(page.locator(".transaction-card")).toBeVisible();
      await expect(page.locator(".transaction-top p")).toHaveCount(0);
      await expect(page.locator(".turn-stage")).toHaveCount(0);
      await send(page, pt);
      await expect(notice).toHaveText(
        pt
          ? "Modo básico · Você pode continuar sua consulta."
          : "Modo básico · Puedes seguir con tu consulta.",
      );
      await expect(notice).toHaveAttribute("role", "status");
      await expect(
        page.getByRole("region", {
          name: pt
            ? "Você reconhece este movimento?"
            : "¿Reconoces este movimiento?",
        }),
      ).toBeVisible();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.locator("#message")).toBeEditable();
      await audit(page);
      await capture(page, `${pt ? "pt" : "es"}-${width}-basic-mode`);
      await send(page, pt);
      await expect(page.locator(".chat-line.aclara")).toHaveCount(3);
      await expect(notice).toHaveCount(0);
      await send(page, pt);
      const verification = page.locator(".receipt-verification");
      await expect(verification).toBeVisible();
      await expect(verification.locator("span")).toHaveText("Verificado");
      expect(
        await verification.evaluate((node) => {
          const icon = node.querySelector("svg")!.getBoundingClientRect();
          const label = node.querySelector("span")!.getBoundingClientRect();
          return (
            icon.width > 0 &&
            label.width > 0 &&
            icon.right <= label.left &&
            Math.abs(
              icon.top + icon.height / 2 - label.top - label.height / 2,
            ) < 2
          );
        }),
      ).toBe(true);
      await expect(notice).toHaveCount(0);
      await expect(page.locator(".turn-stage")).toHaveCount(0);
      await audit(page);
    });

    test(`${pt ? "PT" : "ES"} ${width}: Desk names the customer's workspace, never a bank-wide staff queue`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.route("**/agent/handoffs", (route) =>
        route.fulfill({ json: [multiReasonPacket] }),
      );
      await login(page, pt, true);
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(
        pt ? "Atendimento com contexto." : "Atención con contexto.",
      );
      await expect(
        page.getByRole("heading", {
          name: pt
            ? "Encaminhamentos deste espaço"
            : "Derivaciones de este espacio",
          exact: true,
        }),
      ).toBeVisible();
      await expect(
        page.getByText(
          pt
            ? "Somente os encaminhamentos do seu espaço de cliente. Não é uma fila de outros clientes do banco."
            : "Solo las derivaciones de tu espacio de cliente. No es una cola de otros clientes del banco.",
          { exact: true },
        ),
      ).toBeVisible();
      await audit(page);
      await capture(page, `${pt ? "pt" : "es"}-${width}-workspace-desk`);
    });
  }

  test(`${pt ? "PT" : "ES"}: expiry clears both owner tabs, drafts and receipts before re-login; no replay`, async ({
    page,
    context,
  }) => {
    await login(page, pt);
    await send(page, pt, "Consulta previa de prueba");
    await expect(page.getByRole("log").locator(".aclara")).toHaveCount(1);
    const tab = await context.newPage();
    await tab.goto("/");
    if (pt)
      await tab
        .getByLabel(/Idioma y región|Idioma e região/)
        .selectOption("pt-BR");
    await tab.locator("#message").fill("Borrador privado de prueba");
    let writes = 0;
    page.on("request", (request) => {
      if (/\/(confirm|freeze)$/.test(request.url())) writes++;
    });
    // A missing expired cookie produces a real BFF 401; no bearer is read or logged.
    await context.clearCookies({ name: "aclara_access" });
    await send(page, pt, "Consulta posterior de prueba");
    for (const current of [page, tab]) {
      await expect(current.locator("input[type=password]")).toBeVisible();
      await expect(current.locator("input[type=password]")).toHaveValue("");
      await expect(
        current
          .getByRole("alert")
          .filter({ hasText: pt ? "Sua sessão expirou" : "Tu sesión venció" }),
      ).toBeVisible();
      await expect(current.locator("#message")).toHaveCount(0);
      await expect(current.getByRole("log")).toHaveCount(0);
      await expect(current.getByRole("dialog")).toHaveCount(0);
      await expect(current.getByTestId("sms-code")).toHaveCount(0);
      expect(
        await current.evaluate(() =>
          Object.values(localStorage).some((value) =>
            value.includes("Borrador privado de prueba"),
          ),
        ),
      ).toBe(false);
    }
    expect(writes).toBe(0);
    await audit(page);
    await capture(page, `${pt ? "pt" : "es"}-session-expired`);
    await tab.close();
    await page.reload();
    await expect(page.locator("input[type=password]")).toBeVisible();
    await expect(page.locator("#message")).toHaveCount(0);
  });

  test(`${pt ? "PT" : "ES"}: session-ended response clears stale chat and requests a fresh login`, async ({
    page,
  }) => {
    await login(page, pt);
    await page.route("**/chat/sessions/*/messages", (route) =>
      route.fulfill({
        headers: {
          "Set-Cookie":
            "aclara_access=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict",
        },
        json: {
          response_type: "refuse",
          outcome: "refused_security",
          reply: pt ? "Entre novamente." : "Vuelve a acceder.",
          session_ended: true,
          verified: false,
        },
      }),
    );
    await send(page, pt);
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: pt ? "Sua sessão expirou" : "Tu sesión venció" }),
    ).toBeVisible();
    await expect(page.locator("input[type=password]")).toHaveValue("");
    await expect(page.getByRole("log")).toHaveCount(0);
  });

  test(`${pt ? "PT" : "ES"}: expired login challenge clears the old SMS and submitted OTP`, async ({
    page,
  }) => {
    await page.goto("/");
    if (pt) await page.getByLabel("Idioma y región").selectOption("pt-BR");
    await page
      .locator("input[type=password]")
      .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
    await page.getByRole("button", { name: "Continuar", exact: true }).click();
    await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
    await page.route("**/auth/otp/verify", (route) =>
      route.fulfill({ status: 401, json: { error: "challenge_expired" } }),
    );
    await page
      .getByRole("textbox", { name: "Código de 6 dígitos" })
      .fill("000000");
    await page
      .getByRole("button", {
        name: pt ? "Verificar e entrar" : "Verificar y entrar",
      })
      .click();
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: pt ? "O código expirou" : "El código venció" }),
    ).toBeVisible();
    await expect(page.locator("input[type=password]")).toHaveValue("");
    await expect(page.getByTestId("sms-code")).toHaveCount(0);
    await expect(page.locator("input[autocomplete=one-time-code]")).toHaveCount(
      0,
    );
  });
}
