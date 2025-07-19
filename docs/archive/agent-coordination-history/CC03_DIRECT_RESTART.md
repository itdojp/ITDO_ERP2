# CC03 Frontend Specialist - 直接実行指示

## 🎯 単一タスク

### Issue #138: UI Component Enhancement
```bash
# 環境設定
cd /mnt/c/work/ITDO_ERP2/frontend
export CLAUDE_MODEL="claude-3-5-sonnet-20241022"

# Issue確認（1回のみ）
gh issue view 138 --repo itdojp/ITDO_ERP2

# TypeScript確認
npm run typecheck
```

## 🔧 実装要件
- React 18 + TypeScript 5
- 厳密型（`any`禁止）
- Tailwind CSS使用

## 🚫 禁止事項
- タスクの繰り返し
- 複雑なアーキテクチャ議論

## ✅ 完了基準
```bash
# テスト実行（1回）
npm test

# 報告
gh issue comment 138 --repo itdojp/ITDO_ERP2 --body "🤖 CC03: UI Component実装完了"
```

---
**制限時間**: 30分
**フォーカス**: UI実装のみ