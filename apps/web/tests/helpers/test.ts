import { createHash } from "node:crypto";
import { test as base } from "@playwright/test";

// Each test simulates a different ingress-observed peer. Real limits stay enabled.
export const test = base.extend<{ admissionClient: void }>({
  admissionClient: [
    async ({ context }, use, info) => {
      const hash = createHash("sha256")
        .update(`${info.testId}:${info.repeatEachIndex}:${info.retry}`)
        .digest("hex")
        .slice(0, 24);
      const ip = `2001:db8:${hash.match(/.{4}/g)!.join(":")}`;
      await context.setExtraHTTPHeaders({ "X-Forwarded-For": ip });
      await use();
    },
    { auto: true },
  ],
});
export { expect } from "@playwright/test";
export type { Page, Locator } from "@playwright/test";
