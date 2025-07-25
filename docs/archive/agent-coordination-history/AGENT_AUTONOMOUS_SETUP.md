# エージェント自律動作セットアップガイド

## 概要
claude-code-clusterの自動ループシステムを使用して、エージェントが自律的にタスクを処理できるようにします。

## セットアップ手順

### 1. CC01用自動ループ起動
```bash
cd /tmp/claude-code-cluster
python3 hooks/universal-agent-auto-loop-with-logging.py CC01 itdojp ITDO_ERP2 \
  --specialization "Security & Documentation Specialist" \
  --labels security documentation \
  --keywords security audit docs readme \
  --max-iterations 5 \
  --cooldown 300
```

### 2. CC02用自動ループ起動
```bash
cd /tmp/claude-code-cluster
python3 hooks/universal-agent-auto-loop-with-logging.py CC02 itdojp ITDO_ERP2 \
  --specialization "Backend Performance Engineer" \
  --labels backend performance optimization \
  --keywords api database cache performance \
  --max-iterations 5 \
  --cooldown 300
```

### 3. CC03用自動ループ起動（再起動後）
```bash
cd /tmp/claude-code-cluster
python3 hooks/universal-agent-auto-loop-with-logging.py CC03 itdojp ITDO_ERP2 \
  --specialization "Frontend & CI/CD Engineer" \
  --labels frontend ci-cd testing \
  --keywords frontend test ci pipeline \
  --max-iterations 5 \
  --cooldown 300
```

## モニタリング

### リアルタイムログ監視
```bash
# 全エージェントのログを監視
python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --follow

# 特定エージェントのログ
python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --agent CC01-ITDO_ERP2 --follow
```

### 統計情報確認
```bash
# 実行統計
python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --stats

# エージェント別統計
python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --agent CC02-ITDO_ERP2 --stats
```

## 自動タスク優先順位

1. **🔴 緊急**: CI/CD修正、ビルド失敗対応
2. **🟡 高**: セキュリティ脆弱性、パフォーマンス問題
3. **🟢 中**: ドキュメント更新、コード最適化
4. **🔵 低**: リファクタリング、改善提案

## 停止条件
- max-iterations到達
- 利用可能なタスクがない
- エラーの連続発生

## トラブルシューティング

### エージェントが停止した場合
1. ログを確認: `view-command-logs.py`
2. エラー内容を確認
3. 必要に応じて手動で再起動

### タスクが見つからない場合
1. GitHubのラベルを確認
2. キーワードマッチングを調整
3. 手動でイシューを作成

---
作成: 2025-07-15 16:30 JST