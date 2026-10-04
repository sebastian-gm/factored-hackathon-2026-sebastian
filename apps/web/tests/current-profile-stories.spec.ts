import { test, expect, type Page } from "./helpers/test";
import {
  demoStories,
  storyProfile,
  ledgerStoryDraft,
} from "../src/lib/demo-stories";
import type {
  JudgeProfile,
  ProfileId,
  Transaction,
} from "../src/lib/contracts";

// Authored metadata and browser fixtures only; no serving or evaluation inputs.
const profiles: JudgeProfile[] = [
  {
    profile_id: "mx-es",
    label: "MX",
    locale: "es-MX",
    language: "es",
    demo_stories: ["explain", "fraud"],
  },
  {
    profile_id: "co-es",
    label: "CO",
    locale: "es-CO",
    language: "es",
    demo_stories: ["explain", "fraud"],
  },
  {
    profile_id: "ar-es",
    label: "AR",
    locale: "es-AR",
    language: "es",
    demo_stories: ["explain", "fraud"],
  },
  {
    profile_id: "pt",
    label: "PT",
    locale: "pt-BR",
    language: "pt",
    demo_stories: ["ambiguous"],
  },
];

const purchases: Record<ProfileId, Transaction> = {
  "mx-es": {
    handle: "UI-MX",
    merchant: "Tienda Luna",
    amount: 11.25,
    currency: "USD",
    transaction_date: "2026-06-12T16:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
  "co-es": {
    handle: "UI-CO",
    merchant: "Librería Cumbre",
    amount: 73050,
    currency: "COP",
    transaction_date: "2026-06-13T16:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
  "ar-es": {
    handle: "UI-AR",
    merchant: "Mercado Delta",
    amount: 9800.5,
    currency: "ARS",
    transaction_date: "2026-06-14T16:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
  pt: {
    handle: "UI-PT",
    merchant: "Papelaria Clara",
    amount: 91.15,
    currency: "USD",
    transaction_date: "2026-06-15T16:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
};
const expectedDrafts: Record<ProfileId, string> = {
  "mx-es": "¿Qué es el cargo de Tienda Luna por 11.25 USD del 2026-06-12?",
  "co-es": "¿Qué es el cargo de Librería Cumbre por 73050 COP del 2026-06-13?",
  "ar-es": "¿Qué es el cargo de Mercado Delta por 9800.5 ARS del 2026-06-14?",
  pt: "O que é a cobrança de Papelaria Clara por 91.15 USD em 2026-06-15?",
};

test("ledger draft uses the latest complete purchase without rounding or changing the input", () => {
  const rows = [
    purchases["mx-es"],
    { ...purchases.pt, amount: 91.125 },
    {
      ...purchases.pt,
      merchant: null,
      transaction_date: "2026-06-16T00:00:00Z",
    },
  ];
  const before = JSON.stringify(rows);
  expect(ledgerStoryDraft(demoStories[1], rows)).toBe(
    "O que é a cobrança de Papelaria Clara por 91.125 USD em 2026-06-15?",
  );
  expect(JSON.stringify(rows)).toBe(before);
  expect(
    ledgerStoryDraft(demoStories[0], [
      purchases.pt,
      { ...purchases["mx-es"], status: "Pending" },
    ]),
  ).toBe(expectedDrafts["mx-es"]);
  expect(ledgerStoryDraft(demoStories[0], [])).toBeNull();
  expect(
    ledgerStoryDraft(demoStories[0], [
      { ...purchases.pt, transaction_type: "Transfer" },
    ]),
  ).toBeNull();
});

for (const width of [1440, 390])
  test(`PT ${width}px: Entender skips merchant-less charges and prefers a complete pending charge`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    const observed = watchAuthority(page);
    await page.route("**/api/bff/transactions", (route) =>
      route.fulfill({
        json: [
          {
            ...purchases.pt,
            handle: "UI-PT-no-merchant",
            merchant: null,
            status: "Pending",
          },
          {
            ...purchases.pt,
            handle: "UI-PT-blank-merchant",
            merchant: "  ",
            status: "Pending",
          },
          {
            ...purchases.pt,
            handle: "UI-PT-approved",
            merchant: "Mercado Sol",
          },
          {
            ...purchases.pt,
            status: "Pending",
            transaction_date: "2026-06-14T16:00:00Z",
          },
        ],
      }),
    );
    await loginJudge(page);
    await page.getByTestId("profile-pt").click();
    await expect(page.locator(".composer textarea")).toBeEditable();
    await page.getByTestId("quickstart-ambiguous").click();
    await expect(page.locator(".composer textarea")).toHaveValue(
      "O que é a cobrança de Papelaria Clara por 91.15 USD em 2026-06-14?",
    );
    await expect(page.locator(".composer textarea")).toBeFocused();
    await expect(page.locator(".composer textarea")).toBeInViewport();
    expect(observed.actions()).toBe(0);
  });

for (const id of ["co-es", "ar-es"] as const) {
  test(`${id}: eligible current story wins over the preferred MX profile`, () => {
    for (const story of [demoStories[0], demoStories[2]])
      expect(storyProfile(profiles, story, id)?.profile_id).toBe(id);
  });
}

test("explicit cross-profile recording stories keep their eligible fallback", () => {
  expect(storyProfile(profiles, demoStories[1], "co-es")?.profile_id).toBe(
    "pt",
  );
  expect(storyProfile(profiles, demoStories[0], "pt")?.profile_id).toBe(
    "mx-es",
  );
  expect(storyProfile(profiles, demoStories[0])?.profile_id).toBe("mx-es");
  expect(storyProfile([], demoStories[0], "co-es")).toBeUndefined();
});

async function loginJudge(page: Page) {
  await page.route("**/api/bff/config", async (route) => {
    const config = await (await route.fetch()).json();
    await route.fulfill({
      json: {
        ...config,
        personas: [
          {
            username: "demo.judge",
            label: "Judge",
            role: "customer",
            locale: "es-MX",
          },
        ],
      },
    });
  });
  await page.route("**/auth/judge/profiles", async (route) => {
    const current = await (await route.fetch()).json();
    await route.fulfill({ json: { ...current, profiles } });
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

function watchAuthority(page: Page) {
  const selections: ProfileId[] = [];
  let actions = 0;
  page.on("request", (request) => {
    if (request.method() !== "POST") return;
    const path = new URL(request.url()).pathname;
    if (path.endsWith("/auth/judge/profile"))
      selections.push(request.postDataJSON().profile_id);
    if (/\/(messages|confirm|freeze|claim|reset)$/.test(path)) actions++;
  });
  return { selections, actions: () => actions };
}

for (const id of ["mx-es", "co-es", "ar-es", "pt"] as const)
  for (const width of [1440, 390]) {
    test(`${id} ${width}px: Quickstart reads the current profile ledger and only prepares a draft`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      const observed = watchAuthority(page);
      let ledgerReads = 0;
      await page.route("**/api/bff/transactions", async (route) => {
        ledgerReads++;
        expect(observed.selections.at(-1)).toBe(id);
        expect(route.request().method()).toBe("GET");
        await route.fulfill({ json: [purchases[id]] });
      });
      await loginJudge(page);
      await page.getByTestId(`profile-${id}`).click();
      await expect(page.locator(".composer textarea")).toBeEditable();
      expect(ledgerReads).toBe(0);
      await page
        .getByTestId(
          id === "pt" ? "quickstart-ambiguous" : "quickstart-explain",
        )
        .click();
      await expect.poll(() => observed.selections.length).toBe(2);
      await expect(page.locator(".composer textarea")).toHaveValue(
        expectedDrafts[id],
      );
      expect(ledgerReads).toBeGreaterThan(0);
      await expect(page.locator(".composer textarea")).toBeFocused();
      await expect(page.locator(".composer textarea")).toBeInViewport();
      expect(observed.selections).toEqual([id, id]);
      expect(observed.actions()).toBe(0);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(
        page.locator(".chat-line, .receipt, .proposal-bar"),
      ).toHaveCount(0);
      if (id === "pt")
        await expect(page.getByTestId("quickstart-ambiguous")).toHaveText(
          "Entender cobrança",
        );
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    });
  }

test("recording helper can explicitly prepare a PT story from the CO profile", async ({
  page,
}) => {
  const observed = watchAuthority(page);
  await page.route("**/api/bff/transactions", (route) =>
    route.fulfill({ json: [purchases.pt] }),
  );
  await loginJudge(page);
  await page.getByTestId("profile-co-es").click();
  await expect(
    page.getByRole("button", { name: /Cambiar perfil/ }),
  ).toContainText("CO");
  const helper = page.locator("#recording-helper");
  await helper.locator("summary").click();
  await helper
    .getByRole("button", { name: "Elegir una compra · PT", exact: true })
    .click();
  await expect.poll(() => observed.selections.length).toBe(2);
  await expect(
    page.getByRole("button", { name: /Trocar perfil/ }),
  ).toContainText("Falante PT");
  await expect(page.locator(".composer textarea")).toHaveValue(
    expectedDrafts.pt,
  );
  expect(observed.selections).toEqual(["co-es", "pt"]);
  expect(observed.actions()).toBe(0);
});

for (const profile of ["mx-es", "pt"] as const)
  for (const failure of ["empty", "unavailable", "malformed"] as const)
    test(`${profile} Quickstart ${failure} ledger explains the generic fallback and leaves it editable`, async ({
      page,
    }) => {
      const observed = watchAuthority(page);
      await page.route("**/api/bff/transactions", (route) =>
        route.fulfill({
          status: failure === "unavailable" ? 503 : 200,
          json:
            failure === "empty"
              ? []
              : failure === "malformed"
                ? [{ handle: "UI-incomplete" }]
                : { error: "service_unavailable" },
        }),
      );
      await loginJudge(page);
      await page.getByTestId(`profile-${profile}`).click();
      await expect(page.locator(".composer textarea")).toBeEditable();
      await page
        .getByTestId(
          profile === "pt" ? "quickstart-ambiguous" : "quickstart-explain",
        )
        .click();
      await expect(
        page.locator(".customer-grid").getByRole("alert"),
      ).toHaveText(
        profile === "pt"
          ? "Não encontramos uma compra com dados completos para preparar a mensagem. Você pode escrever sua consulta."
          : "No encontramos una compra con datos completos para preparar el mensaje. Puedes escribir tu consulta.",
      );
      await expect(page.locator(".composer textarea")).toBeEditable();
      await expect(page.locator(".composer textarea")).toHaveValue(
        profile === "pt"
          ? "Quero entender uma cobrança. Quais dados preciso informar para identificar a compra?"
          : "Quiero entender un cargo. ¿Qué datos necesitas para identificarlo?",
      );
      expect(observed.actions()).toBe(0);
    });

test("late ledger response from a retired profile cannot fill the new profile draft", async ({
  page,
}) => {
  const observed = watchAuthority(page);
  let releaseOld!: () => void;
  let finishedOld!: () => void;
  const oldReady = new Promise<void>((resolve) => {
    releaseOld = resolve;
  });
  const oldFinished = new Promise<void>((resolve) => {
    finishedOld = resolve;
  });
  let reads = 0;
  await page.route("**/api/bff/transactions", async (route) => {
    const profile = observed.selections.at(-1)!;
    reads++;
    if (profile === "co-es") {
      await oldReady;
      try {
        await route.fulfill({ json: [purchases["co-es"]] });
      } catch {
        /* The retired request may already be aborted. */
      } finally {
        finishedOld();
      }
    } else await route.fulfill({ json: [purchases.pt] });
  });
  await loginJudge(page);
  await page.getByTestId("profile-co-es").click();
  await expect(page.locator(".composer textarea")).toBeEditable();
  await page.getByTestId("quickstart-explain").click();
  await expect.poll(() => reads).toBeGreaterThan(0);
  await expect(page.getByTestId("quickstart-explain")).toBeDisabled();
  await page.getByRole("button", { name: /Cambiar perfil/ }).click();
  await page.getByTestId("profile-pt").click();
  await expect(page.locator(".composer textarea")).toBeEditable();
  await page.getByTestId("quickstart-ambiguous").click();
  await expect(page.locator(".composer textarea")).toHaveValue(
    expectedDrafts.pt,
  );
  releaseOld();
  await oldFinished;
  await expect(page.locator(".composer textarea")).toHaveValue(
    expectedDrafts.pt,
  );
  expect(observed.actions()).toBe(0);
});
