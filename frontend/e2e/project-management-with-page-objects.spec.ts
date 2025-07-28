/**
 * Page Objectパターンを使用したプロジェクト管理システムE2Eテスト
 */

import { test, expect } from '@playwright/test';
import {
  ProjectListPage,
  ProjectFormPage,
  ProjectDetailPage,
  TaskPage,
  TaskFormPage,
  MemberPage,
  BudgetPage,
} from './pages/ProjectManagementPage';
import {
  testProjects,
  testTasks,
  testMembers,
  testBudget,
  generateProjectCode,
  cleanupTestProjects,
} from './utils/project-test-data';

test.describe('プロジェクト管理システム - Page Object使用', () => {
  let projectListPage: ProjectListPage;
  let projectFormPage: ProjectFormPage;
  let projectDetailPage: ProjectDetailPage;
  let taskPage: TaskPage;
  let taskFormPage: TaskFormPage;
  let memberPage: MemberPage;
  let budgetPage: BudgetPage;

  test.beforeEach(async ({ page }) => {
    // Page Objectの初期化
    projectListPage = new ProjectListPage(page);
    projectFormPage = new ProjectFormPage(page);
    projectDetailPage = new ProjectDetailPage(page);
    taskPage = new TaskPage(page);
    taskFormPage = new TaskFormPage(page);
    memberPage = new MemberPage(page);
    budgetPage = new BudgetPage(page);

    // ベースURLの設定
    await page.goto('http://localhost:3000');
  });

  test.afterEach(async ({ page }) => {
    // テストデータのクリーンアップ
    await cleanupTestProjects(page, 'E2E');
  });

  test('完全なプロジェクトワークフロー', async ({ page }) => {
    // 1. プロジェクト一覧ページへ移動
    await projectListPage.goto();
    
    // 2. 新規プロジェクト作成
    await projectListPage.clickNewProject();
    
    const projectData = {
      ...testProjects.parent,
      code: generateProjectCode(),
    };
    
    await projectFormPage.fillForm(projectData);
    await projectFormPage.submit();
    
    // プロジェクト詳細ページへの遷移を確認
    await expect(page).toHaveURL(/\/projects\/\d+/);
    
    // 3. タスクの追加
    await projectDetailPage.switchTab('tasks');
    await taskPage.addTask();
    
    await taskFormPage.fillForm(testTasks.design);
    await taskFormPage.submit();
    
    // タスクが追加されたことを確認
    await expect(page.locator(`text="${testTasks.design.name}"`)).toBeVisible();
    
    // 4. サブタスクの追加
    await taskPage.addSubTask(testTasks.design.name);
    await taskFormPage.fillForm(testTasks.subtask);
    await taskFormPage.submit();
    
    // 5. メンバーの追加
    await projectDetailPage.switchTab('members');
    await memberPage.addMember(
      testMembers.manager.userId,
      testMembers.manager.role,
      testMembers.manager.allocationPercentage
    );
    
    // 6. 予算の設定
    await projectDetailPage.switchTab('budget');
    await budgetPage.editBudget();
    await budgetPage.updateCost('labor', 'planned', testBudget.labor.planned);
    await budgetPage.updateCost('labor', 'actual', testBudget.labor.actual);
    await budgetPage.updateRevenue(testBudget.revenue);
    await budgetPage.save();
    
    // 7. ガントチャートの確認
    await projectDetailPage.switchTab('gantt');
    await expect(page.locator('h3:has-text("ガントチャート")')).toBeVisible();
    
    // 8. ダッシュボードで全体を確認
    await projectDetailPage.switchTab('dashboard');
    await expect(page.locator('h2:has-text("プロジェクト概要")')).toBeVisible();
    await expect(page.locator('h2:has-text("進捗状況")')).toBeVisible();
  });

  test('プロジェクト検索とフィルタリング', async ({ page }) => {
    // テストプロジェクトを作成
    await projectListPage.goto();
    
    // 複数のプロジェクトを作成
    for (let i = 0; i < 3; i++) {
      await projectListPage.clickNewProject();
      await projectFormPage.fillForm({
        code: `E2E-SEARCH-${i}`,
        name: `検索テストプロジェクト${i}`,
        startDate: '2024-01-01',
        endDate: '2024-12-31',
        budget: '1000000',
        status: i === 0 ? 'active' : 'planning',
      });
      await projectFormPage.submit();
      await projectListPage.goto();
    }
    
    // 検索テスト
    await projectListPage.searchProjects('検索テスト');
    await page.waitForTimeout(500);
    
    // 検索結果の確認
    const searchResults = page.locator('text="検索テストプロジェクト"');
    await expect(searchResults).toHaveCount(3);
    
    // ステータスフィルタリング
    await projectListPage.filterByStatus('active');
    await page.waitForTimeout(500);
    
    // フィルタ結果の確認
    await expect(page.locator('text="検索テストプロジェクト0"')).toBeVisible();
    await expect(page.locator('text="検索テストプロジェクト1"')).not.toBeVisible();
  });

  test('タスクの進捗管理', async ({ page }) => {
    // プロジェクトとタスクを作成
    await projectListPage.goto();
    await projectListPage.clickNewProject();
    
    await projectFormPage.fillForm({
      ...testProjects.parent,
      code: generateProjectCode('PROGRESS'),
    });
    await projectFormPage.submit();
    
    // タスクを追加
    await projectDetailPage.switchTab('tasks');
    await taskPage.addTask();
    await taskFormPage.fillForm(testTasks.development);
    await taskFormPage.submit();
    
    // タスクの進捗を更新
    await taskPage.editTask(testTasks.development.name);
    await taskFormPage.fillForm({
      progressPercentage: '50',
      actualHours: '160',
    });
    await taskFormPage.submit();
    
    // 進捗が更新されたことを確認
    await expect(page.locator('text="50%完了"')).toBeVisible();
    
    // 進捗を100%に更新
    await taskPage.editTask(testTasks.development.name);
    await taskFormPage.fillForm({
      progressPercentage: '100',
    });
    
    // ステータスが自動的に完了になることを確認
    const statusSelect = page.locator('select[id="status"]');
    await expect(statusSelect).toHaveValue('completed');
    
    await taskFormPage.submit();
  });

  test('プロジェクト階層の管理', async ({ page }) => {
    // 親プロジェクトを作成
    await projectListPage.goto();
    await projectListPage.clickNewProject();
    
    const parentProject = {
      ...testProjects.parent,
      code: generateProjectCode('PARENT'),
    };
    
    await projectFormPage.fillForm(parentProject);
    await projectFormPage.submit();
    
    // 子プロジェクトを作成
    await projectListPage.goto();
    await projectListPage.clickNewProject();
    
    // 親プロジェクトを選択
    const parentOption = `${parentProject.code} - ${parentProject.name}`;
    await projectFormPage.parentSelect.selectOption({ label: parentOption });
    
    await projectFormPage.fillForm({
      ...testProjects.child,
      code: generateProjectCode('CHILD'),
    });
    await projectFormPage.submit();
    
    // 子プロジェクトが作成されたことを確認
    await expect(page).toHaveURL(/\/projects\/\d+/);
    
    // ダッシュボードで親プロジェクトの表示を確認
    await expect(page.locator(`text="${parentProject.name}"`)).toBeVisible();
  });

  test('予算管理と収益性分析', async ({ page }) => {
    // プロジェクトを作成
    await projectListPage.goto();
    await projectListPage.clickNewProject();
    
    await projectFormPage.fillForm({
      ...testProjects.parent,
      code: generateProjectCode('BUDGET'),
    });
    await projectFormPage.submit();
    
    // 予算管理タブへ
    await projectDetailPage.switchTab('budget');
    
    // 予算がない場合の表示を確認
    await expect(page.locator('text="予算情報がありません"')).toBeVisible();
    
    // 予算を設定
    await page.click('button:has-text("予算を設定")');
    await budgetPage.updateCost('labor', 'planned', testBudget.labor.planned);
    await budgetPage.updateCost('labor', 'actual', testBudget.labor.actual);
    await budgetPage.updateCost('outsourcing', 'planned', testBudget.outsourcing.planned);
    await budgetPage.updateCost('outsourcing', 'actual', testBudget.outsourcing.actual);
    await budgetPage.updateCost('expense', 'planned', testBudget.expense.planned);
    await budgetPage.updateCost('expense', 'actual', testBudget.expense.actual);
    await budgetPage.updateRevenue(testBudget.revenue);
    await budgetPage.save();
    
    // 収益性分析が表示されることを確認
    await expect(page.locator('h3:has-text("収益性分析")')).toBeVisible();
    await expect(page.locator('text="利益"')).toBeVisible();
    await expect(page.locator('text="利益率"')).toBeVisible();
  });

  test('エラーハンドリング', async ({ page }) => {
    // プロジェクト作成画面へ
    await projectListPage.goto();
    await projectListPage.clickNewProject();
    
    // 無効な日付範囲でプロジェクトを作成
    await projectFormPage.fillForm({
      code: 'ERROR-TEST',
      name: 'エラーテスト',
      startDate: '2024-12-31',
      endDate: '2024-01-01', // 開始日より前
      budget: '1000000',
    });
    await projectFormPage.submit();
    
    // エラーメッセージの確認
    await expect(page.locator('text="終了日は開始日より後に設定してください"')).toBeVisible();
    
    // 必須フィールドを空にして送信
    await page.reload();
    await projectListPage.clickNewProject();
    await projectFormPage.submit();
    
    // 必須フィールドのエラーメッセージ
    await expect(page.locator('text="プロジェクトコードは必須です"')).toBeVisible();
    await expect(page.locator('text="プロジェクト名は必須です"')).toBeVisible();
  });

  test('レスポンシブデザインのテスト', async ({ page }) => {
    // デスクトップビュー
    await page.setViewportSize({ width: 1920, height: 1080 });
    await projectListPage.goto();
    
    // ナビゲーションが表示されることを確認
    await expect(page.locator('.hidden.sm\\:flex')).toBeVisible();
    
    // タブレットビュー
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('.hidden.sm\\:flex')).toBeVisible();
    
    // モバイルビュー
    await page.setViewportSize({ width: 375, height: 667 });
    
    // モバイルメニューが表示されることを確認
    await expect(page.locator('.sm\\:hidden')).toBeVisible();
    
    // プロジェクトカードがスタックされることを確認
    const projectCards = page.locator('.grid > div');
    const firstCard = await projectCards.first().boundingBox();
    const secondCard = await projectCards.nth(1).boundingBox();
    
    if (firstCard && secondCard) {
      // モバイルビューでは縦に並ぶ
      expect(secondCard.y).toBeGreaterThan(firstCard.y + firstCard.height);
    }
  });
});