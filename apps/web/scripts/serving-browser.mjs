// Owner-only serving UI smoke. Credentials arrive on stdin; no screenshots,
// traces, console forwarding, DOM dumps or organizer records are emitted.
import { chromium } from "@playwright/test";
let input = "";
for await (const chunk of process.stdin) input += chunk;
const { url, password } = JSON.parse(input);
const browser = await chromium.launch();
let stage = "login_navigation";
try {
  const page = await browser.newPage();
  // Scale-to-zero can cold-start web and then the internal API. Match the
  // owner smoke client's 190s allowance; never retry an action or POST.
  page.setDefaultNavigationTimeout(190_000);
  page.setDefaultTimeout(190_000);
  await page.goto(url);
  stage = "login_form";
  await page.locator("form select").selectOption("demo.es.mx");
  await page.locator("input[type=password]").fill(password);
  stage = "login_submit";
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  stage = "login_sms";
  await page.waitForFunction(() =>
    /^\d{6}$/.test(
      document.querySelector('[data-testid="sms-code"]')?.textContent ?? "",
    ),
  );
  await page
    .getByRole("textbox", { name: "Código de 6 dígitos" })
    .fill(await page.getByTestId("sms-code").textContent());
  stage = "login_verify";
  await page.getByRole("button", { name: "Verificar y entrar" }).click();
  stage = "customer_handoff";
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Quiero hablar con una persona");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await page
    .getByRole("heading", { name: "Tu solicitud está en buenas manos" })
    .waitFor();
  stage = "agent_desk";
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await page.getByRole("button", { name: "Tomar solicitud" }).click();
  await page.getByRole("button", { name: "Marcar como resuelta" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await page.getByText("Resuelto · Verificado").waitFor();
  stage = "ops";
  await page
    .getByRole("button", { name: "Evidencia y operaciones", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Actividad de este espacio" })
    .waitFor();
  await page.getByText("Registro del organizador · últimos 120 días").waitFor();
  const valid = await page.evaluate(async () => {
    const r = await fetch("/api/bff/ops/snapshot");
    const d = await r.json();
    return (
      r.ok &&
      d.source_kind === "organizer_serving" &&
      d.metrics.handoffs === 1 &&
      d.metrics.sar === null &&
      d.metrics.unsafe_rate === null
    );
  });
  if (!valid) throw new Error("aggregate verification failed");
  console.log(
    JSON.stringify({
      browser_serving: "passed",
      surfaces: 3,
      handoffs: 1,
      resolved: 1,
    }),
  );
} catch (error) {
  console.log(
    JSON.stringify({
      browser_serving: "failed",
      stage,
      error_class: error?.name ?? "Error",
    }),
  );
  process.exitCode = 1;
} finally {
  await browser.close();
}
