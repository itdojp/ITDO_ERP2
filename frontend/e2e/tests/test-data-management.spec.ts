import { test, expect } from '../fixtures/test-data.fixture';

/**
 * Test Data Management Suite
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Tests for test data isolation, cleanup, and management
 */

test.describe('Test Data Management', () => {
  test('テストデータの作成と削除', async ({ testDataManager }) => {
    // Create test organization
    const organization = await testDataManager.createOrganization({
      name: 'Test Data Management Org'
    });

    expect(organization.data.name).toBe('Test Data Management Org');
    expect(organization.id).toMatch(/^org-\d+$/);

    // Create dependent entities
    const department = await testDataManager.createDepartment(organization.data.id);
    const user = await testDataManager.createUser(organization.data.id);

    // Verify entities exist
    expect(testDataManager.getEntity(organization.id)).toBeDefined();
    expect(testDataManager.getEntity(department.id)).toBeDefined();
    expect(testDataManager.getEntity(user.id)).toBeDefined();

    // Delete organization should cascade
    await testDataManager.deleteEntity(organization.id);

    // All entities should be gone
    expect(testDataManager.getEntity(organization.id)).toBeUndefined();
    expect(testDataManager.getEntity(department.id)).toBeUndefined();
    expect(testDataManager.getEntity(user.id)).toBeUndefined();
  });

  test('完全なテストシナリオの作成', async ({ testDataManager }) => {
    const scenario = await testDataManager.createTestScenario('complete-scenario');

    // Verify all entities were created
    expect(scenario.organization.data.name).toContain('complete-scenario');
    expect(scenario.department.data.name).toContain('complete-scenario');
    expect(scenario.users).toHaveLength(3);
    expect(scenario.project.data.name).toContain('complete-scenario');
    expect(scenario.tasks).toHaveLength(3);

    // Verify task priorities
    const priorities = scenario.tasks.map(task => task.data.priority);
    expect(priorities).toContain('high');
    expect(priorities).toContain('medium');
    expect(priorities).toContain('low');

    // Verify dependencies
    expect(scenario.department.dependencies).toContain(scenario.organization.id);
    scenario.users.forEach(user => {
      expect(user.dependencies).toContain(scenario.organization.id);
    });
  });

  test('テストデータの分離', async ({ testDataManager }) => {
    // Create two separate test scenarios
    const scenario1 = await testDataManager.createTestScenario('scenario-1');
    const scenario2 = await testDataManager.createTestScenario('scenario-2');

    // Verify they are separate
    expect(scenario1.organization.data.id).not.toBe(scenario2.organization.data.id);
    expect(scenario1.organization.data.name).toContain('scenario-1');
    expect(scenario2.organization.data.name).toContain('scenario-2');

    // Users should be in different organizations
    expect(scenario1.users[0].data.organization_id).toBe(scenario1.organization.data.id);
    expect(scenario2.users[0].data.organization_id).toBe(scenario2.organization.data.id);
  });

  test('エンティティタイプ別の取得', async ({ testDataManager }) => {
    // Create multiple entities of different types
    const org1 = await testDataManager.createOrganization({ name: 'Org 1' });
    const org2 = await testDataManager.createOrganization({ name: 'Org 2' });
    const user1 = await testDataManager.createUser(org1.data.id);
    const user2 = await testDataManager.createUser(org2.data.id);

    // Get entities by type
    const organizations = testDataManager.getEntitiesByType('organization');
    const users = testDataManager.getEntitiesByType('user');

    expect(organizations).toHaveLength(2);
    expect(users).toHaveLength(2);

    // Verify correct entities
    expect(organizations.map(o => o.data.name)).toContain('Org 1');
    expect(organizations.map(o => o.data.name)).toContain('Org 2');
  });

  test('テストデータのエクスポート', async ({ testDataManager }) => {
    // Create some test data
    const org = await testDataManager.createOrganization({ name: 'Export Test Org' });
    const user = await testDataManager.createUser(org.data.id, { 
      full_name: 'Export Test User' 
    });

    // Export data
    const exportedData = testDataManager.exportTestData();
    const parsedData = JSON.parse(exportedData);

    // Verify export contains correct data
    expect(parsedData).toHaveLength(2);
    expect(parsedData.find((e: any) => e.type === 'organization')).toBeDefined();
    expect(parsedData.find((e: any) => e.type === 'user')).toBeDefined();

    // Verify structure
    const orgData = parsedData.find((e: any) => e.type === 'organization');
    expect(orgData).toHaveProperty('id');
    expect(orgData).toHaveProperty('type');
    expect(orgData).toHaveProperty('data');
    expect(orgData).toHaveProperty('createdAt');
    expect(orgData).toHaveProperty('dependencies');
  });

  test('大量データの処理', async ({ testDataManager }) => {
    const organization = await testDataManager.createOrganization({
      name: 'Bulk Data Test Org'
    });

    // Create multiple users
    const userPromises = [];
    for (let i = 0; i < 10; i++) {
      userPromises.push(
        testDataManager.createUser(organization.data.id, {
          full_name: `Bulk User ${i}`,
          email: `bulk-user-${i}@e2e.test`
        })
      );
    }

    const users = await Promise.all(userPromises);

    // Verify all users were created
    expect(users).toHaveLength(10);

    // Verify they all belong to the same organization
    users.forEach(user => {
      expect(user.data.organization_id).toBe(organization.data.id);
      expect(user.dependencies).toContain(organization.id);
    });

    // Verify cleanup summary
    const summary = testDataManager.getCleanupSummary();
    expect(summary.user).toBe(10);
    expect(summary.organization).toBe(1);
  });

  test('エラーハンドリング', async ({ testDataManager }) => {
    // Try to create user with invalid organization ID
    await expect(
      testDataManager.createUser(99999, { full_name: 'Invalid User' })
    ).rejects.toThrow('Failed to create user');

    // Try to get non-existent entity
    const nonExistentEntity = testDataManager.getEntity('non-existent-id');
    expect(nonExistentEntity).toBeUndefined();
  });

  test('並行テストでのデータ分離', async ({ testDataManager }) => {
    // Create multiple scenarios concurrently
    const scenarios = await Promise.all([
      testDataManager.createTestScenario('concurrent-1'),
      testDataManager.createTestScenario('concurrent-2'),
      testDataManager.createTestScenario('concurrent-3')
    ]);

    // Verify all scenarios are separate
    const orgIds = scenarios.map(s => s.organization.data.id);
    const uniqueOrgIds = new Set(orgIds);
    expect(uniqueOrgIds.size).toBe(3);

    // Verify each scenario has its own data
    scenarios.forEach((scenario, index) => {
      expect(scenario.organization.data.name).toContain(`concurrent-${index + 1}`);
      expect(scenario.users).toHaveLength(3);
      expect(scenario.tasks).toHaveLength(3);
    });
  });

  test('タイムアウト処理', async ({ testDataManager }) => {
    const org = await testDataManager.createOrganization();
    
    // Should find entity immediately
    const foundEntity = await testDataManager.waitForEntity(org.id, 1000);
    expect(foundEntity).toBeDefined();
    expect(foundEntity.id).toBe(org.id);

    // Should timeout for non-existent entity
    await expect(
      testDataManager.waitForEntity('non-existent-id', 500)
    ).rejects.toThrow('Entity non-existent-id not found within timeout');
  });
});