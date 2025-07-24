# 即座実行アクション - 最小限版

## 🚨 今すぐ実行（各エージェント1コマンドから開始）

### CC01 (Backend Specialist)
```bash
gh issue view 137 --repo itdojp/ITDO_ERP2
```
**次**: Department Management実装開始

### CC02 (Database Specialist)
```bash
gh pr view 97 --repo itdojp/ITDO_ERP2
```
**次**: データベース側面の5分確認

### CC03 (Frontend Specialist)
```bash
gh issue view 138 --repo itdojp/ITDO_ERP2
```
**次**: UI Component実装開始

## ⚠️ 重要な注意事項

### Usage Policy違反の回避
1. **各コマンドは1回のみ実行**
2. **同じタスクを繰り返さない**
3. **30分で完了できるタスクのみ選択**

### 成功のための3原則
1. **Simple**: 複雑にしない
2. **Direct**: 直接的に実装
3. **Once**: 一度で完了

## 📊 本日の目標

### 最小限の成功基準
- [ ] 各エージェント1タスク着手
- [ ] Usage違反: 0件
- [ ] 実装時間: 30分以内/タスク

### 報告フォーマット（シンプル）
```bash
# 完了時のみ報告
gh issue comment [ISSUE_NUMBER] --repo itdojp/ITDO_ERP2 --body "✅ 完了"
```

## 🔧 claude-code-cluster活用

### 新しいツールの利用
```bash
# コマンドロギング確認
python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --stats

# 自動ループシステム（必要時のみ）
python3 /tmp/claude-code-cluster/hooks/universal-agent-auto-loop-with-logging.py CC01 itdojp ITDO_ERP2 --max-iterations 1
```

---

**開始方法**: 上記の最初のコマンドを実行
**制限時間**: 各タスク30分
**成功指標**: 1タスク完了 > 0タスク分析