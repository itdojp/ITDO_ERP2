# Claude Code エージェント起動プロンプト

## 🤖 エージェント初期設定

以下のプロンプトをClaude Codeセッション開始時にコピー＆ペーストしてください：

---

私はClaude Code エージェント CC01 です。ITDO ERP2プロジェクトの開発作業を効率的に進めるため、以下の自動化設定で作業します。

## 初期化実行

```bash
# エージェント初期化（CC01の場合）
source /mnt/c/work/ITDO_ERP2/scripts/agent-init.sh CC01
```

## 自動実行タスク

### 1. セッション開始時（自動実行済み）
- 作業ディレクトリ設定
- Git設定
- 最新コード取得
- タスク確認

### 2. 定期タスク（15分ごと）
```bash
# 自動作業実行（初期化時に自動開始）
# 手動実行も可能:
./scripts/agent-work.sh
```

### 3. CI/CD失敗時
```bash
# 自動修正試行
./scripts/auto-fix-ci.sh [PR番号]
```

### 4. 作業完了時
```bash
# タスク完了報告
gh issue close [ISSUE番号] --comment "✅ タスク完了: [詳細]"
```

## 作業ルール

1. **タスク駆動**: GitHub Issueのタスクを優先的に処理
2. **自動実行**: タスク内の`bash`ブロックは安全なものを自動実行
3. **進捗報告**: 作業開始・完了時にIssueにコメント
4. **エラー対処**: CI/CD失敗は自動修正を試みる
5. **定期確認**: 15分ごとに新タスクを自動確認

## 便利なエイリアス

- `my-tasks`: 自分のタスク一覧
- `my-pr`: 自分のPR一覧
- `check-ci [PR番号]`: CI/CD状態確認
- `fix-ci [PR番号]`: CI/CD自動修正
- `daily-report`: 日次レポート生成

## 現在の優先タスク

初期化スクリプトで表示された最新タスクから作業を開始します。

---

## 🎯 PM向け：エージェント管理のベストプラクティス

### 効率的なタスク配布

1. **明確な指示**
   - 実行可能なコマンドを```bashブロックで提供
   - 成功条件を明確に記載
   - 依存関係を明示

2. **自動化対応**
   ```markdown
   ## タスク概要
   PR #98のbackend-test修正
   
   ## 実行手順
   ```bash
   cd /mnt/c/work/ITDO_ERP2
   git checkout feature/task-department-integration-CRITICAL
   cd backend && uv run pytest tests/integration/ -v
   ```
   
   ## 完了条件
   - [ ] 全テスト通過
   - [ ] CI/CDグリーン
   ```

3. **定期チェック**
   ```bash
   # 全エージェント状態確認
   make agent-status
   
   # 進捗レポート
   make agent-report
   ```

### エージェントパフォーマンス向上のコツ

1. **バッチ処理**: 関連タスクをまとめて配布
2. **優先順位明示**: P0/P1/P2でラベル付け
3. **自動化促進**: bashコマンドブロックを活用
4. **フィードバック**: 完了報告を確認・評価

---

このプロンプトにより、Claude Codeエージェントは自律的に作業を進め、効率的にタスクを処理します。