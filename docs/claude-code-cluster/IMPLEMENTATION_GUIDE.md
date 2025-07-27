# SDAD × Claude Code Cluster 実装ガイド

## 1. セットアップ手順

### 1.1 Claude Code Clusterの準備

```bash
# 1. クローン（ITDO_ERP2と同じ階層に配置）
cd /mnt/c/work
git clone https://github.com/ootakazuhiko/claude-code-cluster.git

# 2. ディレクトリ構造
# /mnt/c/work/
# ├── ITDO_ERP2/           # メインプロジェクト
# └── claude-code-cluster/ # エージェント管理システム
```

### 1.2 SDAD環境の初期化

```bash
cd /mnt/c/work/ITDO_ERP2

# Git Hooksの有効化
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

# SDAD作業ディレクトリの作成
./scripts/sdad-phase-manager.sh init

# 実行権限の付与
chmod +x scripts/sdad-phase-manager.sh
```

### 1.3 GitHub設定

```bash
# 必要なラベルの作成
gh label create "phase-0-kickoff" --color "CCCCCC" --description "SDAD Phase 0: Kickoff"
gh label create "phase-1-discovery" --color "0E8A16" --description "SDAD Phase 1: Discovery"
gh label create "phase-2-documentation" --color "1D76DB" --description "SDAD Phase 2: Documentation"
gh label create "phase-3-validation" --color "FBCA04" --description "SDAD Phase 3: Validation"
gh label create "phase-4-generation" --color "5319E7" --description "SDAD Phase 4: Generation"

# エージェント用ラベル
gh label create "agent-task" --color "F9D0C4" --description "Task for AI agents"
gh label create "CC01" --color "7057FF" --description "Frontend Agent"
gh label create "CC02" --color "00B050" --description "Backend Agent"
gh label create "CC03" --color "E99695" --description "Infrastructure Agent"
gh label create "COORD" --color "0075CA" --description "Coordinator Agent"
```

## 2. パイロット実装手順（商品管理機能）

### 2.1 Phase 0: キックオフ（人間のみ）

```bash
# フィーチャーブリーフの作成
cat > docs/products/feature_brief.md << 'EOF'
# Feature Brief: 商品管理機能（最小構成版）

## 1. 目的と背景 (Why)
- **解決したい課題**: 20人規模の組織での基本的な商品情報管理
- **ビジネス価値**: 在庫と価格の可視化による業務効率化
- **成功の測定指標 (KPI)**: 商品検索時間50%削減

## 2. 機能概要 (What)
シンプルな商品マスタ管理（CRUD操作）

## 3. スコープ
- **スコープ内**: 商品の登録・更新・削除・一覧表示
- **スコープ外**: 複雑な在庫管理、価格履歴、承認ワークフロー

## 4. 主要な関係者
- **プロダクトオーナー**: [Your Name]
- **開発リード**: CC01/CC02
- **QAリード**: Coordinator
EOF

# Issueの作成
gh issue create \
  --title "[SDAD] Phase 0: 商品管理機能の最小実装" \
  --body-file docs/products/feature_brief.md \
  --label "phase-0-kickoff" \
  --milestone "Pilot Implementation"
```

### 2.2 Phase 1: ディスカバリー

```bash
# Coordinatorへのタスクパケット生成
./scripts/sdad-phase-manager.sh packet phase-1 products COORD

# タスクの割り当て
./scripts/sdad-phase-manager.sh assign task-packets/ITDO-ERP2-phase-1-products-*.yaml COORD

# Coordinatorの期待される成果物:
# - features/products.feature (Gherkinシナリオ)
# - docs/products/acceptance_criteria.md
```

### 2.3 Phase 2: ドキュメント化

```bash
# 各エージェントへのタスクパケット生成（並列実行）
./scripts/sdad-phase-manager.sh packet phase-2 products CC01
./scripts/sdad-phase-manager.sh packet phase-2 products CC02
./scripts/sdad-phase-manager.sh packet phase-2 products CC03

# 期待される成果物:
# - docs/products/frontend_spec.md (CC01)
# - docs/products/api_spec.yaml (CC02)
# - docs/products/deployment_spec.md (CC03)
```

### 2.4 Phase 3: バリデーション

```bash
# テスト作成タスク
./scripts/sdad-phase-manager.sh packet phase-3 products CC01
./scripts/sdad-phase-manager.sh packet phase-3 products CC02

# 検証コマンド（テストが失敗することを確認）
cd backend && uv run pytest -k products && echo "ERROR: Tests should fail!" || echo "OK: Tests failing as expected"
cd frontend && npm test products && echo "ERROR: Tests should fail!" || echo "OK: Tests failing as expected"
```

### 2.5 Phase 4: ジェネレーション

```bash
# 実装タスク
./scripts/sdad-phase-manager.sh packet phase-4 products CC01
./scripts/sdad-phase-manager.sh packet phase-4 products CC02

# 完了確認
./scripts/sdad-phase-manager.sh gate phase-4 products
```

## 3. エージェントへの指示例

### 3.1 Coordinator Agent

```bash
# claude-code-clusterでCoordinatorを起動
cd /mnt/c/work/claude-code-cluster

# プロンプトファイルを指定して実行
./run-agent.sh \
  --agent coordinator \
  --prompt /mnt/c/work/ITDO_ERP2/docs/claude-code-cluster/coordinator-agent-prompt.md \
  --task "Phase 1: Create Gherkin scenarios for products feature based on feature brief"
```

### 3.2 Worker Agents (CC01/CC02/CC03)

```bash
# Frontend Agent (CC01)
./run-agent.sh \
  --agent cc01 \
  --prompt /mnt/c/work/ITDO_ERP2/docs/claude-code-cluster/cc01-frontend-agent-prompt.md \
  --task-packet /mnt/c/work/ITDO_ERP2/task-packets/ITDO-ERP2-phase-3-products-*-CC01.yaml

# Backend Agent (CC02)
./run-agent.sh \
  --agent cc02 \
  --prompt /mnt/c/work/ITDO_ERP2/docs/claude-code-cluster/cc02-backend-agent-prompt.md \
  --task-packet /mnt/c/work/ITDO_ERP2/task-packets/ITDO-ERP2-phase-3-products-*-CC02.yaml
```

## 4. 日々の運用フロー

### 4.1 朝のスタンドアップ

```bash
# プロジェクト全体のステータス確認
./scripts/sdad-phase-manager.sh status

# 各エージェントのタスク進捗確認
gh issue list --label "agent-task" --label "in-progress"
```

### 4.2 エージェントタスクの監視

```bash
# タスクの自動割り当て（GitHub Actions経由）
# 1. Issueにphaseラベルを付ける
# 2. 自動的にタスクパケットが生成される
# 3. エージェントがPRを作成

# PR一覧の確認
gh pr list --label "agent-task"
```

### 4.3 フェーズゲートの確認

```bash
# 特定フィーチャーのフェーズ確認
./scripts/sdad-phase-manager.sh check <issue_number>

# フェーズ要件の検証
./scripts/sdad-phase-manager.sh gate <phase> <feature>
```

## 5. トラブルシューティング

### 5.1 エージェントがスタックした場合

```yaml
# エスカレーション用Issue作成
gh issue create \
  --title "[Escalation] CC01 blocked on products implementation" \
  --body "Task ID: ITDO-ERP2-phase-4-products-20250127
  
  ## Problem
  テストケース 'test_product_validation' が原因不明のエラーで失敗
  
  ## Error Log
  ```
  AssertionError: Expected status 200, got 422
  ```
  
  ## Attempted Solutions
  1. Validation logic reviewed
  2. Test data updated
  3. API schema checked
  
  ## Request
  仕様の明確化が必要：商品コードの形式要件" \
  --label "needs-human-input,CC01,phase-4"
```

### 5.2 フェーズ間の不整合

```bash
# 全フェーズの成果物確認
find features docs tests -name "*products*" -type f | sort

# 不足している成果物の特定
./scripts/sdad-phase-manager.sh gate phase-2 products
```

### 5.3 Git Hooks が動作しない場合

```bash
# Git設定の確認
git config core.hooksPath

# 手動でフック実行
./.githooks/pre-commit
```

## 6. メトリクス収集

### 6.1 週次レポート生成

```bash
# 開発速度メトリクス
gh issue list \
  --label "phase-4" \
  --state closed \
  --json number,title,closedAt,createdAt \
  --jq '.[] | {
    issue: .number,
    title: .title,
    duration: ((.closedAt | fromdate) - (.createdAt | fromdate)) / 86400 | floor
  }'

# 手戻り率（Revert commits）
git log --oneline --grep="Revert" --since="1 week ago" | wc -l
```

### 6.2 品質メトリクス

```bash
# テストカバレッジ
cd backend && uv run pytest --cov=app --cov-report=term
cd frontend && npm run coverage

# コード量の削減率
echo "APIs: $(find backend/app/api -name "*.py" | wc -l) files"
echo "Components: $(find frontend/src/components -name "*.tsx" | wc -l) files"
```

## 7. ベストプラクティス

### 7.1 コミットメッセージ

```bash
# フェーズを明示
git commit -m "feat(phase-1): Add product management scenarios

- Define 5 user scenarios for basic CRUD
- Include edge cases for duplicate SKUs
- Add acceptance criteria for search functionality

Issue: #100"
```

### 7.2 PR作成

```bash
# エージェントタスクPRテンプレート
gh pr create \
  --title "[CC01] Phase 3: Product list component tests" \
  --body "Task_ID: ITDO-ERP2-phase-3-products-20250127

## Summary
Created failing tests for product list component following TDD approach.

## Test Coverage
- Component rendering
- User interactions
- API integration
- Error handling

## Definition of Done
- [x] All scenarios have corresponding tests
- [x] Tests are failing (Red phase)
- [x] CI/CD configured

## Next Steps
Ready for Phase 4 implementation." \
  --label "agent-task,CC01,phase-3"
```

## 8. 次のステップ

1. **今すぐ実行**:
   ```bash
   # セットアップスクリプトの実行
   make setup-sdad
   ```

2. **今日中に完了**:
   - パイロット機能のPhase 1開始
   - Coordinatorへの最初のタスク割り当て

3. **今週中に達成**:
   - Phase 1-2の完了
   - 3人のエージェントの稼働確認

Remember: 自動化は手段であり目的ではない。人間の判断と品質を最優先に。