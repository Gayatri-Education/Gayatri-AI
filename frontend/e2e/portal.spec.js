import { test, expect } from "@playwright/test";

test("student completes an image-backed practice attempt and resumes history", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Your name").fill("Portal Browser Test");
  await page
    .getByLabel("Email address")
    .fill(`browser-${Date.now()}@example.test`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-password");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Let’s make today count/ }),
  ).toBeVisible();
  await expect(page.getByText("2,240", { exact: true })).toBeVisible();
  await page.screenshot({ path: "/tmp/gayatri-dashboard.png", fullPage: true });
  await page.getByRole("button", { name: "View session" }).click();
  await expect(
    page.getByRole("heading", { name: /Before you begin/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("option", { name: /awaiting answer keys/ }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Begin session" }).click();
  await expect(
    page.getByRole("heading", { name: /One question at a time/ }),
  ).toBeVisible();
  await page.locator(".option").first().click();
  await expect(page.locator(".save-status")).toHaveText(/Saved/);
  await page.getByRole("button", { name: "Flag for review" }).click();
  await expect(
    page.getByRole("button", { name: "Flagged", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next question" }).click();
  await page.getByRole("button", { name: "Question 1", exact: true }).click();
  await expect(page.locator(".option.selected")).toHaveCount(1);
  await page.reload();
  await expect(page.locator(".option.selected")).toHaveCount(1);
  const imageButton = page.getByRole("button", {
    name: /View original question image/,
  });
  if (await imageButton.count()) await imageButton.click();
  await expect(page.locator(".source img")).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator(".source img")
        .evaluate((img) => img.complete && img.naturalWidth > 0),
    )
    .toBe(true);
  await page.screenshot({ path: "/tmp/gayatri-exam.png", fullPage: true });
  await page.getByRole("button", { name: "Finish session" }).click();
  await page
    .getByRole("button", { name: "Submit session", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Progress looks good/ }),
  ).toBeVisible();
  await expect(page.getByText("Unscored", { exact: true })).toBeVisible();
  await expect(page.getByText("1/15", { exact: true })).toBeVisible();
  await expect(page.getByText(/Awaiting verified key/).first()).toBeVisible();
  await page.getByRole("link", { name: "My attempts" }).click();
  await expect(page.locator(".history-row")).toHaveCount(1);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Let’s make today count/ }),
  ).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBe(true);
  await page.screenshot({ path: "/tmp/gayatri-mobile.png", fullPage: true });
  expect(errors).toEqual([]);
});
