import { defineConfig, devices } from "@playwright/test";
const staff = process.env.FRONTEND_E2E_STAFF === "1";
const live = process.env.FRONTEND_E2E_LIVE === "1";
const secret = process.env.FRONTEND_FIXTURE_PASSWORD ?? "";
export default defineConfig({
  testDir: "./tests",
  testMatch: staff
    ? "**/staff.spec.ts"
    : live
      ? "**/live.spec.ts"
      : [
          "**/stories.spec.ts",
          "**/conversation-contract.spec.ts",
          "**/startup.spec.ts",
          "**/judge-ux.spec.ts",
        ],
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  retries: 0,
  outputDir: "../../artifacts/frontend/playwright",
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3212",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    ...(live
      ? [
          {
            command: "../../.venv/bin/python scripts/fixture-bank.py",
            url: "http://127.0.0.1:8212/healthz",
            reuseExistingServer: false,
            env: {
              FRONTEND_FIXTURE_PASSWORD: secret,
              FRONTEND_E2E_STAFF: staff ? "1" : "0",
            },
            stdout: "ignore" as const,
            stderr: "pipe" as const,
          },
        ]
      : []),
    {
      command:
        process.env.FRONTEND_E2E_PRODUCTION === "1"
          ? "pnpm exec next start --hostname 127.0.0.1 --port 3212"
          : "pnpm dev --webpack --hostname 127.0.0.1 --port 3212",
      url: "http://127.0.0.1:3212",
      reuseExistingServer: false,
      timeout: 120000,
      env: {
        WATCHPACK_POLLING: "1000",
        FRONTEND_ALLOW_DEMO_RESET: staff ? "true" : "false",
        FRONTEND_DEMO_MODE: live ? "live" : "fixtures",
        FRONTEND_FIXTURE_PASSWORD: secret,
        NEXT_TELEMETRY_DISABLED: "1",
        API_BASE_URL: "http://127.0.0.1:8212",
        BANK_CLOCK: "2026-06-18T06:00:00Z",
      },
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
