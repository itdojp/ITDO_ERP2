import { test as base } from '@playwright/test';
import { TestDataManager } from '../utils/test-data-manager';

/**
 * Test Data Fixture
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Provides test data management capabilities to tests
 */

export const test = base.extend<{
  testDataManager: TestDataManager;
}>({
  testDataManager: async ({ request }, use) => {
    const manager = new TestDataManager(request, {
      autoCleanup: true,
      isolationLevel: 'test',
      seedData: false
    });

    // Authenticate
    await manager.authenticate();

    // Use the manager
    await use(manager);

    // Cleanup after test
    await manager.cleanup();
    
    const summary = manager.getCleanupSummary();
    console.log('Test data cleanup summary:', summary);
  }
});

export { expect } from '@playwright/test';