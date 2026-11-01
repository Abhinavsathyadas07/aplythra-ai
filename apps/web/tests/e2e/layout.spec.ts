import { expect, test } from "@playwright/test";

import { signUp } from "./helpers";

const LABELS = ["Dashboard", "Jobs", "Applications", "Activity", "Settings"];

test("navigation adapts to the viewport", async ({ page }, testInfo) => {
  await signUp(page);
  const mobile = testInfo.project.name === "mobile";

  const visibleNav = page.getByRole("navigation", { name: "Main" }).and(page.locator(":visible"));
  await expect(visibleNav).toHaveCount(1);
  const box = await visibleNav.boundingBox();
  const viewport = page.viewportSize()!;

  if (mobile) {
    // Bottom tab bar pinned to the bottom edge.
    expect(box!.y + box!.height).toBeGreaterThan(viewport.height - 2);
    expect(box!.width).toBeGreaterThan(viewport.width - 2);
  } else {
    // Left sidebar (the nav sits inside its padding).
    expect(box!.x).toBeLessThan(40);
    expect(box!.width).toBeLessThan(viewport.width / 2);
  }

  for (const label of LABELS) {
    await expect(visibleNav.getByRole("link", { name: label })).toBeVisible();
  }
  await expect(visibleNav.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
});

test("every section is reachable and marks itself current", async ({ page }) => {
  await signUp(page);
  const nav = page.getByRole("navigation", { name: "Main" }).and(page.locator(":visible"));

  for (const [label, heading] of [
    ["Jobs", "Jobs"],
    ["Applications", "Applications"],
    ["Activity", "Activity"],
    ["Settings", "Settings"],
    ["Dashboard", "Dashboard"],
  ]) {
    await nav.getByRole("link", { name: label }).click();
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    await expect(nav.getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
  }
});

test("pages never scroll sideways and tap targets are comfortable", async ({ page }, testInfo) => {
  await page.goto("/login");
  for (const path of ["/login", "/dashboard", "/settings"]) {
    if (path !== "/login" && page.url().includes("/login")) await signUp(page);
    await page.goto(path);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, `${path} overflows horizontally`).toBeLessThanOrEqual(0);
  }

  if (testInfo.project.name === "mobile") {
    for (const link of await page.getByRole("navigation", { name: "Main" }).and(page.locator(":visible")).getByRole("link").all()) {
      const box = await link.boundingBox();
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }
  }
});
