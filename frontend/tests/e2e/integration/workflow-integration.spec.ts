import { test, expect } from '../fixtures/auth.fixture';

test.describe('Workflow Integration', () => {
  test('complete user-to-task workflow', async ({ authenticatedPage: page }) => {
    // 1. Create a new project
    await page.goto('/projects');
    await page.click('[data-testid="create-project-btn"]');
    await page.fill('[data-testid="project-name"]', 'E2E Workflow Project');
    await page.fill('[data-testid="project-code"]', 'E2E_PROJ');
    await page.fill('[data-testid="project-description"]', 'Integration test project');
    await page.click('[data-testid="submit-project"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 2. Create tasks for the project
    await page.goto('/tasks');
    await page.click('[data-testid="create-task-btn"]');
    await page.fill('[data-testid="task-title"]', 'Integration Test Task');
    await page.fill('[data-testid="task-description"]', 'Task created during workflow test');
    await page.selectOption('[data-testid="task-project"]', 'E2E Workflow Project');
    await page.selectOption('[data-testid="task-priority"]', 'HIGH');
    await page.click('[data-testid="submit-task"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 3. Assign task to user
    const taskItem = page.locator('[data-testid="task-item"]').filter({ hasText: 'Integration Test Task' });
    await taskItem.locator('[data-testid="assign-task"]').click();
    await page.selectOption('[data-testid="assignee-select"]', 'test@example.com');
    await page.click('[data-testid="confirm-assign"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 4. Update task progress
    await taskItem.click();
    await page.locator('[data-testid="progress-slider"]').fill('50');
    await page.click('[data-testid="save-progress"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 5. Add task comments
    await page.fill('[data-testid="comment-input"]', 'Progress update: 50% complete');
    await page.click('[data-testid="add-comment"]');
    
    await expect(page.locator('[data-testid="comment-list"]')).toContainText('Progress update: 50% complete');
    
    // 6. Complete the task
    await page.selectOption('[data-testid="task-status"]', 'COMPLETED');
    await page.click('[data-testid="save-status"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(taskItem).toContainText('COMPLETED');
  });

  test('organization hierarchy and permission flow', async ({ authenticatedPage: page }) => {
    // 1. Navigate to organization management
    await page.goto('/admin/organizations');
    
    // 2. Create a sub-organization
    await page.click('[data-testid="create-org-btn"]');
    await page.fill('[data-testid="org-name"]', 'Sub Organization');
    await page.fill('[data-testid="org-code"]', 'SUB_ORG');
    await page.selectOption('[data-testid="parent-org"]', '1'); // Test Organization
    await page.click('[data-testid="submit-org"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 3. Create department in sub-organization
    await page.goto('/departments');
    await page.click('[data-testid="create-department-btn"]');
    await page.fill('[data-testid="dept-name"]', 'Sub Department');
    await page.fill('[data-testid="dept-code"]', 'SUB_DEPT');
    await page.selectOption('[data-testid="dept-organization"]', 'Sub Organization');
    await page.click('[data-testid="submit-department"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 4. Create user in sub-department
    await page.goto('/admin/users');
    await page.click('[data-testid="create-user-btn"]');
    await page.fill('[data-testid="user-email"]', 'subdept@example.com');
    await page.fill('[data-testid="user-name"]', 'Sub Dept User');
    await page.fill('[data-testid="user-password"]', 'password123');
    await page.selectOption('[data-testid="user-department"]', 'Sub Department');
    await page.click('[data-testid="submit-user"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 5. Verify hierarchical permissions
    const subUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'subdept@example.com' });
    await subUser.click();
    await page.click('[data-testid="effective-permissions-tab"]');
    
    // Verify user inherits organization-level permissions
    await expect(page.locator('[data-testid="inherited-permissions"]')).toBeVisible();
  });

  test('cross-module data consistency', async ({ authenticatedPage: page }) => {
    // 1. Create user
    await page.goto('/admin/users');
    await page.click('[data-testid="create-user-btn"]');
    await page.fill('[data-testid="user-email"]', 'consistency@example.com');
    await page.fill('[data-testid="user-name"]', 'Consistency Test User');
    await page.fill('[data-testid="user-password"]', 'password123');
    await page.click('[data-testid="submit-user"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 2. Create project and assign the user as owner
    await page.goto('/projects');
    await page.click('[data-testid="create-project-btn"]');
    await page.fill('[data-testid="project-name"]', 'Consistency Test Project');
    await page.fill('[data-testid="project-code"]', 'CONS_PROJ');
    await page.selectOption('[data-testid="project-owner"]', 'consistency@example.com');
    await page.click('[data-testid="submit-project"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 3. Create task assigned to the same user
    await page.goto('/tasks');
    await page.click('[data-testid="create-task-btn"]');
    await page.fill('[data-testid="task-title"]', 'Consistency Test Task');
    await page.selectOption('[data-testid="task-project"]', 'Consistency Test Project');
    await page.selectOption('[data-testid="task-assignee"]', 'consistency@example.com');
    await page.click('[data-testid="submit-task"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 4. Verify data consistency across modules
    // Check project shows correct owner
    await page.goto('/projects');
    const projectItem = page.locator('[data-testid="project-item"]').filter({ hasText: 'Consistency Test Project' });
    await expect(projectItem).toContainText('Consistency Test User');
    
    // Check task shows correct assignee
    await page.goto('/tasks');
    const taskItem = page.locator('[data-testid="task-item"]').filter({ hasText: 'Consistency Test Task' });
    await expect(taskItem).toContainText('Consistency Test User');
    
    // Check user profile shows associated projects and tasks
    await page.goto('/admin/users');
    const userItem = page.locator('[data-testid="user-item"]').filter({ hasText: 'consistency@example.com' });
    await userItem.click();
    
    await page.click('[data-testid="user-projects-tab"]');
    await expect(page.locator('[data-testid="user-project-list"]')).toContainText('Consistency Test Project');
    
    await page.click('[data-testid="user-tasks-tab"]');
    await expect(page.locator('[data-testid="user-task-list"]')).toContainText('Consistency Test Task');
  });

  test('audit trail verification', async ({ authenticatedPage: page }) => {
    // 1. Perform various actions that should be audited
    await page.goto('/tasks');
    await page.click('[data-testid="create-task-btn"]');
    await page.fill('[data-testid="task-title"]', 'Audit Test Task');
    await page.fill('[data-testid="task-description"]', 'Task for audit testing');
    await page.click('[data-testid="submit-task"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 2. Edit the task
    const taskItem = page.locator('[data-testid="task-item"]').filter({ hasText: 'Audit Test Task' });
    await taskItem.locator('[data-testid="edit-task"]').click();
    await page.fill('[data-testid="task-title"]', 'Audit Test Task - Edited');
    await page.click('[data-testid="save-task"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 3. Change task status
    await taskItem.click();
    await page.selectOption('[data-testid="task-status"]', 'IN_PROGRESS');
    await page.click('[data-testid="save-status"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 4. Check audit trail
    await page.click('[data-testid="task-history-tab"]');
    
    // Verify audit entries exist
    await expect(page.locator('[data-testid="audit-entry"]')).toHaveCount(3); // Create, Edit, Status Change
    await expect(page.locator('[data-testid="audit-entry"]')).toContainText('task_created');
    await expect(page.locator('[data-testid="audit-entry"]')).toContainText('task_updated');
    await expect(page.locator('[data-testid="audit-entry"]')).toContainText('status_changed');
    
    // Verify audit details
    const firstAudit = page.locator('[data-testid="audit-entry"]').first();
    await expect(firstAudit).toContainText('Test User'); // User who made the change
    await expect(firstAudit).toContainText(new Date().toISOString().split('T')[0]); // Today's date
  });

  test('error handling and recovery', async ({ authenticatedPage: page }) => {
    // 1. Test validation errors
    await page.goto('/tasks');
    await page.click('[data-testid="create-task-btn"]');
    
    // Submit empty form to trigger validation
    await page.click('[data-testid="submit-task"]');
    
    // Verify validation errors are shown
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('Title is required');
    
    // 2. Fix validation errors and submit successfully
    await page.fill('[data-testid="task-title"]', 'Error Recovery Test');
    await page.click('[data-testid="submit-task"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // 3. Test network error simulation (if applicable)
    // This would require additional setup for network mocking
    
    // 4. Test concurrent edit handling
    // Open task in two "windows" (simulate multiple users)
    const taskItem = page.locator('[data-testid="task-item"]').filter({ hasText: 'Error Recovery Test' });
    await taskItem.locator('[data-testid="edit-task"]').click();
    
    // Simulate another user editing by making a direct API call
    // This would require additional API testing setup
    
    // For now, just verify optimistic locking messages appear when needed
    await page.fill('[data-testid="task-title"]', 'Modified Title');
    await page.click('[data-testid="save-task"]');
    
    // Should succeed since we're the only editor
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});