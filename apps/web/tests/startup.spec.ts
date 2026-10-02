import { test, expect } from "./helpers/test";
import { upstreamFetch } from "../src/lib/server/upstream-fetch";

test("BFF timing reports duration on reads and refusals without altering authority", async ({
  request,
}) => {
  const config = await request.get("/api/bff/config");
  expect(config.status()).toBe(200);
  expect(config.headers()["server-timing"]).toMatch(
    /^aclara_bff;dur=\d+\.\d{2}$/,
  );
  expect(config.headers()["cache-control"]).toBe("no-store, private");
  const publicConfig = await config.json();
  expect(publicConfig.personas.length).toBeGreaterThan(0);
  expect(
    publicConfig.personas.every(
      (p: { role: string; username: string }) =>
        p.role === "customer" &&
        !p.username.startsWith("judge.") &&
        !["demo.agent", "demo.ops", "demo.judge"].includes(p.username),
    ),
  ).toBe(true);
  const refused = await request.post("/api/bff/chat/sessions", {
    headers: { Origin: "https://authored-other.invalid" },
    data: {},
  });
  expect(refused.status()).toBe(403);
  expect(await refused.json()).toEqual({ error: "origin_rejected" });
  expect(refused.headers()["server-timing"]).toMatch(
    /^aclara_bff;dur=\d+\.\d{2}$/,
  );
});

for (const path of ["me", "clock", "transactions", "config", "personas"]) {
  test(`startup GET ${path} has a cold-start timeout and one retry`, async () => {
    const originalFetch = globalThis.fetch;
    const originalTimeout = AbortSignal.timeout;
    const timeouts: number[] = [];
    const signals: AbortSignal[] = [];
    let calls = 0;
    AbortSignal.timeout = (ms: number) => {
      timeouts.push(ms);
      return new AbortController().signal;
    };
    globalThis.fetch = async (_url, init) => {
      signals.push(init!.signal!);
      calls++;
      if (calls === 1) throw new Error("cold API timeout");
      return Response.json({ ready: true });
    };
    try {
      const result = await upstreamFetch("http://fixture/", path, {
        method: "GET",
      });
      expect(result.status).toBe(200);
      expect(calls).toBe(2);
      expect(timeouts).toEqual([75000, 75000]);
      expect(signals[0]).not.toBe(signals[1]);
    } finally {
      globalThis.fetch = originalFetch;
      AbortSignal.timeout = originalTimeout;
    }
  });
}

for (const status of [401, 403, 429, 500, 502, 503, 504]) {
  test(`GET retry respects HTTP ${status}`, async () => {
    const original = globalThis.fetch;
    let calls = 0;
    globalThis.fetch = async () => {
      calls++;
      return Response.json({}, { status });
    };
    try {
      expect(
        (await upstreamFetch("http://fixture", "me", { method: "GET" })).status,
      ).toBe(status);
      expect(calls).toBe([502, 503, 504].includes(status) ? 2 : 1);
    } finally {
      globalThis.fetch = original;
    }
  });
}

for (const path of [
  "auth/login",
  "chat/sessions",
  "chat/sessions/fixture/messages",
  "chat/sessions/fixture/confirm",
  "cards/fixture/freeze",
]) {
  for (const networkFailure of [false, true]) {
    test(`POST ${path} is never replayed (${networkFailure ? "network" : "503"})`, async () => {
      const original = globalThis.fetch;
      let calls = 0;
      globalThis.fetch = async () => {
        calls++;
        if (networkFailure) throw new Error("connection lost");
        return Response.json({}, { status: 503 });
      };
      try {
        const call = upstreamFetch("http://fixture", path, {
          method: "POST",
          body: "{}",
        });
        if (networkFailure)
          await expect(call).rejects.toThrow("connection lost");
        else expect((await call).status).toBe(503);
        expect(calls).toBe(1);
      } finally {
        globalThis.fetch = original;
      }
    });
  }
}

test("a second GET network failure ends the retry", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw new Error("still unavailable");
  };
  try {
    await expect(
      upstreamFetch("http://fixture", "me", { method: "GET" }),
    ).rejects.toThrow("still unavailable");
    expect(calls).toBe(2);
  } finally {
    globalThis.fetch = original;
  }
});

test("startup stays friendly in ES and PT while configuration is pending", async ({
  page,
}) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/bff/config", async (route) => {
    await pending;
    await route.continue();
  });
  try {
    // The startup text also renders on the server. Wait for the bootstrap fetch
    // to prove hydration before interacting with the locale selector.
    const boot = page.waitForRequest("**/api/bff/config");
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await boot;
    await expect(page.getByRole("status")).toHaveText("Iniciando el servicio…");
    await expect(page.locator(".clock")).toHaveText("Iniciando el servicio…");
    await page.getByLabel("Idioma y región").selectOption("pt-BR");
    await expect(page.getByRole("status")).toHaveText("Iniciando o serviço…");
    release();
    await expect(page.locator("input[type=password]")).toBeVisible();
    await expect(page.locator(".clock")).not.toContainText("Iniciando");
  } finally {
    release();
  }
});

test("failed startup offers a friendly retry instead of the chat error", async ({
  page,
}) => {
  await page.route("**/api/bff/config", (route) =>
    route.fulfill({ status: 503, json: { error: "service_unavailable" } }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "El servicio aún no está disponible. Vuelve a intentarlo.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Volver a intentar" }),
  ).toBeVisible();
  await expect(
    page.getByText("No pudimos completar la solicitud. Inténtalo de nuevo."),
  ).toHaveCount(0);
});

test("a transient identity-read failure does not silently render a fresh login", async ({
  page,
}) => {
  await page.route("**/api/bff/me", (route) =>
    route.fulfill({ status: 503, json: { error: "service_unavailable" } }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "El servicio aún no está disponible. Vuelve a intentarlo.",
    }),
  ).toBeVisible();
  await expect(page.locator("input[type=password]")).toHaveCount(0);
});
