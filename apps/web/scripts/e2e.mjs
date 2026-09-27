import { randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
// Ephemeral test credential: shared only through the child environment, never logged.
const live = process.argv.includes("--live");
const args = process.argv.slice(2).filter((arg) => arg !== "--live");
const result = spawnSync(
  process.execPath,
  [require.resolve("@playwright/test/cli"), "test", ...args],
  {
    stdio: "inherit",
    env: {
      ...process.env,
      FRONTEND_E2E_LIVE: live ? "1" : "0",
      FRONTEND_FIXTURE_PASSWORD: randomBytes(32).toString("hex"),
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
);
process.exit(result.status ?? 1);
