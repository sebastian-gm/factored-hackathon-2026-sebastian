import { defineConfig } from "@playwright/test";

// Playwright otherwise creates a DOM snapshot even when traces are disabled.
process.env.PLAYWRIGHT_NO_COPY_PROMPT = "1";

// External stack only: never start a fixture server or reuse ordinary test config.
const mode = process.env.JUDGE_TOUR_MODE;
const url = new URL(process.env.JUDGE_TOUR_URL ?? "http://localhost");
if (
  !["demo", "live"].includes(mode ?? "") ||
  url.username ||
  url.password ||
  url.search ||
  url.hash ||
  url.pathname !== "/" ||
  (mode === "live" && url.protocol !== "https:") ||
  (mode === "demo" && !["localhost", "127.0.0.1"].includes(url.hostname))
)
  throw new Error("Tour requires an explicit safe demo or live origin");

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/judge-tour.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180000,
  expect: { timeout: 30000 },
  outputDir: `../../artifacts/ux-audit/go-live/${mode}/test-results`,
  reporter: "./scripts/tour-reporter.ts",
  use: {
    baseURL: url.origin,
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: ["es", "pt"].flatMap((language) => [
    {
      name: `${language}-desktop`,
      use: { viewport: { width: 1440, height: 1000 } },
    },
    {
      name: `${language}-phone`,
      use: {
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ]),
});
