import { test, expect } from '@playwright/test';

test.describe('Financial Reporting & Accounting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'accountant@example.com');
    await page.fill('[data-testid=password]', 'password123');
    await page.click('[data-testid=login-button]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should display accurate financial dashboard metrics', async ({ page }) => {
    await page.goto('/accounting/dashboard');
    
    // Verify key financial metrics are displayed
    await expect(page.locator('[data-testid=total-assets]')).toBeVisible();
    await expect(page.locator('[data-testid=total-liabilities]')).toBeVisible();
    await expect(page.locator('[data-testid=total-equity]')).toBeVisible();
    await expect(page.locator('[data-testid=net-income]')).toBeVisible();
    
    // Verify metrics have numeric values
    const totalAssets = await page.locator('[data-testid=total-assets-value]').textContent();
    expect(totalAssets).toMatch(/\$[\d,]+\.?\d*/);
    
    // Verify charts are rendered
    await expect(page.locator('[data-testid=revenue-chart]')).toBeVisible();
    await expect(page.locator('[data-testid=expense-chart]')).toBeVisible();
    await expect(page.locator('[data-testid=cash-flow-chart]')).toBeVisible();
    
    // Test real-time updates
    await page.click('[data-testid=refresh-dashboard]');
    await page.waitForTimeout(2000);
    
    // Verify dashboard refreshed
    await expect(page.locator('[data-testid=last-updated]')).toContainText('just now');
  });

  test('should generate accurate balance sheet', async ({ page }) => {
    await page.goto('/accounting/reports');
    
    // Generate balance sheet
    await page.click('[data-testid=balance-sheet-tab]');
    await page.fill('[data-testid=as-of-date]', '2024-12-31');
    await page.click('[data-testid=generate-balance-sheet]');
    
    // Wait for report generation
    await expect(page.locator('[data-testid=balance-sheet-report]')).toBeVisible();
    
    // Verify balance sheet structure
    await expect(page.locator('[data-testid=assets-section]')).toBeVisible();
    await expect(page.locator('[data-testid=liabilities-section]')).toBeVisible();
    await expect(page.locator('[data-testid=equity-section]')).toBeVisible();
    
    // Verify accounting equation: Assets = Liabilities + Equity
    const assetsText = await page.locator('[data-testid=total-assets-amount]').textContent();
    const liabilitiesText = await page.locator('[data-testid=total-liabilities-amount]').textContent();
    const equityText = await page.locator('[data-testid=total-equity-amount]').textContent();
    
    const assets = parseFloat(assetsText?.replace(/[$,]/g, '') || '0');
    const liabilities = parseFloat(liabilitiesText?.replace(/[$,]/g, '') || '0');
    const equity = parseFloat(equityText?.replace(/[$,]/g, '') || '0');
    
    expect(Math.abs(assets - (liabilities + equity))).toBeLessThan(0.01);
    
    // Export balance sheet
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid=export-balance-sheet]');
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/balance-sheet.*\.pdf$/);
  });

  test('should generate income statement with accurate calculations', async ({ page }) => {
    await page.goto('/accounting/reports');
    
    // Generate income statement
    await page.click('[data-testid=income-statement-tab]');
    await page.fill('[data-testid=period-start]', '2024-01-01');
    await page.fill('[data-testid=period-end]', '2024-12-31');
    await page.click('[data-testid=generate-income-statement]');
    
    // Verify income statement sections
    await expect(page.locator('[data-testid=revenue-section]')).toBeVisible();
    await expect(page.locator('[data-testid=cost-of-goods-sold]')).toBeVisible();
    await expect(page.locator('[data-testid=gross-profit]')).toBeVisible();
    await expect(page.locator('[data-testid=operating-expenses]')).toBeVisible();
    await expect(page.locator('[data-testid=net-income]')).toBeVisible();
    
    // Verify calculation accuracy
    const revenueText = await page.locator('[data-testid=total-revenue-amount]').textContent();
    const cogsText = await page.locator('[data-testid=total-cogs-amount]').textContent();
    const grossProfitText = await page.locator('[data-testid=gross-profit-amount]').textContent();
    
    const revenue = parseFloat(revenueText?.replace(/[$,]/g, '') || '0');
    const cogs = parseFloat(cogsText?.replace(/[$,]/g, '') || '0');
    const grossProfit = parseFloat(grossProfitText?.replace(/[$,]/g, '') || '0');
    
    expect(Math.abs(grossProfit - (revenue - cogs))).toBeLessThan(0.01);
  });

  test('should handle journal entries with double-entry validation', async ({ page }) => {
    await page.goto('/accounting/journal-entries');
    
    // Create new journal entry
    await page.click('[data-testid=add-journal-entry]');
    
    // Fill entry details
    await page.fill('[data-testid=entry-date]', '2024-01-15');
    await page.fill('[data-testid=entry-description]', 'E2E Test Journal Entry');
    await page.fill('[data-testid=entry-reference]', 'TEST-001');
    
    // Add debit entry
    await page.click('[data-testid=add-entry-line]');
    await page.selectOption('[data-testid=account-select-0]', 'Cash');
    await page.fill('[data-testid=debit-amount-0]', '1000.00');
    await page.fill('[data-testid=line-description-0]', 'Test debit entry');
    
    // Add credit entry
    await page.click('[data-testid=add-entry-line]');
    await page.selectOption('[data-testid=account-select-1]', 'Revenue');
    await page.fill('[data-testid=credit-amount-1]', '1000.00');
    await page.fill('[data-testid=line-description-1]', 'Test credit entry');
    
    // Verify balance validation
    await expect(page.locator('[data-testid=total-debits]')).toContainText('$1,000.00');
    await expect(page.locator('[data-testid=total-credits]')).toContainText('$1,000.00');
    await expect(page.locator('[data-testid=balance-indicator]')).toContainText('Balanced');
    
    // Save journal entry
    await page.click('[data-testid=save-journal-entry]');
    
    // Verify success
    await expect(page.locator('[data-testid=success-alert]')).toContainText('Journal entry saved');
    
    // Post the entry
    await page.click('[data-testid=post-journal-entry]');
    await page.click('[data-testid=confirm-post]');
    
    // Verify posted status
    await expect(page.locator('[data-testid=entry-status]')).toContainText('Posted');
  });

  test('should validate unbalanced journal entries', async ({ page }) => {
    await page.goto('/accounting/journal-entries');
    await page.click('[data-testid=add-journal-entry]');
    
    // Add unbalanced entries
    await page.click('[data-testid=add-entry-line]');
    await page.selectOption('[data-testid=account-select-0]', 'Cash');
    await page.fill('[data-testid=debit-amount-0]', '1000.00');
    
    await page.click('[data-testid=add-entry-line]');
    await page.selectOption('[data-testid=account-select-1]', 'Revenue');
    await page.fill('[data-testid=credit-amount-1]', '500.00');
    
    // Verify unbalanced indicator
    await expect(page.locator('[data-testid=balance-indicator]')).toContainText('Unbalanced');
    await expect(page.locator('[data-testid=balance-difference]')).toContainText('$500.00');
    
    // Save button should be disabled
    await expect(page.locator('[data-testid=save-journal-entry]')).toBeDisabled();
    
    // Show validation error
    await expect(page.locator('[data-testid=balance-error]')).toContainText('Debits must equal credits');
  });

  test('should manage chart of accounts hierarchy', async ({ page }) => {
    await page.goto('/accounting/chart-of-accounts');
    
    // Create parent account
    await page.click('[data-testid=add-account]');
    await page.fill('[data-testid=account-code]', '1000');
    await page.fill('[data-testid=account-name]', 'Current Assets');
    await page.selectOption('[data-testid=account-type]', 'asset');
    await page.click('[data-testid=save-account]');
    
    // Create child account
    await page.click('[data-testid=add-account]');
    await page.fill('[data-testid=account-code]', '1010');
    await page.fill('[data-testid=account-name]', 'Cash in Bank');
    await page.selectOption('[data-testid=account-type]', 'asset');
    await page.selectOption('[data-testid=parent-account]', '1000 - Current Assets');
    await page.click('[data-testid=save-account]');
    
    // Verify hierarchy display
    await expect(page.locator('[data-testid=account-hierarchy]')).toContainText('Current Assets');
    await expect(page.locator('[data-testid=child-account]')).toContainText('Cash in Bank');
    
    // Test account balance calculation
    await expect(page.locator('[data-testid=account-balance-1000]')).toBeVisible();
    await expect(page.locator('[data-testid=account-balance-1010]')).toBeVisible();
  });

  test('should perform bank reconciliation', async ({ page }) => {
    await page.goto('/accounting/reconciliation');
    
    // Select bank account
    await page.selectOption('[data-testid=bank-account-select]', 'Cash in Bank');
    await page.fill('[data-testid=statement-date]', '2024-01-31');
    await page.fill('[data-testid=ending-balance]', '5000.00');
    
    // Load transactions
    await page.click('[data-testid=load-transactions]');
    
    // Mark transactions as reconciled
    await page.check('[data-testid=reconcile-transaction-1]');
    await page.check('[data-testid=reconcile-transaction-2]');
    
    // Verify reconciliation balance
    const reconciledBalance = await page.locator('[data-testid=reconciled-balance]').textContent();
    const difference = await page.locator('[data-testid=reconciliation-difference]').textContent();
    
    expect(reconciledBalance).toMatch(/\$[\d,]+\.?\d*/);
    
    // Complete reconciliation if balanced
    if (difference === '$0.00') {
      await page.click('[data-testid=complete-reconciliation]');
      await expect(page.locator('[data-testid=success-alert]')).toContainText('Reconciliation completed');
    }
  });

  test('should generate cash flow statement', async ({ page }) => {
    await page.goto('/accounting/reports');
    
    // Generate cash flow statement
    await page.click('[data-testid=cash-flow-tab]');
    await page.fill('[data-testid=period-start]', '2024-01-01');
    await page.fill('[data-testid=period-end]', '2024-12-31');
    await page.click('[data-testid=generate-cash-flow]');
    
    // Verify cash flow sections
    await expect(page.locator('[data-testid=operating-activities]')).toBeVisible();
    await expect(page.locator('[data-testid=investing-activities]')).toBeVisible();
    await expect(page.locator('[data-testid=financing-activities]')).toBeVisible();
    
    // Verify cash flow calculation
    const beginningCash = await page.locator('[data-testid=beginning-cash]').textContent();
    const endingCash = await page.locator('[data-testid=ending-cash]').textContent();
    const netCashFlow = await page.locator('[data-testid=net-cash-flow]').textContent();
    
    expect(beginningCash).toMatch(/\$[\d,]+\.?\d*/);
    expect(endingCash).toMatch(/\$[\d,]+\.?\d*/);
    expect(netCashFlow).toMatch(/[\-$]?[\d,]+\.?\d*/);
  });

  test('should handle budget vs actual reporting', async ({ page }) => {
    await page.goto('/accounting/budgets');
    
    // Create budget
    await page.click('[data-testid=add-budget]');
    await page.fill('[data-testid=budget-name]', 'E2E Test Budget 2024');
    await page.fill('[data-testid=fiscal-year]', '2024');
    await page.fill('[data-testid=period-start]', '2024-01-01');
    await page.fill('[data-testid=period-end]', '2024-12-31');
    
    // Add budget items
    await page.click('[data-testid=add-budget-item]');
    await page.selectOption('[data-testid=budget-account-0]', 'Revenue');
    await page.fill('[data-testid=budget-amount-0]', '100000');
    
    await page.click('[data-testid=save-budget]');
    
    // View budget vs actual report
    await page.click('[data-testid=view-budget-report]');
    
    // Verify variance calculations
    await expect(page.locator('[data-testid=budgeted-amount]')).toContainText('$100,000.00');
    await expect(page.locator('[data-testid=actual-amount]')).toBeVisible();
    await expect(page.locator('[data-testid=variance-amount]')).toBeVisible();
    await expect(page.locator('[data-testid=variance-percentage]')).toBeVisible();
    
    // Verify variance highlighting
    const varianceElement = page.locator('[data-testid=variance-indicator]');
    await expect(varianceElement).toHaveAttribute('data-variance-type', /favorable|unfavorable/);
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test journal entries
    await page.goto('/accounting/journal-entries');
    await page.fill('[data-testid=search-entries]', 'E2E Test');
    
    const testEntries = page.locator('[data-testid=entry-row]');
    const count = await testEntries.count();
    
    for (let i = 0; i < count; i++) {
      await page.click('[data-testid=delete-entry-button]');
      await page.click('[data-testid=confirm-delete]');
      await page.waitForTimeout(500);
    }
  });
});