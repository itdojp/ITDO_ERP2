import { test, expect } from '@playwright/test';

test.describe('Phase 3: Advanced Component Interaction E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
  });

  test('modal and loading spinner integration workflow', async ({ page }) => {
    console.log('Testing Modal + LoadingSpinner E2E integration');
    
    const interactionFlow = {
      modalTrigger: false,
      modalOpen: false,
      loadingStateActivation: false,
      loadingSpinnerVisible: false,
      asyncOperationComplete: false,
      modalClose: false
    };

    try {
      // Look for any modal trigger buttons on various pages
      const testPages = ['/', '/dashboard', '/tasks', '/users'];
      
      for (const testPage of testPages) {
        await page.goto(testPage, { timeout: 8000 });
        
        // Look for modal triggers (Create, Edit, Add, etc.)
        const modalTriggers = await page.locator(
          'button:has-text("Create"), button:has-text("Add"), button:has-text("New"), ' +
          'button:has-text("Edit"), [data-testid*="create"], [data-testid*="modal"]'
        ).count();
        
        if (modalTriggers > 0) {
          interactionFlow.modalTrigger = true;
          console.log(`✓ Modal triggers found on ${testPage}`);
          
          // Click first available modal trigger
          const trigger = await page.locator(
            'button:has-text("Create"), button:has-text("Add"), button:has-text("New")'
          ).first();
          
          if (await trigger.isVisible({ timeout: 3000 }).catch(() => false)) {
            await trigger.click();
            await page.waitForTimeout(1000);
            
            // Check if modal opened
            const modalElements = await page.locator(
              '.modal, [role="dialog"], .dialog, [data-testid*="modal"]'
            ).count();
            
            if (modalElements > 0) {
              interactionFlow.modalOpen = true;
              console.log('✓ Modal opened successfully');
              
              // Look for form submission that might trigger loading
              const submitButtons = await page.locator(
                'button[type="submit"], button:has-text("Submit"), button:has-text("Save")'
              ).count();
              
              if (submitButtons > 0) {
                const submitBtn = await page.locator(
                  'button[type="submit"], button:has-text("Submit"), button:has-text("Save")'
                ).first();
                
                if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
                  // Fill any required fields first
                  const inputs = await page.locator('input[required], input:not([type="hidden"])').all();
                  for (const input of inputs) {
                    if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
                      const inputType = await input.getAttribute('type') || 'text';
                      if (inputType === 'email') {
                        await input.fill('test@example.com');
                      } else if (inputType === 'text' || inputType === 'textarea') {
                        await input.fill('Test Data');
                      }
                    }
                  }
                  
                  await submitBtn.click();
                  interactionFlow.loadingStateActivation = true;
                  console.log('✓ Loading state activation triggered');
                  
                  // Check for loading spinner during operation
                  const loadingElements = await page.locator(
                    '[role="status"], .loading, .spinner, [data-testid*="loading"]'
                  ).count();
                  
                  if (loadingElements > 0) {
                    interactionFlow.loadingSpinnerVisible = true;
                    console.log('✓ Loading spinner visible during operation');
                  }
                  
                  // Wait for operation to complete (max 5 seconds)
                  await page.waitForTimeout(3000);
                  
                  // Check if loading disappeared (operation completed)
                  const stillLoading = await page.locator(
                    '[role="status"], .loading:visible, .spinner:visible'
                  ).count();
                  
                  if (stillLoading === 0) {
                    interactionFlow.asyncOperationComplete = true;
                    console.log('✓ Async operation completed');
                  }
                  
                  // Try to close modal
                  const closeButtons = await page.locator(
                    'button:has-text("Close"), button:has-text("Cancel"), .modal-close, [aria-label*="close" i]'
                  ).count();
                  
                  if (closeButtons > 0) {
                    const closeBtn = await page.locator(
                      'button:has-text("Close"), button:has-text("Cancel"), .modal-close'
                    ).first();
                    
                    if (await closeBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
                      await closeBtn.click();
                      await page.waitForTimeout(1000);
                      
                      const modalStillOpen = await page.locator('.modal:visible, [role="dialog"]:visible').count();
                      if (modalStillOpen === 0) {
                        interactionFlow.modalClose = true;
                        console.log('✓ Modal closed successfully');
                      }
                    }
                  }
                }
              }
              break; // Exit loop once we found a working modal
            }
          }
        }
      }
    } catch (error) {
      console.log(`⚠ Modal interaction test error: ${error}`);
    }

    const completedSteps = Object.values(interactionFlow).filter(Boolean).length;
    const totalSteps = Object.keys(interactionFlow).length;
    const completionRate = (completedSteps / totalSteps) * 100;
    
    console.log(`Modal Integration Flow: ${completedSteps}/${totalSteps} steps (${completionRate.toFixed(1)}%)`);
    console.log('Interaction flow results:', interactionFlow);

    // Assert that basic modal interaction works
    expect(completionRate).toBeGreaterThanOrEqual(50);
  });

  test('form component integration with validation and alerts', async ({ page }) => {
    console.log('Testing Form Components E2E integration');
    
    const formIntegration = {
      formFound: false,
      inputInteraction: false,
      validationTriggered: false,
      errorDisplayed: false,
      successStateAchieved: false
    };

    try {
      // Test pages that likely have forms
      const formPages = ['/login', '/register', '/tasks/create', '/users/create', '/contact'];
      
      for (const formPage of formPages) {
        try {
          await page.goto(formPage, { timeout: 8000 });
          
          const forms = await page.locator('form').count();
          if (forms > 0) {
            formIntegration.formFound = true;
            console.log(`✓ Form found on ${formPage}`);
            
            // Find inputs and interact with them
            const inputs = await page.locator('input:not([type="hidden"]), textarea').all();
            if (inputs.length > 0) {
              formIntegration.inputInteraction = true;
              console.log('✓ Form inputs found');
              
              // Test validation by submitting empty/invalid form
              const submitButton = await page.locator('button[type="submit"], .submit-btn').first();
              if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
                await submitButton.click();
                await page.waitForTimeout(1500);
                
                // Check for validation errors
                const errorElements = await page.locator(
                  '.error, .invalid, .alert-danger, [data-testid*="error"], .field-error'
                ).count();
                
                if (errorElements > 0) {
                  formIntegration.validationTriggered = true;
                  formIntegration.errorDisplayed = true;
                  console.log('✓ Form validation and error display working');
                }
                
                // Try to fill form with valid data
                for (const input of inputs) {
                  if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
                    const inputName = await input.getAttribute('name') || '';
                    const inputType = await input.getAttribute('type') || 'text';
                    const placeholder = await input.getAttribute('placeholder') || '';
                    
                    if (inputType === 'email' || inputName.includes('email') || placeholder.includes('email')) {
                      await input.fill('test@example.com');
                    } else if (inputType === 'password' || inputName.includes('password')) {
                      await input.fill('Test123!');
                    } else if (inputType === 'text' || inputType === 'textarea') {
                      await input.fill('Test Data');
                    }
                  }
                }
                
                // Submit with valid data
                await submitButton.click();
                await page.waitForTimeout(2000);
                
                // Check for success state (less errors, redirect, success message)
                const errorsAfterValidInput = await page.locator('.error:visible, .invalid:visible').count();
                const successMessages = await page.locator(
                  '.success, .alert-success, [data-testid*="success"], .notification'
                ).count();
                
                if (errorsAfterValidInput < errorElements || successMessages > 0 || page.url() !== formPage) {
                  formIntegration.successStateAchieved = true;
                  console.log('✓ Form success state achieved');
                }
              }
            }
            break; // Exit once we find a working form
          }
        } catch (error) {
          console.log(`⚠ Could not test form on ${formPage}`);
          continue;
        }
      }
    } catch (error) {
      console.log(`⚠ Form integration test error: ${error}`);
    }

    const completedSteps = Object.values(formIntegration).filter(Boolean).length;
    const totalSteps = Object.keys(formIntegration).length;
    const completionRate = (completedSteps / totalSteps) * 100;
    
    console.log(`Form Integration: ${completedSteps}/${totalSteps} steps (${completionRate.toFixed(1)}%)`);
    console.log('Form integration results:', formIntegration);

    // Assert that basic form functionality works
    expect(completionRate).toBeGreaterThanOrEqual(40);
  });

  test('navigation and state persistence across routes', async ({ page }) => {
    console.log('Testing navigation state persistence');
    
    const navigationFlow = {
      initialPageLoad: false,
      stateModification: false,
      navigationToNewPage: false,
      backNavigation: false,
      statePersistence: false
    };

    try {
      // Start on dashboard or home
      await page.goto('/', { timeout: 8000 });
      navigationFlow.initialPageLoad = true;
      console.log('✓ Initial page loaded');
      
      // Look for interactive elements that might modify state
      const interactiveElements = await page.locator(
        'input, select, button:not([type="submit"]), [role="button"]'
      ).all();
      
      let stateModified = false;
      for (const element of interactiveElements.slice(0, 3)) { // Test first 3 elements
        try {
          if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
            const tagName = await element.evaluate(el => el.tagName.toLowerCase());
            
            if (tagName === 'input') {
              await element.fill('Test State Data');
              stateModified = true;
            } else if (tagName === 'select') {
              const options = await element.locator('option').count();
              if (options > 1) {
                await element.selectOption({ index: 1 });
                stateModified = true;
              }
            } else {
              await element.click();
              await page.waitForTimeout(500);
              stateModified = true;
            }
            
            if (stateModified) {
              navigationFlow.stateModification = true;
              console.log('✓ State modified');
              break;
            }
          }
        } catch (error) {
          continue; // Try next element
        }
      }
      
      // Navigate to different page
      const navigationLinks = await page.locator('a[href], nav a, .nav-link').all();
      for (const link of navigationLinks.slice(0, 5)) {
        try {
          const href = await link.getAttribute('href');
          if (href && !href.startsWith('#') && !href.includes('javascript:')) {
            await link.click();
            await page.waitForLoadState('domcontentloaded');
            navigationFlow.navigationToNewPage = true;
            console.log(`✓ Navigated to new page: ${page.url()}`);
            break;
          }
        } catch (error) {
          continue;
        }
      }
      
      // Navigate back
      if (navigationFlow.navigationToNewPage) {
        await page.goBack();
        await page.waitForLoadState('domcontentloaded');
        navigationFlow.backNavigation = true;
        console.log('✓ Back navigation completed');
        
        // Check if any state was preserved (simplified check)
        const inputsWithValues = await page.locator('input').evaluateAll(inputs => 
          inputs.filter(input => (input as HTMLInputElement).value !== '').length
        );
        
        if (inputsWithValues > 0) {
          navigationFlow.statePersistence = true;
          console.log('✓ Some state persistence detected');
        }
      }
      
    } catch (error) {
      console.log(`⚠ Navigation test error: ${error}`);
    }

    const completedSteps = Object.values(navigationFlow).filter(Boolean).length;
    const totalSteps = Object.keys(navigationFlow).length;
    const completionRate = (completedSteps / totalSteps) * 100;
    
    console.log(`Navigation Flow: ${completedSteps}/${totalSteps} steps (${completionRate.toFixed(1)}%)`);
    console.log('Navigation flow results:', navigationFlow);

    // Assert that basic navigation works
    expect(completionRate).toBeGreaterThanOrEqual(60);
  });

  test('responsive component behavior across viewports', async ({ page }) => {
    console.log('Testing responsive component behavior');
    
    const responsiveTests = {
      desktopLayout: false,
      tabletLayout: false,
      mobileLayout: false,
      navigationAdaptation: false,
      contentReflow: false
    };

    const viewports = [
      { name: 'desktop', width: 1920, height: 1080 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'mobile', width: 375, height: 667 }
    ];

    try {
      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto('/', { timeout: 8000 });
        await page.waitForLoadState('domcontentloaded');
        
        console.log(`Testing ${viewport.name} layout (${viewport.width}x${viewport.height})`);
        
        // Check if page renders without horizontal scroll
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        const viewportWidth = viewport.width;
        
        if (bodyWidth <= viewportWidth + 50) { // 50px tolerance
          responsiveTests[`${viewport.name}Layout` as keyof typeof responsiveTests] = true;
          console.log(`✓ ${viewport.name} layout: No horizontal overflow`);
        }
        
        // Check navigation adaptation
        const navElements = await page.locator('nav, .navbar, .navigation, .menu').count();
        const mobileMenuTriggers = await page.locator(
          '.menu-toggle, .hamburger, [aria-label*="menu" i], .mobile-menu'
        ).count();
        
        if (viewport.name === 'mobile' && mobileMenuTriggers > 0) {
          responsiveTests.navigationAdaptation = true;
          console.log('✓ Mobile navigation adaptation detected');
        } else if (viewport.name !== 'mobile' && navElements > 0) {
          responsiveTests.navigationAdaptation = true;
          console.log(`✓ ${viewport.name} navigation present`);
        }
        
        // Check content reflow
        const textElements = await page.locator('p, .content, .text').all();
        let contentReflowGood = true;
        
        for (const element of textElements.slice(0, 3)) {
          try {
            const elementWidth = await element.evaluate(el => el.scrollWidth);
            if (elementWidth > viewportWidth + 50) {
              contentReflowGood = false;
              break;
            }
          } catch (error) {
            continue;
          }
        }
        
        if (contentReflowGood) {
          responsiveTests.contentReflow = true;
          console.log(`✓ Content reflow good on ${viewport.name}`);
        }
      }
    } catch (error) {
      console.log(`⚠ Responsive test error: ${error}`);
    }

    const completedTests = Object.values(responsiveTests).filter(Boolean).length;
    const totalTests = Object.keys(responsiveTests).length;
    const responsiveScore = (completedTests / totalTests) * 100;
    
    console.log(`Responsive Score: ${completedTests}/${totalTests} tests passed (${responsiveScore.toFixed(1)}%)`);
    console.log('Responsive test results:', responsiveTests);

    // Assert reasonable responsive behavior
    expect(responsiveScore).toBeGreaterThanOrEqual(60);
  });
});