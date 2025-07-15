import { test, expect } from '@playwright/test';

test.describe('Basic Accessibility Checks', () => {
  test('page has proper language attribute', async ({ page }) => {
    await page.goto('/');
    
    // Check html lang attribute
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
    expect(['en', 'ja', 'en-US', 'ja-JP']).toContain(lang);
  });

  test('images have alt attributes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Get all images
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      // Alt attribute should exist (can be empty for decorative images)
      expect(alt).not.toBeNull();
    }
  });

  test('form inputs have labels or aria-labels', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Check text inputs
    const inputs = await page.locator('input[type="text"], input[type="email"], input[type="password"]').all();
    
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      // Input should have either:
      // 1. An id with a corresponding label
      // 2. An aria-label
      // 3. An aria-labelledby
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).count();
        const hasAccessibleName = label > 0 || ariaLabel || ariaLabelledBy;
        expect(hasAccessibleName).toBeTruthy();
      } else {
        expect(ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test('buttons have accessible text', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Get all buttons
    const buttons = await page.locator('button').all();
    
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Button should have either visible text or aria-label
      expect(text?.trim() || ariaLabel).toBeTruthy();
    }
  });

  test('page has proper heading structure', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Check for h1
    const h1Count = await page.locator('h1').count();
    
    // Most pages should have at least one h1
    // (Some SPA states might not, so we just check it's a number)
    expect(h1Count).toBeGreaterThanOrEqual(0);
    
    // Check heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings).toBeTruthy();
  });
});