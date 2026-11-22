import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
    launchOptions: {
      executablePath:
        process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/chromium",
      args: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-crash-reporter",
      ],
      env: {
        ...process.env,
        XDG_CONFIG_HOME: "/tmp/gayatri-browser-config",
        XDG_CACHE_HOME: "/tmp/gayatri-browser-cache",
      },
    },
  },
  reporter: "list",
  outputDir: "/tmp/gayatri-playwright-results",
});
