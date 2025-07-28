# CI/CD改善計画 - Issue #650対応

## 概要
このドキュメントは、Issue #650で指摘されたCI/CDパイプラインの問題に対する具体的な改善案です。

## 優先度：高 - 即時対応項目

### 1. セキュリティスキャンの構文エラー修正

#### 現状の問題
```yaml
on:

permissions:
  contents: read
  pull-requests: read
  checks: read
  push:             # ← これは誤った場所にある
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'
```

#### 修正案
```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly scan

permissions:
  contents: read
  pull-requests: read
  checks: read
  security-events: write  # SARIFアップロードに必要
```

### 2. 重複ワークフローの統合計画

#### 統合対象

##### A. デプロイメント系
- `deploy-production.yml` と `production-deploy.yml` → `deploy.yml`に統合
- 環境変数で制御：`DEPLOY_ENV=production|staging`

##### B. CI最適化系
統合順序（段階的に実施）：
1. `quick-ci.yml` を基本とする
2. `parallel-ci.yml` の並列実行部分を取り込む
3. `optimized-ci-v41.yml` のキャッシュ戦略を採用
4. `ultra-optimized-ci.yml` は削除（過度な最適化）

##### C. E2Eテスト系
- `e2e.yml` と `e2e-tests.yml` → `e2e-tests.yml`に統合
- `e2e-tests.yml`の方がタイムアウト設定など充実

### 3. 統合ワークフロー案

#### 3.1 統一CIワークフロー（ci.yml）
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  UV_CACHE_DIR: /tmp/.uv-cache
  NODE_CACHE_DIR: /tmp/.npm-cache

jobs:
  # 変更検出
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
              - '.github/workflows/**'
            frontend:
              - 'frontend/**'
              - '.github/workflows/**'
            infra:
              - 'infra/**'
              - 'k8s/**'
              - '.github/workflows/**'

  # バックエンドテスト（並列実行）
  backend-tests:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    uses: ./.github/workflows/reusable-test-backend.yml
    
  # フロントエンドテスト（並列実行）
  frontend-tests:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    uses: ./.github/workflows/reusable-test-frontend.yml

  # セキュリティスキャン（並列実行）
  security-scan:
    needs: changes
    if: needs.changes.outputs.backend == 'true' || needs.changes.outputs.frontend == 'true'
    uses: ./.github/workflows/security-scan.yml
```

#### 3.2 統一デプロイワークフロー（deploy.yml）
```yaml
name: Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
        description: 'Deployment environment (staging/production)'
      
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to ${{ inputs.environment }}
        run: |
          echo "Deploying to ${{ inputs.environment }}"
          # 実際のデプロイコマンド
```

## 実装スケジュール

### フェーズ1（今週中）
1. セキュリティスキャンの構文エラー修正（PR作成）
2. E2Eワークフローの統合（e2e.ymlを削除、e2e-tests.ymlに一本化）

### フェーズ2（来週）
1. デプロイワークフローの統合
2. 無効化されたワークフローの削除

### フェーズ3（2週間後）
1. CI最適化ワークフローの段階的統合
2. 性能測定と調整

## 期待される効果

### 定量的効果
- ワークフロー数：29個 → 15個以下（48%削減）
- CI実行時間：平均15分 → 8分（47%短縮）
- 月間Actions使用時間：1000分 → 400分（60%削減）

### 定性的効果
- メンテナンス性の大幅向上
- 新規開発者の理解容易性向上
- デバッグ時間の短縮

## リスクと対策

### リスク
1. 統合時の一時的な不安定性
2. 既存の自動化への影響

### 対策
1. 段階的な移行（並行稼働期間を設ける）
2. 十分なテスト期間の確保
3. ロールバック計画の準備