import { mkdirSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { test, expect, type Page } from "./helpers/test";
import { selectLoginPersona } from "./helpers/login-persona";
import { multiReasonPacket, offerFixture } from "./fixtures/conversation-ui";

async function login(page: Page, username: string, pt = false) {
  await page.goto("/");
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
  if (username === "demo.agent")
    await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await selectLoginPersona(page, username);
  await page
    .locator("input[autocomplete=current-password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
  await page
    .locator("input[autocomplete=one-time-code]")
    .fill((await page.getByTestId("sms-code").textContent())!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(
    page.locator(username === "demo.agent" ? ".desk-grid" : ".chat-panel"),
  ).toBeVisible();
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
}
async function invitation(page: Page) {
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await page.locator(".login-panel > button").click();
  const field = page.getByRole("dialog").locator("input[type=password]");
  await expect(field).not.toHaveValue("");
  await audit(page);
  const value = await field.inputValue();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /Cerrar|Fechar/ })
    .click();
  await expect(field).toHaveCount(0);
  return value;
}
async function connect(page: Page, value: string) {
  const access = page.locator(".staff-realm-access");
  if (
    !(await access.evaluate((element) => (element as HTMLDetailsElement).open))
  )
    await access.locator("summary").click();
  await access.locator("input").fill(value);
  await access.locator("button[type=submit]").click();
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
  if (page.viewportSize()!.width >= 1024) {
    const rail = await page.locator(".sidebar").boundingBox();
    expect(rail?.y).toBe(0);
    expect(rail?.height).toBe(page.viewportSize()!.height);
  }
}

async function capture(page: Page, name: string) {
  // Full-page captures otherwise place a fixed rail at the current scroll offset.
  await page.evaluate(() => window.scrollTo(0, 0));
  mkdirSync("../../artifacts/ux-audit/staff-realm", { recursive: true });
  await page.screenshot({
    path: `../../artifacts/ux-audit/staff-realm/${name}.png`,
    fullPage: true,
  });
}

for (const pt of [false, true])
  for (const width of [1440, 390]) {
    test(`${pt ? "PT" : "ES"} ${width}: independent OTP staff links masked visit, inspects packet and reads back claim`, async ({
      page,
      browser,
    }) => {
      await page.setViewportSize({ width, height: 1000 });
      await login(page, "demo.customer", pt);
      await page
        .locator(".composer textarea")
        .fill(
          pt
            ? "Quero falar com uma pessoa sobre esta compra."
            : "Quiero hablar con una persona sobre esta compra.",
        );
      await page.locator(".composer button[type=submit]").click();
      await expect(page.locator(".handoff-receipt")).toBeVisible();
      const value = await invitation(page);
      const context = await browser.newContext({
        viewport: { width, height: 1000 },
        extraHTTPHeaders: { "X-Forwarded-For": "2001:db8:abcd::1" },
      });
      try {
        const staff = await context.newPage();
        await login(staff, "demo.agent", pt);
        await audit(staff);
        await connect(staff, value);
        await expect(staff.locator(".queue-item")).toHaveCount(1);
        await expect(
          staff.getByRole("heading", {
            name: pt
              ? "Solicitações desta visita"
              : "Solicitudes de esta visita",
            exact: true,
          }),
        ).toBeVisible();
        await expect(
          staff.getByRole("heading", {
            name: pt ? "Solicitação do cliente" : "Solicitud del cliente",
            exact: true,
          }),
        ).toBeVisible();
        await expect(
          staff.locator(".packet-section").first(),
        ).not.toContainText(
          pt ? "Sem resumo registrado" : "Sin resumen registrado",
        );
        await expect(staff.locator(".action-timeline li")).toHaveCount(1);
        await audit(staff);
        await capture(staff, `${pt ? "pt" : "es"}-${width}-queue`);
        await staff
          .getByRole("button", {
            name: pt ? "Assumir solicitação" : "Tomar solicitud",
            exact: true,
          })
          .click();
        await expect(
          staff.getByRole("status").filter({
            hasText: pt ? "Atribuição verificada" : "Asignación verificada",
          }),
        ).toBeVisible();
        await expect(
          staff.getByRole("button", {
            name: /Marcar como resuelta|Marcar como resolvida/,
          }),
        ).toHaveCount(0);
        await audit(staff);
        await capture(staff, `${pt ? "pt" : "es"}-${width}-claimed`);
        // Switching/reloading never persists the invitation in browser storage or URLs.
        expect(
          await staff.evaluate(() =>
            [...Object.keys(localStorage), ...Object.keys(sessionStorage)].some(
              (key) => /invitation|realm|capability/i.test(key),
            ),
          ),
        ).toBe(false);
        for (const tab of [page, staff]) {
          expect(
            await tab.evaluate(
              (capability) =>
                [localStorage, sessionStorage].some((storage) =>
                  Object.values(storage).some((stored) =>
                    stored.includes(capability),
                  ),
                ),
              value,
            ),
          ).toBe(false);
        }
        expect(staff.url().includes(value)).toBe(false);
        await page
          .getByRole("button", {
            name: pt ? "Sair" : "Cerrar sesión",
            exact: true,
          })
          .click();
        await expect(
          page.locator(".login-panel input[autocomplete=current-password]"),
        ).toBeVisible();
        await staff.reload();
        // Reinstallation uses the signed-in identity's ES locale. Change the
        // presentation language only after that authoritative read completes.
        await expect(staff.locator(".queue-panel .load-failed")).toBeVisible();
        await staff
          .locator(".locale-select select")
          .selectOption(pt ? "pt-BR" : "es-MX");
        await expect(staff.locator(".queue-panel .load-failed")).toContainText(
          pt ? "Não foi possível carregar a fila" : "No pudimos cargar la cola",
        );
        await expect(staff.locator(".queue-item")).toHaveCount(0);
        await expect(staff.locator(".packet-heading")).toHaveCount(0);
      } finally {
        await context.close();
      }
    });
  }

test("invalid invitation does not link the staff session or retain a pasted capability", async ({
  page,
}) => {
  await login(page, "demo.agent");
  await connect(page, "authored.invalid.invitation.only");
  await expect(page.locator(".staff-realm-access .error")).toContainText(
    "No pudimos verificar el vínculo",
  );
  await expect(page.locator(".staff-realm-access input")).toHaveValue("");
  await expect(page.locator(".queue-item")).toHaveCount(0);
});

for (const pt of [false, true]) {
  test(`${pt ? "PT" : "ES"}: multi-reason realm packet shows request, facts and a refreshed verified claim`, async ({
    page,
  }) => {
    const packet = {
      ...multiReasonPacket,
      scope: "current_realm",
      customer_display: pt ? "Pessoa de teste UI" : "Persona de prueba UI",
      created_at: new Date().toISOString(),
      sla_due_at: new Date(Date.now() + 15 * 86400000).toISOString(),
      route: { ...multiReasonPacket.route, language: pt ? "pt" : "es" },
      request_summary: {
        text: pt
          ? "Revisar a compra e os sinais de risco."
          : "Revisar la compra y las señales de riesgo.",
      },
      open_questions: [
        pt
          ? "Confirmar de que ajuda a pessoa precisa."
          : "Confirmar qué ayuda necesita la persona.",
      ],
      verified_facts: [offerFixture(pt).transaction],
    };
    await page.route("**/agent/handoffs", (route) =>
      route.fulfill({ json: [packet] }),
    );
    await page.route(`**/agent/handoffs/${packet.handoff_id}/claim`, (route) =>
      route.fulfill({
        json: {
          ...packet,
          status: "claimed",
          claimed_by: "agent_authored",
          version: 2,
        },
      }),
    );
    await page.route(`**/agent/handoffs/${packet.handoff_id}`, (route) =>
      route.fulfill({
        json: {
          ...packet,
          status: "claimed",
          claimed_by: "agent_authored",
          version: 3,
        },
      }),
    );
    await page.setViewportSize({ width: 390, height: 1000 });
    await login(page, "demo.agent", pt);
    await expect(page.locator(".handoff-reasons li").first()).toContainText(
      pt ? "Motivo principal" : "Motivo principal",
    );
    await expect(page.locator(".handoff-reasons li").first()).toContainText(
      pt ? "Fraude / cartão" : "Fraude / tarjeta",
    );
    await expect(page.locator(".packet-panel .transaction-card")).toHaveCount(
      1,
    );
    await page
      .getByRole("button", {
        name: pt ? "Assumir solicitação" : "Tomar solicitud",
        exact: true,
      })
      .click();
    await expect(
      page.getByRole("status").filter({
        hasText: pt ? "Atribuição verificada" : "Asignación verificada",
      }),
    ).toBeVisible();
    await audit(page);
    await capture(page, `${pt ? "pt" : "es"}-390-multi-reason`);
    await page.setViewportSize({ width: 1440, height: 1000 });
    await audit(page);
    await capture(page, `${pt ? "pt" : "es"}-1440-multi-reason`);
  });
}
for (const failure of ["stale", "claimant", "scope"]) {
  test(`claim ${failure} mismatch never shows a verified assignment`, async ({
    page,
  }) => {
    const packet = { ...multiReasonPacket, scope: "current_realm" };
    const receipt = {
      ...packet,
      status: "claimed",
      claimed_by: "agent_authored",
      version: 2,
    };
    const actual =
      failure === "stale"
        ? { ...receipt, version: 1 }
        : failure === "claimant"
          ? { ...receipt, claimed_by: "agent_other" }
          : { ...receipt, scope: "current_workspace" };
    await page.route("**/agent/handoffs", (route) =>
      route.fulfill({ json: [packet] }),
    );
    await page.route(`**/agent/handoffs/${packet.handoff_id}/claim`, (route) =>
      route.fulfill({ json: receipt }),
    );
    await page.route(`**/agent/handoffs/${packet.handoff_id}`, (route) =>
      route.fulfill({ json: actual }),
    );
    await login(page, "demo.agent");
    await page
      .getByRole("button", { name: "Tomar solicitud", exact: true })
      .click();
    await expect(
      page
        .locator(
          ".main-content > .workspace-pane > .error, .workspace-pane .error",
        )
        .last(),
    ).toBeVisible();
    await expect(
      page.getByRole("status").filter({ hasText: "Asignación verificada" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Tomar solicitud", exact: true }),
    ).toBeDisabled();
  });
}

test("changing the visit clears old packets in both staff tabs before joining", async ({
  page,
  context,
}) => {
  const oldPacket = { ...multiReasonPacket, scope: "current_realm" };
  const newPacket = {
    ...oldPacket,
    handoff_id: "HO-UI-NEW-VISIT",
    customer_display: "Nueva visita de prueba",
  };
  let packet = oldPacket;
  let completeJoin!: () => void;
  const pendingJoin = new Promise<void>((resolve) => {
    completeJoin = resolve;
  });
  await context.route("**/agent/handoffs", (route) =>
    route.fulfill({ json: [packet] }),
  );
  await context.route("**/agent/handoff-realm", async (route) => {
    await pendingJoin;
    await route.fulfill({ json: { joined: true, verified: true } });
  });
  await login(page, "demo.agent");
  const second = await context.newPage();
  await second.goto("/");
  await expect(second.locator(".queue-item")).toContainText(
    oldPacket.handoff_id,
  );
  await connect(page, "authored.replacement.invitation.only");
  await expect(page.locator(".queue-item")).toHaveCount(0);
  await expect(second.locator(".queue-item")).toHaveCount(0);
  await expect(second.locator(".packet-heading")).toHaveCount(0);
  packet = newPacket;
  completeJoin();
  for (const tab of [page, second]) {
    await expect(tab.locator(".queue-item")).toContainText(
      newPacket.handoff_id,
    );
    await expect(tab.locator(".queue-item")).not.toContainText(
      oldPacket.handoff_id,
    );
  }
});

test("expired customer invitation is removed from the open dialog", async ({
  page,
}) => {
  await login(page, "demo.customer");
  await page.clock.install();
  await page.route("**/handoffs/realm-invitations", (route) =>
    route.fulfill({
      json: {
        invitation: "authored.short.lived.invitation.only",
        expires_at: new Date(Date.now() + 5000).toISOString(),
        verified: true,
      },
    }),
  );
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await page.locator(".login-panel > button").click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator("input[type=password]")).toBeVisible();
  await page.clock.fastForward(5001);
  await expect(dialog.locator("input[type=password]")).toHaveCount(0);
  await expect(dialog.getByRole("status")).toContainText("venció");
});
