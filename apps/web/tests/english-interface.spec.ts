import AxeBuilder from "@axe-core/playwright";
import { test, expect, type Page } from "./helpers/test";
import { staffGuidance } from "../src/lib/staff-guidance-en";
import { offerFixture } from "./fixtures/conversation-ui";

// Authored UI fixtures only. Customer language and interface language are separate.
const notice =
  "Customers chat in Spanish or Portuguese, the languages this bank serves. The interface is in English for reviewers.";
const profiles = [
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

async function audit(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
}

async function englishDefault(page: Page) {
  await page.addInitScript(() => {
    if (/^https?:$/.test(location.protocol))
      localStorage.removeItem("aclara.interfaceLanguage");
  });
}

async function loginJudge(page: Page) {
  await englishDefault(page);
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
  await page.goto("/");
  await expect(page.getByLabel("Interface language")).toHaveValue("en-US");
  await expect(page.locator(".login-panel")).toContainText("Password");
  await audit(page);
  await page
    .locator("input[type=password]")
    .fill(process.env.FRONTEND_FIXTURE_PASSWORD!);
  await page.locator(".login-panel button[type=submit]").click();
  const sms = page.getByTestId("sms-code");
  await expect(sms).toHaveText(/^\d{6}$/);
  await page
    .locator("input[autocomplete=one-time-code]")
    .fill((await sms.textContent())!);
  await page.locator(".login-panel button[type=submit]").click();
  await expect(page.getByTestId("profile-mx-es")).toBeEnabled();
  await expect(page.locator(".profile-picker h2")).toContainText("profile");
  await expect(page.getByTestId("profile-pt")).toContainText("Portuguese");
  await audit(page);
}

for (const width of [1440, 390])
  for (const pt of [false, true])
    test(`EN ${width}px with ${pt ? "PT" : "ES"} customer: English chrome, scoped draft, original reply and translated status`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      const errors: string[] = [];
      const messageLanguages: string[] = [];
      let messages = 0;
      page.on("pageerror", (error) => errors.push(error.message));
      const response = {
        ...offerFixture(pt),
        policy_rules: ["TXN-01", "AUTH-03"],
      };
      await page.route("**/api/bff/transactions", (route) =>
        route.fulfill({ json: [response.transaction] }),
      );
      await page.route("**/chat/sessions/*/messages", (route) => {
        messages++;
        messageLanguages.push(route.request().headers()["accept-language"]);
        return route.fulfill({ json: response });
      });
      await loginJudge(page);
      await page.getByTestId(`profile-${pt ? "pt" : "mx-es"}`).click();
      await expect(page.locator(".composer textarea")).toBeEditable();
      await expect(page.getByLabel("Interface language")).toHaveValue("en-US");
      await expect(page.locator(".chat-header")).toContainText(notice);
      await expect(page.locator(".chat-stages")).toContainText("Understand");
      await expect(page.locator(".chat-stages")).toContainText("Verify");
      const quickstart = page.getByTestId(
        pt ? "quickstart-ambiguous" : "quickstart-explain",
      );
      await expect(quickstart).toContainText("Understand");
      await quickstart.click();
      await expect(page.locator(".composer textarea")).toHaveValue(
        pt
          ? "O que é a cobrança de Papelaria Prisma por 64.25 USD?"
          : "¿Qué es el cargo de Papelería Prisma por 64.25 USD?",
      );
      expect(messages).toBe(0);
      await expect(page.locator(".composer textarea")).toBeInViewport();
      await audit(page);
      await page.locator(".composer button[type=submit]").click();
      await expect(page.locator(".chat-line.aclara .bubble")).toContainText(
        response.reply,
      );
      await expect(page.locator(".transaction-card .badge")).toHaveText(
        "Approved",
      );
      expect(messageLanguages).toEqual([pt ? "pt-BR" : "es-MX"]);
      await page.getByRole("button", { name: "Why?", exact: true }).click();
      await expect(page.getByRole("dialog")).toContainText(
        "Transaction status",
      );
      await expect(page.getByRole("dialog")).not.toContainText(
        /Estado del movimiento|Estado do movimento/,
      );
      await audit(page);
      await page.keyboard.press("Escape");
      await page.getByLabel("Interface language").selectOption("es-MX");
      await expect(
        page.locator(".composer button[type=submit]"),
      ).toHaveAttribute("aria-label", /Enviar/);
      await page.locator(".locale-select select").selectOption("pt-BR");
      await expect(
        page.locator(".composer button[type=submit]"),
      ).toHaveAttribute("aria-label", /Enviar/);
      await page.locator(".locale-select select").selectOption("en-US");
      await expect(
        page.locator(".composer button[type=submit]"),
      ).toHaveAttribute("aria-label", /Send/);
      expect(messages).toBe(1);
      expect(errors).toEqual([]);
    });

for (const width of [1440, 390])
  test(`EN ${width}px: Insights has English headings, legends and evidence notes without writes`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    await englishDefault(page);
    const writes: string[] = [],
      errors: string[] = [];
    page.on("request", (request) => {
      if (!["GET", "HEAD"].includes(request.method()))
        writes.push(request.url());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/insights");
    await expect(page.getByLabel("Interface language")).toHaveValue("en-US");
    await expect(page.locator(".insights-hero")).toContainText("complaints");
    await expect(page.locator(".insights-hero-stat")).toContainText(
      "first contact",
    );
    await expect(page.getByTestId("insights-comparison")).toContainText(
      "Rules only",
    );
    await expect(page.locator(".insights-safety")).toContainText("safety");
    await expect(page.getByTestId("insights-latency")).toContainText("cold");
    await expect(page.locator(".insights-sources")).toContainText("Source");
    await audit(page);
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  });

for (const state of ["rate-limited", "expired", "degraded", "healthy"] as const)
  test(`EN phone: ${state} message shows the appropriate English notice`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await loginJudge(page);
    await page.getByTestId("profile-mx-es").click();
    await expect(page.locator(".composer textarea")).toBeEditable();
    let sends = 0;
    await page.route("**/chat/sessions/*/messages", (route) => {
      sends++;
      return route.fulfill(
        state === "rate-limited"
          ? {
              status: 429,
              headers: { "Retry-After": "7" },
              json: { error: "rate_limited" },
            }
          : state === "expired"
            ? { status: 401, json: { error: "session_expired" } }
            : {
                json: {
                  ...offerFixture(false),
                  degraded: state === "degraded",
                },
              },
      );
    });
    await page
      .locator(".composer textarea")
      .fill("Quiero revisar esta compra.");
    await page.locator(".composer button[type=submit]").click();
    if (state === "rate-limited") {
      await expect(
        page.locator("#main-content").getByRole("alert"),
      ).toContainText("Too many attempts");
      await expect(page.locator(".composer textarea")).toHaveValue(
        "Quiero revisar esta compra.",
      );
    } else if (state === "expired") {
      await expect(
        page.locator("#main-content").getByRole("alert"),
      ).toContainText("Your session expired");
      await expect(page.locator(".composer textarea")).toHaveCount(0);
      await expect(page.locator("input[type=password]")).toBeVisible();
    } else {
      await expect(page.locator(".chat-line.aclara .bubble")).toContainText(
        offerFixture(false).reply,
      );
      if (state === "degraded")
        await expect(page.getByTestId("basic-mode")).toHaveText(
          "Basic mode · You can continue your inquiry.",
        );
      else await expect(page.getByTestId("basic-mode")).toHaveCount(0);
    }
    expect(sends).toBe(1);
    await audit(page);
  });

test("EN staff guidance is reason-based and has a conservative unknown-code fallback", () => {
  const fraud = staffGuidance(["FRD-01"])[0];
  expect(fraud.summary).toBe("The request needs fraud review.");
  expect(fraud.question).toContain("lost card");
  expect(fraud.next).toContain("fraud team");
  expect(staffGuidance(["UNKNOWN-01"])[0].next).toContain(
    "no outcome is guaranteed",
  );
});
