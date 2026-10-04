import { test, expect, type Page } from "./helpers/test";
import { demoStories, storyProfile } from "../src/lib/demo-stories";
import type { JudgeProfile, ProfileId } from "../src/lib/contracts";

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

for (const id of ["co-es", "ar-es"] as const) {
  test(`${id}: Quickstart preserves the chosen customer and only prepares a draft`, async ({
    page,
  }) => {
    const observed = watchAuthority(page);
    await loginJudge(page);
    await page.getByTestId(`profile-${id}`).click();
    await expect(
      page.getByRole("button", { name: /Cambiar perfil/ }),
    ).toContainText(id === "co-es" ? "CO" : "AR");
    await page.getByTestId("quickstart-explain").click();
    await expect.poll(() => observed.selections.length).toBe(2);
    await expect(page.locator(".composer textarea")).toHaveValue(
      "Quiero entender un cargo en mi tarjeta.",
    );
    expect(observed.selections).toEqual([id, id]);
    expect(observed.actions()).toBe(0);
  });
}

test("recording helper can explicitly prepare a PT story from the CO profile", async ({
  page,
}) => {
  const observed = watchAuthority(page);
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
    "Quero entender uma cobrança no meu cartão. Quais compras posso revisar?",
  );
  expect(observed.selections).toEqual(["co-es", "pt"]);
  expect(observed.actions()).toBe(0);
});
