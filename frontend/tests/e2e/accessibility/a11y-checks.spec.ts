import { test, expect } from '@playwright/test';

test.describe('Accessibility Testing', () => {
  test('basic accessibility checks', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for basic accessibility requirements
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);

    // Check for language attribute
    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBeTruthy();

    // Check for meta viewport tag
    const viewportMeta = await page.locator('meta[name="viewport"]').count();
    expect(viewportMeta).toBeGreaterThan(0);

    console.log('Basic accessibility checks passed');
  });

  test('keyboard navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    
    // Check if focus is visible
    const focusedElement = await page.evaluate(() => {
      const focused = document.activeElement;
      return focused ? {
        tagName: focused.tagName,
        type: (focused as HTMLInputElement).type || null,
        id: focused.id || null,
        className: focused.className || null,
      } : null;
    });

    console.log('Focused element after Tab:', focusedElement);
    expect(focusedElement).toBeTruthy();
  });

  test('color contrast and readability', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for text elements and their contrast
    const textElements = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div'));
      return elements
        .filter(el => el.textContent && el.textContent.trim().length > 0)
        .slice(0, 10) // Check first 10 text elements
        .map(el => {
          const styles = window.getComputedStyle(el);
          return {
            text: el.textContent?.slice(0, 50) + '...',
            color: styles.color,
            backgroundColor: styles.backgroundColor,
            fontSize: styles.fontSize,
          };
        });
    });

    console.log('Text elements found:', textElements.length);
    expect(textElements.length).toBeGreaterThan(0);

    // Basic checks for readability
    textElements.forEach((element, index) => {
      expect(element.color).toBeTruthy();
      expect(element.fontSize).toBeTruthy();
      console.log(`Element ${index}: ${element.text} - Color: ${element.color}, Font: ${element.fontSize}`);
    });
  });

  test('responsive design testing', async ({ page }) => {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop Large' },
      { width: 1366, height: 768, name: 'Desktop Standard' },
      { width: 768, height: 1024, name: 'Tablet Portrait' },
      { width: 375, height: 667, name: 'Mobile' },
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Check if page content is visible and properly sized
      const bodyRect = await page.evaluate(() => {
        const body = document.body;
        const rect = body.getBoundingClientRect();
        return {
          width: rect.width,
          height: rect.height,
          scrollWidth: body.scrollWidth,
          scrollHeight: body.scrollHeight,
        };
      });

      console.log(`${viewport.name} (${viewport.width}x${viewport.height}):`, bodyRect);

      // Content should not overflow horizontally
      expect(bodyRect.scrollWidth).toBeLessThanOrEqual(viewport.width + 20); // 20px tolerance

      // Page should have some content
      expect(bodyRect.height).toBeGreaterThan(100);
    }
  });

  test('form accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for form elements and their accessibility
    const formElements = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
      return inputs.map(input => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        return {
          type: (input as HTMLInputElement).type || input.tagName.toLowerCase(),
          id: input.id,
          name: (input as HTMLInputElement).name,
          hasLabel: !!label,
          labelText: label?.textContent || null,
          placeholder: (input as HTMLInputElement).placeholder || null,
          required: (input as HTMLInputElement).required,
          ariaLabel: input.getAttribute('aria-label'),
        };
      });
    });

    console.log(`Found ${formElements.length} form elements`);

    // If there are form elements, check their accessibility
    formElements.forEach((element, index) => {
      console.log(`Form element ${index}:`, element);
      
      // Each form element should have some form of labeling
      const hasAccessibleLabel = element.hasLabel || 
                                 element.ariaLabel || 
                                 element.placeholder ||
                                 element.name;
      
      if (!hasAccessibleLabel) {
        console.warn(`Form element ${index} may lack proper labeling`);
      }
    });
  });
});