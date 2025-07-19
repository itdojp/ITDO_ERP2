import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Disable parallel for CI stability
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0, // Reduce retries for faster execution
  workers: 1, // Single worker for stability
  timeout: 30000, // Reduce timeout for faster CI
  expect: {
    timeout: 10000,
  },
  globalTimeout: process.env.CI ? 5 * 60 * 1000 : undefined, // 5 minutes for CI
  reporter: [
    ['html', { 
      outputFolder: 'playwright-report',
      open: 'never',
    }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/test-results.json' }],
    ...(process.env.CI ? [['github']] : [['list']]),
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    // WebKitはCI環境では依存関係の問題でスキップ
    ...(process.env.CI ? [] : [
      {
        name: 'webkit',
        use: { ...devices['Desktop Safari'] },
      },
    ]),
  ],
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});