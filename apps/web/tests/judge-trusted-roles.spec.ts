import { test, expect } from "./helpers/test";

// The fixture backend chooses these roles; the caller can choose only profile_id.
for (const [profile, role] of [
  ["mx-es", "ops"],
  ["co-es", "agent"],
] as const) {
  test(`BFF preserves independently verified ${role} source role during judge selection`, async ({
    page,
    context,
    playwright,
    baseURL,
  }) => {
    const origin = baseURL!;
    const headers = { Origin: origin };
    const login = await context.request.post("/api/bff/auth/login", {
      headers,
      data: {
        username: "demo.judge",
        password: process.env.FRONTEND_FIXTURE_PASSWORD!,
      },
    });
    expect(login.status()).toBe(200);
    const challenge = await login.json();
    const sms = await context.request.get(
      `/api/bff/auth/challenges/${challenge.challenge_id}/sms`,
    );
    expect(sms.status()).toBe(200);
    const otp = await context.request.post("/api/bff/auth/otp/verify", {
      headers,
      data: {
        challenge_id: challenge.challenge_id,
        code: (await sms.json()).code,
      },
    });
    expect(otp.status()).toBe(200);
    const initial = (await context.cookies()).find(
      (c) => c.name === "aclara_access",
    )!;
    await page.goto("/");
    await expect(page.getByTestId(`profile-${profile}`)).toBeEnabled();
    const response = page.waitForResponse((r) =>
      r.url().endsWith("/auth/judge/profile"),
    );
    await page.getByTestId(`profile-${profile}`).click();
    const selected = await response;
    expect(selected.status()).toBe(200);
    const view = await selected.json();
    expect(view.verified).toBe(true);
    expect(view.identity).toMatchObject({
      role,
      judge_profile_id: profile,
      profile_selection_required: false,
    });
    expect(view).not.toHaveProperty("access_token");
    const current = await context.request.get("/api/bff/me");
    expect(current.status()).toBe(200);
    expect(await current.json()).toEqual(view.identity);
    const active = (await context.cookies()).find(
      (c) => c.name === "aclara_access",
    )!;
    expect(active.value).not.toBe(initial.value);
    expect(active.httpOnly).toBe(true);
    const stale = await playwright.request.newContext({
      extraHTTPHeaders: { Cookie: `aclara_access=${initial.value}` },
    });
    expect((await stale.get(origin + "/api/bff/me")).status()).toBe(401);
    await stale.dispose();
    const forged = await context.request.post("/api/bff/auth/judge/profile", {
      headers,
      data: { profile_id: profile, role: "ops" },
    });
    expect(forged.status()).toBe(422);
    const logout = await context.request.post("/api/bff/auth/logout", {
      headers,
      data: {},
    });
    expect(logout.status()).toBe(200);
    expect(await logout.json()).toEqual({ signed_out: true });
    expect((await context.request.get("/api/bff/me")).status()).toBe(401);
  });
}
