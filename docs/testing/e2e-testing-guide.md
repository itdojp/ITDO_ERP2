# E2E Testing Guide - ITDO ERP System v2

## 📋 目次

1. [概要](#概要)
2. [環境設定](#環境設定)
3. [テスト構造](#テスト構造)
4. [実行方法](#実行方法)
5. [新テスト追加ガイド](#新テスト追加ガイド)
6. [トラブルシューティング](#トラブルシューティング)
7. [ベストプラクティス](#ベストプラクティス)
8. [CI/CD統合](#cicd統合)

## 概要

ITDO ERP System v2のE2Eテストは、Playwrightを使用してブラウザベースの統合テストを実行します。
本システムは、フロントエンド（React + TypeScript）とバックエンド（FastAPI + Python）の完全な統合テストを提供します。

### テストの目的

- **機能検証**: ユーザー視点での機能が正常に動作することを確認
- **統合確認**: フロントエンドとバックエンドの連携動作を検証
- **リグレッション防止**: 新機能追加による既存機能の破綻を防止
- **パフォーマンス監視**: ページロード時間、API応答時間の監視
- **アクセシビリティ**: WCAG準拠の確認

## 環境設定

### 前提条件

```bash
# Node.js 18以上
node --version  # v18.0.0+

# Python 3.13
python --version  # 3.13.0+

# uv (Pythonパッケージマネージャー)
uv --version

# PostgreSQL 15 & Redis 7 (Podman/Docker経由)
podman --version
```

### 開発環境セットアップ

```bash
# 1. データレイヤー起動
make start-data

# 2. バックエンド準備
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/init_test_data.py

# 3. フロントエンド準備
cd frontend
npm install
npx playwright install --with-deps

# 4. 開発サーバー起動
# ターミナル1: バックエンド
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ターミナル2: フロントエンド
cd frontend && npm run dev
```

### 環境変数設定

```bash
# backend/.env
DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ENVIRONMENT=development
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
API_V1_PREFIX=/api/v1
```

## テスト構造

```
frontend/tests/e2e/
├── fixtures/                 # テストフィクスチャ
│   ├── auth.fixture.ts       # 認証関連
│   └── data.fixture.ts       # テストデータ
├── critical/                 # 重要パステスト
│   └── critical-path.spec.ts # アプリケーション起動等
├── smoke/                    # スモークテスト
│   └── app-startup.spec.ts   # 基本機能確認
├── integration/              # 統合テスト
│   ├── user-management.spec.ts
│   ├── organization.spec.ts
│   └── task-management.spec.ts
├── performance/              # パフォーマンステスト
│   ├── load-testing.spec.ts
│   └── concurrent-users.spec.ts
├── accessibility/            # アクセシビリティテスト
│   └── wcag-compliance.spec.ts
└── visual/                   # ビジュアルリグレッション
    └── screenshot-tests.spec.ts
```

### テストカテゴリー

#### 1. Critical Path Tests
- アプリケーション起動
- 基本的なナビゲーション
- API接続性

#### 2. Smoke Tests
- 重要な機能の基本動作
- データ表示確認
- エラーハンドリング

#### 3. Integration Tests
- ユーザー管理（CRUD操作）
- 組織管理
- タスク管理
- 認証フロー

#### 4. Performance Tests
- ページロード時間測定
- API応答時間
- 同時ユーザー負荷
- メモリリーク検証

#### 5. Accessibility Tests
- WCAG 2.1 AA準拠確認
- キーボードナビゲーション
- スクリーンリーダー対応

## 実行方法

### ローカル実行

```bash
# 全テスト実行
npm run test:e2e

# 特定カテゴリー実行
npx playwright test tests/e2e/smoke/
npx playwright test tests/e2e/critical/
npx playwright test tests/e2e/integration/

# デバッグモード
npx playwright test --debug

# ヘッドフルモード（ブラウザ表示）
npx playwright test --headed

# 特定ブラウザで実行
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# 並列実行制御
npx playwright test --workers=1  # シングルワーカー
npx playwright test --workers=4  # 4並列実行
```

### CI環境での実行

```bash
# CI用設定で実行
CI=true npx playwright test

# リポート生成
npx playwright test --reporter=html,json,github

# 失敗時の詳細情報
npx playwright test --trace=retain-on-failure
```

### レポート確認

```bash
# HTMLレポート表示
npx playwright show-report

# テスト結果ファイル
cat test-results/test-results.json
```

## 新テスト追加ガイド

### 1. 基本テストファイル作成

```typescript
// tests/e2e/new-feature/example.spec.ts
import { test, expect } from '@playwright/test';

test.describe('New Feature Tests', () => {
  test.beforeEach(async ({ page }) => {
    // テスト前の共通設定
    await page.goto('/');
  });

  test('should perform basic operation', async ({ page }) => {
    // テストロジック
    await page.click('[data-testid="new-feature-button"]');
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });
});
```

### 2. フィクスチャの使用

```typescript
// fixtures/custom.fixture.ts
import { test as base } from '@playwright/test';

type CustomFixtures = {
  authenticatedPage: Page;
  testData: TestData;
};

export const test = base.extend<CustomFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // 認証済みページの提供
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
    await use(page);
  },
});
```

### 3. Page Object Model

```typescript
// pages/UserManagementPage.ts
export class UserManagementPage {
  constructor(private page: Page) {}

  async navigateToUsers() {
    await this.page.click('[data-testid="users-nav"]');
    await this.page.waitForURL('/users');
  }

  async createUser(userData: UserData) {
    await this.page.click('[data-testid="create-user-button"]');
    await this.page.fill('[data-testid="user-name"]', userData.name);
    await this.page.fill('[data-testid="user-email"]', userData.email);
    await this.page.click('[data-testid="save-user"]');
  }

  async getUserList() {
    return await this.page.locator('[data-testid="user-list"] tr').count();
  }
}
```

### 4. API テスト統合

```typescript
test('should handle API interactions', async ({ page, request }) => {
  // APIリクエスト
  const response = await request.post('/api/v1/users', {
    data: { name: 'Test User', email: 'test@example.com' }
  });
  expect(response.ok()).toBeTruthy();
  
  // UI反映確認
  await page.reload();
  await expect(page.locator('text=Test User')).toBeVisible();
});
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. テストタイムアウト

```bash
# エラー: Test timeout of 30000ms exceeded.

# 解決方法:
test.setTimeout(60000); // 60秒に延長

# または個別設定
await page.goto('/', { timeout: 45000 });
```

#### 2. 要素が見つからない

```bash
# エラー: Locator not found

# 解決方法: 要素の出現を待機
await page.waitForSelector('[data-testid="element"]');
await expect(page.locator('[data-testid="element"]')).toBeVisible();
```

#### 3. 非同期処理の待機

```typescript
// APIコール完了を待機
await page.waitForResponse(response => 
  response.url().includes('/api/v1/users') && response.status() === 200
);

// ネットワークアイドル状態を待機
await page.waitForLoadState('networkidle');
```

#### 4. CI環境での失敗

```yaml
# CI用タイムアウト調整
test.setTimeout(process.env.CI ? 120000 : 60000);

# リトライ設定
npx playwright test --retries=2
```

### デバッグ方法

```bash
# 1. ステップ実行
npx playwright test --debug

# 2. スクリーンショット取得
await page.screenshot({ path: 'debug.png' });

# 3. ページコンテンツ確認
console.log(await page.content());

# 4. 要素の状態確認
console.log(await page.locator('[data-testid="element"]').count());
```

## ベストプラクティス

### 1. テスト設計原則

- **独立性**: 各テストは他のテストに依存しない
- **再現性**: 同じ条件で同じ結果が得られる
- **明確性**: テストの目的が明確である
- **迅速性**: 実行時間を最小限に抑える

### 2. 要素選択

```typescript
// ❌ 悪い例: CSSセレクターに依存
await page.click('.btn-primary');

// ✅ 良い例: data-testid属性を使用
await page.click('[data-testid="submit-button"]');

// ✅ 良い例: 役割やテキストベース
await page.click('button:has-text("Submit")');
await page.click('[role="button"][name="Submit"]');
```

### 3. 待機処理

```typescript
// ❌ 悪い例: 固定時間待機
await page.waitForTimeout(5000);

// ✅ 良い例: 条件ベース待機
await page.waitForSelector('[data-testid="result"]');
await page.waitForLoadState('networkidle');
await expect(page.locator('[data-testid="result"]')).toBeVisible();
```

### 4. テストデータ管理

```typescript
// ✅ テストデータの分離
const testData = {
  validUser: { name: 'Test User', email: 'test@example.com' },
  invalidUser: { name: '', email: 'invalid-email' }
};

// ✅ ランダムデータの使用
const uniqueEmail = `test+${Date.now()}@example.com`;
```

### 5. エラーハンドリング

```typescript
test('should handle errors gracefully', async ({ page }) => {
  // エラー監視
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  
  // テスト実行
  await page.goto('/');
  
  // エラーチェック
  expect(errors).toHaveLength(0);
});
```

## CI/CD統合

### GitHub Actions設定

```yaml
# .github/workflows/e2e.yml
- name: Run E2E Tests
  run: |
    cd frontend
    npx playwright test \
      --reporter=html,json,github \
      --workers=1 \
      --timeout=120000 \
      --retries=2
  env:
    CI: true
    PLAYWRIGHT_BASE_URL: http://localhost:3000
```

### 品質ゲート

- **必須テスト**: Critical PathとSmoke Testsは必須通過
- **カバレッジ**: 主要機能の80%以上をカバー
- **パフォーマンス**: ページロード時間5秒以内
- **アクセシビリティ**: WCAG 2.1 AA基準準拠

### 継続的改善

1. **フレイキーテスト対策**: 不安定なテストの特定と修正
2. **実行時間最適化**: 並列実行とテスト分割
3. **レポート分析**: 失敗傾向の分析と改善
4. **メンテナンス**: 定期的なテストケース見直し

## パフォーマンス最適化

### 実行時間短縮

```typescript
// ✅ 並列実行対応設計
test.describe.configure({ mode: 'parallel' });

// ✅ 共通設定の再利用
test.beforeAll(async ({ browser }) => {
  const context = await browser.newContext();
  // 共通設定
});

// ✅ 必要最小限の操作
await page.goto('/', { waitUntil: 'domcontentloaded' }); // networkidleより高速
```

### リソース最適化

```typescript
// ✅ 不要なリソース読み込み停止
await page.route('**/*.{png,jpg,jpeg}', route => route.abort());

// ✅ ヘッドレスモード使用
// playwright.config.ts
export default defineConfig({
  use: { headless: true }
});
```

---

## 付録

### A. 設定ファイル例

#### playwright.config.ts
```typescript
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: process.env.CI ? 120000 : 60000,
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

### B. 有用なコマンド集

```bash
# テスト生成
npx playwright codegen localhost:3000

# テスト記録
npx playwright test --trace=on

# レポート表示
npx playwright show-report

# 設定確認
npx playwright test --list

# ブラウザ情報
npx playwright --version
```

### C. 参考資料

- [Playwright公式ドキュメント](https://playwright.dev/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [CI/CD Integration](https://playwright.dev/docs/ci)

---

**更新日**: 2025-07-09  
**バージョン**: 2.0  
**担当**: Development Team