import { test, expect } from '../fixtures/auth.fixture';

/**
 * Accessibility Testing Suite
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Tests for WCAG compliance, keyboard navigation, screen reader support, and accessibility features
 */

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable accessibility features
    await page.emulateMedia({ reducedMotion: 'reduce' });
  });

  test('WCAG 2.1 AA準拠チェック - ログインページ', async ({ page }) => {
    await page.goto('/login');
    
    // Check for accessibility violations
    const violations = await page.evaluate(() => {
      // Note: In a real implementation, you would use axe-core
      // This is a simplified check for demonstration
      const issues = [];
      
      // Check for missing alt text
      const images = document.querySelectorAll('img');
      images.forEach(img => {
        if (!img.alt && !img.getAttribute('aria-label')) {
          issues.push(`Image missing alt text: ${img.src}`);
        }
      });
      
      // Check for missing form labels
      const inputs = document.querySelectorAll('input');
      inputs.forEach(input => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (!label && !input.getAttribute('aria-label')) {
          issues.push(`Input missing label: ${input.name || input.id}`);
        }
      });
      
      // Check for heading hierarchy
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      let previousLevel = 0;
      headings.forEach(heading => {
        const level = parseInt(heading.tagName.charAt(1));
        if (level > previousLevel + 1) {
          issues.push(`Heading level skip: ${heading.tagName} after h${previousLevel}`);
        }
        previousLevel = level;
      });
      
      return issues;
    });
    
    console.log('Accessibility violations:', violations);
    
    // Assert no critical violations
    expect(violations).toHaveLength(0);
  });

  test('キーボードナビゲーションテスト', async ({ page }) => {
    await page.goto('/login');
    
    // Test Tab navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBe('email-input');
    
    await page.keyboard.press('Tab');
    focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBe('password-input');
    
    await page.keyboard.press('Tab');
    focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBe('login-button');
    
    // Test Enter key on button
    await page.keyboard.press('Enter');
    
    // Should show validation errors
    await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
  });

  test('スクリーンリーダー対応チェック', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for ARIA attributes
    const ariaLabels = await page.evaluate(() => {
      const elements = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby]');
      return Array.from(elements).map(el => ({
        tag: el.tagName,
        role: el.getAttribute('role'),
        ariaLabel: el.getAttribute('aria-label'),
        ariaLabelledBy: el.getAttribute('aria-labelledby'),
        ariaDescribedBy: el.getAttribute('aria-describedby')
      }));
    });
    
    console.log('ARIA labels found:', ariaLabels);
    
    // Navigation should have proper ARIA labels
    await expect(page.locator('[data-testid="main-navigation"]')).toHaveAttribute('role', 'navigation');
    await expect(page.locator('[data-testid="main-navigation"]')).toHaveAttribute('aria-label', 'Main navigation');
  });

  test('色覚障害者向けアクセシビリティ', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check color contrast
    const contrastIssues = await page.evaluate(() => {
      const issues = [];
      
      // Simple color contrast check (in real implementation, use a library)
      const elements = document.querySelectorAll('*');
      elements.forEach(el => {
        const style = window.getComputedStyle(el);
        const bgColor = style.backgroundColor;
        const textColor = style.color;
        
        // Check if colors are not just relying on color differences
        if (bgColor !== 'rgba(0, 0, 0, 0)' && textColor !== 'rgba(0, 0, 0, 0)') {
          // In real implementation, calculate contrast ratio
          // For now, just check if there are patterns or icons for color coding
          if (el.textContent && el.textContent.includes('status')) {
            const hasIcon = el.querySelector('svg, i, .icon');
            if (!hasIcon) {
              issues.push(`Status indicator may rely only on color: ${el.textContent}`);
            }
          }
        }
      });
      
      return issues;
    });
    
    console.log('Color contrast issues:', contrastIssues);
    
    // Status indicators should not rely solely on color
    expect(contrastIssues.length).toBeLessThan(5);
  });

  test('フォーカス管理テスト', async ({ page }) => {
    await page.goto('/admin/users');
    
    // Test modal focus management
    await page.click('[data-testid="add-user-button"]');
    await page.waitForSelector('[data-testid="user-form"]');
    
    // Focus should be trapped in modal
    let focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBe('user-email-input');
    
    // Test Escape key to close modal
    await page.keyboard.press('Escape');
    
    // Focus should return to trigger button
    focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBe('add-user-button');
  });

  test('アニメーション縮小設定の尊重', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    await page.goto('/dashboard');
    
    // Check that animations are disabled
    const animationState = await page.evaluate(() => {
      const element = document.querySelector('[data-testid="animated-element"]');
      if (element) {
        const style = window.getComputedStyle(element);
        return {
          animationDuration: style.animationDuration,
          transitionDuration: style.transitionDuration
        };
      }
      return null;
    });
    
    if (animationState) {
      // Animations should be disabled or very short
      expect(animationState.animationDuration).toBe('0s');
      expect(animationState.transitionDuration).toBe('0s');
    }
  });

  test('言語サポートとローカライゼーション', async ({ page }) => {
    await page.goto('/');
    
    // Check for lang attribute
    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('ja');
    
    // Check for proper text direction
    const textDirection = await page.evaluate(() => {
      return document.documentElement.dir || 'ltr';
    });
    expect(textDirection).toBe('ltr');
  });

  test('エラーメッセージのアクセシビリティ', async ({ page }) => {
    await page.goto('/login');
    
    // Trigger validation errors
    await page.click('[data-testid="login-button"]');
    
    // Check error messages accessibility
    const errorElement = page.locator('[data-testid="email-error"]');
    await expect(errorElement).toBeVisible();
    
    // Error should be associated with input
    const emailInput = page.locator('[data-testid="email-input"]');
    const ariaDescribedBy = await emailInput.getAttribute('aria-describedby');
    expect(ariaDescribedBy).toContain('email-error');
    
    // Error should have proper role
    await expect(errorElement).toHaveAttribute('role', 'alert');
  });

  test('テーブルアクセシビリティ', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Check table structure
    const table = adminPage.locator('[data-testid="users-table"]');
    await expect(table).toHaveAttribute('role', 'table');
    
    // Check headers
    const headers = table.locator('th');
    const headerCount = await headers.count();
    expect(headerCount).toBeGreaterThan(0);
    
    // Headers should have proper scope
    for (let i = 0; i < headerCount; i++) {
      const header = headers.nth(i);
      const scope = await header.getAttribute('scope');
      expect(scope).toBe('col');
    }
  });

  test('フォームアクセシビリティ', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    await adminPage.click('[data-testid="add-user-button"]');
    
    // Check form structure
    const form = adminPage.locator('[data-testid="user-form"]');
    await expect(form).toHaveAttribute('role', 'form');
    
    // Check fieldset and legend
    const fieldset = form.locator('fieldset');
    if (await fieldset.count() > 0) {
      const legend = fieldset.locator('legend');
      await expect(legend).toBeVisible();
    }
    
    // Check required fields
    const requiredFields = form.locator('input[required]');
    const requiredCount = await requiredFields.count();
    
    for (let i = 0; i < requiredCount; i++) {
      const field = requiredFields.nth(i);
      const ariaRequired = await field.getAttribute('aria-required');
      expect(ariaRequired).toBe('true');
    }
  });

  test('スキップリンクテスト', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test skip to main content
    await page.keyboard.press('Tab');
    
    const skipLink = page.locator('[data-testid="skip-to-main"]');
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeFocused();
      await page.keyboard.press('Enter');
      
      // Main content should be focused
      const mainContent = page.locator('[data-testid="main-content"]');
      await expect(mainContent).toBeFocused();
    }
  });

  test('音声・映像コンテンツのアクセシビリティ', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for video elements
    const videos = page.locator('video');
    const videoCount = await videos.count();
    
    for (let i = 0; i < videoCount; i++) {
      const video = videos.nth(i);
      
      // Should have controls
      await expect(video).toHaveAttribute('controls');
      
      // Should have captions track
      const tracks = video.locator('track[kind="captions"]');
      await expect(tracks).toHaveCount(1);
    }
  });

  test('ズーム機能のサポート', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test zoom to 200%
    await page.setViewportSize({ width: 640, height: 360 }); // Simulate 200% zoom
    
    // Content should still be accessible
    await expect(page.locator('[data-testid="main-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    
    // Navigation should still work
    await page.click('[data-testid="nav-tasks"]');
    await expect(page).toHaveURL(/\/tasks/);
  });

  test('時間制限のあるコンテンツのアクセシビリティ', async ({ page }) => {
    await page.goto('/dashboard');
    
    // If there are any auto-refreshing elements, they should be pausable
    const autoRefreshElements = page.locator('[data-auto-refresh]');
    const autoRefreshCount = await autoRefreshElements.count();
    
    for (let i = 0; i < autoRefreshCount; i++) {
      const element = autoRefreshElements.nth(i);
      const pauseButton = element.locator('[data-testid="pause-refresh"]');
      
      // Should have pause/play controls
      await expect(pauseButton).toBeVisible();
    }
  });

  test('検索機能のアクセシビリティ', async ({ page }) => {
    await page.goto('/dashboard');
    
    const searchInput = page.locator('[data-testid="search-input"]');
    if (await searchInput.count() > 0) {
      // Should have proper labeling
      await expect(searchInput).toHaveAttribute('aria-label', 'Search');
      
      // Should have search role
      await expect(searchInput).toHaveAttribute('role', 'searchbox');
      
      // Should have live region for results
      const searchResults = page.locator('[data-testid="search-results"]');
      if (await searchResults.count() > 0) {
        await expect(searchResults).toHaveAttribute('aria-live', 'polite');
      }
    }
  });
});