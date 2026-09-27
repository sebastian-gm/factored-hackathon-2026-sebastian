// Run INSIDE the web container before a release. No credentials or bodies are logged.
const configured = process.env.API_BASE_URL ?? process.env.BROWSER_API_BASE_URL;
if (!configured) throw new Error("Configure the server-side bank API URL");
const base = new URL(configured);
if (
  base.username ||
  base.password ||
  !["http:", "https:"].includes(base.protocol)
)
  throw new Error("API URL must be HTTP(S) without embedded credentials");
const checks = [];
for (const path of ["healthz", "personas"]) {
  try {
    const response = await fetch(`${base.href.replace(/\/$/, "")}/${path}`, {
      redirect: "error",
      signal: AbortSignal.timeout(10000),
      cache: "no-store",
    });
    let valid = response.ok;
    if (valid && path === "personas") {
      const data = await response.json();
      valid =
        Array.isArray(data) &&
        data.every(
          (p) =>
            typeof p.username === "string" &&
            ["customer", "agent", "ops"].includes(p.role),
        );
    }
    checks.push({ check: path, status: response.status, passed: valid });
  } catch {
    checks.push({
      check: path,
      passed: false,
      error: "unreachable_or_invalid",
    });
  }
}
process.stdout.write(
  JSON.stringify({ source: "web_runtime_api_hop", checks }) + "\n",
);
process.exit(checks.every((check) => check.passed) ? 0 : 1);
