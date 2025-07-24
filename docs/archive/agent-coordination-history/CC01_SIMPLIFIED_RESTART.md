# CC01 Backend Specialist - 簡潔再開指示

## 🎯 最重要事項
**Usage Policy違反を避けるため、タスクの重複実行を絶対に回避**

## 📋 即座の実行タスク

### 1. Issue #137: Department Management Enhancement
```bash
# 環境確認
cd /mnt/c/work/ITDO_ERP2
source scripts/agent-config/sonnet-default.sh

# Issue確認（1回のみ）
gh issue view 137 --repo itdojp/ITDO_ERP2

# 作業開始
git checkout -b feature/issue-137-department-management
```

### 2. 実装方針
- **単一実行**: 各コマンドは1回のみ実行
- **効率的実装**: 最小限のコードで要件を満たす
- **Sonnetモデル使用**: コスト最適化

### 3. 品質基準
- テストカバレッジ >80%
- 型安全性の確保
- エラーハンドリング必須

## 🚫 禁止事項
- 同じタスクの繰り返し実行
- 複雑なフレームワークの構築
- メタディスカッション

## ✅ 完了報告
```bash
# 進捗報告（1日1回）
gh issue comment 137 --repo itdojp/ITDO_ERP2 --body "🤖 CC01: Department Management実装完了"
```

---
**制限時間**: 30分以内
**エスカレーション**: 技術的ブロックは即座に報告