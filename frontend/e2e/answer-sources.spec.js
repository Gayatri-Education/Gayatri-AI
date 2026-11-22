import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";

test("administrator can inspect sourced keys and conflicts without approving them", async ({
  page,
}) => {
  test.skip(
    !process.env.PORTAL_E2E_STATE_DIR,
    "Requires an explicitly isolated temporary database",
  );
  const state = path.resolve(process.env.PORTAL_E2E_STATE_DIR);
  if (!state.startsWith("/tmp/"))
    throw new Error("Admin browser fixture must use a temporary database");
  const email = `source-review-${Date.now()}@example.test`;
  const password = "isolated-browser-test-password";
  const response = await page.request.post("/api/auth/register", {
    data: { name: "Source Review Fixture", email, password },
  });
  expect(response.status()).toBe(201);
  const user = await response.json();
  const root = path.resolve(import.meta.dirname, "../..");
  execFileSync(
    process.env.PORTAL_TEST_PYTHON || path.join(root, ".venv/bin/python"),
    [
      "-c",
      "import sys; from backend.database import SessionLocal; from backend.models import User; session=SessionLocal(); user=session.get(User,int(sys.argv[1])); user.role='admin'; session.commit(); session.close()",
      String(user.id),
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        PORTAL_STATE_DIR: state,
        DATABASE_URL: `sqlite:///${state}/portal.db`,
      },
    },
  );
  await page.goto("/#/admin");
  await expect(
    page.getByRole("heading", { name: /A question bank you can trust/ }),
  ).toBeVisible();
  await expect(page.getByText(/947 answer proposals/)).toBeVisible();
  await page
    .getByPlaceholder("e.g. NEET_2024_PHYSICS_001")
    .fill("NEET_2024_PHYSICS_001");
  await expect(
    page.getByText("Sources disagree · no answer selected"),
  ).toBeVisible();
  await expect(page.getByLabel("Verified correct option")).toHaveValue("");
  await page.getByText(/Compare .* source references/).click();
  await expect(page.locator(".source-reference").first()).toBeVisible();
  await page.screenshot({
    path: "/tmp/gayatri-key-conflict.png",
    fullPage: true,
  });
  await page
    .getByPlaceholder("e.g. NEET_2024_PHYSICS_001")
    .fill("NEET_2025_CHEMISTRY_082");
  await expect(
    page.getByText("Published-source proposal · not approved"),
  ).toBeVisible();
  await expect(page.getByLabel("Verified correct option")).toHaveValue("B");
  await expect(page.getByLabel("Verified explanation")).toHaveValue("");
  await expect(
    page.getByRole("checkbox", { name: /I checked the original image/ }),
  ).not.toBeChecked();
  await expect(page.locator(".accepted-key-options input:checked")).toHaveCount(
    1,
  );
  const reports = await page.request.get("/api/admin/reports");
  expect((await reports.json()).approved).toBe(0);
});
