# マルチエージェント調整ワークフロー

## 🎯 概要

複数のClaude Codeエージェントを効率的に管理するためのワークフローです。

## 📋 推奨方法

### 方法1: GitHub Issues経由の指示管理（推奨）

#### セットアップ
```bash
# 専用ラベルの作成
gh label create "claude-code-task" --description "Claude Code agents task" --color "0052CC"
gh label create "cc01" --description "For Claude Code 1" --color "1D76DB"
gh label create "cc02" --description "For Claude Code 2" --color "5319E7" 
gh label create "cc03" --description "For Claude Code 3" --color "B60205"
```

#### 指示の作成と配布
```bash
# 全エージェント向けタスク作成
gh issue create --title "【全CC】Phase 3 PR修正作業" \
  --label "claude-code-task,cc01,cc02,cc03" \
  --body "$(cat <<'EOF'
## タスク概要
Phase 3のPR修正を完了させてください。

## 担当割り当て
- **CC01**: PR #98 (Task-Department Integration)
- **CC02**: PR #97 (Role Service)  
- **CC03**: PR #95 (E2E Tests)

## 共通指示
1. 最新のmainブランチをpull
2. CI/CDエラーを修正
3. テストを全て通過させる
4. 完了したらこのIssueにコメント

## 期限
2025年7月14日
EOF
)"
```

#### 各エージェントでの実行
```bash
# Claude Code 1で実行
gh issue list --label "cc01" --state open

# 最新タスクを確認
gh issue view [ISSUE番号]

# 完了報告
gh issue comment [ISSUE番号] --body "CC01: PR #98の修正完了しました。"
```

### 方法2: 共有指示ファイルシステム

#### ディレクトリ構造
```
docs/agent-tasks/
├── active/           # アクティブなタスク
│   ├── CC01_task.md
│   ├── CC02_task.md
│   └── CC03_task.md
├── completed/        # 完了タスク
└── templates/        # タスクテンプレート
```

#### タスク作成スクリプト
```bash
#!/bin/bash
# scripts/create-agent-tasks.sh

TASK_DIR="docs/agent-tasks/active"
DATE=$(date +%Y%m%d_%H%M)

# テンプレートから生成
cat > "$TASK_DIR/CC01_task.md" << 'EOF'
# Claude Code 1 タスク

**作成日時:** DATE_PLACEHOLDER
**優先度:** 高

## 本日のタスク
1. PR #98の修正
   - backend-test失敗の解決
   - CI/CD全通過確認

## 完了条件
- [ ] 全テスト通過
- [ ] CI/CDグリーン
- [ ] PRレビュー準備完了

## 報告方法
完了したら`completed/CC01_DATE_PLACEHOLDER.md`に移動
EOF

sed -i "s/DATE_PLACEHOLDER/$DATE/g" "$TASK_DIR/CC01_task.md"
```

### 方法3: プロジェクトボード活用

```bash
# GitHubプロジェクトボードでタスク管理
# Projects → New project → "Claude Code Tasks"

# カラム構成
- Backlog（待機中）
- CC01 Active（作業中）
- CC02 Active（作業中）
- CC03 Active（作業中）
- Review（レビュー待ち）
- Done（完了）
```

### 方法4: 自動化スクリプト

#### 一括指示配布スクリプト
```bash
#!/bin/bash
# scripts/distribute-tasks.sh

# 共通指示
COMMON_INSTRUCTION="最新のmainブランチをpullしてから作業開始してください"

# 個別タスク
declare -A TASKS
TASKS[CC01]="PR #98 のbackend-test修正"
TASKS[CC02]="PR #97 のCore Foundation Tests修正"
TASKS[CC03]="PR #95 のE2E環境設定"

# GitHub Issue作成
for agent in CC01 CC02 CC03; do
  gh issue create \
    --title "【$agent】$(date +%Y%m%d) タスク" \
    --label "claude-code-task,${agent,,}" \
    --body "## 共通指示\n$COMMON_INSTRUCTION\n\n## 個別タスク\n${TASKS[$agent]}"
done
```

## 🎯 推奨運用フロー

### 朝の開始時
```bash
# 1. タスク状況確認
make agent-status  # Makefileに追加

# 2. 新規タスク作成
./scripts/distribute-tasks.sh

# 3. 各エージェントで確認
gh issue list --label "claude-code-task" --state open
```

### 作業中
```bash
# 進捗報告（各エージェント）
gh issue comment [ISSUE番号] --body "進捗: テスト修正50%完了"

# 質問・ブロッカー報告
gh issue comment [ISSUE番号] --body "🚨 ブロッカー: SQLAlchemyエラーで支援必要"
```

### 完了時
```bash
# 完了報告
gh issue close [ISSUE番号] --comment "✅ タスク完了: 全テスト通過確認"

# 次回への引き継ぎ
./scripts/create-handover.sh CC01
```

## 📊 効果測定

### Before（現在）
- 手動コピペ: 3分/エージェント
- 状態確認: 5分/回
- 合計: 約20分/日

### After（自動化後）
- タスク作成: 1分（自動）
- 状態確認: 1分（一覧表示）
- 合計: 約3分/日

**効率化率: 85%削減**

## 🔧 Makefile統合

```makefile
# エージェントタスク管理
agent-tasks:
	@./scripts/distribute-tasks.sh

agent-status:
	@echo "=== Active Claude Code Tasks ==="
	@gh issue list --label "claude-code-task" --state open

agent-report:
	@echo "=== Today's Progress ==="
	@gh issue list --label "claude-code-task" --state closed --limit 10

.PHONY: agent-tasks agent-status agent-report
```

## 💡 ベストプラクティス

1. **一貫性のある命名規則**
   - Issue: `【CC01】YYYY-MM-DD タスク概要`
   - Label: `cc01`, `cc02`, `cc03`

2. **定型フォーマット使用**
   - タスク概要
   - 成功条件
   - 期限
   - 依存関係

3. **自動化の活用**
   - GitHub Actions
   - シェルスクリプト
   - Makefile統合

4. **可視化**
   - プロジェクトボード
   - 進捗ダッシュボード
   - 日次レポート

---

*このワークフローにより、マルチエージェント管理の効率が大幅に向上します。*