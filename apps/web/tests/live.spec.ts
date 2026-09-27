import { test, expect } from "@playwright/test";
test("live frozen API through BFF: password, OTP and verified transaction explanation", async ({
  page,
}) => {
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
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Conexión pendiente" }),
  ).toBeVisible();
  const status = await page.evaluate(
    async () => (await fetch("/api/bff/agent/handoffs")).status,
  );
  expect(status).toBe(501);
});
