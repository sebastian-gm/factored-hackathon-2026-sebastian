import { test, expect, type Page } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import { proposalFixture } from "./fixtures/conversation-ui";
import {
  AdmissionLimiter,
  chatWindows,
  clientAddress,
  admissionMessage,
} from "../src/lib/server/admission";

test("rolling minute/day limits, independent sessions, expiry and rotation", () => {
  const limiter = new AdmissionLimiter();
  for (let i = 0; i < 20; i++)
    expect(limiter.consume("session", chatWindows, 0)).toBeNull();
  expect(limiter.consume("session", chatWindows, 1)).toBe(60);
  expect(limiter.consume("other", chatWindows, 1)).toBeNull();
  limiter.rotate("session", "rotated");
  expect(limiter.consume("rotated", chatWindows, 1000)).toBe(59);
  for (let block = 1; block < 15; block++)
    for (let i = 0; i < 20; i++)
      expect(
        limiter.consume("rotated", chatWindows, block * 60_000),
      ).toBeNull();
  expect(limiter.consume("rotated", chatWindows, 15 * 60_000)).toBe(85500);
  expect(limiter.consume("rotated", chatWindows, 86_400_000)).toBeNull();
});

test("capacity rejects new keys without evicting active limits; expired keys free space", () => {
  const limiter = new AdmissionLimiter(1);
  const windows = [{ limit: 1, ms: 60_000 }];
  expect(limiter.consume("first", windows, 0)).toBeNull();
  expect(limiter.consume("second", windows, 1)).toBe(60);
  expect(limiter.consume("first", windows, 1)).toBe(60);
  expect(limiter.consume("second", windows, 60_000)).toBeNull();
});

test("only trusted rightmost peer is used; IPv6 aliases and spoofed prefixes cannot split buckets", () => {
  const headers = new Headers({
    "x-forwarded-for": "198.51.100.99, 203.0.113.7",
    "x-real-ip": "198.51.100.1",
  });
  expect(clientAddress(headers, true)).toBe("203.0.113.7");
  expect(clientAddress(headers, false)).toBe("unresolved-peer");
  headers.set("x-forwarded-for", "bad, nope");
  expect(clientAddress(headers, true)).toBe("unresolved-peer");
  headers.set("x-forwarded-for", "2001:0db8:0:0:0:0:0:1");
  expect(clientAddress(headers, true)).toBe("2001:db8::1");
  headers.set("x-forwarded-for", "::ffff:203.0.113.7");
  expect(clientAddress(headers, true)).toBe("203.0.113.7");
  headers.set("x-forwarded-for", "fe80::1%eth0");
  expect(clientAddress(headers, true)).toBe("unresolved-peer");
});

async function login(page: Page, pt = false) {
  await page.goto("/");
  if (pt) await page.getByLabel("Idioma y región").selectOption("pt-BR");
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
  await expect(
    page.getByRole("textbox", { name: pt ? "Sua mensagem" : "Tu mensaje" }),
  ).toBeVisible();
}

for (const pt of [false, true]) {
  test(`a locally rejected confirmation retains the exact proposal and never auto-replays (${pt ? "PT" : "ES"})`, async ({
    page,
  }) => {
    await login(page, pt);
    const proposal = proposalFixture(pt);
    await page.route("**/chat/sessions/*/messages", (route) =>
      route.fulfill({ json: proposal }),
    );
    const confirms: unknown[] = [];
    await page.route("**/chat/sessions/*/confirm", async (route) => {
      confirms.push(route.request().postDataJSON());
      if (confirms.length === 1)
        await route.fulfill({
          status: 429,
          headers: { "Retry-After": "17" },
          json: { error: "admission_limited" },
        });
      else
        await route.fulfill({
          json: {
            response_type: "cancelled",
            outcome: "cancelled",
            reply: pt ? "Ação cancelada." : "Acción cancelada.",
          },
        });
    });
    await page
      .getByRole("textbox", { name: pt ? "Sua mensagem" : "Tu mensaje" })
      .fill("Solicitud de prueba UI");
    await page
      .getByRole("button", { name: pt ? "Enviar mensagem" : "Enviar mensaje" })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog
      .getByRole("button", { name: "Confirmar", exact: true })
      .click();
    await expect(dialog.getByRole("alert")).toContainText("17 s.");
    await expect(dialog).toContainText(proposal.transaction!.merchant!);
    expect(confirms).toEqual([
      { confirmed: true, proposal_hash: proposal.proposal!.proposal_hash },
    ]);
    await expect(page.locator("#message")).toBeDisabled();
    await dialog.getByRole("button", { name: "Cancelar", exact: true }).click();
    await expect(dialog).toHaveCount(0);
    expect(confirms).toEqual([
      { confirmed: true, proposal_hash: proposal.proposal!.proposal_hash },
      { confirmed: false, proposal_hash: proposal.proposal!.proposal_hash },
    ]);
  });

  test(`actual BFF login attempts return localized no-store 429 (${pt ? "PT" : "ES"})`, async ({
    page,
  }) => {
    await page.goto("/");
    const replies = await page.evaluate(
      async (language) => {
        const values = [];
        for (let i = 0; i < 11; i++) {
          const response = await fetch("/api/bff/auth/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept-Language": language,
            },
            body: JSON.stringify({
              username: "invented-account",
              password: "invented-invalid",
            }),
          });
          values.push({
            status: response.status,
            body: await response.json(),
            retry: response.headers.get("Retry-After"),
            cache: response.headers.get("Cache-Control"),
          });
        }
        return values;
      },
      pt ? "pt-BR" : "es-MX",
    );
    expect(replies.slice(0, 10).map((reply) => reply.status)).toEqual(
      Array(10).fill(401),
    );
    const limited = replies[10];
    expect(limited.status).toBe(429);
    expect(limited.cache).toContain("no-store");
    expect(limited.body.error).toBe("admission_limited");
    expect(limited.body.message).toBe(
      admissionMessage(pt ? "pt" : "es", Number(limited.retry)),
    );
    if (pt) await page.getByLabel("Idioma y región").selectOption("pt-BR");
    await page.locator("input[type=password]").fill("invented-invalid");
    await page.getByRole("button", { name: "Continuar", exact: true }).click();
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: pt ? "Muitas tentativas" : "Demasiados intentos" }),
    ).toContainText(pt ? "Muitas tentativas" : "Demasiados intentos");
    await expect(page.locator("input[type=password]")).toHaveValue("");
  });

  test(`OTP attempt bucket is independent of login and rejects the 21st attempt (${pt ? "PT" : "ES"})`, async ({
    page,
  }) => {
    await page.goto("/");
    const statuses = await page.evaluate(async () => {
      const result = [];
      for (let i = 0; i < 21; i++) {
        const response = await fetch("/api/bff/auth/otp/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            challenge_id: "invented-challenge",
            code: "000000",
          }),
        });
        result.push(response.status);
      }
      return result;
    });
    expect(statuses.slice(0, 20)).toEqual(Array(20).fill(401));
    expect(statuses[20]).toBe(429);
    // A valid password can still start its own bucket; OTP remains throttled.
    if (pt) await page.getByLabel("Idioma y región").selectOption("pt-BR");
    await page
      .locator("input[type=password]")
      .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
    await page.getByRole("button", { name: "Continuar", exact: true }).click();
    await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
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
        .filter({ hasText: pt ? "Muitas tentativas" : "Demasiados intentos" }),
    ).toContainText(pt ? "Muitas tentativas" : "Demasiados intentos");
    await expect(
      page.getByRole("textbox", { name: "Código de 6 dígitos" }),
    ).toHaveValue("");
  });

  test(`20 admitted chat turns across conversations; rejected draft is editable without duplicate or replay (${pt ? "PT" : "ES"})`, async ({
    page,
    context,
  }) => {
    await login(page, pt);
    const status = await page.evaluate(async () => {
      const result = [];
      for (let conversation = 0; conversation < 2; conversation++) {
        const start = await fetch("/api/bff/chat/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        const { conversation_id } = await start.json();
        for (let i = 0; i < 10; i++) {
          const response = await fetch(
            `/api/bff/chat/sessions/${conversation_id}/messages`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: "Consulta de ejemplo" }),
            },
          );
          result.push(response.status);
        }
      }
      return result;
    });
    expect(status).toEqual(Array(20).fill(200));
    const draft = "Mensaje pendiente de enviar";
    const message = page.getByRole("textbox", {
      name: pt ? "Sua mensagem" : "Tu mensaje",
    });
    await message.fill(draft);
    const response = page.waitForResponse((r) => r.url().endsWith("/messages"));
    await page
      .getByRole("button", { name: pt ? "Enviar mensagem" : "Enviar mensaje" })
      .click();
    expect((await response).status()).toBe(429);
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: pt ? "Muitas tentativas" : "Demasiados intentos" }),
    ).toContainText(pt ? "Muitas tentativas" : "Demasiados intentos");
    await expect(message).toHaveValue(draft);
    await expect(message).toBeEditable();
    await expect(page.getByRole("log").getByText(draft)).toHaveCount(0);
    await expect(page.locator("input[type=password]")).toHaveCount(0);
    expect(
      (await context.cookies()).find(
        (cookie) => cookie.name === "aclara_access",
      )?.httpOnly,
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
}
