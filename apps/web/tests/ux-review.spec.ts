import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { offerFixture, multiReasonPacket } from "./fixtures/conversation-ui";

// Authored presentation fixtures only; no evaluation rows or policy execution.
async function login(page: Page, pt: boolean, agent = false, persona?: string) {
  await page.goto("/");
  if (agent) await page.locator(".sidebar nav button").nth(1).click();
  await page
    .locator(".login-panel select")
    .selectOption(
      persona ?? (agent ? "demo.agent" : pt ? "demo.pt.br" : "demo.es.mx"),
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
    page.locator(agent ? ".desk-grid" : ".chat-panel"),
  ).toBeVisible();
}
async function rail(page: Page) {
  const bounds = await page.locator(".sidebar").boundingBox();
  expect(bounds?.x).toBe(0);
  expect(bounds?.y).toBe(0);
  expect(bounds?.height).toBe(page.viewportSize()!.height);
}

for (const pt of [false, true]) {
  for (const width of [1440, 390]) {
    test(`${pt ? "PT" : "ES"} ${width}: skip link is a focus-only overlay and moves focus to content without shifting layout`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.goto("/");
      await expect(page.locator(".login-panel")).toBeVisible();
      await page
        .locator(".locale-select select")
        .selectOption(pt ? "pt-BR" : "es-MX");
      const link = page.locator(".skip-link");
      await expect(link).toHaveCSS("position", "absolute");
      await expect(link).toHaveCSS("clip-path", "inset(50%)");
      const before = await page.locator(".sidebar").boundingBox();
      // Use real tab navigation, including from an otherwise unfocused page.
      await page.evaluate(() => {
        document.body.tabIndex = -1;
        document.body.focus();
        document.body.removeAttribute("tabindex");
      });
      await page.keyboard.press("Control+Home");
      await page.keyboard.press("Tab");
      await expect(link).toBeFocused();
      await expect(link).toHaveCSS("clip-path", "none");
      expect(await page.locator(".sidebar").boundingBox()).toEqual(before);
      await page.keyboard.press("Enter");
      await expect(page.locator("#main-content")).toBeFocused();
      await expect(link).toHaveCSS("clip-path", "inset(50%)");
      if (width === 1440) {
        await rail(page);
        await page.evaluate(() =>
          window.scrollTo(0, document.body.scrollHeight),
        );
        await rail(page);
      }
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
    });
  }
  test(`${pt ? "PT" : "ES"}: offers and multi-reason Desk packets keep the rail at the viewport top after scrolling`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.route("**/chat/sessions/*/messages", (r) =>
      r.fulfill({ json: offerFixture(pt) }),
    );
    await login(page, pt);
    await page
      .locator(".composer textarea")
      .fill(
        pt
          ? "Quero revisar esta compra de teste."
          : "Quiero revisar esta compra de prueba.",
      );
    await page.locator(".composer button[type=submit]").click();
    await expect(page.locator(".recognition-actions")).toBeVisible();
    await rail(page);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await rail(page);
    await page
      .getByRole("button", { name: pt ? "Sair" : "Cerrar sesión", exact: true })
      .click();
    await page.route("**/agent/handoffs", (r) =>
      r.fulfill({ json: [multiReasonPacket] }),
    );
    await login(page, pt, true);
    await page.locator(".queue-item").click();
    // Authored fixture deadlines keep their bank-clock basis even when the
    // workstation is months later; the live-clock correction must not alter it.
    await expect(page.locator(".sla-countdown")).toContainText("6h 0m");
    await rail(page);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await rail(page);
    await expect(page.locator(".skip-link")).toHaveCSS(
      "clip-path",
      "inset(50%)",
    );
  });
  test(`${pt ? "PT" : "ES"}: Desk localizes all five reasons, attaches the primary label, and keeps action references secondary`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/agent/handoffs", (r) =>
      r.fulfill({
        json: [
          {
            ...multiReasonPacket,
            reason_codes: [
              "AUTH-02",
              "ESC-02",
              "ESC-03",
              "ESC-01",
              "FRD-01",
              "FUTURE-99",
            ],
            actions: [
              ...multiReasonPacket.actions,
              {
                action: "freeze_card",
                status: "failed",
                evidence_ref: "UI-UNVERIFIED",
              },
            ],
          },
        ],
      }),
    );
    await login(page, pt, true);
    const reasons = page.locator(".handoff-reasons");
    await expect(reasons.locator("li strong")).toHaveText(
      pt
        ? [
            "Fraude / cartão",
            "Verificação reforçada necessária",
            "Reclamação regulatória ou jurídica",
            "Angústia expressa",
            "Pediu atendimento humano",
            "Outro motivo indicado pelo serviço",
          ]
        : [
            "Fraude / tarjeta",
            "Verificación reforzada requerida",
            "Queja regulatoria o legal",
            "Angustia expresada",
            "Pidió una persona",
            "Otro motivo indicado por el servicio",
          ],
    );
    await expect(reasons.locator("li.primary")).toHaveCount(1);
    await expect(reasons.locator("li.primary .reason-kind")).toHaveText(
      "Motivo principal",
    );
    await expect(reasons.locator("li.primary code")).toHaveText("FRD-01");
    const verified = page.locator(".action-timeline li").first();
    await expect(verified.locator("strong")).toHaveText(
      pt ? "Encaminhamento criado" : "Derivación creada",
    );
    await expect(verified.locator(".badge")).toHaveText(
      pt ? "Verificado nos registros" : "Verificado en registros",
    );
    await expect(
      verified.getByText("create_handoff", { exact: true }),
    ).toBeHidden();
    await verified.locator("summary").click();
    await expect(
      verified.getByText("create_handoff", { exact: true }),
    ).toBeVisible();
    await expect(
      verified.getByText("UI-HANDOFF-READBACK", { exact: true }),
    ).toBeVisible();
    const failed = page.locator(".action-timeline li").last();
    await expect(failed.locator("strong")).toHaveText(
      pt ? "Tentativa de bloqueio do cartão" : "Intento de bloqueo de tarjeta",
    );
    await expect(
      failed.locator(".timeline-check.failed[data-status=failed]"),
    ).toBeVisible();
    await expect(failed.locator(".badge")).not.toContainText(
      pt ? "Verificado nos registros" : "Verificado en registros",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
    ).toBe(false);
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
  });
  test(`${pt ? "PT" : "ES"}: recording tools are hidden by default and require the exact opt-in flag`, async ({
    page,
  }) => {
    await login(page, pt);
    await expect(page.locator(".recording-helper")).toHaveCount(0);
    await page.goto("/?grabar=0");
    await expect(page.locator(".chat-panel")).toBeVisible();
    await expect(page.locator(".recording-helper")).toHaveCount(0);
    await page.goto("/?grabar=1");
    // The locale select exists in server HTML. Restored chat proves the
    // bootstrap completed and its change handler is attached after navigation.
    await expect(page.locator(".chat-panel")).toBeVisible();
    await page
      .locator(".locale-select select")
      .selectOption(pt ? "pt-BR" : "es-MX");
    await expect(page.locator(".locale-select select")).toHaveValue(
      pt ? "pt-BR" : "es-MX",
    );
    await expect(page.locator(".recording-helper")).toBeVisible();
    await page.locator(".recording-helper summary").click();
    // Opt-in does not grant the customer operations authority.
    await expect(
      page.getByRole("button", {
        name: pt
          ? "Entrar em operações para redefinir"
          : "Entrar en operaciones para restablecer",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", {
        name: pt ? "Redefinir demo e abrir ES" : "Restablecer demo y abrir ES",
        exact: true,
      }),
    ).toHaveCount(0);
    await page.goto("/");
    await expect(page.locator(".chat-panel")).toBeVisible();
    await expect(page.locator(".recording-helper")).toHaveCount(0);
  });
}
test("Mexico native fixtures display USD; Portuguese-speaking Mexico fixtures also display USD", async ({
  page,
}) => {
  await login(page, false);
  await page
    .locator(".composer textarea")
    .fill("¿Qué es el cargo de Café Horizonte?");
  await page.locator(".composer button[type=submit]").click();
  await expect(page.getByText(/USD\s*185\.00/)).toBeVisible();
  await expect(page.getByText(/MXN/)).toHaveCount(0);
  expect(offerFixture(true).transaction?.currency).toBe("USD");
  expect(offerFixture(false).transaction?.currency).toBe("USD");
});

for (const [persona, currency] of [
  ["demo.es.co", "COP"],
  ["demo.es.ar", "ARS"],
])
  for (const pt of [false, true]) {
    test(`${persona} in ${pt ? "PT" : "ES"}: ledger and charge choices retain country currency ${currency}`, async ({
      page,
    }) => {
      await login(page, pt, false, persona);
      await page
        .locator(".composer textarea")
        .fill(
          pt
            ? "Não reconheço uma compra de cerca de 90 pesos."
            : "No reconozco una compra de unos 90 pesos.",
        );
      await page.locator(".composer button[type=submit]").click();
      await expect(page.locator(".candidate-grid article")).toHaveCount(3);
      for (const card of await page.locator(".candidate-grid article").all()) {
        await expect(card).toContainText(currency);
        await expect(card).not.toContainText("USD");
      }
      await page
        .locator(".locale-select select")
        .selectOption(pt ? "es-CO" : "pt-BR");
      for (const card of await page.locator(".candidate-grid article").all())
        await expect(card).toContainText(currency);
    });
  }
