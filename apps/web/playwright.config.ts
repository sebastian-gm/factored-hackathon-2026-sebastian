import { defineConfig, devices } from "@playwright/test";
const staff = process.env.FRONTEND_E2E_STAFF === "1";
const live = process.env.FRONTEND_E2E_LIVE === "1";
const judgeRoles = process.env.FRONTEND_E2E_JUDGE_ROLES === "1";
const secret = process.env.FRONTEND_FIXTURE_PASSWORD ?? "";
const webPort = Number(process.env.FRONTEND_E2E_WEB_PORT ?? "3212");
const apiPort = Number(process.env.FRONTEND_E2E_API_PORT ?? "8212");
if (
  [webPort, apiPort].some(
    (port) => !Number.isInteger(port) || port < 1024 || port > 65535,
  ) ||
  webPort === apiPort
)
  throw new Error(
    "Browser test ports must be distinct valid unprivileged ports",
  );
export default defineConfig({
  testDir: "./tests",
  testMatch: judgeRoles
    ? "**/judge-trusted-roles.spec.ts"
    : staff
      ? ["**/staff.spec.ts", "**/staff-realm.spec.ts"]
      : live
        ? "**/live.spec.ts"
        : [
            "**/stories.spec.ts",
            "**/conversation-contract.spec.ts",
            "**/startup.spec.ts",
            "**/judge-ux.spec.ts",
            "**/ux-review.spec.ts",
            "**/insights.spec.ts",
            "**/video-readiness.spec.ts",
            "**/minimal-design.spec.ts",
            "**/judge-profiles.spec.ts",
            "**/judge-guide.spec.ts",
            "**/admission.spec.ts",
            "**/resilience-ux.spec.ts",
          ],
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  retries: 0,
  outputDir: "../../artifacts/frontend/playwright",
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
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
            url: `http://127.0.0.1:${apiPort}/healthz`,
            reuseExistingServer: false,
            env: {
              FRONTEND_FIXTURE_PASSWORD: secret,
              FRONTEND_E2E_STAFF: staff ? "1" : "0",
              FRONTEND_E2E_API_PORT: String(apiPort),
            },
            stdout: "ignore" as const,
            stderr: "pipe" as const,
          },
        ]
      : []),
    {
      command:
        process.env.FRONTEND_E2E_PRODUCTION === "1"
          ? `pnpm exec next start --hostname 127.0.0.1 --port ${webPort}`
          : `pnpm dev --webpack --hostname 127.0.0.1 --port ${webPort}`,
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      timeout: 120000,
      env: {
        WATCHPACK_POLLING: "1000",
        FRONTEND_ALLOW_DEMO_RESET: staff ? "true" : "false",
        FRONTEND_DEMO_MODE: live ? "live" : "fixtures",
        FRONTEND_FIXTURE_PASSWORD: secret,
        FRONTEND_FIXTURE_JUDGE_ACCESS: live ? "false" : "true",
        FRONTEND_FIXTURE_JUDGE_TRUSTED_ROLES: judgeRoles ? "true" : "false",
        NEXT_TELEMETRY_DISABLED: "1",
        // Exercise ACA header parsing with a test-owned simulated ingress.
        CONTAINER_APP_NAME: "aclara-browser-fixture",
        API_BASE_URL: `http://127.0.0.1:${apiPort}`,
        BANK_CLOCK: "2026-06-18T06:00:00Z",
      },
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
