import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";

async function login(page: Page, persona = "demo.es.mx") {
  await page
    .locator("select")
    .filter({ has: page.locator(`option[value='${persona}']`) })
    .selectOption(persona);
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
  surface: "Agent Desk" | "Ops · glass box",
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
    page.getByText("Synthetic data · Simulated bank · Not a real service"),
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
  await expect(page.getByText("185,00")).not.toBeVisible(); // MX formatting is not forced to PT.
  await expect(page.getByText(/MXN\s*185\.00/)).toBeVisible();
  await page.getByRole("button", { name: "¿Por qué?", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("TXN-01");
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
      name: "Não reconheço uma compra de uns 90 reais",
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
  await expect(dialog).toContainText("Mercado do Bairro");
  await expect(dialog).toContainText(/BRL\s*92,50/);
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
  await switchRole(page, "Agent Desk", "demo.agent");
  await expect(page.getByText("FRD-01", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Hechos verificados" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Evidencia del registro ·/ }).click();
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
  await switchRole(page, "Ops · glass box", "demo.ops");
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
      name: "Não reconheço uma compra de uns 90 reais",
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
    ["Ops · glass box", "demo.ops", "phone-ops"],
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
      name: "Não reconheço uma compra de uns 90 reais",
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
  await expect(page.getByText(replay.id, { exact: true })).toBeVisible();
  const other = await browser.newContext();
  const tab = await other.newPage();
  try {
    await tab.goto("http://127.0.0.1:3212/");
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
