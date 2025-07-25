import { test, expect } from '@playwright/test';

test.describe('Product Management Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login to the application
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'admin@example.com');
    await page.fill('[data-testid=password]', 'password123');
    await page.click('[data-testid=login-button]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create a new product successfully', async ({ page }) => {
    // Navigate to products page
    await page.goto('/products');
    await expect(page.locator('h1')).toContainText('Products');

    // Click add product button
    await page.click('[data-testid=add-product-button]');
    await expect(page.locator('[data-testid=product-form]')).toBeVisible();

    // Fill product form
    await page.fill('[data-testid=product-name]', 'Test Product E2E');
    await page.fill('[data-testid=product-sku]', 'TEST-E2E-001');
    await page.fill('[data-testid=product-price]', '99.99');
    await page.fill('[data-testid=product-cost]', '60.00');
    await page.fill('[data-testid=product-stock]', '100');
    await page.fill('[data-testid=product-min-stock]', '10');
    await page.selectOption('[data-testid=product-category]', 'Electronics');
    await page.fill('[data-testid=product-description]', 'E2E test product for automated testing');

    // Submit form
    await page.click('[data-testid=save-product-button]');
    
    // Verify success message
    await expect(page.locator('[data-testid=success-alert]')).toBeVisible();
    await expect(page.locator('[data-testid=success-alert]')).toContainText('Product created successfully');

    // Verify product appears in list
    await page.fill('[data-testid=search-products]', 'Test Product E2E');
    await expect(page.locator('[data-testid=product-row]').first()).toContainText('Test Product E2E');
  });

  test('should update product information', async ({ page }) => {
    await page.goto('/products');
    
    // Search for existing product
    await page.fill('[data-testid=search-products]', 'Test Product E2E');
    await page.waitForTimeout(1000); // Wait for search debounce
    
    // Click edit button on first product
    await page.click('[data-testid=edit-product-button]');
    await expect(page.locator('[data-testid=product-form]')).toBeVisible();

    // Update product information
    await page.fill('[data-testid=product-name]', 'Updated Test Product E2E');
    await page.fill('[data-testid=product-price]', '119.99');

    // Save changes
    await page.click('[data-testid=save-product-button]');
    
    // Verify success message
    await expect(page.locator('[data-testid=success-alert]')).toBeVisible();
    
    // Verify updated information
    await page.fill('[data-testid=search-products]', 'Updated Test Product E2E');
    await expect(page.locator('[data-testid=product-row]').first()).toContainText('Updated Test Product E2E');
    await expect(page.locator('[data-testid=product-row]').first()).toContainText('$119.99');
  });

  test('should filter products by category', async ({ page }) => {
    await page.goto('/products');
    
    // Open filters
    await page.click('[data-testid=filters-button]');
    await expect(page.locator('[data-testid=filters-drawer]')).toBeVisible();

    // Select Electronics category
    await page.selectOption('[data-testid=category-filter]', 'Electronics');
    
    // Close filters drawer
    await page.click('[data-testid=close-filters]');
    
    // Verify filtered results
    await expect(page.locator('[data-testid=product-row]')).toHaveCount({ min: 1 });
    
    // Verify all visible products are Electronics
    const categoryChips = page.locator('[data-testid=product-category-chip]');
    const count = await categoryChips.count();
    for (let i = 0; i < count; i++) {
      await expect(categoryChips.nth(i)).toContainText('Electronics');
    }
  });

  test('should handle low stock alerts', async ({ page }) => {
    await page.goto('/products');
    
    // Open filters
    await page.click('[data-testid=filters-button]');
    
    // Filter by low stock
    await page.selectOption('[data-testid=stock-status-filter]', 'low_stock');
    await page.click('[data-testid=close-filters]');
    
    // Verify low stock products are highlighted
    const lowStockProducts = page.locator('[data-testid=low-stock-indicator]');
    expect(await lowStockProducts.count()).toBeGreaterThan(0);
  });

  test('should perform bulk operations', async ({ page }) => {
    await page.goto('/products');
    
    // Select multiple products
    await page.check('[data-testid=select-all-products]');
    
    // Verify bulk actions are enabled
    await expect(page.locator('[data-testid=bulk-actions-toolbar]')).toBeVisible();
    
    // Test bulk status update
    await page.click('[data-testid=bulk-update-button]');
    await page.selectOption('[data-testid=bulk-status-select]', 'inactive');
    await page.click('[data-testid=confirm-bulk-update]');
    
    // Verify success message
    await expect(page.locator('[data-testid=success-alert]')).toBeVisible();
  });

  test('should export product data', async ({ page }) => {
    await page.goto('/products');
    
    // Start download
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid=export-products-button]');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/products.*\.csv$/);
  });

  test('should handle pagination correctly', async ({ page }) => {
    await page.goto('/products');
    
    // Verify pagination controls are visible
    await expect(page.locator('[data-testid=pagination-controls]')).toBeVisible();
    
    // Check page size options
    await page.click('[data-testid=page-size-select]');
    await expect(page.locator('[data-testid=page-size-option-25]')).toBeVisible();
    await expect(page.locator('[data-testid=page-size-option-50]')).toBeVisible();
    
    // Select different page size
    await page.click('[data-testid=page-size-option-50]');
    
    // Verify URL parameters
    await expect(page).toHaveURL(/pageSize=50/);
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: Delete test products
    await page.goto('/products');
    await page.fill('[data-testid=search-products]', 'Test Product E2E');
    
    const testProducts = page.locator('[data-testid=product-row]');
    const count = await testProducts.count();
    
    for (let i = 0; i < count; i++) {
      await page.click('[data-testid=delete-product-button]');
      await page.click('[data-testid=confirm-delete]');
      await page.waitForTimeout(500);
    }
  });
});