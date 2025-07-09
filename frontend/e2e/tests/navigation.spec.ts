import { test, expect } from '../fixtures/auth.fixture';

test.describe('Navigation Testing', () => {
  test('メインナビゲーションが正しく表示される', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Check main navigation elements
    await expect(authenticatedPage.locator('[data-testid="main-navigation"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="nav-dashboard"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="nav-tasks"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="nav-projects"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('ダッシュボードナビゲーションが機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/');
    
    // Click dashboard navigation
    await authenticatedPage.click('[data-testid="nav-dashboard"]');
    
    // Verify navigation to dashboard
    await expect(authenticatedPage).toHaveURL(/\/dashboard/);
    await expect(authenticatedPage.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });

  test('タスクページへのナビゲーションが機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Click tasks navigation
    await authenticatedPage.click('[data-testid="nav-tasks"]');
    
    // Verify navigation to tasks
    await expect(authenticatedPage).toHaveURL(/\/tasks/);
    await expect(authenticatedPage.locator('[data-testid="tasks-content"]')).toBeVisible();
  });

  test('プロジェクトページへのナビゲーションが機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Click projects navigation
    await authenticatedPage.click('[data-testid="nav-projects"]');
    
    // Verify navigation to projects
    await expect(authenticatedPage).toHaveURL(/\/projects/);
    await expect(authenticatedPage.locator('[data-testid="projects-content"]')).toBeVisible();
  });

  test('管理者メニューが管理者にのみ表示される', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');
    
    // Admin should see admin navigation
    await expect(adminPage.locator('[data-testid="nav-admin"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="nav-admin-users"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="nav-admin-organizations"]')).toBeVisible();
  });

  test('一般ユーザーには管理者メニューが表示されない', async ({ userPage }) => {
    await userPage.goto('/dashboard');
    
    // Regular user should NOT see admin navigation
    await expect(userPage.locator('[data-testid="nav-admin"]')).not.toBeVisible();
    await expect(userPage.locator('[data-testid="nav-admin-users"]')).not.toBeVisible();
    await expect(userPage.locator('[data-testid="nav-admin-organizations"]')).not.toBeVisible();
  });

  test('ユーザーメニューが正しく動作する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Click user menu
    await authenticatedPage.click('[data-testid="user-menu"]');
    
    // Check dropdown menu
    await expect(authenticatedPage.locator('[data-testid="user-dropdown"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="profile-link"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="settings-link"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="logout-button"]')).toBeVisible();
  });

  test('プロフィールページへのナビゲーションが機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Open user menu and click profile
    await authenticatedPage.click('[data-testid="user-menu"]');
    await authenticatedPage.click('[data-testid="profile-link"]');
    
    // Verify navigation to profile
    await expect(authenticatedPage).toHaveURL(/\/profile/);
    await expect(authenticatedPage.locator('[data-testid="profile-content"]')).toBeVisible();
  });

  test('設定ページへのナビゲーションが機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Open user menu and click settings
    await authenticatedPage.click('[data-testid="user-menu"]');
    await authenticatedPage.click('[data-testid="settings-link"]');
    
    // Verify navigation to settings
    await expect(authenticatedPage).toHaveURL(/\/settings/);
    await expect(authenticatedPage.locator('[data-testid="settings-content"]')).toBeVisible();
  });

  test('パンくずナビゲーションが表示される', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/tasks');
    
    // Check breadcrumb navigation
    await expect(authenticatedPage.locator('[data-testid="breadcrumb"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="breadcrumb-home"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="breadcrumb-tasks"]')).toBeVisible();
  });

  test('サイドバーの開閉が機能する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Check sidebar is initially visible
    await expect(authenticatedPage.locator('[data-testid="sidebar"]')).toBeVisible();
    
    // Toggle sidebar
    await authenticatedPage.click('[data-testid="sidebar-toggle"]');
    
    // Check sidebar is collapsed
    await expect(authenticatedPage.locator('[data-testid="sidebar"]')).toHaveClass(/collapsed/);
    
    // Toggle again to expand
    await authenticatedPage.click('[data-testid="sidebar-toggle"]');
    
    // Check sidebar is expanded
    await expect(authenticatedPage.locator('[data-testid="sidebar"]')).not.toHaveClass(/collapsed/);
  });

  test('モバイルナビゲーションが機能する', async ({ authenticatedPage }) => {
    // Set mobile viewport
    await authenticatedPage.setViewportSize({ width: 375, height: 667 });
    await authenticatedPage.goto('/dashboard');
    
    // Check mobile menu button
    await expect(authenticatedPage.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    // Open mobile menu
    await authenticatedPage.click('[data-testid="mobile-menu-button"]');
    
    // Check mobile navigation
    await expect(authenticatedPage.locator('[data-testid="mobile-navigation"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="mobile-nav-dashboard"]')).toBeVisible();
  });

  test('検索機能が正しく動作する', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Check global search
    await expect(authenticatedPage.locator('[data-testid="global-search"]')).toBeVisible();
    
    // Perform search
    await authenticatedPage.fill('[data-testid="search-input"]', 'test');
    await authenticatedPage.press('[data-testid="search-input"]', 'Enter');
    
    // Check search results
    await expect(authenticatedPage.locator('[data-testid="search-results"]')).toBeVisible();
  });

  test('ページタイトルが正しく設定される', async ({ authenticatedPage }) => {
    // Test different page titles
    await authenticatedPage.goto('/dashboard');
    await expect(authenticatedPage).toHaveTitle(/ダッシュボード|Dashboard.*ITDO ERP/);
    
    await authenticatedPage.goto('/tasks');
    await expect(authenticatedPage).toHaveTitle(/タスク|Tasks.*ITDO ERP/);
    
    await authenticatedPage.goto('/projects');
    await expect(authenticatedPage).toHaveTitle(/プロジェクト|Projects.*ITDO ERP/);
  });

  test('アクティブなナビゲーション項目がハイライトされる', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/tasks');
    
    // Check that tasks navigation item is active
    await expect(authenticatedPage.locator('[data-testid="nav-tasks"]')).toHaveClass(/active/);
    
    // Check that other items are not active
    await expect(authenticatedPage.locator('[data-testid="nav-dashboard"]')).not.toHaveClass(/active/);
    await expect(authenticatedPage.locator('[data-testid="nav-projects"]')).not.toHaveClass(/active/);
  });

  test('未認証ユーザーはログインページにリダイレクトされる', async ({ page }) => {
    // Try to access protected page without authentication
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('ロールベースでのページアクセス制御が機能する', async ({ userPage }) => {
    // Regular user tries to access admin page
    await userPage.goto('/admin/users');
    
    // Should show access denied or redirect
    const accessDenied = userPage.locator('[data-testid="access-denied"]');
    const loginPage = page => page.url().includes('/login');
    
    // Either show access denied or redirect to login
    const hasAccessDenied = await accessDenied.isVisible();
    const isLoginPage = loginPage(userPage);
    
    expect(hasAccessDenied || isLoginPage).toBeTruthy();
  });
});