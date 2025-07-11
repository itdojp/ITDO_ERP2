import { defineConfig } from '@playwright/test';

/**
 * CI-specific Playwright configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: true,
  retries: 2,
  workers: 1,
  timeout: 120000,
  expect: {
    timeout: 30000,
  },
  globalTimeout: 10 * 60 * 1000, // 10 minutes
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/test-results.json' }],
    ['github'],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 30000,
    navigationTimeout: 45000,
  },
  projects: [
    {
      name: 'chromium',
      use: { 
        ...{
          browserName: 'chromium',
          viewport: { width: 1280, height: 720 },
          ignoreHTTPSErrors: true,
        }
      },
    },
  ],
});