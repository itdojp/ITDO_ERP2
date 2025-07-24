# 🎯 実効的エージェント指示 - 現実的アプローチ

**作成日時**: 2025年7月17日 22:45 JST  
**作成者**: Claude Code (CC01) - システム統合担当  
**目的**: 停止中エージェントへの実効的な指示

## 📢 CC03への緊急指示

### フェーズ1: 生存確認（10分以内）

```markdown
@cc03

緊急タスク: 最小限の生存確認を実施してください。

手順:
1. .github/workflows/cc03-alive.yml を作成
2. 内容は echo "CC03 is alive" のみ
3. git add, commit, push
4. 完了報告

成功基準: 10分以内にコミットが確認できれば成功
```

### フェーズ2: Issue #173の最小実装（30分以内）

```markdown
@cc03

フェーズ1成功後のタスク:

Issue #173の最小実装:
1. .github/auto-assign.yml に1行追加
2. `# TODO: Add assignee logic` とコメント追加
3. コミットしてPR作成
4. 「[WIP] #173: Auto-assign improvement - Phase 1」というタイトル

ポイント: 完璧でなくても良い。まず動くことを優先。
```

### フェーズ3: 継続的活動（1時間以内）

```markdown
@cc03

フェーズ2成功後:

次のタスクリストから1つ選んで実施:
1. Issue #174のButtonコンポーネントの雛形作成
2. CI/CDワークフローにコメント追加
3. README.mdに「Last updated by CC03: [date]」追加

選んだタスクを1つ完了させること。
```

## 📢 CC01/CC02へのシンプル指示

### CC01への初動指示

```markdown
@cc01

シンプルタスク:
1. frontend/docs/CC01_ACTIVE.md を作成
2. 内容: "CC01 Frontend Agent Active - [current date]"
3. git add && git commit -m "chore: CC01 activation confirmation"
4. 完了報告

成功後はフロントエンドの簡単なタスクを割り当てます。
```

### CC02への初動指示

```markdown
@cc02

シンプルタスク:
1. backend/docs/CC02_ACTIVE.md を作成
2. 内容: "CC02 Backend Agent Active - [current date]"
3. git add && git commit -m "chore: CC02 activation confirmation"
4. 完了報告

成功後はAPIの簡単なタスクを割り当てます。
```

## 📋 成功判定基準

### 即座の成功指標（30分以内）
- ✅ 少なくとも1エージェントからコミット
- ✅ ファイル作成または変更確認
- ✅ Gitログに記録

### 短期成功指標（24時間以内）
- ✅ 3エージェント全てが活動
- ✅ 割り当てたタスクの進捗
- ✅ 継続的なコミット

### 失敗時の対処
1. **30分無応答**: 別の最小タスクを試す
2. **1時間無応答**: 人間介入を検討
3. **24時間無応答**: エージェントシステムの根本的見直し

## 🔧 サポートツール

### 活動チェックスクリプト
```bash
#!/bin/bash
# scripts/check-agent-activity.sh

echo "=== Agent Activity Check ==="
echo "Time: $(date)"
echo ""

# Check commits
echo "Recent Agent Commits:"
git log --oneline --since="1 hour ago" --author="CC0[123]" | head -5

# Check files
echo -e "\nAgent Status Files:"
ls -la **/CC0*_*.md 2>/dev/null || echo "No status files found"

echo -e "\n=== End of Check ==="
```

### 緊急リセット手順
```bash
# 全エージェントの最小タスクを作成
gh issue create --title "chore: Agent health check" \
  --body "Add a status file confirming agent is active" \
  --label "cc01,cc02,cc03,good-first-issue"
```

## 💡 重要なポイント

### 成功の鍵
1. **極度にシンプル**: 1ファイル、1行から
2. **即座のフィードバック**: 30分以内に判断
3. **明確な成功基準**: コミットがあれば成功

### 避けるべきこと
1. **複雑な並行作業**: 1つずつ確実に
2. **完璧主義**: 動くことが最優先
3. **長時間の待機**: 30分で判断

## 🌟 結論

エージェントシステムを再起動するため、最もシンプルなタスクから開始します。
成功を確認したら段階的に拡大し、失敗したら早期に別案へ移行します。

人間の開発が順調に進んでいるため、エージェントは補助的な役割から
再開し、将来的により重要なタスクを担当できるよう段階的に成長させます。

---

**📌 最優先アクション**: CC03の生存確認タスクから開始