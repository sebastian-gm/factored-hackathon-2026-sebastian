import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { chromium } from "@playwright/test";
const root = fileURLToPath(new URL("../../../", import.meta.url));
const mode = process.argv[2];
try {
  if (!["demo", "live"].includes(mode)) throw new Error();
  const values =
    mode === "demo"
      ? Object.fromEntries(
          readFileSync(path.join(root, "artifacts/demo/es/.env"), "utf8")
            .trim()
            .split("\n")
            .map((line) => {
              const i = line.indexOf("=");
              return [line.slice(0, i), line.slice(i + 1)];
            }),
        )
      : {};
  const url = new URL(
    mode === "demo"
      ? `http://localhost:${values.WEB_HOST_PORT}`
      : process.env.JUDGE_TOUR_URL,
  );
  if (
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (mode === "live" && url.protocol !== "https:") ||
    (mode === "demo" && !["localhost", "127.0.0.1"].includes(url.hostname))
  )
    throw new Error();
  const directory = path.join(root, `artifacts/ux-audit/go-live/${mode}`);
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  for (const formFactor of ["desktop", "mobile"]) {
    const result = spawnSync(
      "pnpm",
      [
        "dlx",
        "lighthouse@13.0.3",
        `${url.origin}/insights`,
        "--output=json",
        "--output-path=stdout",
        "--quiet",
        "--only-categories=performance,accessibility,best-practices,seo",
        "--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage",
        ...(formFactor === "desktop" ? ["--preset=desktop"] : []),
      ],
      {
        encoding: "utf8",
        env: { ...process.env, CHROME_PATH: chromium.executablePath() },
        maxBuffer: 10 * 1024 * 1024,
      },
    );
    if (result.status !== 0) throw new Error();
    const report = JSON.parse(result.stdout);
    const summary = {
      mode,
      form_factor: formFactor,
      lighthouse_version: report.lighthouseVersion,
      page: "/insights",
      model_calls: 0,
      categories: Object.fromEntries(
        Object.entries(report.categories).map(([key, value]) => [
          key,
          value.score,
        ]),
      ),
      metrics: Object.fromEntries(
        [
          "first-contentful-paint",
          "largest-contentful-paint",
          "total-blocking-time",
          "cumulative-layout-shift",
        ].map((key) => [key, report.audits[key].numericValue]),
      ),
      failed_audits: Object.entries(report.audits)
        .filter(([, value]) => value.score !== null && value.score < 1)
        .map(([key]) => key),
      // Public aggregate-only Insights page: selectors locate visual defects.
      accessibility_selectors: Object.fromEntries(
        ["target-size", "label-content-name-mismatch"].map((key) => [
          key,
          (report.audits[key]?.details?.items ?? [])
            .map((item) => item.node?.selector)
            .filter(Boolean),
        ]),
      ),
    };
    writeFileSync(
      path.join(directory, `lighthouse-${formFactor}.json`),
      JSON.stringify(summary, null, 2) + "\n",
      { mode: 0o600 },
    );
    process.stdout.write(JSON.stringify(summary) + "\n");
  }
} catch {
  process.stderr.write("Lighthouse tour failed; raw diagnostics suppressed.\n");
  process.exitCode = 1;
}
