# E2E Testing Troubleshooting Guide

## 🚨 緊急時対応ガイド

### CI/CDでE2Eテストが失敗した場合

1. **即座の確認事項**
   ```bash
   # GitHub Actions実行ログ確認
   gh run view <run-id> --log
   
   # アーティファクト確認
   gh run download <run-id>
   ```

2. **サービス起動チェック**
   - PostgreSQL: ポート5432
   - Redis: ポート6379  
   - Backend API: ポート8000
   - Frontend: ポート3000

3. **ログの確認箇所**
   - Backend logs: `backend/backend.log`
   - Frontend logs: `frontend/frontend.log`
   - Test reports: `playwright-report/`

## 🔧 よくある問題と解決方法

### 1. データベース接続エラー

#### 問題
```
SettingsError: error parsing value for field "BACKEND_CORS_ORIGINS"
```

#### 解決方法
```bash
# .envファイルの形式確認
cat backend/.env | grep CORS

# 正しい形式
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# または
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### 修正スクリプト
```bash
cd backend
echo 'BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000' >> .env
```

### 2. テストタイムアウト

#### 問題
```
Test timeout of 30000ms exceeded
```

#### 解決方法
```typescript
// テストファイル内で調整
test.setTimeout(120000); // 2分

// CI環境の場合のみ延長
if (process.env.CI) {
  test.setTimeout(180000); // 3分
}
```

#### playwright.config.ts調整
```typescript
export default defineConfig({
  timeout: process.env.CI ? 120000 : 60000,
  expect: { timeout: process.env.CI ? 30000 : 15000 },
});
```

### 3. サービス起動失敗

#### PostgreSQL起動エラー
```bash
# コンテナ状態確認
podman ps -a | grep postgres

# ログ確認
podman logs <postgres-container-id>

# 再起動
make stop-data
make start-data
```

#### Backend起動エラー
```bash
# ポート確認
netstat -tlpn | grep :8000

# プロセス確認
ps aux | grep uvicorn

# ログ確認
tail -f backend/backend.log
```

#### Frontend起動エラー
```bash
# Node.jsバージョン確認
node --version  # 18以上必要

# 依存関係再インストール
cd frontend
rm -rf node_modules package-lock.json
npm install

# ポート確認
netstat -tlpn | grep :3000
```

### 4. Playwright関連エラー

#### ブラウザがインストールされていない
```bash
# ブラウザインストール
cd frontend
npx playwright install --with-deps

# Chromiumのみ
npx playwright install chromium
```

#### 要素が見つからない
```typescript
// ❌ 問題のあるコード
await page.click('#submit');

// ✅ 解決方法
await page.waitForSelector('#submit', { timeout: 30000 });
await page.click('#submit');

// または
await expect(page.locator('#submit')).toBeVisible();
await page.click('#submit');
```

#### 非同期処理の待機
```typescript
// API完了を待機
await page.waitForResponse(response => 
  response.url().includes('/api/users') && response.status() === 200
);

// ページ遷移を待機
await page.waitForURL('/dashboard');

// 要素の状態変化を待機
await expect(page.locator('[data-testid="loading"]')).toBeHidden();
```

### 5. CI環境特有の問題

#### GitHub Actions実行権限
```yaml
# .github/workflows/e2e.yml
permissions:
  contents: read
  actions: read
  checks: write
  pull-requests: write
```

#### メモリ不足
```yaml
# GitHubActionsランナーのメモリ制限
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    # リソース調整が必要な場合はより大きなランナーを使用
```

#### 環境変数設定
```yaml
env:
  CI: true
  NODE_ENV: test
  PLAYWRIGHT_BASE_URL: http://localhost:3000
  VITE_API_URL: http://localhost:8000
```

## 🛠️ デバッグ手法

### 1. ローカルデバッグ

```bash
# 1. ステップ実行モード
npx playwright test --debug

# 2. ヘッドフルモード
npx playwright test --headed

# 3. スローモーション
npx playwright test --headed --slowMo=1000

# 4. 特定テストのみ実行
npx playwright test tests/e2e/smoke/app-startup.spec.ts --debug
```

### 2. ログとスクリーンショット

```typescript
test('debug example', async ({ page }) => {
  // スクリーンショット取得
  await page.screenshot({ path: 'debug-1.png' });
  
  // ページ状態ログ
  console.log('Page URL:', page.url());
  console.log('Page title:', await page.title());
  
  // 要素情報
  const button = page.locator('[data-testid="submit"]');
  console.log('Button count:', await button.count());
  console.log('Button visible:', await button.isVisible());
  
  // ネットワーク監視
  page.on('response', response => {
    console.log('Response:', response.url(), response.status());
  });
});
```

### 3. トレース分析

```bash
# トレース有効化
npx playwright test --trace=on

# 失敗時のみトレース
npx playwright test --trace=retain-on-failure

# トレース表示
npx playwright show-trace test-results/*/trace.zip
```

### 4. CI環境のログ確認

```bash
# GitHub CLI使用
gh run list --limit 10
gh run view <run-id> --log
gh run download <run-id>

# アーティファクト確認
unzip artifacts.zip
cat test-results/test-results.json | jq '.results[] | select(.status == "failed")'
```

## 🔍 パフォーマンス問題

### 1. 実行時間が長い

#### 原因特定
```typescript
test('performance measurement', async ({ page }) => {
  const startTime = Date.now();
  
  await page.goto('/');
  console.log('Page load:', Date.now() - startTime, 'ms');
  
  const actionStart = Date.now();
  await page.click('[data-testid="button"]');
  console.log('Action time:', Date.now() - actionStart, 'ms');
});
```

#### 最適化方法
```typescript
// ✅ 不要なリソース読み込み停止
await page.route('**/*.{png,jpg,jpeg,svg}', route => route.abort());

// ✅ 必要最小限の待機
await page.goto('/', { waitUntil: 'domcontentloaded' });

// ✅ 並列実行
test.describe.configure({ mode: 'parallel' });
```

### 2. メモリリーク

#### 検出方法
```typescript
test('memory monitoring', async ({ page }) => {
  const initialMemory = await page.evaluate(() => 
    (performance as any).memory?.usedJSHeapSize || 0
  );
  
  // 操作実行
  for (let i = 0; i < 10; i++) {
    await page.reload();
  }
  
  const finalMemory = await page.evaluate(() => 
    (performance as any).memory?.usedJSHeapSize || 0
  );
  
  const growth = finalMemory - initialMemory;
  console.log('Memory growth:', growth, 'bytes');
  expect(growth).toBeLessThan(10 * 1024 * 1024); // 10MB未満
});
```

## 📊 監視とアラート

### 1. テスト結果の監視

```bash
# 成功率計算
total_tests=$(cat test-results.json | jq '.results | length')
failed_tests=$(cat test-results.json | jq '.results[] | select(.status == "failed") | length')
success_rate=$((($total_tests - $failed_tests) * 100 / $total_tests))
echo "Success rate: $success_rate%"
```

### 2. パフォーマンス監視

```typescript
// レスポンス時間監視
test('API performance monitoring', async ({ request }) => {
  const endpoints = ['/api/v1/health', '/api/v1/users'];
  
  for (const endpoint of endpoints) {
    const start = Date.now();
    const response = await request.get(`http://localhost:8000${endpoint}`);
    const duration = Date.now() - start;
    
    console.log(`${endpoint}: ${duration}ms`);
    expect(duration).toBeLessThan(1000); // 1秒以内
    expect(response.ok()).toBeTruthy();
  }
});
```

### 3. フレイキーテスト検出

```bash
# 同じテストを複数回実行
for i in {1..10}; do
  echo "Run $i"
  npx playwright test tests/e2e/smoke/app-startup.spec.ts --reporter=json > run-$i.json
done

# 成功率計算
success_count=0
for i in {1..10}; do
  if jq -e '.results[] | select(.status == "passed")' run-$i.json > /dev/null; then
    success_count=$((success_count + 1))
  fi
done
echo "Flaky test success rate: $((success_count * 10))%"
```

## 🚀 緊急対応手順

### 1. 本番リリース前のE2E失敗

1. **即座の確認**
   ```bash
   # 最新のテスト結果確認
   gh pr checks <pr-number>
   
   # ローカルで再現確認
   git checkout <branch>
   make test-e2e
   ```

2. **クリティカルパステスト**
   ```bash
   # 最重要機能のみテスト
   npx playwright test tests/e2e/critical/
   ```

3. **一時的回避策**
   ```typescript
   // 該当テストを一時的にスキップ
   test.skip('flaky test', async ({ page }) => {
     // テスト内容
   });
   ```

### 2. CI環境での継続的失敗

1. **サービス依存関係チェック**
   ```bash
   # 各サービスの状態確認
   ./scripts/wait-for-services.sh
   ```

2. **設定ファイル検証**
   ```bash
   # 設定ファイルの構文チェック
   cd backend && python -c "from app.core.config import Settings; Settings()"
   cd frontend && npm run typecheck
   ```

3. **段階的復旧**
   ```bash
   # 1. スモークテストのみ実行
   npx playwright test tests/e2e/smoke/ --workers=1
   
   # 2. 成功したら統合テスト追加
   npx playwright test tests/e2e/integration/ --workers=1
   ```

## 📞 エスカレーション

### レベル1: 開発者対応
- テストコードの修正
- 設定ファイルの調整
- 軽微な環境問題

### レベル2: チーム対応  
- インフラストラクチャの問題
- CI/CDパイプラインの修正
- パフォーマンス問題

### レベル3: システム管理者対応
- インフラストラクチャの障害
- セキュリティ関連問題
- 大規模な環境変更

## 📚 参考資料

- [Playwright Debugging Guide](https://playwright.dev/docs/debug)
- [CI Best Practices](https://playwright.dev/docs/ci)
- [Performance Testing](https://playwright.dev/docs/test-timeouts)

---

**最終更新**: 2025-07-09  
**作成者**: Development Team  
**レビュー**: Lead Engineer