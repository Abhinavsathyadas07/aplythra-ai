import { expect, test } from "@playwright/test";

import { signUp } from "./helpers";

test("responses carry security headers", async ({ page }) => {
  const response = await page.goto("/login");
  const headers = response!.headers();
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(headers["content-security-policy"]).toContain("object-src 'none'");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["x-powered-by"]).toBeUndefined();
  expect(headers["cache-control"]).toContain("no-store");
});

test("connect-src is limited to the app, auth server and API", async ({ page }) => {
  const csp = (await page.goto("/login"))!.headers()["content-security-policy"];
  const connect = csp.split(";").map((d) => d.trim()).find((d) => d.startsWith("connect-src"))!;
  expect(connect).toContain("http://localhost:54321");
  expect(connect).toContain("http://localhost:8100");
  expect(connect).not.toContain("*");
});

test("no server-side secrets reach the browser bundle", async ({ page }) => {
  const scripts: string[] = [];
  page.on("response", async (response) => {
    if (response.url().endsWith(".js") || response.headers()["content-type"]?.includes("javascript")) {
      scripts.push(await response.text().catch(() => ""));
    }
  });
  await signUp(page);
  await expect(page.getByTestId("api-connected")).toBeVisible();

  expect(scripts.length).toBeGreaterThan(0);
  const joined = scripts.join("\n");
  for (const forbidden of ["service_role", "SERVICE_ROLE", "ANTHROPIC_API_KEY", "DATABASE_URL", "dev_app_pw"]) {
    expect(joined, `bundle contains ${forbidden}`).not.toContain(forbidden);
  }
});

test("access token is not written to local storage by the app shell", async ({ page }) => {
  await signUp(page);
  const leaked = await page.evaluate(() =>
    Object.entries(localStorage).filter(([, v]) => /eyJ[\w-]+\.[\w-]+\./.test(v)).map(([k]) => k),
  );
  expect(leaked).toEqual([]);
});
