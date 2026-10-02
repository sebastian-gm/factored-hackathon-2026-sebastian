import { selectLoginPersona } from "./helpers/login-persona";
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";

async function login(page: Page, persona = "demo.es.mx") {
  await selectLoginPersona(page, persona);
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  const authResponse = page.waitForResponse((r) =>
    r.url().endsWith("/auth/login"),
  );
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  const authBody = await (await authResponse).json();
  expect(authBody).not.toHaveProperty("preauth_token");
  expect(authBody).toHaveProperty("challenge_id");
  const code = page.getByTestId("sms-code");
  await expect(code).toHaveText(/^\d{6}$/);
  await page
    .getByRole("textbox", { name: /Código de 6/ })
    .fill((await code.textContent())!);
  await page
    .getByRole("button", { name: /Verificar y entrar|Verificar e entrar/ })
    .click();
  await expect(
    page.getByRole("button", { name: /Cerrar sesión|Sair/, exact: true }),
  ).toBeVisible();
}
async function switchRole(
  page: Page,
  surface: "Agent Desk" | "Operaciones",
  persona: string,
) {
  await page.getByRole("button", { name: surface, exact: true }).click();
  await page
    .getByRole("button", { name: /Usar otra cuenta|Usar outra conta/ })
    .click();
  await login(page, persona);
}
async function screenshot(page: Page, name: string) {
  await mkdir("../../artifacts/frontend/screenshots", { recursive: true });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `../../artifacts/frontend/screenshots/${name}.png`,
    fullPage: true,
  });
}
async function audit(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}
test("ES normal: password + OTP, grounded explanation and safe why drawer", async ({
  page,
  context,
}) => {
  await page.goto("/");
  await expect(
    page.getByText("Banco simulado · No es un servicio real"),
  ).toBeVisible();
  await expect(page.locator("input[type=password]")).toBeVisible();
  await screenshot(page, "login-desktop");
  await audit(page);
  await login(page);
  await page
    .getByRole("button", {
      name: "¿Qué es el cargo de Café Horizonte?",
      exact: true,
    })
    .click();
  await expect(
    page.getByText(/Es una autorización|es una autorización/),
  ).toBeVisible();
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Verificar",
  );
  await expect(page.getByText("185,00")).not.toBeVisible(); // MX formatting is not forced to PT.
  await expect(page.getByText(/USD\s*185\.00/)).toBeVisible();
  await page.getByRole("button", { name: "¿Por qué?", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Estado del movimiento");
  await expect(page.getByRole("dialog")).toContainText(
    "no razonamiento interno",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const cookies = await context.cookies();
  expect(cookies.find((c) => c.name === "aclara_access")).toMatchObject({
    httpOnly: true,
    sameSite: "Strict",
  });
  expect(await page.evaluate(() => document.cookie)).not.toContain(
    "aclara_access",
  );
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  await screenshot(page, "chat-desktop");
  await audit(page);
  await page.getByLabel("Idioma y región").selectOption("pt-BR");
  await page
    .getByRole("textbox", { name: "Sua mensagem" })
    .fill("O que é a cobrança de Café Horizonte?");
  await page.getByRole("button", { name: "Enviar mensagem" }).click();
  await expect(
    page.getByText(/A cobrança de Café Horizonte é uma autorização/),
  ).toBeVisible();
});
test("PT ambiguous: top three, exact confirmation, verified case receipt", async ({
  page,
}) => {
  await page.goto("/");
  await login(page, "demo.pt.br");
  await page
    .getByRole("button", {
      name: "Não reconheço uma compra de uns 90 dólares",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Revisar este movimento" }),
  ).toHaveCount(3);
  await page
    .getByRole("button", { name: "Revisar este movimento" })
    .nth(1)
    .click();
  const dialog = page.getByRole("dialog");
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Agir",
  );
  await expect(dialog).toContainText("Mercado do Bairro");
  await expect(dialog).toContainText(/USD\s*92,50/);
  await expect(dialog).toContainText("Registrar contestação");
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toHaveJSProperty("tagName", "BUTTON");
  const request = page.waitForRequest(
    (r) => r.url().endsWith("/confirm") && r.method() === "POST",
  );
  await dialog.getByRole("button", { name: "Confirmar", exact: true }).click();
  expect((await request).postDataJSON()).toMatchObject({
    confirmed: true,
    proposal_hash: expect.stringMatching(/^[a-f0-9]{64}$/),
  });
  await expect(
    page.getByRole("heading", { name: "Seu caso está registrado" }),
  ).toBeVisible();
  await expect(
    page.getByText("Recebido para análise", { exact: false }),
  ).toBeVisible();
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Verificar",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  const receiptTitle = await page
    .getByRole("heading", { name: "Seu caso está registrado" })
    .boundingBox();
  const receiptLog = await page.locator(".conversation-log").boundingBox();
  expect(receiptTitle!.y).toBeGreaterThanOrEqual(receiptLog!.y);
  expect(receiptTitle!.y).toBeGreaterThanOrEqual(0);
  expect(receiptTitle!.y + receiptTitle!.height).toBeLessThan(844);
  await screenshot(page, "pt-receipt");
  await audit(page);
});
test("fraud: customer handoff, agent evidence, claim and resolve, ops trace and reset", async ({
  page,
}) => {
  await page.goto("/");
  await login(page, "demo.fraud");
  await page
    .getByRole("button", {
      name: "Perdí mi tarjeta y no reconozco una compra",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tu solicitud está en buenas manos" }),
  ).toBeVisible();
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Derivar",
  );
  await switchRole(page, "Agent Desk", "demo.agent");
  await expect(
    page
      .getByRole("region", { name: "Motivos de la derivación" })
      .getByText("FRD-01", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Hechos verificados" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Evidencia del registro/ }).click();
  await expect(page.getByRole("dialog")).toContainText("get_transaction");
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Tomar solicitud", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Marcar como resuelta" }),
  ).toBeVisible();
  await screenshot(page, "agent-desk");
  await audit(page);
  await page.getByRole("button", { name: "Marcar como resuelta" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(page.getByText("Resuelto · Verificado")).toBeVisible();
  await switchRole(page, "Operaciones", "demo.ops");
  await expect(
    page.getByText("HANDOFF_CREATED", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("scripted-frontend-fixture", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: /Linaje del manifiesto/ }),
  ).toBeVisible();
  await screenshot(page, "ops-desktop");
  await audit(page);
  await page
    .getByRole("button", { name: "Restablecer personas demo", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Espacio restablecido y verificado."),
  ).toBeVisible();
  await expect(
    page.getByText("Inicia una conversación para ver su recorrido."),
  ).toBeVisible();
});
test("cancel consumes the proposal without creating a case", async ({
  page,
}) => {
  await page.goto("/");
  await login(page, "demo.pt.br");
  await page
    .getByRole("button", {
      name: "Não reconheço uma compra de uns 90 dólares",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Revisar este movimento" })
    .first()
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancelar", exact: true })
    .click();
  await expect(
    page.getByText("Cancelado. Nenhuma contestação foi registrada."),
  ).toBeVisible();
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Agir",
  );
  await expect(
    page.getByRole("heading", { name: "Seu caso está registrado" }),
  ).toHaveCount(0);
});
test("phone layouts, keyboard entry and all locales", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Ir al contenido" }),
  ).toBeFocused();
  await page.getByLabel("Idioma y región").selectOption("es-CO");
  await expect(page.locator("html")).toHaveAttribute("lang", "es-CO");
  await page.getByLabel("Idioma y región").selectOption("es-AR");
  await expect(page.locator("html")).toHaveAttribute("lang", "es-AR");
  await page.getByLabel("Idioma y región").selectOption("es-MX");
  await login(page, "demo.fraud");
  await page
    .getByRole("button", {
      name: "Perdí mi tarjeta y no reconozco una compra",
      exact: true,
    })
    .click();
  await screenshot(page, "phone-chat");
  await audit(page);
  for (const [surface, persona, name] of [
    ["Agent Desk", "demo.agent", "phone-desk"],
    ["Operaciones", "demo.ops", "phone-ops"],
  ] as const) {
    await switchRole(page, surface, persona);
    await page.waitForLoadState("networkidle");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await screenshot(page, name);
    await audit(page);
  }
});
test("server blocks cross-origin writes, forged confirmation, and customer staff access", async ({
  page,
  request,
}) => {
  const cross = await request.post("/api/bff/auth/login", {
    headers: { Origin: "https://foreign.invalid" },
    data: { username: "demo.es.mx", password: "not-a-credential" },
  });
  expect(cross.status()).toBe(403);
  await page.goto("/");
  await login(page, "demo.pt.br");
  const checks = await page.evaluate(async () => {
    const send = (path: string, body?: unknown) =>
      fetch(`/api/bff/${path}`, {
        method: body ? "POST" : "GET",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
    const staff = await send("agent/handoffs");
    const reset = await send("ops/demo/reset", { confirmed: true });
    const c = await (await send("chat/sessions", {})).json();
    const forged = await send(`chat/sessions/${c.conversation_id}/confirm`, {
      proposal_hash: "0".repeat(64),
      confirmed: true,
    });
    return [staff.status, reset.status, forged.status];
  });
  expect(checks).toEqual([403, 403, 409]);
});

test("proposal replay is idempotent and another authenticated browser cannot confirm it", async ({
  page,
  browser,
}) => {
  await page.goto("/");
  await login(page, "demo.pt.br");
  await page
    .getByRole("button", {
      name: "Não reconheço uma compra de uns 90 dólares",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Revisar este movimento" })
    .first()
    .click();
  const captured = page.waitForRequest((r) => r.url().endsWith("/confirm"));
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  const call = await captured;
  await expect(
    page.getByRole("heading", { name: "Seu caso está registrado" }),
  ).toBeVisible();
  const replay = await page.evaluate(
    async ({ url, body }) => {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      const result = await r.json();
      return {
        status: r.status,
        verified: result.verified,
        id: result.case?.case_id,
      };
    },
    { url: call.url(), body: call.postData()! },
  );
  expect(replay).toMatchObject({
    status: 200,
    verified: true,
    id: expect.stringMatching(/^DSP-/),
  });
  await page.locator(".case-reference summary").click();
  await expect(page.getByText(replay.id, { exact: true })).toBeVisible();
  const other = await browser.newContext();
  const tab = await other.newPage();
  try {
    await tab.goto("/");
    await login(tab, "demo.pt.br");
    const status = await tab.evaluate(
      async ({ url, body }) =>
        (
          await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body,
          })
        ).status,
      { url: call.url(), body: call.postData()! },
    );
    expect(status).toBe(404);
  } finally {
    await other.close();
  }
});

test("OTP is required; failed challenge locks after five attempts and can restart", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  const code = page.getByTestId("sms-code");
  await expect(code).toHaveText(/^\d{6}$/);
  const wrong = (await code.textContent()) === "000000" ? "111111" : "000000";
  for (let i = 0; i < 5; i++) {
    await page
      .getByRole("textbox", { name: "Código de 6 dígitos" })
      .fill(wrong);
    const response = page.waitForResponse((r) =>
      r.url().endsWith("/otp/verify"),
    );
    await page.getByRole("button", { name: "Verificar y entrar" }).click();
    expect((await response).status()).toBe(401);
  }
  await page
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await code.textContent())!);
  const locked = page.waitForResponse((r) => r.url().endsWith("/otp/verify"));
  await page.getByRole("button", { name: "Verificar y entrar" }).click();
  expect((await locked).status()).toBe(401);
  await page
    .getByRole("button", { name: "Usar otra cuenta", exact: true })
    .click();
  await login(page);
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toBeVisible();
});

test("recording helper resets with read-back, selects all personas and reaches the desk", async ({
  page,
}) => {
  await page.goto("/?grabar=1");
  await page.getByText("Preparar grabación", { exact: true }).click();
  await page
    .getByRole("button", { name: "Entrar en operaciones para restablecer" })
    .click();
  await expect(page.locator('input[autocomplete="username"]')).toBeVisible();
  await expect(page.locator(".login-panel select")).toHaveCount(0);
  await login(page, "demo.ops");
  await page
    .getByRole("button", { name: "Restablecer demo y abrir ES" })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Espacio restablecido" }),
  ).toBeVisible();
  await expect(
    page
      .locator("select")
      .filter({ has: page.locator("option[value='demo.es.mx']") }),
  ).toHaveValue("demo.es.mx");
  await login(page);
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "¿Qué es el cargo de Café Horizonte?",
  );
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByText(/Es una autorización|es una autorización/),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: /Elegir una compra · PT|Escolher compra · PT/,
    })
    .click();
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  await expect(
    page
      .locator("select")
      .filter({ has: page.locator("option[value='demo.pt.br']") }),
  ).toHaveValue("demo.pt.br");
  await login(page, "demo.pt.br");
  await page.getByRole("button", { name: "Enviar mensagem" }).click();
  await expect(
    page.getByRole("button", { name: "Revisar este movimento" }),
  ).toHaveCount(3);
  await page
    .getByRole("button", { name: "Revisar este movimento" })
    .nth(1)
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Seu caso está registrado" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /Pedir ayuda · ES|Pedir ajuda · ES/ })
    .click();
  await expect(
    page
      .locator("select")
      .filter({ has: page.locator("option[value='demo.fraud']") }),
  ).toHaveValue("demo.fraud");
  await login(page, "demo.fraud");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByRole("heading", { name: "Tu solicitud está en buenas manos" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Abrir Agent Desk", exact: true })
    .click();
  await login(page, "demo.agent");
  await expect(
    page
      .getByRole("region", { name: "Motivos de la derivación" })
      .getByText("FRD-01", { exact: true }),
  ).toBeVisible();
});

test("recording helper never opens a story when reset read-back fails", async ({
  page,
}) => {
  await page.goto("/?grabar=1");
  await page.getByText("Preparar grabación", { exact: true }).click();
  await page
    .getByRole("button", { name: "Entrar en operaciones para restablecer" })
    .click();
  await login(page, "demo.ops");
  await page.route("**/ops/demo/reset", (route) =>
    route.fulfill({ json: { verified: false } }),
  );
  await page
    .getByRole("button", { name: "Restablecer demo y abrir ES" })
    .click();
  await expect(
    page.locator(".recording-helper").getByRole("alert"),
  ).toContainText("No se completó la preparación");
  await expect(page.locator("input[type=password]")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Cada paso, a la vista." }),
  ).toBeVisible();
});

test("glass box shows call cost precision, partial totals, fallback and risk union without raw text", async ({
  page,
}) => {
  await page.goto("/");
  await login(page, "demo.fraud");
  await page
    .getByRole("button", {
      name: "Perdí mi tarjeta y no reconozco una compra",
      exact: true,
    })
    .click();
  const flags = {
    lost_stolen: false,
    regulator: false,
    legal: false,
    distress: false,
    injection_suspected: false,
    human_requested: false,
  };
  const probabilities = {
    lost_stolen: 0.12,
    regulator: 0.02,
    legal: 0.03,
    distress: 0.84,
    injection_suspected: 0.1,
    human_requested: 0.1,
  };
  const risk = {
    gemini_raw_flags: flags,
    gemini_raw_probabilities: Object.fromEntries(
      Object.keys(flags).map((cue) => [cue, null]),
    ),
    jev_raw_probabilities: probabilities,
    jev_threshold_flags: { ...flags, distress: true },
    union_flags: { ...flags, distress: true },
    threshold: 0.5,
    degradation: null,
    primary_failed: false,
  };
  await page.route("**/ops/overview", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    const call = {
      provider: "openai_compat",
      model: "google/gemini-3-flash-preview",
      prompt_version: "nlu-v4",
      input_tokens: 321,
      output_tokens: 21,
      latency_ms: 1234.5,
      cost_usd: null,
      status: "provider_error",
      attempt: 1,
    };
    const event = {
      stage: "Understand",
      state: "llm_call",
      tool: null,
      rules: [],
      verified: false,
    };
    data.conversations[0].events = [
      { ...event, id: "failure", llm: call },
      {
        ...event,
        id: "fallback",
        llm: {
          ...call,
          model: "x-ai/grok-4.20",
          route: "fallback_grok_4_20",
          cost_usd: 0.000964,
          status: "valid",
        },
      },
      {
        ...event,
        id: "risk",
        llm: {
          ...call,
          provider: "typesafe",
          model: "jev-1.13.0",
          prompt_version: "risk-v1",
          cost_usd: 0.0000392,
          judgments: risk,
          status: "valid",
        },
      },
    ];
    data.conversations.push({
      id: "degraded-authored",
      events: [
        {
          ...event,
          id: "timeout",
          llm: {
            ...call,
            provider: "typesafe",
            model: "jev-1.13.0",
            judgments: {
              gemini_raw_flags: { distress: null },
              jev_raw_probabilities: null,
              jev_threshold_flags: null,
              union_flags: {},
              degradation: "timeout",
            },
          },
        },
      ],
    });
    await route.fulfill({ json: data });
  });
  await switchRole(page, "Operaciones", "demo.ops");
  await page
    .getByRole("combobox", { name: "Tu conversación", exact: true })
    .selectOption({ index: 0 });
  const cost = page.getByLabel("Costo de esta conversación");
  await expect(cost).toContainText("0.0010032");
  await expect(cost).toContainText("3 llamadas registradas");
  await expect(cost).toContainText("1 costo desconocido");
  await expect(cost).toContainText("Subtotal conocido");
  await expect(cost).toContainText("Ruta alternativa Grok registrada");
  await expect(
    page.locator(".llm-metadata").filter({ hasText: "x-ai/grok-4.20" }),
  ).toContainText("fallback_grok_4_20");
  await expect(page.getByText("nlu-v4", { exact: true })).toHaveCount(2);
  await expect(
    page.getByText("1234.5 ms", { exact: false }).first(),
  ).toBeVisible();
  const row = page
    .getByRole("row")
    .filter({ has: page.getByRole("rowheader", { name: "Angustia" }) });
  await expect(row).toContainText("84.0%");
  await expect(row.getByRole("cell")).toHaveText(["Sí", "No", "84.0%", "Sí"]);
  await expect(page.getByText(/sin probabilidades por señal/)).toBeVisible();
  await audit(page);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const riskTable = page.locator(".risk-table");
  await expect(riskTable.locator("thead th").nth(1)).toHaveText("Unión");
  await expect(page.locator(".lineage-zoom")).toHaveAttribute(
    "href",
    "/dbt-lineage.svg",
  );
  await riskTable.locator("..").evaluate((element) => {
    element.scrollLeft = element.scrollWidth;
  });
  const signal = await riskTable.locator("thead th").first().boundingBox();
  const union = await riskTable.locator("thead th").nth(1).boundingBox();
  expect(signal!.x).toBeGreaterThanOrEqual(0);
  expect(union!.x + union!.width).toBeLessThanOrEqual(390);
  await audit(page);
  await screenshot(page, "recording-glassbox-phone");
  await page
    .getByRole("combobox", { name: "Tu conversación", exact: true })
    .selectOption("degraded-authored");
  await expect(
    page.getByRole("status").filter({ hasText: "Segunda opinión degradada" }),
  ).toContainText("timeout");
  await expect(row.getByRole("cell")).toHaveText([
    "No registrado",
    "No registrado",
    "—",
    "No registrado",
  ]);
  await expect(cost).toContainText("1 costo desconocido");
});

test("trace projection accepts old events and strips non-display payloads", async () => {
  const { traceSchema } = await import("../src/lib/staff-contracts");
  const { callTotals, riskSchema } = await import("../src/lib/trace");
  const flags = {
    lost_stolen: false,
    regulator: false,
    legal: false,
    distress: false,
    injection_suspected: false,
    human_requested: false,
  };
  const incomplete = riskSchema.parse({
    gemini_raw_flags: flags,
    gemini_raw_probabilities: Object.fromEntries(
      Object.keys(flags).map((cue) => [cue, null]),
    ),
    jev_raw_probabilities: { distress: 0.7, unexpected_text: "must-not-cross" },
    jev_threshold_flags: null,
    union_flags: flags,
    threshold: 0.5,
    degradation: "incomplete_risk_answers",
    primary_failed: false,
  });
  expect(incomplete.jev_raw_probabilities).toEqual({ distress: 0.7 });
  expect(
    riskSchema.safeParse({
      ...incomplete,
      jev_raw_probabilities: { distress: 1.5 },
    }).success,
  ).toBe(false);
  const event = {
    id: "call-1",
    stage: "Understand",
    state: "llm_call",
    tool: null,
    rules: [],
    verified: false,
    llm: {
      provider: "mock",
      model: "fixture",
      prompt_version: "none",
      input_tokens: 0,
      output_tokens: 0,
      latency_ms: 0,
      cost_usd: null,
      thinking: "must-not-cross",
      completion: "must-not-cross",
    },
  };
  const trace = traceSchema.parse({
    conversation_id: "authored",
    policy_version: "v1",
    scope: "current_workspace",
    events: [event],
  });
  expect(JSON.stringify(trace)).not.toContain("must-not-cross");
  expect(
    traceSchema.parse({
      ...trace,
      events: [
        {
          ...event,
          llm: { ...event.llm, route: null, status: null, attempt: null },
        },
      ],
    }).events[0].llm,
  ).toMatchObject({ route: null, status: null, attempt: null });
  expect(callTotals([trace.events[0], trace.events[0]])).toMatchObject({
    count: 1,
    unknown: 1,
    known: 0,
  });
  expect(callTotals([{ ...trace.events[0], llm: null }])).toMatchObject({
    count: 0,
  });
  expect(
    traceSchema.parse({
      ...trace,
      events: [
        { ...event, llm: { ...event.llm, judgments: { union_flags: {} } } },
      ],
    }).events[0].llm?.judgments,
  ).toEqual({ union_flags: {} });
  expect(riskSchema.parse({ degradation: null })).toEqual({
    degradation: null,
  });
  expect(
    riskSchema.parse({
      gemini_raw_flags: { distress: null, arbitrary_text: "must-not-cross" },
      union_flags: null,
      thinking: "must-not-cross",
    }),
  ).toEqual({ gemini_raw_flags: { distress: null }, union_flags: null });
  expect(
    riskSchema.safeParse({ union_flags: { distress: "false" } }).success,
  ).toBe(false);
});
