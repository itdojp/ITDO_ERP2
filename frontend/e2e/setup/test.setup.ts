import { test as setup } from '@playwright/test';
import { ApiClient, TestDataGenerator } from '../fixtures/api.fixture';
import { AuthFixture } from '../fixtures/auth.fixture';

/**
 * Global Test Setup
 * Sprint 2 Day 1 - E2E Test Infrastructure
 * 
 * Prepares test environment before running E2E tests
 */

setup('global test setup', async ({ request }) => {
  console.log('🚀 Starting global test setup...');
  
  const apiClient = new ApiClient();
  await apiClient.init();
  
  try {
    // 1. Wait for services to be ready
    console.log('⏳ Waiting for services...');
    await apiClient.waitForApi();
    
    // 2. Reset test data generator counter
    TestDataGenerator.reset();
    
    // 3. Create test organizations if needed
    console.log('🏢 Setting up test organizations...');
    
    try {
      // Create Organization 1
      const org1 = await apiClient.post('/admin/organizations', {
        name: 'E2E Test Organization 1',
        code: 'E2E-ORG-001',
        description: 'E2E testing organization 1',
        industry: 'Technology',
        website: 'https://e2e-org1.example.com',
      });
      
      console.log('✅ Created organization 1:', org1.id);
      
      // Create Organization 2 for multi-tenant testing
      const org2 = await apiClient.post('/admin/organizations', {
        name: 'E2E Test Organization 2',
        code: 'E2E-ORG-002',
        description: 'E2E testing organization 2',
        industry: 'Finance',
        website: 'https://e2e-org2.example.com',
      });
      
      console.log('✅ Created organization 2:', org2.id);
      
      // Store organization IDs for later use
      process.env.E2E_ORG1_ID = String(org1.id);
      process.env.E2E_ORG2_ID = String(org2.id);
      
    } catch (error) {
      console.log('⚠️ Organizations might already exist:', error);
    }
    
    // 4. Create default test users
    console.log('👥 Setting up test users...');
    
    const authFixture = new AuthFixture(apiClient);
    const testUsers = await authFixture.createTestUsers();
    
    // 5. Create initial test data
    console.log('📊 Creating initial test data...');
    
    // Create some departments
    if (process.env.E2E_ORG1_ID) {
      try {
        await apiClient.post('/admin/departments', {
          name: 'Engineering Department',
          code: 'E2E-ENG',
          organization_id: parseInt(process.env.E2E_ORG1_ID),
          description: 'E2E test engineering department',
        });
        
        await apiClient.post('/admin/departments', {
          name: 'Sales Department',
          code: 'E2E-SALES',
          organization_id: parseInt(process.env.E2E_ORG1_ID),
          description: 'E2E test sales department',
        });
        
        console.log('✅ Created test departments');
      } catch (error) {
        console.log('⚠️ Departments might already exist:', error);
      }
    }
    
    // 6. Verify Keycloak is accessible
    console.log('🔐 Checking Keycloak...');
    const keycloakHealthCheck = await fetch('http://localhost:8080/health/ready');
    if (!keycloakHealthCheck.ok) {
      console.warn('⚠️ Keycloak might not be fully ready');
    } else {
      console.log('✅ Keycloak is ready');
    }
    
    // 7. Save auth states for different browsers
    console.log('💾 Preparing authentication states...');
    
    // This would normally save auth states, but since we're using
    // API-based auth, we'll handle this in individual tests
    
    console.log('✅ Global test setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error);
    throw error;
  } finally {
    await apiClient.close();
  }
});

// Additional setup for specific test suites
setup('auth test setup', async ({ page }) => {
  console.log('🔑 Setting up authentication tests...');
  
  // Clear any existing sessions
  await page.context().clearCookies();
  await page.context().clearPermissions();
  
  // Set up test-specific permissions if needed
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  
  console.log('✅ Auth test setup completed');
});