import type { BrowserContext } from "@playwright/test";
import { test, expect, type Page } from "./helpers/test";

// Invented profiles; mock/B1, real local API/BFF and independent readbacks.
function bank(context: BrowserContext, origin: string) {
  return {
    async get(path: string, status = 200) {
      const response = await context.request.get(`/api/bff/${path}`);
      expect(response.status()).toBe(status);
      return response.json();
    },
    async post(path: string, data: Record<string, unknown>, status = 200) {
      const response = await context.request.post(`/api/bff/${path}`, {
        headers: { Origin: origin },
        data,
      });
      expect(response.status()).toBe(status);
      return response.json();
    },
  };
}
async function authenticate(context: BrowserContext, origin: string) {
  const client = bank(context, origin);
  const challenge = await client.post("auth/login", {
    username: "judge.authored",
    password: process.env.FRONTEND_FIXTURE_JUDGE_PASSWORD!,
  });
  const sms = await client.get(`auth/challenges/${challenge.challenge_id}/sms`);
  await client.post("auth/otp/verify", { challenge_id: challenge.challenge_id, code: sms.code });
  return client;
}
async function select(page: Page, id: "mx-es" | "co-es" | "pt") {
  await page.getByTestId(`profile-${id}`).click();
  await expect(page.locator(".composer textarea")).toBeVisible();
}
async function handoff(page: Page, pt: boolean) {
  await page
    .locator(".composer textarea")
    .fill(
      pt
        ? "Quero falar com uma pessoa. Meu telefone é 11987654321."
        : "Quiero hablar con una persona. Mi teléfono es 3001234567.",
    );
  await page.locator(".composer button[type=submit]").click();
  await expect(page.locator(".handoff-receipt")).toBeVisible();
}
async function desk(page: Page) {
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
}
async function cookie(context: BrowserContext) {
  return (await context.cookies()).find((item) => item.name === "aclara_access")!.value;
}

for (const pt of [false, true]) {
  test(`${pt ? "PT customer" : "ES Ops"}: same-login masked queue, verified claim and profile-switch recovery`, async ({
    page,
    context,
    playwright,
    baseURL,
  }) => {
    const origin = baseURL!,
      client = await authenticate(context, origin);
    await page.goto("/");
    await select(page, pt ? "pt" : "mx-es");
    const identity = await client.get("me");
    expect(identity.role).toBe(pt ? "customer" : "ops");
    await client.get("agent/handoffs", 403);
    await client.get("ops/snapshot", pt ? 403 : 200);
    await handoff(page, pt);
    const oldCookie = await cookie(context);
    await desk(page);
    const inviteReply = page.waitForResponse((r) =>
      r.url().endsWith("/handoffs/realm-invitations"),
    );
    const joinReply = page.waitForResponse((r) => r.url().endsWith("/agent/handoff-realm"));
    await page
      .getByRole("button", {
        name: pt ? "Abrir a fila desta visita" : "Abrir la cola de esta visita",
        exact: true,
      })
      .click();
    const invitation = await (await inviteReply).json();
    expect(await (await joinReply).json()).toEqual({ joined: true, verified: true });
    expect((await cookie(context)) === oldCookie).toBe(true);
    expect(await client.get("me")).toEqual(identity);
    await expect(page.locator(".queue-item")).toHaveCount(1);
    await expect(page.locator(".staff-realm-access")).toHaveCount(0);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    const [packet] = await client.get("agent/handoffs");
    expect(packet).toMatchObject({
      scope: "current_realm",
      verified: true,
      customer_display: "Cliente demo",
      evidence: [],
    });
    for (const key of [
      "customer_id",
      "transcript",
      "trace",
      "run_id",
      "session_id",
      "transcript_ref",
      "trace_ref",
    ])
      expect(packet).not.toHaveProperty(key);
    expect(JSON.stringify(packet).includes(pt ? "11987654321" : "3001234567")).toBe(false);
    let detailReads = 0;
    const path = `agent/handoffs/${packet.handoff_id}`;
    page.on("request", (r) => {
      if (r.method() === "GET" && r.url().endsWith(`/${path}`)) detailReads++;
    });
    await page
      .getByRole("button", { name: pt ? "Assumir solicitação" : "Tomar solicitud", exact: true })
      .click();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: pt ? "Atribuição verificada" : "Asignación verificada" }),
    ).toBeVisible();
    expect(detailReads).toBeGreaterThan(0);
    const claimed = await client.get(path);
    expect(claimed).toMatchObject({ status: "claimed", verified: true, scope: "current_realm" });
    expect(claimed.version).toBeGreaterThan(packet.version);
    await expect(
      page.getByRole("button", { name: /Marcar como resuelta|Marcar como resolvida/ }),
    ).toHaveCount(0);
    await client.post(
      `${path}/resolve`,
      {
        expected_version: claimed.version,
        idempotency_key: "authored_resolve_denied",
        resolution: "review_completed",
      },
      409,
    );
    // Same-controller replay reads membership; no second invite use or claim.
    expect(await client.post("agent/handoff-realm", { invitation: invitation.invitation })).toEqual(
      { joined: true, verified: true },
    );
    expect((await client.get(path)).version).toBe(claimed.version);
    await client.get("ops/snapshot", pt ? 403 : 200); // Source-role access remains unchanged.
    expect(
      await page.evaluate(
        (capability) =>
          [localStorage, sessionStorage].some((storage) =>
            Object.values(storage).some((value) => value.includes(capability)),
          ) ||
          location.href.includes(capability) ||
          document.body.textContent?.includes(capability),
        invitation.invitation,
      ),
    ).toBe(false);
    await page.reload();
    await desk(page);
    await expect(page.locator(".queue-item")).toHaveCount(1);
    await expect(page.getByRole("button", { name: /Abrir (?:la cola|a fila)/ })).toHaveCount(0);
    await page.getByRole("button", { name: /Cambiar perfil|Trocar perfil/ }).click();
    await select(page, "co-es");
    const stale = await playwright.request.newContext({
      extraHTTPHeaders: { Cookie: `aclara_access=${oldCookie}` },
    });
    try {
      expect((await stale.get(origin + "/api/bff/agent/handoffs")).status()).toBe(401);
    } finally {
      await stale.dispose();
    }
    await desk(page);
    await expect(page.locator(".queue-item")).toHaveCount(1);
    expect((await client.get(path)).version).toBe(claimed.version);
    await page.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
    await expect(page.locator(".login-panel input[autocomplete=current-password]")).toBeVisible();
    await client.get("agent/handoffs", 401);
  });
}

test("another judge visit cannot consume an invitation or read its packet", async ({
  page,
  context,
  browser,
  baseURL,
}) => {
  const origin = baseURL!,
    client = await authenticate(context, origin);
  await page.goto("/");
  await select(page, "mx-es");
  await handoff(page, false);
  const invitation = await client.post("handoffs/realm-invitations", {});
  const other = await browser.newContext({
    baseURL: origin,
    extraHTTPHeaders: { "X-Forwarded-For": "2001:db8:abcd::2" },
  });
  try {
    const outsider = await authenticate(other, origin);
    await outsider.post("auth/judge/profile", { profile_id: "mx-es" });
    await outsider.post("agent/handoff-realm", { invitation: invitation.invitation }, 403);
    await outsider.get("agent/handoffs", 403);
    await client.post("agent/handoff-realm", { invitation: invitation.invitation });
    const [packet] = await client.get("agent/handoffs");
    await outsider.get(`agent/handoffs/${packet.handoff_id}`, 403);
    await outsider.post("agent/handoff-realm", { invitation: invitation.invitation }, 403);
  } finally {
    await other.close();
  }
});
