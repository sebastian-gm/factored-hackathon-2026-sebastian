import { expect, type Page } from "@playwright/test";

// Staff and judge account names are deliberately absent from public config.
export async function selectLoginPersona(page: Page, username: string) {
  const input = page.locator('input[autocomplete="username"]');
  const select = page.locator(".login-panel select");
  await expect(input.or(select).first()).toBeVisible();
  if (await input.count()) await input.fill(username);
  else await select.selectOption(username);
}
