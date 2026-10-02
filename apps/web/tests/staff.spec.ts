import { test, expect } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";

test("live workspace: trusted ops role, handoff claim/resolve, measured traces and OTP reset", async ({
  page,
}) => {
  const probe = JSON.parse(
    execFileSync(process.execPath, ["scripts/check-api-hop.mjs"], {
      env: {
        ...process.env,
        API_BASE_URL: `http://127.0.0.1:${process.env.FRONTEND_E2E_API_PORT ?? "8212"}`,
      },
      encoding: "utf8",
    }),
  );
  expect(probe.checks).toEqual([
    { check: "healthz", status: 200, passed: true },
    { check: "personas", status: 200, passed: true },
  ]);
  await page.goto("/");
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
    .fill("Quiero hablar con una persona");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByRole("heading", { name: "Tu solicitud está en buenas manos" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await expect(
    page.getByText(
      "Solo las derivaciones de tu espacio de cliente. No es una cola de otros clientes del banco.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Tomar solicitud" }),
  ).toBeVisible();
  // A fresh operational deadline is fifteen wall-clock days away, even though
  // the serving ledger is frozen in June. The old bank-clock subtraction showed
  // thousands of hours. Use the actual API receipt instead of fixture dates.
  const packet = await page.evaluate(
    async () => (await (await fetch("/api/bff/agent/handoffs")).json())[0],
  );
  expect(new Date(packet.created_at).getTime()).toBeGreaterThan(
    new Date("2026-06-18T06:00:00Z").getTime(),
  );
  const sla = page.locator(".queue-item .caption").filter({ hasText: "SLA" });
  await expect(sla).toHaveText(/Tiempo para SLA: (?:14d 23h \d+m|15d 0h 0m)/);
  await expect(
    page.getByText("El paquete no incluye movimientos verificados.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.locator(".action-timeline li")).toHaveCount(1);
  expect(packet.actions).toEqual([
    expect.objectContaining({ action: "create_handoff", status: "verified" }),
  ]);
  const action = page.waitForRequest((r) => r.url().endsWith("/claim"));
  await page.getByRole("button", { name: "Tomar solicitud" }).click();
  expect((await action).postDataJSON()).toMatchObject({
    expected_version: 1,
    idempotency_key: expect.any(String),
  });
  await page.getByRole("button", { name: "Marcar como resuelta" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(page.getByText("Resuelto · Verificado")).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.getByRole("button", { name: "Operaciones", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Actividad de este espacio" }),
  ).toBeVisible();
  await expect(
    page.getByText("Sin medir: no hay etiquetas de referencia"),
  ).toHaveCount(2);
  await expect(
    page.getByText("Ejemplo ilustrativo · no es un resultado medido"),
  ).toHaveCount(0);
  const metrics = await page.evaluate(async () =>
    (await fetch("/api/bff/ops/metrics")).json(),
  );
  expect(metrics).toMatchObject({
    source: "current_workspace_operations",
    cases: 0,
    handoffs: 1,
    conversations: 1,
    sar: null,
    unsafe_rate: null,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .getByRole("button", { name: "Restablecer personas demo", exact: true })
    .click();
  const otp = page.getByTestId("reset-otp");
  await expect(otp).toHaveText(/^\d{6}$/);
  await page
    .getByRole("dialog")
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill((await otp.textContent())!);
  await page
    .getByRole("button", { name: "Verificar y revisar acción" })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "Se conservan la autenticación y la auditoría",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Espacio restablecido y verificado."),
  ).toBeVisible();
  const after = await page.evaluate(async () =>
    (await fetch("/api/bff/ops/metrics")).json(),
  );
  expect(after).toMatchObject({
    cases: 0,
    handoffs: 0,
    conversations: 0,
    execution_records: 0,
  });
});
