import { expect, test } from "@playwright/test";

import { PASSWORD, signIn, signUp, uniqueEmail } from "./helpers";

test("unauthenticated visitors are sent to sign-in and returned afterwards", async ({ page }) => {
  await page.goto("/settings");
  await expect(page).toHaveURL(/\/login\?next=%2Fsettings$/);

  // Create an account from the login screen; the next path survives the round trip.
  await page.getByRole("button", { name: "Need an account? Create one" }).click();
  await page.getByLabel("Email").fill(uniqueEmail());
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page).toHaveURL(/\/settings$/);
});

test("sign-up reaches the dashboard and the real API accepts the token", async ({ page }) => {
  const email = await signUp(page);
  const status = page.getByTestId("api-connected");
  await expect(status).toContainText("Connected");
  await expect(status).toContainText(email);
});

test("wrong password shows one generic error and stays on sign-in", async ({ page }) => {
  const email = await signUp(page);
  await page.getByRole("link", { name: "Settings" }).first().click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login/);

  await signIn(page, email, "not-the-password");
  await expect(page.getByTestId("form-error")).toHaveText("Invalid email or password.");
  await expect(page).toHaveURL(/\/login/);

  // Unknown account gets the identical message (no user enumeration).
  await page.getByLabel("Email").fill(uniqueEmail());
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByTestId("form-error")).toHaveText("Invalid email or password.");
});

test("sign out ends the session and protects pages again", async ({ page }) => {
  const email = await signUp(page);
  await page.getByRole("link", { name: "Settings" }).first().click();
  await expect(page.getByTestId("account-email")).toHaveText(email);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login/);

  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login\?next=%2Fdashboard$/);

  // The same account can sign back in.
  await signIn(page, email);
  await expect(page).toHaveURL(/\/dashboard$/);
});

test("signed-in users skip the login page", async ({ page }) => {
  await signUp(page);
  await page.goto("/login");
  await expect(page).toHaveURL(/\/dashboard$/);
});

test("login ignores off-site redirect targets", async ({ page }) => {
  await page.goto("/login?next=//evil.example/steal");
  await page.getByRole("button", { name: "Need an account? Create one" }).click();
  await page.getByLabel("Email").fill(uniqueEmail());
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page).toHaveURL(/localhost:3100\/dashboard$/);
});

test("dashboard reports an unreachable backend and recovers on retry", async ({ page }) => {
  await signUp(page);
  await expect(page.getByTestId("api-connected")).toBeVisible();

  await page.route("**/health/ready", (route) => route.abort());
  await page.reload();
  await expect(page.getByTestId("api-error")).toHaveText("Cannot reach the server");

  await page.unroute("**/health/ready");
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByTestId("api-connected")).toBeVisible();
});

test("duplicate sign-up shows a generic error", async ({ page }) => {
  const email = await signUp(page);
  await page.getByRole("link", { name: "Settings" }).first().click();
  await page.getByRole("button", { name: "Sign out" }).click();

  await page.getByRole("button", { name: "Need an account? Create one" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page.getByTestId("form-error")).toContainText("Could not create the account");
});
