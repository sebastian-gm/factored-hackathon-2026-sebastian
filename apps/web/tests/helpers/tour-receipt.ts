import { test, type Page } from "@playwright/test";

/** Clears only the authenticated local mock workspace; call fresh() afterward. */
export async function resetDemoReceipt(page: Page): Promise<boolean> {
  try {
    if (process.env.JUDGE_TOUR_MODE !== "demo") return false;
    const configured = test.info().project.use.baseURL;
    if (typeof configured !== "string") return false;
    const base = new URL(configured),
      current = new URL(page.url());
    const local = (url: URL) =>
      url.protocol === "http:" &&
      ["localhost", "127.0.0.1"].includes(url.hostname) &&
      !url.username &&
      !url.password;
    if (!local(base) || !local(current) || base.origin !== current.origin)
      return false;

    return await page.evaluate(async (origin) => {
      if (location.origin !== origin) return false;
      async function request(
        path: string,
        body?: Record<string, unknown>,
      ): Promise<Record<string, unknown> | null> {
        const response = await fetch(`/api/bff/${path}`, {
          method: body === undefined ? "GET" : "POST",
          credentials: "same-origin",
          redirect: "error",
          cache: "no-store",
          signal: AbortSignal.timeout(15000),
          ...(body === undefined
            ? {}
            : {
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
              }),
        });
        if (!response.ok) return null;
        const value: unknown = await response.json();
        return value && typeof value === "object" && !Array.isArray(value)
          ? (value as Record<string, unknown>)
          : null;
      }
      try {
        const config = await request("config");
        if (config?.resetEnabled !== true || config.fixtures !== false)
          return false;
        const principal = await request("me");
        if (
          principal?.role !== "ops" ||
          principal.judge_profiles_enabled === true
        )
          return false;
        const challenge = await request("auth/step-up", {});
        const id = challenge?.challenge_id;
        if (typeof id !== "string" || !/^[\w.-]{1,160}$/.test(id)) return false;
        // Challenge credentials remain in this browser callback and are never returned.
        const sms = await request(
          `auth/challenges/${encodeURIComponent(id)}/sms`,
        );
        if (typeof sms?.code !== "string" || !/^\d{6}$/.test(sms.code))
          return false;
        const verified = await request("auth/step-up/verify", {
          challenge_id: id,
          code: sms.code,
        });
        if (verified?.status !== "verified") return false;
        const proposal = await request("ops/reset/proposal", {});
        const hash = proposal?.proposal_hash;
        if (
          typeof hash !== "string" ||
          !/^[a-f0-9]{64}$/.test(hash) ||
          proposal?.action !== "reset_current_workspace" ||
          proposal.scope !== "current_workspace_operations_except_audit_auth"
        )
          return false;
        const committed = await request("ops/reset", {
          proposal_hash: hash,
          confirmed: true,
        });
        const valid = (receipt: Record<string, unknown> | null) =>
          receipt?.receipt_id === hash &&
          receipt.reset === true &&
          receipt.verified === true &&
          receipt.remaining_operations === 0 &&
          receipt.audit_retained === true;
        if (!valid(committed)) return false;
        return valid(await request(`ops/reset/${hash}`));
      } catch {
        return false;
      }
    }, base.origin);
  } catch {
    // No response body, challenge, customer fact, or Playwright call log escapes.
    throw new Error(
      "Local first-time receipt reset failed; details suppressed.",
    );
  }
}
