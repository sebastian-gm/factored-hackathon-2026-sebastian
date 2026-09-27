import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
async function login(page: Page) {
  await page.goto("/");
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
}
test("live frozen API through BFF: password, OTP and verified transaction explanation", async ({
  page,
}) => {
  await login(page);
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("¿Qué es el cargo de Café Central?");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(page.getByText(/Es una autorización;/)).toBeVisible();
  await expect(page.getByText("Producto no informado")).toBeVisible();
  await page.getByRole("button", { name: "¿Por qué?", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("TXN-01");
  await page.keyboard.press("Escape");
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("No reconozco el cargo de Mercado Verde");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(page.getByRole("dialog")).toContainText("Mercado Verde");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tu caso está registrado" }),
  ).toBeVisible();
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
    page.getByRole("heading", { name: "Conexión pendiente" }),
  ).toBeVisible();
  const status = await page.evaluate(
    async () => (await fetch("/api/bff/agent/handoffs")).status,
  );
  expect(status).toBe(501);
});

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
