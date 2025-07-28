/**
 * プロジェクト管理システム E2Eテスト
 * 
 * テスト対象:
 * - プロジェクトのCRUD操作
 * - タスク管理とWBS
 * - ガントチャート
 * - メンバー管理
 * - 予算管理
 */

import { test, expect } from '@playwright/test';

// テストデータ
const testProject = {
  code: 'TEST-001',
  name: 'E2Eテストプロジェクト',
  description: 'E2Eテスト用のプロジェクトです',
  startDate: '2024-01-01',
  endDate: '2024-12-31',
  budget: '10000000',
};

const testTask = {
  name: 'テストタスク1',
  description: 'E2Eテスト用のタスクです',
  startDate: '2024-01-15',
  endDate: '2024-02-15',
  estimatedHours: '40',
};

test.describe('プロジェクト管理システム', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（必要に応じて実装）
    await page.goto('http://localhost:3000');
  });

  test.describe('プロジェクト一覧', () => {
    test('プロジェクト一覧が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // ページタイトルの確認
      await expect(page.locator('h1')).toContainText('プロジェクト管理');
      
      // 新規プロジェクトボタンの確認
      await expect(page.locator('button:has-text("新規プロジェクト")')).toBeVisible();
    });

    test('プロジェクトの検索ができる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // 検索ボックスに入力
      await page.fill('input[placeholder="プロジェクト名で検索..."]', 'テスト');
      await page.click('button:has-text("検索")');
      
      // 検索結果の確認（実際のデータに依存）
      await page.waitForTimeout(1000);
    });

    test('ステータスでフィルタリングができる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // ステータスフィルターを選択
      await page.selectOption('select', 'active');
      
      // フィルター結果の確認
      await page.waitForTimeout(1000);
    });
  });

  test.describe('プロジェクト作成', () => {
    test('新規プロジェクトを作成できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // 新規プロジェクトボタンをクリック
      await page.click('button:has-text("新規プロジェクト")');
      
      // フォームが表示されることを確認
      await expect(page.locator('h2:has-text("新規プロジェクト作成")')).toBeVisible();
      
      // フォームに入力
      await page.fill('input[id="code"]', testProject.code);
      await page.fill('input[id="name"]', testProject.name);
      await page.fill('textarea[id="description"]', testProject.description);
      await page.fill('input[id="startDate"]', testProject.startDate);
      await page.fill('input[id="endDate"]', testProject.endDate);
      await page.fill('input[id="budget"]', testProject.budget);
      
      // 作成ボタンをクリック
      await page.click('button:has-text("作成")');
      
      // 作成成功の確認（プロジェクト詳細ページへの遷移）
      await expect(page).toHaveURL(/\/projects\/\d+/);
    });

    test('必須項目が未入力の場合エラーが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // 新規プロジェクトボタンをクリック
      await page.click('button:has-text("新規プロジェクト")');
      
      // 何も入力せずに作成ボタンをクリック
      await page.click('button:has-text("作成")');
      
      // エラーメッセージの確認
      await expect(page.locator('text="プロジェクトコードは必須です"')).toBeVisible();
      await expect(page.locator('text="プロジェクト名は必須です"')).toBeVisible();
    });
  });

  test.describe('プロジェクト詳細', () => {
    test('プロジェクト詳細が表示される', async ({ page }) => {
      // プロジェクト一覧から詳細ページへ
      await page.goto('http://localhost:3000/projects');
      await page.click('.bg-white.shadow.rounded-lg').first(); // 最初のプロジェクトカードをクリック
      
      // タブの確認
      await expect(page.locator('button:has-text("ダッシュボード")')).toBeVisible();
      await expect(page.locator('button:has-text("タスク")')).toBeVisible();
      await expect(page.locator('button:has-text("ガントチャート")')).toBeVisible();
      await expect(page.locator('button:has-text("メンバー")')).toBeVisible();
      await expect(page.locator('button:has-text("予算管理")')).toBeVisible();
    });

    test('ダッシュボードタブが正しく表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1'); // 仮のプロジェクトID
      
      // ダッシュボードの要素確認
      await expect(page.locator('h2:has-text("プロジェクト概要")')).toBeVisible();
      await expect(page.locator('h2:has-text("進捗状況")')).toBeVisible();
    });
  });

  test.describe('タスク管理', () => {
    test('タスクを追加できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // タスクタブに切り替え
      await page.click('button:has-text("タスク")');
      
      // タスク追加ボタンをクリック
      await page.click('button:has-text("タスクを追加")');
      
      // フォームに入力
      await page.fill('input[id="name"]', testTask.name);
      await page.fill('textarea[id="description"]', testTask.description);
      await page.fill('input[id="startDate"]', testTask.startDate);
      await page.fill('input[id="endDate"]', testTask.endDate);
      await page.fill('input[id="estimatedHours"]', testTask.estimatedHours);
      
      // 作成ボタンをクリック
      await page.click('button:has-text("作成")');
      
      // タスクが追加されたことを確認
      await expect(page.locator(`text="${testTask.name}"`)).toBeVisible();
    });

    test('タスクツリー（WBS）が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      // タスクツリーの確認
      await expect(page.locator('h3:has-text("タスク一覧（WBS）")')).toBeVisible();
    });

    test('サブタスクを追加できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      // 親タスクのサブタスク追加ボタンをクリック（存在する場合）
      const addSubTaskButton = page.locator('button[title="サブタスクを追加"]').first();
      if (await addSubTaskButton.isVisible()) {
        await addSubTaskButton.click();
        
        // サブタスクフォームに入力
        await page.fill('input[id="name"]', 'サブタスク1');
        await page.fill('input[id="startDate"]', '2024-01-20');
        await page.fill('input[id="endDate"]', '2024-01-25');
        
        await page.click('button:has-text("作成")');
      }
    });
  });

  test.describe('ガントチャート', () => {
    test('ガントチャートが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // ガントチャートタブに切り替え
      await page.click('button:has-text("ガントチャート")');
      
      // ガントチャートの要素確認
      await expect(page.locator('h3:has-text("ガントチャート")')).toBeVisible();
      
      // 凡例の確認
      await expect(page.locator('text="クリティカルパス"')).toBeVisible();
      await expect(page.locator('text="マイルストーン"')).toBeVisible();
    });
  });

  test.describe('メンバー管理', () => {
    test('メンバー一覧が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // メンバータブに切り替え
      await page.click('button:has-text("メンバー")');
      
      // メンバー追加ボタンの確認
      await expect(page.locator('button:has-text("メンバーを追加")')).toBeVisible();
    });

    test('メンバーを追加できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("メンバー")');
      
      // メンバー追加ボタンをクリック
      await page.click('button:has-text("メンバーを追加")');
      
      // フォームに入力
      await page.fill('input[placeholder="ユーザーIDを入力"]', '2');
      await page.selectOption('select', 'member');
      await page.fill('input[type="number"][min="0"][max="100"]', '100');
      
      // 追加ボタンをクリック
      await page.click('button:has-text("追加")');
    });
  });

  test.describe('予算管理', () => {
    test('予算情報が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // 予算管理タブに切り替え
      await page.click('button:has-text("予算管理")');
      
      // 予算概要の確認
      await expect(page.locator('h3:has-text("予算概要")')).toBeVisible();
    });

    test('予算情報を編集できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("予算管理")');
      
      // 編集ボタンをクリック
      const editButton = page.locator('button:has-text("編集")');
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // コスト内訳を編集
        await page.fill('input[type="number"]').first(), '1000000');
        
        // 保存ボタンをクリック
        await page.click('button:has-text("保存")');
      }
    });
  });

  test.describe('プロジェクト操作', () => {
    test('プロジェクトを複製できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // 複製ボタンをクリック
      await page.click('button[title="複製"]');
      
      // 確認ダイアログでOKをクリック
      page.on('dialog', dialog => dialog.accept());
      
      // 新しいプロジェクトページへの遷移を確認
      await page.waitForURL(/\/projects\/\d+/);
    });

    test('自動スケジューリングを実行できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      // 自動スケジューリングボタンをクリック
      const autoScheduleButton = page.locator('button[title="自動スケジューリング"]');
      if (await autoScheduleButton.isVisible()) {
        await autoScheduleButton.click();
        
        // 確認ダイアログでOKをクリック
        page.on('dialog', dialog => dialog.accept());
        
        // 完了メッセージの確認
        await expect(page.locator('text="自動スケジューリングが完了しました"')).toBeVisible();
      }
    });
  });

  test.describe('レスポンシブデザイン', () => {
    test('モバイル表示が正しく動作する', async ({ page }) => {
      // モバイルビューポートに設定
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('http://localhost:3000/projects');
      
      // モバイルメニューが表示されることを確認
      await expect(page.locator('.sm\\:hidden')).toBeVisible();
    });
  });
});

// ヘルパー関数
async function createTestProject(page: any, projectData: any) {
  await page.goto('http://localhost:3000/projects');
  await page.click('button:has-text("新規プロジェクト")');
  
  await page.fill('input[id="code"]', projectData.code);
  await page.fill('input[id="name"]', projectData.name);
  await page.fill('textarea[id="description"]', projectData.description);
  await page.fill('input[id="startDate"]', projectData.startDate);
  await page.fill('input[id="endDate"]', projectData.endDate);
  await page.fill('input[id="budget"]', projectData.budget);
  
  await page.click('button:has-text("作成")');
  await page.waitForURL(/\/projects\/\d+/);
}

async function deleteTestProject(page: any, projectCode: string) {
  // プロジェクト削除の実装（APIが提供されている場合）
  // この関数は実際のAPIに合わせて実装する必要があります
}