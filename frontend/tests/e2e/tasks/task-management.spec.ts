import { test, expect } from '../fixtures/auth.fixture';

test.describe('Task Management', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    // Navigate to tasks page
    await page.goto('/tasks');
    await expect(page.locator('h1')).toContainText('Tasks');
  });

  test('should display task list', async ({ authenticatedPage: page }) => {
    // Verify task list is visible
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
    
    // Verify task items are present
    const taskItems = page.locator('[data-testid="task-item"]');
    await expect(taskItems).toHaveCount(3); // Based on test data
    
    // Verify task information is displayed
    await expect(taskItems.first()).toContainText('Test Task 1');
    await expect(taskItems.first()).toContainText('TODO');
  });

  test('should filter tasks by status', async ({ authenticatedPage: page }) => {
    // Click on IN_PROGRESS filter
    await page.click('[data-testid="filter-in-progress"]');
    
    // Wait for filtering
    await page.waitForTimeout(500);
    
    // Verify only in-progress tasks are shown
    const taskItems = page.locator('[data-testid="task-item"]');
    await expect(taskItems).toHaveCount(1);
    await expect(taskItems.first()).toContainText('Test Task 2');
    await expect(taskItems.first()).toContainText('IN_PROGRESS');
  });

  test('should filter tasks by priority', async ({ authenticatedPage: page }) => {
    // Click on HIGH priority filter
    await page.click('[data-testid="filter-high-priority"]');
    
    // Wait for filtering
    await page.waitForTimeout(500);
    
    // Verify only high priority tasks are shown
    const taskItems = page.locator('[data-testid="task-item"]');
    await expect(taskItems).toHaveCount(1);
    await expect(taskItems.first()).toContainText('Test Task 2');
    await expect(taskItems.first()).toContainText('HIGH');
  });

  test('should create new task', async ({ authenticatedPage: page }) => {
    // Click create task button
    await page.click('[data-testid="create-task-btn"]');
    
    // Fill task form
    await page.fill('[data-testid="task-title"]', 'New E2E Test Task');
    await page.fill('[data-testid="task-description"]', 'Created during E2E testing');
    await page.selectOption('[data-testid="task-priority"]', 'HIGH');
    await page.selectOption('[data-testid="task-status"]', 'TODO');
    
    // Submit form
    await page.click('[data-testid="submit-task"]');
    
    // Verify task was created
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="task-list"]')).toContainText('New E2E Test Task');
  });

  test('should edit existing task', async ({ authenticatedPage: page }) => {
    // Click edit button for first task
    await page.click('[data-testid="task-item"]:first-child [data-testid="edit-task"]');
    
    // Modify task details
    await page.fill('[data-testid="task-title"]', 'Updated Task Title');
    await page.selectOption('[data-testid="task-status"]', 'IN_PROGRESS');
    
    // Save changes
    await page.click('[data-testid="save-task"]');
    
    // Verify changes were saved
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="task-list"]')).toContainText('Updated Task Title');
  });

  test('should delete task', async ({ authenticatedPage: page }) => {
    // Get initial task count
    const initialCount = await page.locator('[data-testid="task-item"]').count();
    
    // Click delete button for last task
    await page.click('[data-testid="task-item"]:last-child [data-testid="delete-task"]');
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete"]');
    
    // Verify task was deleted
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    const newCount = await page.locator('[data-testid="task-item"]').count();
    expect(newCount).toBe(initialCount - 1);
  });

  test('should search tasks', async ({ authenticatedPage: page }) => {
    // Enter search query
    await page.fill('[data-testid="task-search"]', 'Test Task 1');
    
    // Wait for search results
    await page.waitForTimeout(500);
    
    // Verify filtered results
    const taskItems = page.locator('[data-testid="task-item"]');
    await expect(taskItems).toHaveCount(1);
    await expect(taskItems.first()).toContainText('Test Task 1');
  });

  test('should change task status via drag and drop', async ({ authenticatedPage: page }) => {
    // Find a TODO task
    const todoTask = page.locator('[data-testid="task-item"]').filter({ hasText: 'TODO' }).first();
    
    // Drag to IN_PROGRESS column
    const inProgressColumn = page.locator('[data-testid="status-column-in-progress"]');
    await todoTask.dragTo(inProgressColumn);
    
    // Verify status change
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(todoTask).toContainText('IN_PROGRESS');
  });

  test('should update task progress', async ({ authenticatedPage: page }) => {
    // Click on first task to open details
    await page.click('[data-testid="task-item"]:first-child');
    
    // Update progress slider
    await page.locator('[data-testid="progress-slider"]').fill('75');
    
    // Save progress
    await page.click('[data-testid="save-progress"]');
    
    // Verify progress was updated
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-display"]')).toContainText('75%');
  });
});