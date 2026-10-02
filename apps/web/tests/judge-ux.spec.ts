import { selectLoginPersona } from "./helpers/login-persona";
import { test, expect, type Page, type Locator } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import {
  offerFixture,
  proposalFixture,
  multiReasonPacket,
} from "./fixtures/conversation-ui";

// Project-authored UI fixtures only: no bank data or held-out scenarios.
async function locale(page: Page, pt: boolean) {
  await page
    .locator(".locale-select select")
    .selectOption(pt ? "pt-BR" : "es-MX");
}
async function login(page: Page, pt = false, role = "customer") {
  await page.goto("/");
  await expect(page.locator(".login-panel")).toBeVisible();
  if (role !== "customer")
    await page
      .locator(".sidebar nav button")
      .nth(role === "agent" ? 1 : 2)
      .click();
  await selectLoginPersona(
    page,
    role === "customer"
      ? pt
        ? "demo.pt.br"
        : "demo.es.mx"
      : role === "agent"
        ? "demo.agent"
        : "demo.ops",
  );
  await locale(page, pt);
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
  await page
    .locator("input[autocomplete=one-time-code]")
    .fill((await page.getByTestId("sms-code").textContent())!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(
    page.getByRole("button", {
      name: pt ? "Sair" : "Cerrar sesión",
      exact: true,
    }),
  ).toBeVisible();
}
async function send(page: Page, text = "Quiero revisar una compra de prueba.") {
  await page.locator(".composer textarea").fill(text);
  await page.locator(".composer button[type=submit]").click();
}
async function inViewport(target: Locator, page: Page) {
  await expect(target).toBeVisible();
  await expect
    .poll(async () => {
      const r = await target.boundingBox();
      return !!r && r.y >= 0 && r.y + r.height <= page.viewportSize()!.height;
    })
    .toBe(true);
}
async function audit(page: Page) {
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}
for (const pt of [false, true])
  for (const width of [1440, 390]) {
    test(`${pt ? "PT" : "ES"} ${width}: three story shortcuts, login, code and chat actions fit the first view`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.goto("/");
      await expect(page.getByTestId("quickstart-explain")).toBeEnabled();
      await locale(page, pt);
      await expect(page.locator(".story-picker button")).toHaveCount(3);
      for (const btn of await page.locator(".story-picker button").all())
        await inViewport(btn, page);
      await inViewport(page.locator(".login-panel button[type=submit]"), page);
      let messages = 0;
      page.on("request", (r) => {
        if (r.method() === "POST" && r.url().endsWith("/messages")) messages++;
      });
      await page.getByTestId("quickstart-ambiguous").click();
      await expect(page.locator(".login-panel select")).toHaveValue(
        "demo.pt.br",
      );
      await expect(page.locator("input[type=password]")).toBeVisible();
      await page
        .locator("input[type=password]")
        .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
      await page.locator(".login-panel button[type=submit]").click();
      await expect(page.getByTestId("sms-code")).toHaveText(/^\d{6}$/);
      await inViewport(page.locator(".login-panel button[type=submit]"), page);
      await page
        .locator("input[autocomplete=one-time-code]")
        .fill((await page.getByTestId("sms-code").textContent())!);
      await page.locator(".login-panel button[type=submit]").click();
      await expect(page.locator(".composer textarea")).toHaveValue(
        "Não reconheço uma compra de uns 90 dólares",
      );
      await inViewport(page.locator(".composer button[type=submit]"), page);
      expect(messages).toBe(0); // Shortcuts select and draft; no send or confirmation.
      await expect(page.locator(".chat-stages li")).toHaveCount(5);
      await audit(page);
    });
  }
for (const pt of [false, true]) {
  test(`${pt ? "PT" : "ES"}: offer actions are brought into view without becoming a write`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    let confirms = 0;
    page.on("request", (r) => {
      if (r.url().endsWith("/confirm")) confirms++;
    });
    await page.route("**/chat/sessions/*/messages", (r) =>
      r.fulfill({ json: offerFixture(pt) }),
    );
    await login(page, pt);
    await send(page);
    await inViewport(page.locator(".recognition-buttons button").last(), page);
    await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
      pt ? "Decidir" : "Decidir",
    );
    await expect(page.locator(".turn-stage")).toHaveText("Decidir");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.locator(".receipt")).toHaveCount(0);
    await expect(page.locator(".composer textarea")).toBeEnabled();
    expect(confirms).toBe(0);
    await audit(page);
  });
}
test("failed Desk and Ops reads cannot masquerade as empty success; retries are GET only", async ({
  page,
}) => {
  let failing = true,
    posts = 0;
  page.on("request", (r) => {
    if (r.method() === "POST" && /\/agent\/|\/ops\//.test(r.url())) posts++;
  });
  await page.route("**/agent/handoffs", async (r) =>
    failing
      ? r.fulfill({ status: 503, json: { error: "service_unavailable" } })
      : r.continue(),
  );
  await login(page, false, "agent");
  await expect(page.locator(".queue-panel [role=alert]")).toContainText(
    "No sabemos si hay solicitudes pendientes",
  );
  await expect(page.locator(".queue-panel")).not.toContainText(
    "La cola está al día",
  );
  await expect(page.locator(".count-badge")).toHaveText("—");
  await expect(page.locator(".queue-panel [role=status]")).toHaveCount(0);
  failing = false;
  await page.locator(".queue-panel [role=alert] button").click();
  await expect(page.locator(".queue-panel [role=alert]")).toHaveCount(0);
  await expect(page.locator(".queue-panel")).toContainText(
    "La cola está al día",
  );
  await page
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await page.route("**/ops/overview", (r) =>
    r.fulfill({ status: 503, json: { error: "service_unavailable" } }),
  );
  await login(page, true, "ops");
  await expect(page.locator(".load-failed")).toContainText(
    "Não foi possível carregar as evidências",
  );
  await expect(page.locator(".metric-grid")).toHaveCount(0);
  await expect(page.getByRole("status")).toHaveCount(0);
  await page.locator(".load-failed button").click();
  await expect(page.locator(".load-failed")).toBeVisible();
  expect(posts).toBe(0);
  await audit(page);
});
test("Desk failed actions use warning cues and primary reason stays first", async ({
  page,
}) => {
  await page.route("**/agent/handoffs", (r) =>
    r.fulfill({
      json: [
        {
          ...multiReasonPacket,
          actions: [
            ...multiReasonPacket.actions,
            {
              action: "freeze_card",
              status: "failed",
              evidence_ref: "UI-FAILED-ACTION",
            },
          ],
        },
      ],
    }),
  );
  await login(page, false, "agent");
  await expect(page.locator(".handoff-reasons li").first()).toContainText(
    "FRD-01",
  );
  const failed = page.locator(".timeline-check[data-status=failed]");
  await expect(failed.locator("svg")).toHaveClass(/circle-alert/);
  await expect(failed.locator("svg.lucide-check-check")).toHaveCount(0);
  await expect(failed.locator("..")).toContainText(
    "Acción fallida · sin verificar",
  );
  await expect(failed.locator("..").locator(".badge")).toHaveClass(/red/);
  await audit(page);
});
test("startup and unavailable states never advertise green readiness", async ({
  page,
}) => {
  let release!: () => void;
  const pending = new Promise<void>((r) => {
    release = r;
  });
  await page.route("**/api/bff/config", async (r) => {
    await pending;
    await r.fulfill({ status: 503, json: { error: "service_unavailable" } });
  });
  try {
    // The connecting label is server-rendered. A bootstrap request proves
    // hydration before the test changes the language, including in dev CI.
    const boot = page.waitForRequest("**/api/bff/config");
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await boot;
    await expect(page.locator(".status-pill")).toHaveText("Conectando");
    await expect(page.locator(".status-pill")).toHaveClass(/neutral/);
    await locale(page, true);
    await expect(page.locator(".locale-select select")).toHaveValue("pt-BR");
    release();
    await expect(page.locator(".status-pill")).toHaveText(
      "Serviço indisponível",
    );
    await expect(page.locator(".clock")).toHaveText("Serviço indisponível");
    await expect(page.locator(".status-pill")).toHaveClass(/neutral/);
    await expect(page.getByRole("status")).toHaveCount(0);
    await audit(page);
  } finally {
    release();
  }
});
test("customer copy explains rule families and hides internal IDs", async ({
  page,
}) => {
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({
      json: {
        ...offerFixture(false),
        policy_rules: ["TXN-01", "AUTH-03", "SEC-01"],
      },
    }),
  );
  await login(page);
  await send(page);
  await page.getByRole("button", { name: "¿Por qué?", exact: true }).click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toContainText("Estado del movimiento");
  await expect(drawer).toContainText("Protección de tu información");
  await expect(drawer).not.toContainText(
    /TXN-01|AUTH-03|SEC-01|txn_ui_papeleria/,
  );
  await page.keyboard.press("Escape");
  await expect(page.locator(".synthetic-banner")).toHaveText(
    "Banco simulado · No es un servicio real",
  );
  await locale(page, true);
  await expect(page.locator(".synthetic-banner")).toHaveText(
    "Banco simulado · Não é um serviço real",
  );
  await expect(page.locator(".sidebar nav")).toContainText("Agent Desk");
  await expect(page.locator(".chat-stages")).toContainText(
    "EntenderDecidirAgirVerificarEncaminhar",
  );
});
test("failed send preserves the draft; unknown confirmation offers drafts without replay", async ({
  page,
}) => {
  let failMessage = true,
    confirms = 0,
    messages = 0;
  await page.route("**/chat/sessions/*/messages", (r) => {
    messages++;
    return failMessage
      ? r.fulfill({ status: 503, json: { error: "service_unavailable" } })
      : r.fulfill({ json: proposalFixture(false) });
  });
  await page.route("**/chat/sessions/*/confirm", (r) => {
    confirms++;
    return r.fulfill({ status: 503, json: { error: "service_unavailable" } });
  });
  await login(page);
  const draft = "Ayúdame con esta compra de prueba.";
  await send(page, draft);
  await expect(page.locator(".composer textarea")).toHaveValue(draft);
  failMessage = false;
  await page.locator(".composer button[type=submit]").click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Preparar consulta de estado", exact: true })
    .click();
  await expect(page.locator(".composer textarea")).toBeFocused();
  await expect(page.locator(".composer textarea")).toContainText(
    "Quiero consultar si se registró",
  );
  await page
    .getByRole("button", { name: "Preparar consulta al equipo", exact: true })
    .click();
  await expect(page.locator(".composer textarea")).toHaveValue(
    "Necesito ayuda humana para comprobar el resultado de la solicitud anterior.",
  );
  expect(confirms).toBe(1);
  expect(messages).toBe(2);
  await expect(page.locator(".receipt")).toHaveCount(0);
  await expect(page.getByTestId("quickstart-explain")).toBeDisabled();
});
test("expired and dismissed proposals retain explicit authority boundaries and permit a new review", async ({
  page,
}) => {
  let confirms = 0,
    sessions = 0;
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/chat/sessions")) sessions++;
    if (r.url().endsWith("/confirm")) confirms++;
  });
  const plan = proposalFixture(false);
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({
      json: {
        ...plan,
        proposal: {
          ...plan.proposal,
          expires_at: new Date(Date.now() + 4000).toISOString(),
        },
      },
    }),
  );
  await login(page);
  await send(page);
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".proposal-bar")).toContainText(
    "La propuesta sigue pendiente",
  );
  await expect(page.locator(".composer textarea")).toBeDisabled();
  await expect(page.getByTestId("quickstart-explain")).toBeDisabled();
  await page
    .getByRole("button", { name: "Revisar y confirmar", exact: true })
    .click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Iniciar nueva revisión", exact: true }),
  ).toBeVisible({ timeout: 10000 });
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Confirmar", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Iniciar nueva revisión", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".review-notice")).toContainText(
    "Nueva conversación preparada",
  );
  await expect(page.locator(".composer textarea")).toBeEnabled();
  expect(confirms).toBe(0);
  expect(sessions).toBe(2);
  await audit(page);
});
test("wrong renewal code keeps the same challenge and proposal for a single explicit retry", async ({
  page,
}) => {
  const confirms: unknown[] = [];
  const codes: unknown[] = [];
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({ json: proposalFixture(false) }),
  );
  await page.route("**/chat/sessions/*/confirm", (r) => {
    confirms.push(r.request().postDataJSON());
    return confirms.length === 1
      ? r.fulfill({ status: 401, json: { error: "step_up_required" } })
      : r.fulfill({
          json: {
            response_type: "cancelled",
            outcome: "cancelled",
            reply: "Respuesta de prueba, sin escritura bancaria.",
          },
        });
  });
  await page.route("**/auth/step-up", (r) =>
    r.fulfill({ json: { challenge_id: "UI-RENEWAL" } }),
  );
  await page.route("**/auth/challenges/UI-RENEWAL/sms", (r) =>
    r.fulfill({ json: { code: "123456" } }),
  );
  await page.route("**/auth/step-up/verify", (r) => {
    codes.push(r.request().postDataJSON());
    return codes.length === 1
      ? r.fulfill({ status: 401, json: { error: "invalid_otp_code" } })
      : r.fulfill({ json: { verified: true } });
  });
  await login(page);
  await send(page);
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Confirmar", exact: true }).click();
  await dialog.locator("input[autocomplete=one-time-code]").fill("000000");
  await dialog.locator("button[type=submit]").click();
  await expect(dialog.getByRole("alert")).toContainText("SMS");
  await expect(dialog.locator("input[autocomplete=one-time-code]")).toHaveValue(
    "",
  );
  expect(confirms).toHaveLength(1);
  await dialog.locator("input[autocomplete=one-time-code]").fill("123456");
  await dialog.locator("button[type=submit]").click();
  await expect(dialog).toHaveCount(0);
  expect(confirms).toEqual([
    { proposal_hash: "a".repeat(64), confirmed: true },
    { proposal_hash: "a".repeat(64), confirmed: true },
  ]);
  expect(codes).toEqual([
    { challenge_id: "UI-RENEWAL", code: "000000" },
    { challenge_id: "UI-RENEWAL", code: "123456" },
  ]);
});
test("an ended session offers sign-in again and never silently creates a write", async ({
  page,
}) => {
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({ status: 401, json: { error: "session_expired" } }),
  );
  await login(page);
  await send(page);
  await expect(page.locator(".composer textarea")).toBeDisabled();
  await expect(page.locator(".chat-header .secure-pill")).toHaveText(
    "Volver a acceder",
  );
  await expect(page.locator(".chat-header .dot")).toHaveClass(/paused/);
  await page
    .getByRole("button", { name: "Volver a acceder", exact: true })
    .click();
  await expect(page.locator("input[type=password]")).toBeVisible();
});

test("card retry keeps the challenge; expiry starts a fresh review without confirming an old hash", async ({
  page,
}) => {
  let challenges = 0,
    verifications = 0,
    writes = 0,
    proposals = 0;
  await page.route("**/api/bff/config", async (r) => {
    const config = await (await r.fetch()).json();
    await r.fulfill({ json: { ...config, fixtures: false } });
  });
  await page.route("**/chat/sessions/*/messages", (r) =>
    r.fulfill({
      json: {
        response_type: "offer_human",
        outcome: "handoff_created",
        reply: "Solicita revisión del bloqueo de tu tarjeta.",
        handoff: multiReasonPacket,
        verified: true,
        freeze_offer: [
          {
            handle: "card_ui_preview",
            product_type: "Credit",
            status: "Active",
          },
        ],
      },
    }),
  );
  await page.route("**/auth/step-up", (r) => {
    challenges++;
    return r.fulfill({ json: { challenge_id: `UI-CARD-${challenges}` } });
  });
  await page.route("**/auth/challenges/UI-CARD-*/sms", (r) =>
    r.fulfill({ json: { code: "123456" } }),
  );
  await page.route("**/auth/step-up/verify", (r) => {
    verifications++;
    return verifications === 1
      ? r.fulfill({ status: 401, json: { error: "invalid_otp_code" } })
      : r.fulfill({ json: { verified: true } });
  });
  await page.route("**/cards/card_ui_preview/freeze/proposal", (r) => {
    proposals++;
    return r.fulfill({
      json: {
        response_type: "confirm_action",
        action: "freeze_card",
        handle: "card_ui_preview",
        handoff_id: multiReasonPacket.handoff_id,
        conversation_id: "UI-CARD-CONV",
        proposal_hash: "b".repeat(64),
        expires_at: new Date(Date.now() - 1000).toISOString(),
        reply: "Revisa la solicitud de bloqueo.",
      },
    });
  });
  await page.route("**/cards/card_ui_preview/freeze", (r) => {
    writes++;
    return r.fulfill({ status: 503, json: { error: "service_unavailable" } });
  });
  await login(page);
  await send(page);
  await page
    .getByRole("button", {
      name: "Bloquear tarjeta · Tarjeta 1 · Crédito",
      exact: true,
    })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).not.toContainText(/card_ui_preview|Credit/);
  for (const story of ["explain", "ambiguous", "fraud"])
    await expect(page.getByTestId(`quickstart-${story}`)).toBeDisabled();
  await dialog.locator("input").fill("000000");
  await dialog.locator("button[type=submit]").click();
  await expect(dialog.getByRole("alert")).toContainText("SMS");
  await expect(dialog.locator("input")).toHaveValue("");
  expect(challenges).toBe(1);
  await dialog.locator("input").fill("123456");
  await dialog.locator("button[type=submit]").click();
  await expect(
    dialog.getByRole("button", { name: "Confirmar", exact: true }),
  ).toHaveCount(0);
  await dialog
    .getByRole("button", { name: "Iniciar nueva revisión", exact: true })
    .click();
  await expect(dialog.locator("input")).toBeVisible();
  await audit(page);
  expect(challenges).toBe(2);
  expect(proposals).toBe(1);
  expect(writes).toBe(0);
  for (const story of ["explain", "ambiguous", "fraud"])
    await expect(page.getByTestId(`quickstart-${story}`)).toBeDisabled();
});

test("unbound live stories stay disabled and failed preparation does not claim a new session", async ({
  page,
}) => {
  await page.route("**/api/bff/config", async (r) => {
    const c = await (await r.fetch()).json();
    await r.fulfill({
      json: {
        ...c,
        fixtures: false,
        personas: c.personas.map((p: Record<string, unknown>) => ({
          ...p,
          demo_stories: [],
        })),
      },
    });
  });
  await page.goto("/");
  // Wait for the mocked config to render all shortcuts before removing its
  // route. Locator.all() can return an empty array while bootstrap is pending.
  await expect(page.locator(".story-picker button")).toHaveCount(3);
  for (const button of await page.locator(".story-picker button").all())
    await expect(button).toBeDisabled();
  await expect(
    page.getByRole("button", { name: /Conoce los datos/ }),
  ).toBeEnabled();
  await page.unroute("**/api/bff/config");
  await login(page);
  await page.route("**/auth/logout", (r) =>
    r.fulfill({ status: 503, json: { error: "service_unavailable" } }),
  );
  await page.getByTestId("quickstart-ambiguous").click();
  await expect(page.locator(".judge-quickstart [role=alert]")).toContainText(
    "No pudimos preparar la historia",
  );
  await expect(page.locator(".composer")).toBeVisible();
  await expect(page.locator("input[type=password]")).toHaveCount(0);
});

test("phone choices show all three review actions; choosing a card still requires separate confirmation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const tx = offerFixture(false).transaction!;
  let messages = 0,
    confirms = 0;
  await page.route("**/chat/sessions/*/messages", (r) => {
    messages++;
    return r.fulfill({
      json:
        messages === 1
          ? {
              response_type: "choose_transaction",
              outcome: "choose_transaction",
              reply: "Elige el movimiento que quieres revisar.",
              candidates: [1, 2, 3].map((i) => ({
                ...tx,
                handle: `txn_ui_option_${i}`,
                amount: 60 + i,
              })),
            }
          : proposalFixture(false),
    });
  });
  page.on("request", (r) => {
    if (r.url().endsWith("/confirm")) confirms++;
  });
  await login(page);
  await send(page);
  await expect(page.locator(".chat-stages [aria-current=step]")).toHaveText(
    "Entender",
  );
  for (const button of await page.locator(".candidate-grid button").all())
    await inViewport(button, page);
  await page.locator(".candidate-grid button").nth(1).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(confirms).toBe(0);
  await audit(page);
});

test("a signed-in judge alias keeps its eligible story account and only prepares a draft", async ({
  page,
}) => {
  let posts = 0;
  page.on("request", (request) => {
    if (request.method() === "POST") posts++;
  });
  await page.route("**/api/bff/config", async (route) => {
    const config = await (await route.fetch()).json();
    const source = {
      username: "demo.es.mx",
      label: "Authored source",
      locale: "es-MX",
      role: "customer",
      demo_stories: ["explain"],
    };
    await route.fulfill({
      json: {
        ...config,
        fixtures: false,
        personas: [
          source,
          { ...source, username: "judge.authored", label: "Authored alias" },
        ],
      },
    });
  });
  await page.route("**/api/bff/me", (route) =>
    route.fulfill({
      json: {
        username: "judge.authored",
        role: "customer",
        locale: "es-MX",
        bank_clock: "2026-06-18T06:00:00Z",
        demo_stories: ["explain"],
      },
    }),
  );
  await page.goto("/");
  await expect(page.locator(".composer")).toBeVisible();
  await page.getByTestId("quickstart-explain").click();
  await expect(page.locator(".composer textarea")).toHaveValue(
    "Quiero entender un cargo en mi tarjeta.",
  );
  await expect(page.locator("input[type=password]")).toHaveCount(0);
  expect(posts).toBe(0); // No logout, message, proposal, OTP renewal or action call.
});
