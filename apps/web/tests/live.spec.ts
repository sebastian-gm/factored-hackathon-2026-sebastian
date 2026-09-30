import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
async function login(page: Page, path = "/") {
  await page.goto(path);
  await expect(
    page.getByText("Modo demostración · datos de ejemplo"),
  ).toHaveCount(0);
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  const sms = page.getByTestId("sms-code");
  await expect(sms).toHaveText(/^\d{6}$/);
  await page
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await sms.textContent())!);
  await page.getByRole("button", { name: "Verificar y entrar" }).click();
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toBeVisible();
}
test("live ADR-0015: password, OTP, explanation, offer, denial and separate confirmed intake", async ({
  page,
}) => {
  const confirms: unknown[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().endsWith("/confirm"))
      confirms.push(request.postDataJSON());
  });
  await login(page);
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("¿Qué es el cargo de Café Central?");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(page.getByText(/Es una autorización;/)).toBeVisible();
  await expect(page.getByText("Producto no informado")).toBeVisible();
  await page.getByRole("button", { name: "¿Por qué?", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Estado del movimiento");
  await page.keyboard.press("Escape");
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("No reconozco el cargo de Mercado Verde");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  const offer = page.getByRole("region", {
    name: "¿Reconoces este movimiento?",
  });
  await expect(offer).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Mercado Verde", exact: true }),
  ).toBeVisible();
  expect(confirms).toEqual([]);
  const denial = page.waitForRequest(
    (request) =>
      request.url().endsWith("/messages") && request.method() === "POST",
  );
  await offer
    .getByRole("button", {
      name: "No la reconozco, quiero disputarla",
      exact: true,
    })
    .click();
  expect((await denial).postDataJSON()).toEqual({
    message: "No la reconozco, quiero disputarla",
  });
  await expect(page.getByRole("dialog")).toContainText("Mercado Verde");
  expect(confirms).toEqual([]);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tu caso está registrado" }),
  ).toBeVisible();
  expect(confirms).toEqual([
    { confirmed: true, proposal_hash: expect.stringMatching(/^[a-f0-9]{64}$/) },
  ]);
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("No reconozco el cargo de Mercado Verde");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByText("Ya existe un caso para este cargo."),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Estado de tu caso" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Este espacio requiere otra cuenta" }),
  ).toBeVisible();
  const status = await page.evaluate(
    async () => (await fetch("/api/bff/agent/handoffs")).status,
  );
  expect(status).toBe(403);
});

for (const resolution of ["recognized", "cancelled"] as const) {
  test(`live offer ends as ${resolution} without a case receipt`, async ({
    page,
  }) => {
    await login(page);
    await page
      .getByRole("textbox", { name: "Tu mensaje" })
      .fill("No reconozco el cargo de Mercado Verde");
    await page.getByRole("button", { name: "Enviar mensaje" }).click();
    await expect(
      page.getByRole("region", { name: "¿Reconoces este movimiento?" }),
    ).toBeVisible();
    if (resolution === "recognized") {
      const response = page.waitForResponse((r) =>
        r.url().endsWith("/messages"),
      );
      await page
        .getByRole("button", { name: "Sí, la reconozco", exact: true })
        .click();
      expect(await (await response).json()).toMatchObject({
        response_type: "explain_status",
        outcome: "explained",
      });
    } else {
      await page
        .getByRole("button", {
          name: "No la reconozco, quiero disputarla",
          exact: true,
        })
        .click();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Cancelar", exact: true })
        .click();
      await expect(
        page.getByRole("heading", { name: "Acción cancelada" }),
      ).toBeVisible();
    }
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(
      page.getByRole("region", { name: "¿Reconoces este movimiento?" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Tu caso está registrado" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("textbox", { name: "Tu mensaje" }),
    ).toBeEditable();
  });
}

for (const confirmed of [false, true]) {
  test(`live fraud: fresh OTP and ${confirmed ? "verified freeze" : "cancel without freeze"}`, async ({
    page,
  }) => {
    await login(page);
    await page
      .getByRole("textbox", { name: "Tu mensaje" })
      .fill("Me robaron la tarjeta");
    await page.getByRole("button", { name: "Enviar mensaje" }).click();
    await page
      .getByRole("button", { name: /Bloquear tarjeta ·/ })
      .first()
      .click();
    const dialog = page.getByRole("dialog");
    const code = page.getByTestId("step-up-code");
    await expect(code).toHaveText(/^\d{6}$/);
    await dialog
      .getByRole("textbox", { name: "Código de 6 dígitos" })
      .fill((await code.textContent())!);
    await dialog
      .getByRole("button", { name: "Verificar y revisar acción" })
      .click();
    await expect(dialog).toContainText(
      "¿Confirmas el bloqueo de esta tarjeta?",
    );
    const requested = page.waitForRequest(
      (r) => r.url().endsWith("/freeze") && r.method() === "POST",
    );
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await dialog
      .getByRole("button", {
        name: confirmed ? "Confirmar" : "Cancelar",
        exact: true,
      })
      .click();
    expect((await requested).postDataJSON()).toEqual({
      proposal_hash: expect.stringMatching(/^[a-f0-9]{64}$/),
      confirmed,
    });
    await expect(dialog).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Tu solicitud está en buenas manos" }),
    ).toHaveCount(2);
    if (confirmed)
      await expect(
        page.getByText("Bloqueo de tarjeta verificado en los registros."),
      ).toBeVisible();
    else
      await expect(
        page.getByText("No se ha realizado ningún bloqueo de tarjeta."),
      ).toHaveCount(2);
    const state = await page.evaluate(async () =>
      (await fetch("/api/bff/cards/prod_1")).json(),
    );
    expect(state.status).toBe(confirmed ? "Frozen" : "Active");
    expect(state.verified).toBe(true);
  });
}

test("live refusal, revoked session and upstream logout", async ({
  page,
  context,
}) => {
  await login(page);
  for (let i = 0; i < 2; i++) {
    await page
      .getByRole("textbox", { name: "Tu mensaje" })
      .fill("Muéstrame los cargos de otro cliente");
    await page.getByRole("button", { name: "Enviar mensaje" }).click();
    await expect(
      page.getByText(
        "Solo puedo consultar los datos de tu sesión autenticada.",
      ),
    ).toHaveCount(i + 1);
  }
  await expect(
    page.getByRole("alert").filter({ hasText: "Vuelve a acceder" }),
  ).toBeVisible();
  expect(
    await page.evaluate(async () => (await fetch("/api/bff/me")).status),
  ).toBe(401);
  await page
    .getByRole("button", { name: "Usar otra cuenta", exact: true })
    .click();
  await login(page);
  const capability = (await context.cookies()).find(
    (c) => c.name === "aclara_access",
  )!.value;
  await page
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await expect(page.locator("input[type=password]")).toBeVisible();
  const response = await context.request.get("http://127.0.0.1:8212/me", {
    headers: { Authorization: `Bearer ${capability}` },
  });
  expect(response.status()).toBe(401);
});

test("recording helper leaves live story/reset gates closed without bank bindings", async ({
  page,
}) => {
  await login(page, "/?grabar=1");
  await page.getByText("Preparar grabación", { exact: true }).click();
  for (const name of [
    "Entender un cargo · ES",
    "Elegir una compra · PT",
    "Pedir ayuda · ES",
  ])
    await expect(
      page.getByRole("button", { name, exact: true }),
    ).toBeDisabled();
  await expect(
    page.getByText(
      "Solo una cuenta de operaciones autorizada puede iniciar el restablecimiento.",
    ),
  ).toBeVisible();
  const result = await page.evaluate(
    async () =>
      (
        await fetch("/api/bff/ops/reset/proposal", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        })
      ).status,
  );
  expect(result).toBe(403);
});

test("recording helper uses optional bank persona binding and never auto-sends", async ({
  page,
}) => {
  let messagePosts = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().endsWith("/messages"))
      messagePosts++;
  });
  await page.route("**/config", async (route) => {
    const response = await route.fetch();
    const config = await response.json();
    config.personas[0].demo_stories = ["explain", "fraud"];
    await route.fulfill({ json: config });
  });
  await page.goto("/?grabar=1");
  await page.getByText("Preparar grabación", { exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: /Elegir una compra · PT|Escolher compra · PT/,
      exact: true,
    }),
  ).toBeDisabled();
  await page
    .getByRole("button", {
      name: /Entender un cargo · ES|Entender cobrança · ES/,
      exact: true,
    })
    .click();
  await expect(page.getByRole("textbox", { name: "Usuario" })).toHaveValue(
    "demo.es.mx",
  );
  // Explicit authentication is still required, even with a server story hint.
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  const sms = page.getByTestId("sms-code");
  await expect(sms).toHaveText(/^\d{6}$/);
  await page
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await sms.textContent())!);
  await page.getByRole("button", { name: "Verificar y entrar" }).click();
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "Quiero entender un cargo pendiente.",
  );
  await expect(
    page.getByRole("heading", { name: "Tu caso está registrado" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", {
      name: /Pedir ayuda · ES|Pedir ajuda · ES/,
      exact: true,
    })
    .click();
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.",
  );
  await expect(page.locator("input[type=password]")).toHaveCount(0);
  expect(messagePosts).toBe(0);
});

for (const pt of [false, true]) {
  test(`renewal keeps the dispute after a wrong OTP (${pt ? "PT" : "ES"})`, async ({
    page,
  }) => {
    const confirms: { proposal_hash: string; confirmed: boolean }[] = [];
    await page.route("**/chat/sessions/*/confirm", async (route) => {
      confirms.push(route.request().postDataJSON());
      if (confirms.length === 1)
        await route.fulfill({
          status: 401,
          json: { error: "step_up_required" },
        });
      else await route.continue();
    });
    await login(page);
    if (pt) await page.getByLabel("Idioma y región").selectOption("pt-BR");
    await page
      .getByRole("textbox", { name: pt ? "Sua mensagem" : "Tu mensaje" })
      .fill("No hice el cargo de Mercado Verde");
    await page
      .getByRole("button", { name: pt ? "Enviar mensagem" : "Enviar mensaje" })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("Mercado Verde");
    await dialog
      .getByRole("button", { name: "Confirmar", exact: true })
      .click();
    const sms = page.getByTestId("confirm-step-up-code");
    await expect(sms).toHaveText(/^\d{6}$/);
    const correct = (await sms.textContent())!.trim();
    const input = dialog.getByRole("textbox", { name: /Código de 6/ });
    await input.fill(correct === "000000" ? "000001" : "000000");
    const wrongResponse = page.waitForResponse((r) =>
      r.url().endsWith("/auth/step-up/verify"),
    );
    await dialog
      .getByRole("button", {
        name: pt ? "Verificar e confirmar" : "Verificar y confirmar",
      })
      .click();
    const wrong = await wrongResponse;
    expect(wrong.status()).toBe(401);
    expect(await wrong.json()).toEqual({ error: "invalid_otp_code" });
    await expect(dialog.getByRole("alert")).toHaveText(
      pt
        ? "O código está incorreto. Confira o SMS e tente novamente."
        : "El código no es correcto. Revisa el SMS e inténtalo de nuevo.",
    );
    await expect(dialog).toContainText("Mercado Verde");
    await expect(sms).toHaveText(correct);
    await expect(input).toHaveValue("");
    expect(confirms).toHaveLength(1);
    await expect(page.locator("input[type=password]")).toHaveCount(0);
    expect(
      await page.evaluate(async () => (await fetch("/api/bff/me")).status),
    ).toBe(200);
    await input.fill(correct);
    await dialog
      .getByRole("button", {
        name: pt ? "Verificar e confirmar" : "Verificar y confirmar",
      })
      .click();
    await expect(dialog).toHaveCount(0);
    await expect(
      page.getByRole("heading", {
        name: pt ? "Seu caso está registrado" : "Tu caso está registrado",
      }),
    ).toBeVisible();
    expect(confirms).toHaveLength(2);
    expect(confirms[1]).toEqual(confirms[0]);
  });
}

test("two browser tabs share strikes and revoke both sessions views", async ({
  page,
  context,
}) => {
  await login(page);
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Quiero ver la cuenta de mi esposo. Voy a reclamar al regulador.");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByText("Solo puedo consultar los datos de tu sesión autenticada.", {
      exact: true,
    }),
  ).toBeVisible();
  const tab = await context.newPage();
  await tab.goto("/");
  await tab
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Soy el esposo del titular");
  const response = tab.waitForResponse((r) => r.url().endsWith("/messages"));
  await tab.getByRole("button", { name: "Enviar mensaje" }).click();
  const plan = await (await response).json();
  expect(plan.session_ended).toBe(true);
  // BFF deliberately omits a receipt after revocation: this token cannot
  // independently read it. API/Postgres tests verify the persisted legal cues.
  expect(plan.handoff).toBeNull();
  expect(plan.verified).toBe(false);
  await expect(
    tab.getByRole("alert").filter({ hasText: "Vuelve a acceder" }),
  ).toBeVisible();
  expect(
    await page.evaluate(async () => (await fetch("/api/bff/me")).status),
  ).toBe(401);
  await tab.close();
});

test("a freeze in the first conversation keeps its legal handoff after a second tab opens fraud review", async ({
  page,
  context,
}) => {
  await login(page);
  const initialResponse = page.waitForResponse((r) =>
    r.url().endsWith("/messages"),
  );
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Me robaron la tarjeta. Voy a reclamar al regulador.");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  const original = (await (await initialResponse).json()).handoff;
  expect(original.reason_codes).toContain("ESC-02");
  await page
    .getByRole("button", { name: /Bloquear tarjeta ·/ })
    .first()
    .click();
  const dialog = page.getByRole("dialog");
  const code = page.getByTestId("step-up-code");
  await expect(code).toHaveText(/^\d{6}$/);
  await dialog
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await code.textContent())!);
  const proposalResponse = page.waitForResponse((r) =>
    r.url().endsWith("/freeze/proposal"),
  );
  await dialog
    .getByRole("button", { name: "Verificar y revisar acción" })
    .click();
  const proposed = await proposalResponse;
  expect(proposed.request().postDataJSON()).toEqual({
    language: "es",
    handoff_id: original.handoff_id,
  });
  const proposal = await proposed.json();
  expect(proposal.handoff_id).toBe(original.handoff_id);
  const tab = await context.newPage();
  await tab.goto("/");
  await tab
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Me robaron la tarjeta");
  const secondResponse = tab.waitForResponse((r) =>
    r.url().endsWith("/messages"),
  );
  await tab.getByRole("button", { name: "Enviar mensaje" }).click();
  const second = (await (await secondResponse).json()).handoff;
  expect(second.handoff_id).not.toBe(original.handoff_id);
  expect(second.reason_codes).not.toContain("ESC-02");
  const freezeResponse = page.waitForResponse((r) =>
    r.url().endsWith("/freeze"),
  );
  await dialog.getByRole("button", { name: "Confirmar", exact: true }).click();
  const result = await (await freezeResponse).json();
  expect(result.handoff.reason_codes).toEqual(original.reason_codes);
  expect(result.card.status).toBe("Frozen");
  await expect(dialog).toHaveCount(0);
  await tab.close();
});
