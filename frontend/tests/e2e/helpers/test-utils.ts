/**
 * E2E test utilities for stability
 */
import { Page, Locator, expect } from '@playwright/test';

export class TestUtils {
  constructor(private page: Page) {}

  /**
   * Wait for network to be idle
   */
  async waitForNetwork() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for element with retry
   */
  async waitForElement(selector: string, options = {}) {
    const defaultOptions = {
      state: 'visible',
      timeout: 30000,
    };

    return this.page.waitForSelector(selector, { ...defaultOptions, ...options });
  }

  /**
   * Click with retry and stability check
   */
  async clickWithRetry(selector: string, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        await this.waitForElement(selector);
        await this.page.click(selector);
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Fill form field with validation
   */
  async fillField(selector: string, value: string) {
    await this.waitForElement(selector);
    await this.page.fill(selector, '');
    await this.page.fill(selector, value);

    // Verify value was set
    const actualValue = await this.page.inputValue(selector);
    expect(actualValue).toBe(value);
  }

  /**
   * Wait for API response
   */
  async waitForAPI(path: string, method = 'GET') {
    return this.page.waitForResponse(
      response =>
        response.url().includes(path) &&
        response.request().method() === method &&
        response.status() < 400
    );
  }

  /**
   * Take screenshot on failure
   */
  async screenshot(name: string) {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true,
    });
  }
}

/**
 * Setup test environment
 */
export async function setupTest(page: Page) {
  // Set default timeout
  page.setDefaultTimeout(30000);

  // Add request logger
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log('API Request:', request.method(), request.url());
    }
  });

  // Add response logger
  page.on('response', response => {
    if (response.url().includes('/api/') && response.status() >= 400) {
      console.error('API Error:', response.status(), response.url());
    }
  });

  return new TestUtils(page);
}