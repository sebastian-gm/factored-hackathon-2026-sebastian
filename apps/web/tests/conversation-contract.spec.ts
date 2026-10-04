import { selectLoginPersona } from "./helpers/login-persona";
import { test, expect, type Page } from "./helpers/test";
import AxeBuilder from "@axe-core/playwright";
import { planSchema, orderedReasons, type Config } from "../src/lib/contracts";
import { deskSchema } from "../src/lib/staff-contracts";
import { demoStories, storyPersona } from "../src/lib/demo-stories";
import {
  offerFixture,
  proposalFixture,
  multiReasonPacket,
} from "./fixtures/conversation-ui";

async function login(page: Page, persona: string) {
  await page.goto("/");
  if (persona === "demo.agent")
    await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await selectLoginPersona(page, persona);
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
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

for (const pt of [false, true]) {
  const locale = pt ? "pt-BR" : "es-MX";
  const recognize = pt ? "Sim, reconheço" : "Sí, la reconozco";
  const recognizeMessage = pt
    ? "Sim, reconheço. Agora lembrei dessa compra."
    : "Sí, la reconozco. Ya me acordé de esta compra.";
  const deny = pt
    ? "Não reconheço, quero contestar"
    : "No la reconozco, quiero disputarla";
  const sendLabel = pt ? "Enviar mensagem" : "Enviar mensaje";

  for (const decision of ["recognize", "dispute"] as const) {
    test(`${locale} offer: ${decision} sends only a message; action confirmation stays separate`, async ({
      page,
    }) => {
      if (pt) await page.setViewportSize({ width: 390, height: 844 });
      const messages: unknown[] = [];
      const confirms: unknown[] = [];
      const offer = offerFixture(pt);
      await page.route("**/chat/sessions/*/messages", async (route) => {
        messages.push(route.request().postDataJSON());
        const result =
          messages.length === 1
            ? offer
            : decision === "dispute"
              ? proposalFixture(pt)
              : {
                  response_type: "explain_status",
                  outcome: "explained",
                  reply: pt
                    ? "Você reconheceu esta compra."
                    : "Reconociste esta compra.",
                  transaction: offer.transaction,
                };
        await route.fulfill({ json: result });
      });
      await page.route("**/chat/sessions/*/confirm", async (route) => {
        confirms.push(route.request().postDataJSON());
        await route.fulfill({
          json: {
            response_type: "cancelled",
            outcome: "cancelled",
            reply: pt
              ? "A proposta foi cancelada."
              : "La propuesta fue cancelada.",
          },
        });
      });
      await login(page, pt ? "demo.pt.br" : "demo.es.mx");
      const composer = page.getByRole("textbox", {
        name: pt ? "Sua mensagem" : "Tu mensaje",
      });
      await composer.fill(
        pt
          ? "Não reconheço uma compra na Papelaria Prisma."
          : "No reconozco una compra en Papelería Prisma.",
      );
      await page.getByRole("button", { name: sendLabel }).click();
      const actions = page.getByRole("region", {
        name: pt
          ? "Você reconhece este movimento?"
          : "¿Reconoces este movimiento?",
      });
      await expect(actions).toBeVisible();
      await expect(
        page.getByRole("heading", { name: offer.transaction!.merchant! }),
      ).toBeVisible();
      await expect(page.locator(".transaction-card")).toContainText("USD");
      await expect(page.locator(".transaction-card time")).toHaveAttribute(
        "datetime",
        offer.transaction!.transaction_date,
      );
      await expect(page.locator(".transaction-card")).toContainText(
        pt ? "Aprovado" : "Aprobado",
      );
      await expect(composer).toBeEditable();
      await expect(
        actions.getByRole("button", { name: recognize, exact: true }),
      ).toBeEnabled();
      await expect(
        actions.getByRole("button", { name: deny, exact: true }),
      ).toBeEnabled();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.locator(".receipt")).toHaveCount(0);
      expect(confirms).toEqual([]);
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
      const button = actions.getByRole("button", {
        name: decision === "recognize" ? recognize : deny,
        exact: true,
      });
      await button.focus();
      await page.keyboard.press("Enter");
      await expect(actions).toHaveCount(0);
      expect(messages).toHaveLength(2);
      expect(messages[1]).toEqual({
        message: decision === "recognize" ? recognizeMessage : deny,
      });
      expect(confirms).toEqual([]);
      if (decision === "dispute") {
        const dialog = page.getByRole("dialog");
        await expect(dialog).toBeVisible();
        await expect(dialog).toContainText(offer.transaction!.merchant!);
        await dialog
          .getByRole("button", { name: "Cancelar", exact: true })
          .click();
        await expect(
          page.getByRole("heading", {
            name: pt ? "Ação cancelada" : "Acción cancelada",
          }),
        ).toBeVisible();
        expect(confirms).toEqual([
          { proposal_hash: "a".repeat(64), confirmed: false },
        ]);
        await expect(page.getByRole("dialog")).toHaveCount(0);
        await expect(page.locator(".proposal-bar, .receipt")).toHaveCount(0);
        await expect(composer).toBeEditable();
      } else {
        await expect(page.getByRole("dialog")).toHaveCount(0);
        await expect(
          page.getByText(
            pt ? "Você reconheceu esta compra." : "Reconociste esta compra.",
            { exact: true },
          ),
        ).toBeVisible();
      }
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
    });
  }
}

test("free text remains available while awaiting recognition", async ({
  page,
}) => {
  const messages: unknown[] = [];
  await page.route("**/chat/sessions/*/messages", async (route) => {
    messages.push(route.request().postDataJSON());
    await route.fulfill({
      json:
        messages.length === 1
          ? offerFixture(false)
          : {
              response_type: "clarify",
              outcome: "clarification",
              reply: "¿Recuerdas haber hecho esa compra?",
            },
    });
  });
  await login(page, "demo.es.mx");
  const composer = page.getByRole("textbox", { name: "Tu mensaje" });
  await composer.fill("Quiero entender esta compra.");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByRole("button", { name: "Sí, la reconozco", exact: true }),
  ).toBeVisible();
  await composer.fill("Todavía no estoy segura; necesito pensarlo.");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();
  await expect(
    page.getByText("¿Recuerdas haber hecho esa compra?", { exact: true }),
  ).toBeVisible();
  expect(messages[1]).toEqual({
    message: "Todavía no estoy segura; necesito pensarlo.",
  });
  await expect(composer).toBeEditable();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("Agent Desk shows the supplied primary reason first and preserves all controls/causes", async ({
  page,
}) => {
  const legacy = {
    ...multiReasonPacket,
    handoff_id: "HO-UI-LEGACY",
    primary_reason: undefined,
    reason_codes: ["ESC-03", "ESC-01"],
  };
  await page.route("**/agent/handoffs", (route) =>
    route.fulfill({ json: [multiReasonPacket, legacy] }),
  );
  await login(page, "demo.agent");
  await page.getByRole("button", { name: "Agent Desk", exact: true }).click();
  await expect(page.locator(".queue-item [hidden]").first()).toBeHidden();
  const reasons = page.getByRole("region", {
    name: "Motivos de la derivación",
  });
  await expect(reasons.locator("li code")).toHaveText([
    "FRD-01",
    "AUTH-02",
    "ESC-02",
  ]);
  await expect(reasons.locator("li").first()).toContainText("Motivo principal");
  await expect(reasons.locator("li code").first()).toBeHidden();
  await reasons.locator("summary").first().click();
  await expect(reasons.locator("li code").first()).toBeVisible();
  await expect(reasons).toContainText(
    "las acciones verificadas se muestran abajo.",
  );
  await expect(page.locator(".packet-heading h2")).toHaveText(
    "Detalle de la solicitud",
  );
  await expect(page.locator(".packet-heading .technical-reference")).toHaveText(
    "HO-UI-MULTI",
  );
  await expect(
    page.locator(".queue-item .row-between > strong").first(),
  ).toHaveText("Persona de prueba UI");
  await expect(
    page.locator(".queue-item").first().locator(".queue-reasons"),
  ).toHaveText(
    "Fraude / tarjeta · Verificación reforzada requerida · Queja regulatoria o legal",
  );
  await page.locator(".action-references summary").click();
  await expect(page.locator(".action-timeline")).toContainText(
    "create_handoff",
  );
  await expect(page.locator(".action-timeline")).not.toContainText(
    "freeze_card",
  );
  await page.locator(".queue-item").filter({ hasText: "HO-UI-LEGACY" }).click();
  await expect(reasons.locator("li code")).toHaveText(["ESC-03", "ESC-01"]);
  await expect(reasons).toContainText(
    "El servicio no indicó un motivo principal.",
  );
  await expect(
    reasons.getByText("Motivo principal", { exact: true }),
  ).toHaveCount(0);
});

test("contract projection rejects offers carrying write authority and inconsistent primary reasons", () => {
  const offer = offerFixture(false);
  expect(planSchema.safeParse({ ...offer, transaction: null }).success).toBe(
    false,
  );
  expect(planSchema.safeParse({ ...offer, outcome: "explained" }).success).toBe(
    false,
  );
  expect(
    planSchema.safeParse({
      ...offer,
      proposal: proposalFixture(false).proposal,
    }).success,
  ).toBe(false);
  expect(planSchema.safeParse({ ...offer, session_ended: true }).success).toBe(
    false,
  );
  expect(
    planSchema.safeParse({
      ...proposalFixture(false),
      response_type: "cancelled",
      outcome: "cancelled",
    }).success,
  ).toBe(false);
  expect(
    deskSchema.safeParse({ ...multiReasonPacket, primary_reason: "ESC-01" })
      .success,
  ).toBe(false);
  expect(
    orderedReasons({
      primary_reason: "FRD-01",
      reason_codes: ["AUTH-02", "FRD-01", "AUTH-02"],
    }),
  ).toEqual(["FRD-01", "AUTH-02"]);
});

test("live recording trusts scoped story hints, allows a shared customer, and never guesses absent bindings", () => {
  const config: Config = {
    fixtures: false,
    bankClock: null,
    personas: [
      {
        username: "demo.agent",
        label: "Staff",
        role: "agent",
        locale: "es-MX",
        demo_stories: ["explain"],
      },
      {
        username: "demo.es.mx",
        label: "ES",
        role: "customer",
        locale: "es-MX",
        demo_stories: ["explain", "fraud"],
      },
      {
        username: "demo.pt.br",
        label: "PT",
        role: "customer",
        locale: "pt-BR",
        demo_stories: ["ambiguous"],
      },
    ],
  };
  expect(
    demoStories.map((story) => storyPersona(config, story)?.username),
  ).toEqual(["demo.es.mx", "demo.pt.br", "demo.es.mx"]);
  const absent = {
    ...config,
    personas: config.personas.map((p) => ({ ...p, demo_stories: undefined })),
  };
  expect(demoStories.map((story) => storyPersona(absent, story))).toEqual([
    undefined,
    undefined,
    undefined,
  ]);
  const opsOnly: Config = {
    ...config,
    personas: config.personas
      .filter((p) => p.username !== "demo.agent")
      .map((p) => ({ ...p, role: "ops" })),
  };
  expect(
    demoStories.map((story) => storyPersona(opsOnly, story)?.username),
  ).toEqual(["demo.es.mx", "demo.pt.br", "demo.es.mx"]);
  // Prefer the authenticated hinted persona, without synthesizing staff rights.
  expect(storyPersona(config, demoStories[0], "demo.agent")?.username).toBe(
    "demo.agent",
  );
});

// Exercise the actual fixture BFF: do not fulfill the /messages route here.
// The backend's 1000-character limit counts Unicode code points, not UTF-16 units.
for (const pt of [false, true])
  for (const kind of ["ascii", "emoji"] as const) {
    test(`${pt ? "PT" : "ES"} BFF ${kind}: invalid message is 422 and a valid follow-up stays read-only`, async ({
      page,
    }) => {
      await login(page, pt ? "demo.pt.br" : "demo.es.mx");
      let financialActions = 0;
      page.on("request", (request) => {
        if (
          request.method() === "POST" &&
          /\/(confirm|freeze)(?:\/proposal)?$/.test(
            new URL(request.url()).pathname,
          )
        )
          financialActions++;
      });
      const text = pt
        ? "Quero revisar um movimento de teste."
        : "Quiero revisar un movimiento de prueba.";
      const invalid =
        kind === "ascii" ? text.padEnd(1001, "x") : "🙂".repeat(1001);
      const replies = await page.evaluate(
        async ({ invalid, text }) => {
          const post = async (path: string, body: unknown) => {
            const response = await fetch(`/api/bff/${path}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            });
            return { status: response.status, body: await response.json() };
          };
          const created = await post("chat/sessions", {});
          if (created.status !== 200)
            throw new Error("Authored fixture conversation was not created");
          const path = `chat/sessions/${created.body.conversation_id}/messages`;
          return [
            await post(path, { message: invalid }),
            await post(path, { message: text.padEnd(1000, "x") }),
            // 1000 emoji occupy 2000 UTF-16 units but are 1000 Unicode characters.
            await post(path, { message: "🙂".repeat(1000) }),
            await post(path, { message: text }),
          ];
        },
        { invalid, text },
      );
      expect(replies[0]).toEqual({
        status: 422,
        body: { error: "invalid_message" },
      });
      for (const reply of replies.slice(1)) {
        expect(reply.status).toBe(200);
        const plan = planSchema.parse(reply.body);
        expect(["clarify", "choose_transaction", "explain_status"]).toContain(
          plan.response_type,
        );
        expect(plan.case ?? null).toBeNull();
        expect(plan.proposal ?? null).toBeNull();
        expect(plan.card ?? null).toBeNull();
      }
      expect(financialActions).toBe(0);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.locator(".composer textarea")).toBeEditable();
    });
  }

for (const pt of [false, true])
  for (const width of [1440, 390]) {
    test(`${pt ? "PT" : "ES"} ${width}px BFF: rejected overlong draft stays editable and recovers`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await login(page, pt ? "demo.pt.br" : "demo.es.mx");
      let financialActions = 0;
      page.on("request", (request) => {
        if (
          request.method() === "POST" &&
          /\/(confirm|freeze)(?:\/proposal)?$/.test(
            new URL(request.url()).pathname,
          )
        )
          financialActions++;
      });
      const composer = page.locator(".composer textarea");
      const alert = page.locator(".chat-panel").getByRole("alert");
      await expect(composer).toHaveAttribute("maxlength", "1000");
      // Bypass only the browser limit to exercise the real BFF rejection and
      // form recovery. No message response is mocked or fulfilled by this test.
      await composer.evaluate((input) => input.removeAttribute("maxlength"));
      const text = pt
        ? "Quero revisar um movimento de teste."
        : "Quiero revisar un movimiento de prueba.";
      const invalid = text.padEnd(1001, "x");
      const send = page.getByRole("button", {
        name: pt ? "Enviar mensagem" : "Enviar mensaje",
        exact: true,
      });
      const messageResponse = () =>
        page.waitForResponse(
          (response) =>
            response.request().method() === "POST" &&
            /\/chat\/sessions\/[^/]+\/messages$/.test(
              new URL(response.url()).pathname,
            ),
        );
      await composer.fill(invalid);
      const rejected = messageResponse();
      await send.click();
      const rejection = await rejected;
      expect(rejection.status()).toBe(422);
      expect(await rejection.json()).toEqual({ error: "invalid_message" });
      await expect(alert).toHaveText(
        pt
          ? "Não foi possível concluir a solicitação. Tente novamente."
          : "No pudimos completar la solicitud. Inténtalo de nuevo.",
      );
      await expect(composer).toBeEditable();
      await expect(composer).toHaveValue(invalid);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await composer.fill(text);
      const accepted = messageResponse();
      await send.click();
      const followUp = await accepted;
      expect(followUp.status()).toBe(200);
      const plan = planSchema.parse(await followUp.json());
      expect(["clarify", "choose_transaction", "explain_status"]).toContain(
        plan.response_type,
      );
      expect(plan.case ?? null).toBeNull();
      expect(plan.proposal ?? null).toBeNull();
      expect(plan.card ?? null).toBeNull();
      await expect(
        page.locator(".chat-line.aclara .bubble > p").last(),
      ).toHaveText(plan.reply);
      await expect(alert).toHaveCount(0);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.locator(".receipt")).toHaveCount(0);
      await expect(composer).toBeEditable();
      await expect(composer).toHaveValue("");
      expect(financialActions).toBe(0);
    });
  }
