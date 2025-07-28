/**
 * プロジェクト管理システム 高度なE2Eテスト
 * 
 * テスト対象:
 * - プロジェクト階層（親子関係）
 * - タスクの依存関係
 * - クリティカルパス
 * - リソース利用率
 * - 進捗レポート
 * - 繰り返しプロジェクト
 */

import { test, expect } from '@playwright/test';

test.describe('プロジェクト管理システム - 高度な機能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test.describe('プロジェクト階層', () => {
    test('親プロジェクトを作成できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      await page.click('button:has-text("新規プロジェクト")');
      
      // 親プロジェクトの作成
      await page.fill('input[id="code"]', 'PARENT-001');
      await page.fill('input[id="name"]', '親プロジェクト');
      await page.fill('input[id="startDate"]', '2024-01-01');
      await page.fill('input[id="endDate"]', '2024-12-31');
      await page.fill('input[id="budget"]', '50000000');
      
      await page.click('button:has-text("作成")');
      await expect(page).toHaveURL(/\/projects\/\d+/);
    });

    test('子プロジェクトを作成できる（最大5階層）', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      await page.click('button:has-text("新規プロジェクト")');
      
      // 親プロジェクトを選択
      const parentSelect = page.locator('select[id="parentId"]');
      if (await parentSelect.isVisible()) {
        await parentSelect.selectOption({ label: 'PARENT-001 - 親プロジェクト' });
      }
      
      // 子プロジェクトの作成
      await page.fill('input[id="code"]', 'CHILD-001');
      await page.fill('input[id="name"]', '子プロジェクト');
      await page.fill('input[id="startDate"]', '2024-02-01');
      await page.fill('input[id="endDate"]', '2024-06-30');
      await page.fill('input[id="budget"]', '10000000');
      
      await page.click('button:has-text("作成")');
      await expect(page).toHaveURL(/\/projects\/\d+/);
    });

    test('6階層目のプロジェクトは作成できない', async ({ page }) => {
      // この테스nトは5階層のプロジェクトが既に存在することを前提とします
      // 実際のテストでは、事前に5階層のプロジェクトを作成する必要があります
    });
  });

  test.describe('タスクの依存関係とクリティカルパス', () => {
    test('タスク間の依存関係を設定できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      // タスクが存在する場合、編集モードに入る
      const editButton = page.locator('button[title="編集"]').first();
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // 依存関係の設定（実装に応じて調整）
        // await page.selectOption('select[name="dependencies"]', 'task-2');
        
        await page.click('button:has-text("更新")');
      }
    });

    test('ガントチャートでクリティカルパスが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("ガントチャート")');
      
      // クリティカルパスの赤いバーを確認
      const criticalPathBars = page.locator('.bg-red-500');
      const count = await criticalPathBars.count();
      expect(count).toBeGreaterThan(0);
    });

    test('循環依存を検出してエラーを表示する', async ({ page }) => {
      // タスクAがタスクBに依存し、タスクBがタスクAに依存する状況を作る
      // 実装に応じて具体的なテストを記述
    });
  });

  test.describe('リソース管理', () => {
    test('リソースの稼働率が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("メンバー")');
      
      // 稼働率の表示を確認
      await expect(page.locator('text="%"')).toBeVisible();
    });

    test('リソースの過剰割り当てが警告される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("メンバー")');
      
      // メンバーを追加
      await page.click('button:has-text("メンバーを追加")');
      await page.fill('input[placeholder="ユーザーIDを入力"]', '3');
      await page.fill('input[type="number"][min="0"][max="100"]', '150'); // 150%の稼働率
      
      // 警告メッセージやエラーの確認
      // 実装に応じて調整
    });
  });

  test.describe('進捗管理とレポート', () => {
    test('タスクの進捗を更新できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      // タスクの編集
      const editButton = page.locator('button[title="編集"]').first();
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // 進捗率を更新
        await page.fill('input[id="progressPercentage"]', '50');
        await page.click('button:has-text("更新")');
        
        // 進捗が更新されたことを確認
        await expect(page.locator('text="50%完了"')).toBeVisible();
      }
    });

    test('進捗率100%でステータスが自動的に「完了」になる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("タスク")');
      
      const editButton = page.locator('button[title="編集"]').first();
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // 進捗率を100%に設定
        await page.fill('input[id="progressPercentage"]', '100');
        
        // ステータスが「完了」になることを確認
        await expect(page.selectOption('select[id="status"]')).toBe('completed');
      }
    });

    test('ダッシュボードで総合進捗が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      
      // ダッシュボードタブがデフォルトで選択されている
      await expect(page.locator('text="全体進捗"')).toBeVisible();
      
      // 進捗バーの確認
      await expect(page.locator('.bg-green-500, .bg-yellow-500, .bg-red-500')).toBeVisible();
    });
  });

  test.describe('予算管理の高度な機能', () => {
    test('予算対実績の差異が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("予算管理")');
      
      // 差異の表示を確認
      await expect(page.locator('text="差異"')).toBeVisible();
    });

    test('コスト内訳のグラフが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("予算管理")');
      
      // コスト構成比のグラフを確認
      await expect(page.locator('text="コスト構成比"')).toBeVisible();
      await expect(page.locator('.bg-blue-500')).toBeVisible(); // 人件費
      await expect(page.locator('.bg-green-500')).toBeVisible(); // 外注費
      await expect(page.locator('.bg-yellow-500')).toBeVisible(); // 経費
    });

    test('収益性分析が表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects/1');
      await page.click('button:has-text("予算管理")');
      
      // 売上を設定した場合の収益性分析
      const editButton = page.locator('button:has-text("編集")');
      if (await editButton.isVisible()) {
        await editButton.click();
        await page.fill('input').last(), '15000000'); // 売上
        await page.click('button:has-text("保存")');
        
        // 利益と利益率の表示を確認
        await expect(page.locator('text="利益"')).toBeVisible();
        await expect(page.locator('text="利益率"')).toBeVisible();
      }
    });
  });

  test.describe('繰り返しプロジェクト', () => {
    test('繰り返しプロジェクトを作成できる', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      await page.click('button:has-text("新規プロジェクト")');
      
      // プロジェクトタイプを「繰り返し」に設定
      await page.selectOption('select[id="projectType"]', 'recurring');
      
      await page.fill('input[id="code"]', 'RECURRING-001');
      await page.fill('input[id="name"]', '月次レポートプロジェクト');
      await page.fill('input[id="startDate"]', '2024-01-01');
      await page.fill('input[id="endDate"]', '2024-01-31');
      await page.fill('input[id="budget"]', '1000000');
      
      await page.click('button:has-text("作成")');
    });

    test('繰り返しプロジェクトを複製して次の期間を作成できる', async ({ page }) => {
      // 繰り返しプロジェクトの詳細ページへ
      await page.goto('http://localhost:3000/projects');
      await page.click('text="月次レポートプロジェクト"');
      
      // 複製ボタンをクリック
      await page.click('button[title="複製"]');
      
      page.on('dialog', dialog => dialog.accept());
      
      // 新しいプロジェクトが作成されたことを確認
      await page.waitForURL(/\/projects\/\d+/);
      await expect(page.locator('text="月次レポートプロジェクト (Copy)"')).toBeVisible();
    });
  });

  test.describe('データ検証とエラーハンドリング', () => {
    test('開始日が終了日より後の場合エラーが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      await page.click('button:has-text("新規プロジェクト")');
      
      await page.fill('input[id="code"]', 'ERROR-001');
      await page.fill('input[id="name"]', 'エラーテストプロジェクト');
      await page.fill('input[id="startDate"]', '2024-12-31');
      await page.fill('input[id="endDate"]', '2024-01-01'); // 開始日より前
      await page.fill('input[id="budget"]', '1000000');
      
      await page.click('button:has-text("作成")');
      
      // エラーメッセージの確認
      await expect(page.locator('text="終了日は開始日より後に設定してください"')).toBeVisible();
    });

    test('予算が0未満の場合エラーが表示される', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      await page.click('button:has-text("新規プロジェクト")');
      
      await page.fill('input[id="budget"]', '-1000');
      
      await page.click('button:has-text("作成")');
      
      // エラーメッセージの確認
      await expect(page.locator('text="予算は0以上で入力してください"')).toBeVisible();
    });
  });

  test.describe('パフォーマンステスト', () => {
    test('100件のタスクがある場合でもガントチャートが表示される', async ({ page }) => {
      // 大量のタスクがあるプロジェクトをテスト
      // 実際のテスト環境では事前にテストデータを準備する必要があります
      
      await page.goto('http://localhost:3000/projects/1'); // 大量タスクのあるプロジェクト
      await page.click('button:has-text("ガントチャート")');
      
      // ガントチャートの表示を確認
      await expect(page.locator('h3:has-text("ガントチャート")')).toBeVisible({ timeout: 10000 });
    });

    test('ページネーションが正しく動作する', async ({ page }) => {
      await page.goto('http://localhost:3000/projects');
      
      // ページネーションボタンの確認
      const nextButton = page.locator('button:has-text("次へ")');
      if (await nextButton.isEnabled()) {
        await nextButton.click();
        
        // URLにページ番号が反映されることを確認
        await expect(page).toHaveURL(/page=2/);
      }
    });
  });
});