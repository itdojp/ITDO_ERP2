# CC02 Database専門エージェント 再開指示

## 状況確認
- **最終確認**: CC02は停止中、タスク待機状態
- **優先度**: HIGH - 即座のアクティベーションが必要

## 🚨 緊急対応事項

### 1. アクティベーション確認
**タスク**: CC02の稼働状態確認と初期設定
```bash
# セッション初期化
cd /mnt/c/work/ITDO_ERP2
source scripts/agent-config/sonnet-default.sh

# 割り当てタスクの確認
gh issue view 134 --repo itdojp/ITDO_ERP2
```

### 2. Phase 4/5 Advanced Foundation Research
**タスク**: Issue #134の継続実行
- データベース最適化の研究
- 高度な基盤技術の調査
- パフォーマンス改善の実装

## 📋 継続タスク

### 即座に実行するタスク
1. **Issue #134**: 🛠️ CC02 Phase 4/5 Advanced Foundation Research
   - データベース最適化戦略の立案
   - インデックス戦略の改善
   - クエリパフォーマンスの分析

2. **PR #124**: Edge case tests for User Service authentication
   - データベースレベルでの認証テスト
   - SQLインジェクション対策の確認
   - パフォーマンステストの追加

3. **データベース関連の技術負債解決**
   - SQL最適化
   - データ整合性の確保
   - バックアップ戦略の改善

## 🔄 作業プロトコル

### Sonnet Model確認
```bash
# 環境設定確認
echo $CLAUDE_MODEL  # claude-3-5-sonnet-20241022であることを確認
export CLAUDE_AGENT_MODE="database_specialist"
export AGENT_ID="CC02"
export AGENT_SPECIALIZATION="Database Specialist"
```

### データベース接続確認
```bash
# データベース接続テスト
make start-data
python -c "
from app.core.database import get_db_session
try:
    db = next(get_db_session())
    print('✅ Database connection successful')
    db.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### エスカレーション基準
- **データ整合性問題**: 即座にエスカレーション
- **パフォーマンス劣化**: 30分以上改善できない場合
- **セキュリティ問題**: 即座にエスカレーション

## 🎯 成果目標

### 今日の目標
- [ ] Issue #134のPhase 4/5研究完了
- [ ] データベース最適化の実装
- [ ] PR #124のレビューと改善
- [ ] パフォーマンスメトリクスの改善

### 品質基準
- データベースクエリ最適化率 >25%
- インデックス効率性の改善
- データ整合性テスト通過
- バックアップ戦略の文書化

## 📊 進捗報告

### 報告タイミング
- 1時間ごとの進捗報告
- 重要な発見があった場合の即時報告
- 完了時の最終報告

### 報告形式
```bash
gh issue comment 134 --repo itdojp/ITDO_ERP2 --body "🤖 CC02 Database Progress Report:
- Status: [現在の状況]
- Database Performance: [パフォーマンス改善状況]
- Completed: [完了した作業]
- Next: [次のアクション]
- Metrics: [測定結果]"
```

## 🚀 開始コマンド

```bash
# 1. 環境確認とアクティベーション
cd /mnt/c/work/ITDO_ERP2
git status
source scripts/agent-config/sonnet-default.sh

# 2. データベース環境の起動
make start-data
make status

# 3. 割り当てタスクの確認
gh issue view 134 --repo itdojp/ITDO_ERP2

# 4. 作業開始の報告
gh issue comment 134 --repo itdojp/ITDO_ERP2 --body "🤖 CC02 Database Specialist - Session Started
- Environment: Activated
- Database: Connected
- Task: Phase 4/5 Advanced Foundation Research
- Action: Starting analysis and optimization work"
```

## 🔧 専門技術フォーカス

### データベース最適化領域
- **クエリ最適化**: 実行計画の分析と改善
- **インデックス戦略**: 適切なインデックスの設計と実装
- **データ整合性**: 制約とトランザクションの最適化
- **パフォーマンス監視**: メトリクス収集とボトルネック特定

### セキュリティ強化
- **SQLインジェクション対策**: パラメータ化クエリの徹底
- **認証・認可**: データベースレベルでのアクセス制御
- **監査ログ**: データベース操作の追跡可能性

---

⚡ **緊急度**: HIGH - データベース最適化が開発効率に直結  
🎯 **目標**: Phase 4/5研究完了とパフォーマンス改善  
⏰ **期限**: 即座に開始、1時間以内に初期報告

🤖 CC02 Database Specialist - Advanced Foundation Research Protocol