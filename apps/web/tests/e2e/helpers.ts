import { randomUUID } from "node:crypto";

import { expect, type Page } from "@playwright/test";

export const PASSWORD = "correct-horse-battery";

export const uniqueEmail = () => `e2e-${randomUUID().slice(0, 8)}@example.test`;

export async function signUp(page: Page, email = uniqueEmail()) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Need an account? Create one" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  return email;
}

export async function signIn(page: Page, email: string, password = PASSWORD) {
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
}
