import { test, expect } from '@playwright/test';

test.describe('Sales Workflow End-to-End', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'sales@example.com');
    await page.fill('[data-testid=password]', 'password123');
    await page.click('[data-testid=login-button]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('complete sales flow: quote → order → invoice → payment', async ({ page }) => {
    // Step 1: Create Customer
    await page.goto('/customers');
    await page.click('[data-testid=add-customer-button]');
    
    await page.fill('[data-testid=customer-name]', 'E2E Test Customer');
    await page.fill('[data-testid=customer-email]', 'e2e@test.com');
    await page.fill('[data-testid=customer-phone]', '+1-555-0123');
    await page.fill('[data-testid=customer-company]', 'E2E Test Corp');
    
    // Billing address
    await page.fill('[data-testid=billing-street]', '123 Test Street');
    await page.fill('[data-testid=billing-city]', 'Test City');
    await page.fill('[data-testid=billing-state]', 'Test State');
    await page.fill('[data-testid=billing-postal]', '12345');
    await page.fill('[data-testid=billing-country]', 'USA');
    
    await page.click('[data-testid=save-customer-button]');
    await expect(page.locator('[data-testid=success-alert]')).toBeVisible();

    // Step 2: Create Quote
    await page.goto('/quotes');
    await page.click('[data-testid=add-quote-button]');
    
    // Select customer
    await page.click('[data-testid=customer-select]');
    await page.fill('[data-testid=customer-search]', 'E2E Test Customer');
    await page.click('[data-testid=customer-option]');
    
    // Add quote items
    await page.click('[data-testid=add-quote-item]');
    await page.click('[data-testid=product-select]');
    await page.fill('[data-testid=product-search]', 'Test Product');
    await page.click('[data-testid=product-option]');
    await page.fill('[data-testid=item-quantity]', '2');
    await page.fill('[data-testid=item-price]', '99.99');
    
    // Set quote details
    await page.fill('[data-testid=quote-notes]', 'E2E test quote');
    await page.fill('[data-testid=valid-until]', '2024-12-31');
    
    await page.click('[data-testid=save-quote-button]');
    await expect(page.locator('[data-testid=success-alert]')).toBeVisible();
    
    // Get quote ID for next steps
    const quoteId = await page.locator('[data-testid=quote-id]').textContent();

    // Step 3: Convert Quote to Order
    await page.click('[data-testid=convert-to-order-button]');
    await page.click('[data-testid=confirm-conversion]');
    
    await expect(page.locator('[data-testid=success-alert]')).toContainText('Quote converted to order');
    await expect(page).toHaveURL(/\/orders\/\d+/);
    
    // Verify order details
    await expect(page.locator('[data-testid=order-customer]')).toContainText('E2E Test Customer');
    await expect(page.locator('[data-testid=order-total]')).toContainText('$199.98');

    // Step 4: Process Order
    await page.click('[data-testid=process-order-button]');
    await page.selectOption('[data-testid=order-status]', 'confirmed');
    await page.click('[data-testid=update-order-status]');
    
    await expect(page.locator('[data-testid=order-status-chip]')).toContainText('Confirmed');

    // Step 5: Create Invoice from Order
    await page.click('[data-testid=create-invoice-button]');
    await page.click('[data-testid=confirm-invoice-creation]');
    
    await expect(page.locator('[data-testid=success-alert]')).toContainText('Invoice created');
    await expect(page).toHaveURL(/\/invoices\/\d+/);
    
    // Verify invoice details
    await expect(page.locator('[data-testid=invoice-customer]')).toContainText('E2E Test Customer');
    await expect(page.locator('[data-testid=invoice-total]')).toContainText('$199.98');
    await expect(page.locator('[data-testid=invoice-status]')).toContainText('Draft');

    // Step 6: Send Invoice
    await page.click('[data-testid=send-invoice-button]');
    await page.click('[data-testid=confirm-send-invoice]');
    
    await expect(page.locator('[data-testid=invoice-status]')).toContainText('Sent');

    // Step 7: Record Payment
    await page.click('[data-testid=record-payment-button]');
    await page.fill('[data-testid=payment-amount]', '199.98');
    await page.selectOption('[data-testid=payment-method]', 'credit_card');
    await page.fill('[data-testid=payment-notes]', 'E2E test payment');
    
    await page.click('[data-testid=save-payment-button]');
    
    await expect(page.locator('[data-testid=success-alert]')).toContainText('Payment recorded');
    await expect(page.locator('[data-testid=invoice-status]')).toContainText('Paid');
    await expect(page.locator('[data-testid=balance-due]')).toContainText('$0.00');
  });

  test('should handle partial payments correctly', async ({ page }) => {
    // Navigate to existing invoice
    await page.goto('/invoices');
    await page.click('[data-testid=invoice-row]');
    
    // Record partial payment
    await page.click('[data-testid=record-payment-button]');
    await page.fill('[data-testid=payment-amount]', '100.00');
    await page.selectOption('[data-testid=payment-method]', 'bank_transfer');
    
    await page.click('[data-testid=save-payment-button]');
    
    // Verify partial payment status
    await expect(page.locator('[data-testid=invoice-status]')).toContainText('Partial');
    await expect(page.locator('[data-testid=paid-amount]')).toContainText('$100.00');
    
    const balanceDue = await page.locator('[data-testid=balance-due]').textContent();
    expect(parseFloat(balanceDue?.replace('$', '') || '0')).toBeGreaterThan(0);
  });

  test('should track order fulfillment', async ({ page }) => {
    await page.goto('/orders');
    await page.click('[data-testid=order-row]');
    
    // Update fulfillment status
    await page.click('[data-testid=fulfill-order-button]');
    
    // Select items to fulfill
    await page.fill('[data-testid=fulfill-quantity-0]', '1');
    await page.click('[data-testid=confirm-fulfillment]');
    
    // Verify fulfillment tracking
    await expect(page.locator('[data-testid=fulfillment-status]')).toContainText('Partially Fulfilled');
    
    // Complete fulfillment
    await page.click('[data-testid=fulfill-order-button]');
    await page.fill('[data-testid=fulfill-quantity-0]', '1');
    await page.click('[data-testid=confirm-fulfillment]');
    
    await expect(page.locator('[data-testid=fulfillment-status]')).toContainText('Fulfilled');
  });

  test('should generate accurate sales reports', async ({ page }) => {
    await page.goto('/reports/sales');
    
    // Set date range
    await page.fill('[data-testid=date-from]', '2024-01-01');
    await page.fill('[data-testid=date-to]', '2024-12-31');
    await page.click('[data-testid=generate-report]');
    
    // Verify report data
    await expect(page.locator('[data-testid=total-revenue]')).toBeVisible();
    await expect(page.locator('[data-testid=total-orders]')).toBeVisible();
    await expect(page.locator('[data-testid=average-order-value]')).toBeVisible();
    
    // Verify chart rendering
    await expect(page.locator('[data-testid=revenue-chart]')).toBeVisible();
    await expect(page.locator('[data-testid=orders-chart]')).toBeVisible();
    
    // Export report
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid=export-report]');
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/sales-report.*\.pdf$/);
  });

  test('should handle quote expiration', async ({ page }) => {
    await page.goto('/quotes');
    
    // Create quote with past expiration date
    await page.click('[data-testid=add-quote-button]');
    await page.click('[data-testid=customer-select]');
    await page.click('[data-testid=customer-option]');
    
    // Set expired date
    await page.fill('[data-testid=valid-until]', '2024-01-01');
    
    await page.click('[data-testid=save-quote-button]');
    
    // Try to convert expired quote
    await page.click('[data-testid=convert-to-order-button]');
    
    // Should show error message
    await expect(page.locator('[data-testid=error-alert]')).toContainText('Quote has expired');
    
    // Verify quote status
    await expect(page.locator('[data-testid=quote-status]')).toContainText('Expired');
  });

  test('should validate inventory availability', async ({ page }) => {
    await page.goto('/orders/new');
    
    // Add product with insufficient stock
    await page.click('[data-testid=add-order-item]');
    await page.click('[data-testid=product-select]');
    await page.click('[data-testid=product-option]');
    
    // Enter quantity higher than available stock
    await page.fill('[data-testid=item-quantity]', '9999');
    
    // Should show validation error
    await expect(page.locator('[data-testid=stock-error]')).toContainText('Insufficient stock');
    
    // Save button should be disabled
    await expect(page.locator('[data-testid=save-order-button]')).toBeDisabled();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test data
    await page.goto('/customers');
    await page.fill('[data-testid=search-customers]', 'E2E Test Customer');
    
    const testCustomers = page.locator('[data-testid=customer-row]');
    const count = await testCustomers.count();
    
    for (let i = 0; i < count; i++) {
      await page.click('[data-testid=delete-customer-button]');
      await page.click('[data-testid=confirm-delete]');
      await page.waitForTimeout(500);
    }
  });
});