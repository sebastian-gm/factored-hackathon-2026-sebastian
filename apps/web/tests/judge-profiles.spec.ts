import { test, expect, type Page } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, chmod } from "node:fs/promises";
import { judgeProfilesSchema, type ProfileId } from "../src/lib/contracts";
import { proposalFixture, offerFixture } from "./fixtures/conversation-ui";

// Invented identities and UI replies only; no held-out or serving records.
async function loginJudge(page: Page) {
  await page.route("**/api/bff/config", async (r) => {
    const data = await (await r.fetch()).json();
    data.personas = [
      {
        username: "demo.judge",
        label: "Judge",
        role: "customer",
        locale: "es-MX",
      },
    ];
    await r.fulfill({ json: data });
  });
  await page.goto("/?grabar=1");
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
  await expect(page.getByTestId("profile-mx-es")).toBeEnabled();
}
async function select(page: Page, id: ProfileId) {
  await page.getByTestId(`profile-${id}`).click();
  await expect(
    page.getByRole("textbox", { name: /Tu mensaje|Sua mensagem/ }),
  ).toBeVisible();
  expect(await page.getByRole("log").evaluate((log) => log.scrollTop)).toBe(0);
  await expect(
    page.getByRole("button", { name: /Cambiar perfil|Trocar perfil/ }),
  ).toContainText(id === "pt" ? "Falante PT" : id.slice(0, 2).toUpperCase());
}
async function openPicker(page: Page) {
  await page
    .getByRole("button", { name: /Cambiar perfil|Trocar perfil/ })
    .click();
  await expect(page.getByTestId("profile-mx-es")).toBeEnabled();
}
async function audit(page: Page) {
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}
async function capture(page: Page, name: string) {
  if (process.env.FRONTEND_PROFILE_CAPTURE !== "1") return;
  const dir = "../../artifacts/ux-audit/judge-profile-picker";
  await mkdir(dir, { recursive: true, mode: 0o700 });
  const path = `${dir}/${name}.png`;
  await page.screenshot({
    path,
    fullPage: true,
    mask: [page.locator("input[type=password]"), page.getByTestId("sms-code")],
  });
  await chmod(path, 0o600);
}

for (const profileId of ["mx-es", "pt"] as const) {
  test(`${profileId}: trusted Ops judge can still invite separate staff; fixtures never fake queue access`, async ({
    page,
  }) => {
    await loginJudge(page);
    await select(page, profileId);
    // Authored UI projection of the trusted Ops-backed production profiles.
    // The BFF selection validator remains owned by the lead's prerequisite PR.
    await page.route("**/api/bff/config", async (route) => {
      const data = await (await route.fetch()).json();
      await route.fulfill({ json: { ...data, fixtures: false } });
    });
    await page.route("**/api/bff/me", async (route) => {
      const data = await (await route.fetch()).json();
      await route.fulfill({ json: { ...data, role: "ops" } });
    });
    await page.reload();
    await expect(page.locator(".composer textarea")).toBeVisible();
    await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
    await expect(
      page.getByRole("heading", {
        name:
          profileId === "pt"
            ? "Compartilhe sua solicitação com o atendimento"
            : "Comparte tu solicitud con atención",
      }),
    ).toBeVisible();
    await expect(page.locator(".desk-grid")).toHaveCount(0);
    await page.route("**/api/bff/handoffs/realm-invitations", (route) =>
      route.fulfill({
        json: {
          invitation: "authored.judge.staff.invitation.only",
          expires_at: new Date(Date.now() + 240000).toISOString(),
          verified: true,
        },
      }),
    );
    await page
      .getByRole("button", {
        name:
          profileId === "pt"
            ? "Criar convite para o Agent Desk"
            : "Crear invitación para Agent Desk",
        exact: true,
      })
      .click();
    await expect(
      page.getByRole("dialog").locator("input[type=password]"),
    ).toBeVisible();
    await audit(page);
  });
}

test("fixture judge cannot fake a successful visit membership or claim", async ({
  page,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await page
    .getByRole("button", { name: "Abrir la cola de esta visita", exact: true })
    .click();
  await expect(page.locator(".login-panel .error[role=alert]")).toContainText(
    "No pudimos verificar el vínculo",
  );
  await expect(page.locator(".desk-grid")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Tomar solicitud", exact: true }),
  ).toHaveCount(0);
});

test("password/OTP opens metadata-only picker; capability stays HttpOnly and expiry never extends", async ({
  page,
  context,
  playwright,
}) => {
  const bankReads: string[] = [];
  page.on("request", (r) => {
    if (/\/api\/bff\/(transactions|accounts|agent\/|ops\/)/.test(r.url()))
      bankReads.push(r.method());
  });
  await loginJudge(page);
  expect(bankReads).toEqual([]);
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveCount(
    0,
  );
  const choices = judgeProfilesSchema.parse(
    await page.evaluate(async () =>
      (await fetch("/api/bff/auth/judge/profiles")).json(),
    ),
  );
  expect(choices.active_profile_id).toBeNull();
  const denied = await page.evaluate(async () =>
    Promise.all(
      ["transactions", "accounts", "agent/handoffs", "ops/snapshot"].map(
        async (p) => (await fetch(`/api/bff/${p}`)).status,
      ),
    ),
  );
  expect(denied).toEqual([403, 403, 403, 403]);
  const first = (await context.cookies()).find(
    (c) => c.name === "aclara_access",
  )!;
  expect(first.httpOnly && first.sameSite === "Strict").toBe(true);
  expect(
    await page.evaluate(() => document.cookie.includes("aclara_access")),
  ).toBe(false);
  const selected = page.waitForResponse((r) =>
    r.url().endsWith("/auth/judge/profile"),
  );
  await select(page, "co-es");
  const body = await (await selected).json();
  expect(Object.keys(body).sort()).toEqual([
    "expires_at",
    "identity",
    "verified",
  ]);
  expect(body.expires_at).toBe(choices.expires_at);
  expect(body.identity).toMatchObject({
    locale: "es-CO",
    judge_profile_id: "co-es",
    profile_selection_required: false,
  });
  const second = (await context.cookies()).find(
    (c) => c.name === "aclara_access",
  )!;
  expect(second.value !== first.value).toBe(true);
  const stale = await playwright.request.newContext();
  const oldRead = await stale.get(new URL("/api/bff/me", page.url()).href, {
    headers: { Cookie: `aclara_access=${first.value}` },
  });
  expect(oldRead.status()).toBe(401);
  expect(Object.keys(oldRead.headers()).includes("set-cookie")).toBe(false);
  await stale.dispose();
  expect(second.httpOnly && second.sameSite === "Strict").toBe(true);
  expect(second.expires <= first.expires + 1).toBe(true);
  if (process.env.FRONTEND_E2E_PRODUCTION === "1")
    expect(second.secure).toBe(true);
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).some((k) =>
        /access|token|profile.data/i.test(k),
      ),
    ),
  ).toBe(false);
  const invalid = await page.evaluate(
    async () =>
      (
        await fetch("/api/bff/auth/judge/profile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            profile_id: "pt",
            customer_id: "not-allowed",
          }),
        })
      ).status,
  );
  expect(invalid).toBe(422);
  await audit(page);
});

for (const locale of ["es-MX", "pt-BR"] as const)
  for (const width of [1440, 390]) {
    test(`${locale} ${width}: minimalist picker and four accessible scopes`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await loginJudge(page);
      await page.getByLabel("Idioma y región").selectOption(locale);
      await expect(
        page.getByRole("heading", {
          name: locale === "pt-BR" ? "Escolha um perfil" : "Elige un perfil",
        }),
      ).toBeVisible();
      await audit(page);
      await capture(page, `${locale}-${width}-picker`);
      for (const id of ["mx-es", "co-es", "ar-es", "pt"] as const) {
        await select(page, id);
        const identity = await page.evaluate(async () =>
          (await fetch("/api/bff/me")).json(),
        );
        expect(identity.judge_profile_id).toBe(id);
        const currencies = await page.evaluate(async () =>
          (await (await fetch("/api/bff/transactions")).json()).map(
            (t: { currency: string }) => t.currency,
          ),
        );
        expect(new Set(currencies)).toEqual(
          new Set([id === "co-es" ? "COP" : id === "ar-es" ? "ARS" : "USD"]),
        );
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
        expect(
          await page.locator(".topbar").evaluate((bar) => {
            const bounds = bar.getBoundingClientRect();
            return [...bar.querySelectorAll("button, select")].every(
              (control) => {
                const rect = control.getBoundingClientRect();
                return (
                  rect.top >= bounds.top &&
                  rect.bottom <= bounds.bottom &&
                  rect.right <= bounds.right
                );
              },
            );
          }),
        ).toBe(true);
        await audit(page);
        if (
          (locale === "pt-BR" && id === "pt") ||
          (locale === "es-MX" && id === "mx-es")
        )
          await capture(page, `${locale}-${width}-active`);
        if (id !== "pt") await openPicker(page);
      }
    });
  }

test("shortcuts follow the active profile, prepare text without sending and never enable judge reset", async ({
  page,
}) => {
  let logins = 0,
    otps = 0,
    messages = 0;
  const ids: string[] = [];
  page.on("request", (r) => {
    if (r.method() !== "POST") return;
    if (r.url().endsWith("/auth/login")) logins++;
    if (r.url().endsWith("/auth/otp/verify")) otps++;
    if (r.url().endsWith("/messages")) messages++;
    if (r.url().endsWith("/auth/judge/profile"))
      ids.push(r.postDataJSON().profile_id);
  });
  await loginJudge(page);
  await select(page, "ar-es");
  await expect(page.getByTestId("quickstart-ambiguous")).toHaveCount(0);
  for (const [story, id] of [
    ["explain", "mx-es"],
    ["ambiguous", "pt"],
    ["fraud", "mx-es"],
  ]) {
    await openPicker(page);
    await select(page, id as ProfileId);
    await page.getByTestId(`quickstart-${story}`).click();
    await expect(
      page.getByRole("textbox", { name: /Tu mensaje|Sua mensagem/ }),
    ).not.toHaveValue("");
    await expect(page.getByTestId(`quickstart-${story}`)).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page.getByRole("button", { name: /Cambiar perfil|Trocar perfil/ }),
    ).toContainText(id === "pt" ? "Falante PT" : "MX · ES");
  }
  expect(ids).toEqual([
    "ar-es",
    "mx-es",
    "mx-es",
    "pt",
    "pt",
    "mx-es",
    "mx-es",
  ]);
  expect([logins, otps, messages]).toEqual([1, 1, 0]);
  await page.getByText("Preparar grabación", { exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: /Restablecer demo|Restablecer sesión/,
      exact: true,
    }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      async () =>
        (
          await fetch("/api/bff/ops/demo/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: "{}",
          })
        ).status,
    ),
  ).toBe(403);
});

test("empty hints never fall back to unsupported story scopes", async ({
  page,
}) => {
  await page.route("**/auth/judge/profiles", async (r) => {
    const data = await (await r.fetch()).json();
    for (const profile of data.profiles) profile.demo_stories = [];
    await r.fulfill({ json: data });
  });
  await loginJudge(page);
  await select(page, "mx-es");
  for (const story of ["explain", "ambiguous", "fraud"])
    await expect(page.getByTestId(`quickstart-${story}`)).toHaveCount(0);
});

test("switch clears proposal/dialog and conversation; selecting same profile also rotates", async ({
  page,
  context,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({ json: proposalFixture(false) }),
  );
  const created = page.waitForResponse(
    (r) =>
      r.url().endsWith("/chat/sessions") && r.request().method() === "POST",
  );
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Consulta de interfaz inventada");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  const old = (await (await created).json()).conversation_id;
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await openPicker(page);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await select(page, "co-es");
  await expect(page.getByRole("log")).not.toContainText(
    "Consulta de interfaz inventada",
  );
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "",
  );
  await page.unroute("**/chat/sessions/*/messages");
  expect(
    await page.evaluate(
      async (id) =>
        (
          await fetch(`/api/bff/chat/sessions/${id}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: "Sin datos anteriores" }),
          })
        ).status,
      old,
    ),
  ).toBe(404);
  const first = (await context.cookies()).find(
    (c) => c.name === "aclara_access",
  )!;
  await openPicker(page);
  await select(page, "co-es");
  expect(
    first.value !==
      (await context.cookies()).find((c) => c.name === "aclara_access")!.value,
  ).toBe(true);
});

test("late old-profile response never renders in new scope", async ({
  page,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  let release!: () => void;
  const wait = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/chat/sessions/*/messages", async (r) => {
    await wait;
    await r
      .fulfill({
        json: { ...offerFixture(false), reply: "OLD-PROFILE-RESPONSE" },
      })
      .catch(() => {});
  });
  const pending = page.waitForRequest((r) => r.url().endsWith("/messages"));
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Mensaje anterior inventado");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await pending;
  await openPicker(page);
  await select(page, "pt");
  release();
  await expect(page.getByRole("log")).not.toContainText(
    /OLD-PROFILE-RESPONSE|Mensaje anterior|Papelería Prisma/,
  );
  await expect(page.getByRole("textbox", { name: "Sua mensagem" })).toHaveValue(
    "",
  );
});

for (const transport of ["channel", "storage"])
  test(`two tabs (${transport}) clear state and refresh rotated identity`, async ({
    page,
    context,
  }) => {
    if (transport === "storage")
      await context.addInitScript(() => {
        Object.defineProperty(window, "BroadcastChannel", { value: undefined });
      });
    await loginJudge(page);
    await select(page, "mx-es");
    const tab = await context.newPage();
    await tab.goto("/");
    await expect(
      tab.getByRole("textbox", { name: "Tu mensaje" }),
    ).toBeVisible();
    await tab
      .getByRole("textbox", { name: "Tu mensaje" })
      .fill("Texto de la pestaña anterior");
    await openPicker(page);
    await select(page, "pt");
    await expect(
      tab.getByRole("button", { name: /Trocar perfil/ }),
    ).toContainText("Falante PT");
    await expect(
      tab.getByRole("textbox", { name: "Sua mensagem" }),
    ).toHaveValue("");
    await tab.close();
  });

test("back navigation and return to a prior profile never restore stale chat", async ({
  page,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("No debe volver con atrás");
  await page.getByRole("button", { name: "Insights", exact: true }).click();
  await page.goBack();
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "",
  );
  await openPicker(page);
  await select(page, "pt");
  await openPicker(page);
  await select(page, "mx-es");
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toHaveValue(
    "",
  );
});

for (const failure of ["unavailable", "lost-response", "unverified"])
  test(`switch ${failure}: single POST and login required`, async ({
    page,
  }) => {
    await loginJudge(page);
    await select(page, "mx-es");
    let posts = 0;
    await page.route("**/auth/judge/profile", async (r) => {
      posts++;
      if (failure === "lost-response") {
        await r.fetch();
        await r.abort();
      } else
        await r.fulfill({
          status: failure === "unavailable" ? 503 : 200,
          json:
            failure === "unavailable"
              ? { error: "service_unavailable" }
              : { verified: false },
        });
    });
    await openPicker(page);
    await page.getByTestId("profile-pt").click();
    await expect(page.locator("input[type=password]")).toBeVisible();
    await expect(
      page.getByRole("alert").filter({ hasText: "Vuelve a iniciar sesión" }),
    ).toContainText("Vuelve a iniciar sesión");
    await expect(
      page.getByRole("textbox", { name: /Tu mensaje|Sua mensagem/ }),
    ).toHaveCount(0);
    expect(posts).toBe(1);
  });

test("logout clears both tabs and cookie", async ({ page, context }) => {
  await loginJudge(page);
  await select(page, "mx-es");
  const tab = await context.newPage();
  await tab.goto("/");
  await expect(tab.getByRole("textbox", { name: "Tu mensaje" })).toBeVisible();
  await page
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await expect(page.locator("input[type=password]")).toBeVisible();
  await expect(tab.locator("input[type=password]")).toBeVisible();
  expect(
    (await context.cookies()).some((c) => c.name === "aclara_access"),
  ).toBe(false);
  await tab.close();
});

test("a verified receipt and step-up dialog disappear on switching", async ({
  page,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({ json: proposalFixture(false) }),
  );
  await page.route("**/chat/sessions/*/confirm", (r) =>
    r.fulfill({
      json: {
        response_type: "report_case",
        outcome: "dispute_filed",
        reply: "Recibo de interfaz inventado.",
        transaction: offerFixture(false).transaction,
        verified: true,
        case: {
          case_id: "DSP-UI-PROFILE",
          transaction_handle: "txn_ui_papeleria",
          status: "received",
          policy_rules: ["DSP-02"],
          created_at: "2026-06-18T06:00:00Z",
        },
      },
    }),
  );
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Revisión inventada");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tu caso está registrado" }),
  ).toBeVisible();
  await openPicker(page);
  await select(page, "co-es");
  await expect(
    page.getByRole("heading", { name: "Tu caso está registrado" }),
  ).toHaveCount(0);
  await page.unroute("**/chat/sessions/*/confirm");
  await page.route("**/chat/sessions/*/confirm", (r) =>
    r.fulfill({ status: 401, json: { error: "step_up_required" } }),
  );
  await page.route("**/auth/step-up", (r) =>
    r.fulfill({ json: { challenge_id: "UI-profile-step-up" } }),
  );
  await page.route("**/auth/challenges/*/sms", (r) =>
    r.fulfill({ json: { code: "123456" } }),
  );
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Otra revisión inventada");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(page.getByTestId("confirm-step-up-code")).toBeVisible();
  await page.keyboard.press("Escape");
  await openPicker(page);
  await select(page, "pt");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByTestId("confirm-step-up-code")).toHaveCount(0);
  await expect(page.getByRole("log")).not.toContainText(
    /Recibo|Revisión|Otra revisión/,
  );
});

test("revocation clears stale data in both tabs without retrying the message", async ({
  page,
  context,
}) => {
  await loginJudge(page);
  await select(page, "mx-es");
  const tab = await context.newPage();
  await tab.goto("/");
  await expect(tab.getByRole("textbox", { name: "Tu mensaje" })).toBeVisible();
  await tab
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Borrador antiguo");
  // Revoke through the authored bank, outside React, then encounter its 401.
  await page.evaluate(async () =>
    fetch("/api/bff/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }),
  );
  let starts = 0;
  page.on("request", (r) => {
    if (r.url().endsWith("/chat/sessions") && r.method() === "POST") starts++;
  });
  await page
    .getByRole("textbox", { name: "Tu mensaje" })
    .fill("Consulta después de revocar");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(page.locator("input[type=password]")).toBeVisible();
  await expect(tab.locator("input[type=password]")).toBeVisible();
  expect(starts).toBe(1);
  await tab.close();
});

test("ordinary owner login retains the original UI and cannot list judge profiles", async ({
  page,
}) => {
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
  await expect(page.getByRole("textbox", { name: "Tu mensaje" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Cambiar perfil/ }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      async () => (await fetch("/api/bff/auth/judge/profiles")).status,
    ),
  ).toBe(403);
});
