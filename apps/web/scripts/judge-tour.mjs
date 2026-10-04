import { readFileSync, statSync, realpathSync, mkdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
const require = createRequire(import.meta.url);
const web = fileURLToPath(new URL("../", import.meta.url));
const root = path.resolve(web, "../..");
const mode = process.argv[2];
try {
  if (!["demo", "live"].includes(mode)) throw new Error();
  const args = process.argv.slice(3);
  // Keep traces, alternate reporters and diagnostic attachments disabled.
  for (let index = 0; index < args.length; index++) {
    if (/^--(project|grep)=.+$/.test(args[index])) continue;
    if (["--project", "--grep"].includes(args[index]) && args[index + 1] && !args[index + 1].startsWith("--")) { index++; continue; }
    throw new Error();
  }
  const env = {
    ...process.env,
    JUDGE_TOUR_MODE: mode,
    PLAYWRIGHT_NO_COPY_PROMPT: "1",
  };
  if (mode === "demo") {
    const language = process.env.DEMO_LANGUAGE === "pt" ? "pt" : "es";
    const file = path.join(root, `artifacts/demo/${language}/.env`);
    if ((statSync(file).mode & 0o777) !== 0o600) throw new Error();
    const values = Object.fromEntries(
      readFileSync(file, "utf8")
        .trim()
        .split("\n")
        .map((line) => {
          const i = line.indexOf("=");
          return [line.slice(0, i), line.slice(i + 1)];
        }),
    );
    if (values.LLM_PROVIDER !== "mock" || values.LEDGER_BACKEND !== "fixture") throw new Error();
    Object.assign(env, {
      JUDGE_TOUR_URL: `http://localhost:${values.WEB_HOST_PORT}`,
      JUDGE_TOUR_USERNAME: values.DEMO_USERNAME,
      JUDGE_TOUR_PASSWORD: values.DEMO_PASSWORD,
      JUDGE_TOUR_STAFF_USERNAME: values.DEMO_USERNAME,
      JUDGE_TOUR_STAFF_PASSWORD: values.DEMO_PASSWORD,
    });
  } else {
    // Runner secrets arrive via environment; owner secrets via an ignored 0600 file.
    const input = process.env.JUDGE_TOUR_CREDENTIALS_FILE;
    if (input) {
      const file = path.resolve(root, input);
      if (!file.startsWith(path.join(root, "artifacts") + path.sep) || realpathSync(file) !== file || (statSync(file).mode & 0o777) !== 0o600) throw new Error();
      const credentials = JSON.parse(readFileSync(file, "utf8"));
      Object.assign(env, credentials.username ? {
        JUDGE_TOUR_USERNAME: credentials.username,
        JUDGE_TOUR_PASSWORD: credentials.password,
        JUDGE_TOUR_URL: credentials.url,
      } : credentials);
      env.JUDGE_TOUR_MODE = "live";
    }
    if (!/^[a-f0-9]{40}$/.test(env.JUDGE_TOUR_RELEASE_SHA ?? "")) throw new Error();
    if (env.JUDGE_TOUR_PAID === "1" || env.JUDGE_TOUR_RESERVE_ALL_HTTP === "1") {
      const adapter = path.resolve(root, env.JUDGE_TOUR_BUDGET_ADAPTER ?? "");
      if (!env.JUDGE_TOUR_BUDGET_SCOPE || !adapter.startsWith(path.join(root, "artifacts") + path.sep) || !adapter.endsWith(".mjs") || realpathSync(adapter) !== adapter || (statSync(adapter).mode & 0o777) !== 0o600) throw new Error();
      env.JUDGE_TOUR_BUDGET_ADAPTER = adapter;
    }
  }
  if (!env.JUDGE_TOUR_USERNAME || !env.JUDGE_TOUR_PASSWORD) throw new Error();
  const network = process.env.GITHUB_ACTIONS === "true" ? "github-runner" : "owner-workstation";
  const directory = path.join(root, `artifacts/ux-audit/go-live/${mode}${mode === "live" ? `/${network}` : ""}`);
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  const result = spawnSync(process.execPath, [require.resolve("@playwright/test/cli"), "test", "--config", "playwright.tour.config.ts", ...args], {
    cwd: web,
    env,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });
  // Deliberately discard raw stderr and any unexpected stdout.
  const summary = JSON.parse(result.stdout.trim());
  summary.mode = mode;
  summary.network = network;
  summary.release_sha = env.JUDGE_TOUR_RELEASE_SHA ?? null;
  const summaryName = process.env.JUDGE_TOUR_SUMMARY_NAME ?? "summary.json";
  if (!/^summary(?:-[a-z0-9-]+)?\.json$/.test(summaryName)) throw new Error();
  writeFileSync(path.join(directory, summaryName), JSON.stringify(summary, null, 2) + "\n", { mode: 0o600 });
  process.stdout.write(JSON.stringify(summary) + "\n");
  process.exitCode = result.status ?? 1;
} catch {
  process.stderr.write("Judge tour failed; raw diagnostics suppressed. Verify mode, private inputs, stack and browser installation.\n");
  process.exitCode = 1;
}
