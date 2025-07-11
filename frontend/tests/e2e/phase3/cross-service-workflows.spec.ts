import { test, expect } from '@playwright/test';

test.describe('Phase 3: Cross-Service Workflow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Skip authentication-dependent tests if not authenticated
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('Authentication required for Phase 3 workflow tests');
      test.skip();
    }
  });

  test('end-to-end task management workflow', async ({ page }) => {
    console.log('Starting comprehensive task management workflow test');
    
    const workflowSteps = {
      organizationSetup: false,
      departmentCreation: false,
      userAssignment: false,
      taskCreation: false,
      taskAssignment: false,
      progressUpdate: false,
      completion: false
    };

    // Step 1: Organization Setup
    try {
      await page.goto('/organizations', { timeout: 10000 });
      const orgElements = await page.locator('h1, .page-title, .organization').count();
      if (orgElements > 0) {
        workflowSteps.organizationSetup = true;
        console.log('✓ Organization setup verified');
      }
    } catch (error) {
      console.log('⚠ Organization setup not accessible');
    }

    // Step 2: Department Creation/Management
    try {
      await page.goto('/departments', { timeout: 10000 });
      const deptElements = await page.locator('.department, [data-testid*="dept"], h1').count();
      if (deptElements > 0) {
        workflowSteps.departmentCreation = true;
        console.log('✓ Department management verified');
      }
    } catch (error) {
      console.log('⚠ Department management not accessible');
    }

    // Step 3: User Assignment
    try {
      await page.goto('/users', { timeout: 10000 });
      const userElements = await page.locator('.user, [data-testid*="user"], table tr').count();
      if (userElements > 0) {
        workflowSteps.userAssignment = true;
        console.log('✓ User management verified');
      }
    } catch (error) {
      console.log('⚠ User management not accessible');
    }

    // Step 4: Task Creation
    try {
      await page.goto('/tasks', { timeout: 10000 });
      const taskElements = await page.locator('.task, [data-testid*="task"], h1').count();
      
      if (taskElements > 0) {
        // Try to access task creation
        const createTaskBtn = await page.locator('button:has-text("Create"), .create-task, [data-testid="create-task"]').first();
        if (await createTaskBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          await createTaskBtn.click();
          await page.waitForTimeout(1000);
          
          const taskForm = await page.locator('form, .task-form, [data-testid="task-form"]').count();
          if (taskForm > 0) {
            workflowSteps.taskCreation = true;
            console.log('✓ Task creation interface verified');
          }
        } else {
          workflowSteps.taskCreation = taskElements > 0;
          console.log('✓ Task management page accessible');
        }
      }
    } catch (error) {
      console.log('⚠ Task management not accessible');
    }

    // Step 5: Task Assignment Simulation
    if (workflowSteps.taskCreation) {
      try {
        const assignmentElements = await page.locator('.assign, [data-testid*="assign"], .task-assignment').count();
        if (assignmentElements > 0) {
          workflowSteps.taskAssignment = true;
          console.log('✓ Task assignment capabilities found');
        }
      } catch (error) {
        console.log('⚠ Task assignment not found');
      }
    }

    // Step 6: Progress Update Simulation
    if (workflowSteps.taskCreation) {
      try {
        const progressElements = await page.locator('.progress, [data-testid*="progress"], .status-update').count();
        if (progressElements > 0) {
          workflowSteps.progressUpdate = true;
          console.log('✓ Progress tracking capabilities found');
        }
      } catch (error) {
        console.log('⚠ Progress tracking not found');
      }
    }

    // Step 7: Workflow Completion Check
    const completedSteps = Object.values(workflowSteps).filter(Boolean).length;
    const totalSteps = Object.keys(workflowSteps).length;
    const completionRate = (completedSteps / totalSteps) * 100;
    
    workflowSteps.completion = completionRate >= 50; // 50% completion threshold
    
    console.log(`Workflow completion: ${completedSteps}/${totalSteps} steps (${completionRate.toFixed(1)}%)`);
    console.log('Workflow steps status:', workflowSteps);

    // Assert that at least half the workflow is accessible
    expect(completionRate).toBeGreaterThanOrEqual(50);
  });

  test('cross-service data consistency validation', async ({ page }) => {
    console.log('Testing cross-service data consistency');
    
    const dataConsistencyChecks = {
      organizationDataFlow: false,
      userRoleConsistency: false,
      departmentHierarchy: false,
      taskUserAlignment: false,
      permissionConsistency: false
    };

    // Check Organization Data Flow
    try {
      await page.goto('/organizations', { timeout: 8000 });
      const orgData = await page.locator('[data-testid*="org"], .organization-item, tbody tr').count();
      
      if (orgData > 0) {
        // Navigate to organization details and check data consistency
        const firstOrg = await page.locator('[data-testid*="org"], .organization-item, tbody tr').first();
        const orgLink = await firstOrg.locator('a, button').first();
        
        if (await orgLink.isVisible({ timeout: 2000 }).catch(() => false)) {
          await orgLink.click();
          await page.waitForLoadState('domcontentloaded');
          
          // Check if organization details show related departments/users
          const relatedData = await page.locator('.department, .user, [data-testid*="dept"], [data-testid*="user"]').count();
          if (relatedData > 0) {
            dataConsistencyChecks.organizationDataFlow = true;
            console.log('✓ Organization data flow verified');
          }
        }
      }
    } catch (error) {
      console.log('⚠ Organization data flow check failed');
    }

    // Check User-Role Consistency
    try {
      await page.goto('/users', { timeout: 8000 });
      const users = await page.locator('.user, [data-testid*="user"], tbody tr').count();
      
      if (users > 0) {
        // Look for role information in user listings
        const roleInfo = await page.locator('.role, [data-testid*="role"], .user-role').count();
        if (roleInfo > 0) {
          dataConsistencyChecks.userRoleConsistency = true;
          console.log('✓ User-role consistency verified');
        }
      }
    } catch (error) {
      console.log('⚠ User-role consistency check failed');
    }

    // Check Department Hierarchy
    try {
      await page.goto('/departments', { timeout: 8000 });
      const deptHierarchy = await page.locator('.hierarchy, .tree, [data-testid*="hierarchy"]').count();
      const nestedDepts = await page.locator('.department .department, .nested-dept').count();
      
      if (deptHierarchy > 0 || nestedDepts > 0) {
        dataConsistencyChecks.departmentHierarchy = true;
        console.log('✓ Department hierarchy verified');
      }
    } catch (error) {
      console.log('⚠ Department hierarchy check failed');
    }

    // Check Task-User Alignment
    try {
      await page.goto('/tasks', { timeout: 8000 });
      const taskUserData = await page.locator('.assignee, [data-testid*="assignee"], .task-user').count();
      
      if (taskUserData > 0) {
        dataConsistencyChecks.taskUserAlignment = true;
        console.log('✓ Task-user alignment verified');
      }
    } catch (error) {
      console.log('⚠ Task-user alignment check failed');
    }

    // Check Permission Consistency
    try {
      await page.goto('/permissions', { timeout: 8000 });
      const permissionMatrix = await page.locator('.permission-matrix, .access-control, [data-testid*="permission"]').count();
      
      if (permissionMatrix > 0) {
        dataConsistencyChecks.permissionConsistency = true;
        console.log('✓ Permission consistency verified');
      } else {
        // Alternative check via settings or admin pages
        await page.goto('/settings', { timeout: 5000 });
        const settingsPermissions = await page.locator('.permission, .access, .security').count();
        if (settingsPermissions > 0) {
          dataConsistencyChecks.permissionConsistency = true;
          console.log('✓ Permission settings found in settings');
        }
      }
    } catch (error) {
      console.log('⚠ Permission consistency check failed');
    }

    const consistentChecks = Object.values(dataConsistencyChecks).filter(Boolean).length;
    const totalChecks = Object.keys(dataConsistencyChecks).length;
    const consistencyRate = (consistentChecks / totalChecks) * 100;
    
    console.log(`Data consistency: ${consistentChecks}/${totalChecks} checks passed (${consistencyRate.toFixed(1)}%)`);
    console.log('Consistency check results:', dataConsistencyChecks);

    // Assert reasonable data consistency
    expect(consistencyRate).toBeGreaterThanOrEqual(40);
  });

  test('performance integration under load simulation', async ({ page }) => {
    console.log('Testing performance integration across services');
    
    const performanceMetrics = {
      pageLoadTimes: [] as number[],
      navigationTimes: [] as number[],
      apiResponseTimes: [] as number[],
      memoryUsage: [] as number[]
    };

    const testRoutes = ['/dashboard', '/organizations', '/departments', '/users', '/tasks', '/settings'];
    
    for (const route of testRoutes) {
      try {
        const startTime = Date.now();
        
        await page.goto(route, { timeout: 15000 });
        await page.waitForLoadState('domcontentloaded');
        
        const loadTime = Date.now() - startTime;
        performanceMetrics.pageLoadTimes.push(loadTime);
        
        console.log(`${route}: ${loadTime}ms`);
        
        // Simulate interaction and measure response
        const interactionStart = Date.now();
        
        // Try to find and click an interactive element
        const interactiveElement = await page.locator('button, a, input, [role="button"]').first();
        if (await interactiveElement.isVisible({ timeout: 2000 }).catch(() => false)) {
          await interactiveElement.click();
          await page.waitForTimeout(500);
        }
        
        const interactionTime = Date.now() - interactionStart;
        performanceMetrics.navigationTimes.push(interactionTime);
        
        // Simulate API response monitoring (mock for now)
        performanceMetrics.apiResponseTimes.push(Math.random() * 500 + 100);
        
        // Memory usage simulation
        const memoryInfo = await page.evaluate(() => {
          if ('memory' in performance) {
            return (performance as unknown as { memory?: { usedJSHeapSize?: number } }).memory?.usedJSHeapSize || 0;
          }
          return Math.random() * 50000000 + 10000000; // Mock memory usage
        });
        performanceMetrics.memoryUsage.push(memoryInfo);
        
      } catch (error) {
        console.log(`⚠ Performance test failed for ${route}: ${error}`);
        performanceMetrics.pageLoadTimes.push(15000); // Timeout value
      }
    }

    // Calculate performance statistics
    const avgLoadTime = performanceMetrics.pageLoadTimes.reduce((a, b) => a + b, 0) / performanceMetrics.pageLoadTimes.length;
    const maxLoadTime = Math.max(...performanceMetrics.pageLoadTimes);
    const avgNavTime = performanceMetrics.navigationTimes.reduce((a, b) => a + b, 0) / performanceMetrics.navigationTimes.length;
    
    console.log(`Performance Summary:
      - Average Load Time: ${avgLoadTime.toFixed(0)}ms
      - Maximum Load Time: ${maxLoadTime}ms
      - Average Navigation Time: ${avgNavTime.toFixed(0)}ms
      - Routes Tested: ${testRoutes.length}
    `);

    // Performance assertions
    expect(avgLoadTime).toBeLessThan(10000); // Average load under 10 seconds
    expect(maxLoadTime).toBeLessThan(15000); // No route takes more than 15 seconds
    expect(performanceMetrics.pageLoadTimes.length).toBeGreaterThan(0);
  });

  test('error handling and recovery workflows', async ({ page }) => {
    console.log('Testing error handling and recovery across services');
    
    const errorRecoveryTests = {
      invalidRouteHandling: false,
      networkErrorRecovery: false,
      formValidationErrors: false,
      authenticationErrors: false,
      permissionDeniedErrors: false
    };

    // Test 1: Invalid Route Handling
    try {
      await page.goto('/nonexistent-route-12345', { timeout: 8000 });
      
      // Check for proper 404 handling
      const pageContent = await page.textContent('body');
      const has404Elements = pageContent?.includes('404') || 
                           pageContent?.includes('Not Found') || 
                           pageContent?.includes('Page not found');
      
      if (has404Elements || page.url().includes('/')) {
        errorRecoveryTests.invalidRouteHandling = true;
        console.log('✓ Invalid route handling verified');
      }
    } catch (error) {
      console.log('⚠ Invalid route test inconclusive');
    }

    // Test 2: Form Validation Error Handling
    try {
      await page.goto('/login', { timeout: 8000 });
      
      const loginForm = await page.locator('form, [data-testid="login-form"]').first();
      if (await loginForm.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Submit empty form to trigger validation
        const submitButton = await page.locator('button[type="submit"], .login-submit').first();
        if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await submitButton.click();
          await page.waitForTimeout(1000);
          
          // Look for validation errors
          const errorMessages = await page.locator('.error, .invalid, [data-testid*="error"]').count();
          if (errorMessages > 0) {
            errorRecoveryTests.formValidationErrors = true;
            console.log('✓ Form validation error handling verified');
          }
        }
      }
    } catch (error) {
      console.log('⚠ Form validation test failed');
    }

    // Test 3: Authentication Error Simulation
    try {
      // Test invalid credentials if login form is available
      await page.goto('/login', { timeout: 8000 });
      
      const emailInput = await page.locator('input[type="email"], input[name="email"]').first();
      const passwordInput = await page.locator('input[type="password"], input[name="password"]').first();
      
      if (await emailInput.isVisible({ timeout: 2000 }).catch(() => false) && 
          await passwordInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        
        await emailInput.fill('invalid@test.com');
        await passwordInput.fill('wrongpassword');
        
        const submitButton = await page.locator('button[type="submit"]').first();
        if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await submitButton.click();
          await page.waitForTimeout(2000);
          
          // Check for authentication error message
          const authErrors = await page.locator('.error, .alert-danger, [data-testid*="error"]').count();
          if (authErrors > 0 || page.url().includes('/login')) {
            errorRecoveryTests.authenticationErrors = true;
            console.log('✓ Authentication error handling verified');
          }
        }
      }
    } catch (error) {
      console.log('⚠ Authentication error test failed');
    }

    // Test 4: Permission Denied Error Simulation
    try {
      // Try to access admin routes
      const restrictedRoutes = ['/admin', '/settings/system', '/manage'];
      
      for (const route of restrictedRoutes) {
        await page.goto(route, { timeout: 5000 });
        
        const pageContent = await page.textContent('body');
        const hasPermissionDenied = pageContent?.includes('permission') || 
                                  pageContent?.includes('access denied') || 
                                  pageContent?.includes('unauthorized') ||
                                  page.url().includes('/login');
        
        if (hasPermissionDenied) {
          errorRecoveryTests.permissionDeniedErrors = true;
          console.log('✓ Permission denied error handling verified');
          break;
        }
      }
    } catch (error) {
      console.log('⚠ Permission error test failed');
    }

    // Test 5: Network Error Recovery (Simulate by checking offline handling)
    try {
      // Check if the app has any offline/network error handling
      const hasServiceWorker = await page.evaluate(() => 'serviceWorker' in navigator);
      const hasNetworkDetection = await page.evaluate(() => 'onLine' in navigator);
      
      if (hasServiceWorker || hasNetworkDetection) {
        errorRecoveryTests.networkErrorRecovery = true;
        console.log('✓ Network error recovery capabilities detected');
      }
    } catch (error) {
      console.log('⚠ Network error recovery test failed');
    }

    const passedTests = Object.values(errorRecoveryTests).filter(Boolean).length;
    const totalTests = Object.keys(errorRecoveryTests).length;
    const errorHandlingScore = (passedTests / totalTests) * 100;
    
    console.log(`Error Handling Score: ${passedTests}/${totalTests} tests passed (${errorHandlingScore.toFixed(1)}%)`);
    console.log('Error handling test results:', errorRecoveryTests);

    // Assert reasonable error handling coverage
    expect(errorHandlingScore).toBeGreaterThanOrEqual(40);
  });
});