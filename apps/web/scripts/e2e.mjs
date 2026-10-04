import { randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
// Ephemeral test credential: shared only through the child environment, never logged.
const staff = process.argv.includes("--staff");
const judgeStaff = process.argv.includes("--judge-staff");
const live = process.argv.includes("--live") || staff || judgeStaff;
const judgeRoles = process.argv.includes("--judge-roles");
if (judgeRoles && live)
  throw new Error("Judge role fixtures require an isolated mock run");
const args = process.argv
  .slice(2)
  .filter(
    (arg) =>
      !["--live", "--staff", "--judge-roles", "--judge-staff"].includes(arg),
  );
const result = spawnSync(
  process.execPath,
  [require.resolve("@playwright/test/cli"), "test", ...args],
  {
    stdio: "inherit",
    env: {
      ...process.env,
      FRONTEND_E2E_LIVE: live ? "1" : "0",
      FRONTEND_E2E_STAFF: staff ? "1" : "0",
      FRONTEND_E2E_JUDGE_ROLES: judgeRoles ? "1" : "0",
      FRONTEND_E2E_JUDGE_STAFF: judgeStaff ? "1" : "0",
      FRONTEND_FIXTURE_PASSWORD: randomBytes(32).toString("hex"),
      FRONTEND_FIXTURE_JUDGE_PASSWORD: randomBytes(32).toString("hex"),
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
);
process.exit(result.status ?? 1);
