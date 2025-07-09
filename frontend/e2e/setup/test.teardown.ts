import { test as teardown } from '@playwright/test';
import { ApiClient } from '../fixtures/api.fixture';

/**
 * Global Test Teardown
 * Sprint 2 Day 1 - E2E Test Infrastructure
 * 
 * Cleans up test environment after E2E tests
 */

teardown('global test teardown', async ({ request }) => {
  console.log('🧹 Starting global test teardown...');
  
  const apiClient = new ApiClient();
  await apiClient.init();
  
  try {
    // 1. Clean up test data created during tests
    console.log('🗑️ Cleaning up test data...');
    
    // Get organization IDs from environment
    const org1Id = process.env.E2E_ORG1_ID;
    const org2Id = process.env.E2E_ORG2_ID;
    
    // Clean up in reverse order of creation to handle dependencies
    
    // Delete test tasks
    try {
      const tasks = await apiClient.get('/tasks?limit=100');
      const testTasks = tasks.items?.filter((task: any) => 
        task.title?.startsWith('Test Task') || 
        task.title?.startsWith('E2E')
      );
      
      for (const task of testTasks || []) {
        try {
          await apiClient.delete(`/tasks/${task.id}`);
          console.log(`✅ Deleted test task: ${task.title}`);
        } catch (error) {
          console.log(`⚠️ Failed to delete task ${task.id}:`, error);
        }
      }
    } catch (error) {
      console.log('⚠️ Error cleaning up tasks:', error);
    }
    
    // Delete test users (except the default ones we need)
    try {
      const users = await apiClient.get('/admin/users?limit=100');
      const testUsers = users.items?.filter((user: any) => 
        user.email?.includes('@e2e.test') && 
        !['superadmin@e2e.test', 'orgadmin@e2e.test', 'manager@e2e.test', 'user@e2e.test']
          .includes(user.email)
      );
      
      for (const user of testUsers || []) {
        try {
          await apiClient.delete(`/admin/users/${user.id}`);
          console.log(`✅ Deleted test user: ${user.email}`);
        } catch (error) {
          console.log(`⚠️ Failed to delete user ${user.id}:`, error);
        }
      }
    } catch (error) {
      console.log('⚠️ Error cleaning up users:', error);
    }
    
    // Delete test departments
    if (org1Id || org2Id) {
      try {
        const departments = await apiClient.get('/admin/departments?limit=100');
        const testDepts = departments.items?.filter((dept: any) => 
          dept.code?.startsWith('E2E-') || 
          dept.code?.startsWith('TEST-')
        );
        
        for (const dept of testDepts || []) {
          try {
            await apiClient.delete(`/admin/departments/${dept.id}`);
            console.log(`✅ Deleted test department: ${dept.name}`);
          } catch (error) {
            console.log(`⚠️ Failed to delete department ${dept.id}:`, error);
          }
        }
      } catch (error) {
        console.log('⚠️ Error cleaning up departments:', error);
      }
    }
    
    // Delete test organizations (optional - you might want to keep them)
    const shouldDeleteOrgs = process.env.E2E_CLEANUP_ORGS === 'true';
    if (shouldDeleteOrgs && (org1Id || org2Id)) {
      try {
        if (org1Id) {
          await apiClient.delete(`/admin/organizations/${org1Id}`);
          console.log('✅ Deleted test organization 1');
        }
        if (org2Id) {
          await apiClient.delete(`/admin/organizations/${org2Id}`);
          console.log('✅ Deleted test organization 2');
        }
      } catch (error) {
        console.log('⚠️ Error deleting test organizations:', error);
      }
    }
    
    // 2. Clear any cached data
    console.log('🧹 Clearing cached data...');
    
    // This would clear Redis cache if needed
    try {
      await apiClient.post('/admin/cache/clear', {});
      console.log('✅ Cleared cache');
    } catch (error) {
      console.log('⚠️ Cache clear not available:', error);
    }
    
    // 3. Reset test counters
    console.log('🔄 Resetting test counters...');
    // This is handled by TestDataGenerator.reset() in setup
    
    // 4. Log final cleanup summary
    console.log('📊 Teardown Summary:');
    console.log('- Test data cleaned up');
    console.log('- Cache cleared');
    console.log('- Environment reset');
    
    console.log('✅ Global test teardown completed successfully!');
    
  } catch (error) {
    console.error('❌ Teardown failed:', error);
    // Don't throw in teardown - we don't want to fail the test run
  } finally {
    await apiClient.close();
  }
});

// Cleanup for specific test suites
teardown('auth test cleanup', async ({ page }) => {
  console.log('🔑 Cleaning up authentication tests...');
  
  // Clear all cookies and storage
  await page.context().clearCookies();
  await page.context().clearPermissions();
  
  // Clear local storage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  
  console.log('✅ Auth test cleanup completed');
});