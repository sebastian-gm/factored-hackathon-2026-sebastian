import { test, expect } from "./test";

test.beforeEach(async () => {
  const port = process.env.FRONTEND_E2E_API_PORT ?? "8212";
  const response = await fetch(
    `http://127.0.0.1:${port}/_fixture/reset-bank-state`,
    {
      method: "POST",
      headers: { "X-Fixture-Secret": process.env.FRONTEND_FIXTURE_PASSWORD! },
    },
  );
  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ reset: true });
});
