import { createHash } from "node:crypto";
import { test as base, type BrowserContext } from "@playwright/test";

export async function seedLegacyInterfaceLanguage(context: BrowserContext) {
  await context.addInitScript(() => {
    if (!["http:", "https:"].includes(location.protocol)) return;
    try {
      const key = "aclara.interfaceLanguage";
      if (localStorage.getItem(key) === null)
        localStorage.setItem(key, "es-MX");
    } catch {
      // Opaque or sandboxed audit frames cannot access origin storage.
    }
  });
}

// Each test simulates a different ingress-observed peer. Real limits stay enabled.
export const test = base.extend<{ admissionClient: void }>({
  admissionClient: [
    async ({ context }, use, info) => {
      const hash = createHash("sha256")
        .update(`${info.testId}:${info.repeatEachIndex}:${info.retry}`)
        .digest("hex")
        .slice(0, 24);
      const ip = `2001:db8:${hash.match(/.{4}/g)!.join(":")}`;
      // Existing ES/PT suites explicitly opt into their historical UI language.
      if (!info.file.endsWith("english-interface.spec.ts"))
        await seedLegacyInterfaceLanguage(context);
      await context.setExtraHTTPHeaders({ "X-Forwarded-For": ip });
      await use();
    },
    { auto: true },
  ],
});
export { expect } from "@playwright/test";
export type { Page, Locator } from "@playwright/test";
