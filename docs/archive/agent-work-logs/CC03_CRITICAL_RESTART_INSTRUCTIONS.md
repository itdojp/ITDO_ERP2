# CC03 Frontend専門エージェント 緊急再開指示

## 🚨 緊急状況
- **最終確認**: CC03は30分以上無応答 (Issue #132)
- **優先度**: **CRITICAL** - エスカレーション対応が必要

## ⚠️ 緊急対応プロトコル

### 1. 即座の状況確認
**タスク**: CC03の応答性確認と状況報告
```bash
# 緊急セッション開始
cd /mnt/c/work/ITDO_ERP2
source scripts/agent-config/sonnet-default.sh

# エスカレーション対応
gh issue comment 132 --repo itdojp/ITDO_ERP2 --body "🚨 CC03 EMERGENCY RESPONSE:
- Status: Agent CC03 back online
- Time: $(date)
- Priority: Addressing escalation immediately
- Action: Investigating previous non-response"
```

### 2. インフラ改善成果の確認
**タスク**: Issue #135で報告した改善内容の検証
- CI/CD Performance: 60-70% improvement
- Development Environment: 75% startup time reduction
- Monitoring: Prometheus + Grafana system
- Scalability: Architecture design

## 📋 緊急対応タスク

### 即座に実行するタスク
1. **Issue #132**: エスカレーション対応
   - 無応答の原因分析
   - 他エージェントとの協調確認
   - 緊急度の評価

2. **Issue #135**: Development Infrastructure Revolution
   - インフラ改善の最終確認
   - 監視システムの稼働確認
   - パフォーマンス改善の検証

3. **CI/CD Pipeline問題への対応**
   - フロントエンド関連の CI/CD 問題の調査
   - ビルド失敗の原因特定
   - 修正の実装

## 🔄 作業プロトコル

### Sonnet Model確認
```bash
# 環境設定確認
echo $CLAUDE_MODEL  # claude-3-5-sonnet-20241022であることを確認
export CLAUDE_AGENT_MODE="frontend_specialist"
export AGENT_ID="CC03"
export AGENT_SPECIALIZATION="Frontend Specialist"
```

### フロントエンド環境確認
```bash
# フロントエンド環境の確認
cd frontend
npm run typecheck
npm run lint
npm test
```

### エスカレーション基準
- **即座のエスカレーション**: 技術的問題が解決できない場合
- **定期報告**: 15分間隔での進捗報告
- **完了報告**: 各タスク完了時の即時報告

## 🎯 成果目標

### 緊急目標 (次の1時間以内)
- [ ] エスカレーション対応の完了
- [ ] CI/CDパイプライン問題の調査
- [ ] インフラ改善の検証
- [ ] 他エージェントとの協調回復

### 品質基準
- TypeScript厳密チェック通過
- フロントエンドテスト通過
- CI/CDパイプライン正常化
- パフォーマンス改善の維持

## 📊 進捗報告

### 報告タイミング
- **即座**: エスカレーション対応状況
- **15分間隔**: 継続的な進捗報告
- **完了時**: 最終報告

### 報告形式
```bash
gh issue comment 132 --repo itdojp/ITDO_ERP2 --body "🚨 CC03 CRITICAL STATUS:
- Response Time: [応答時間]
- Current Task: [現在のタスク]
- Progress: [進捗状況]
- Next Action: [次のアクション]
- Escalation: [エスカレーション必要性]"
```

## 🚀 緊急開始コマンド

```bash
# 1. 緊急セッション開始
cd /mnt/c/work/ITDO_ERP2
git status
source scripts/agent-config/sonnet-default.sh

# 2. エスカレーション対応の開始
gh issue comment 132 --repo itdojp/ITDO_ERP2 --body "🚨 CC03 EMERGENCY RESPONSE INITIATED:
- Agent: CC03 Frontend Specialist
- Status: BACK ONLINE
- Time: $(date)
- Priority: CRITICAL - Addressing escalation
- Action: Investigating infrastructure and CI/CD issues"

# 3. 現在の状況確認
gh issue view 132 --repo itdojp/ITDO_ERP2
gh issue view 135 --repo itdojp/ITDO_ERP2

# 4. CI/CD状況確認
gh run list --repo itdojp/ITDO_ERP2 --limit 5
```

## 🔧 専門技術フォーカス

### フロントエンド最適化
- **ビルドパフォーマンス**: Vite設定の最適化
- **TypeScript**: 厳密型チェックの維持
- **テスト**: Vitest + React Testing Library
- **CI/CD**: GitHub Actions の最適化

### インフラ監視
- **Prometheus**: メトリクス収集の確認
- **Grafana**: ダッシュボードの動作確認
- **パフォーマンス**: 75%改善の維持

## ⚡ 緊急連絡

### 重要事項
1. **応答性**: 15分以内の定期報告必須
2. **エスカレーション**: 技術的問題は即座に報告
3. **協調**: CC01, CC02との連携確認
4. **品質**: 緊急時でも品質基準を維持

---

🚨 **緊急度**: **CRITICAL** - 30分以上無応答によるエスカレーション  
🎯 **目標**: エスカレーション解決とインフラ安定化  
⏰ **期限**: 即座に開始、15分以内に初期報告

🤖 CC03 Frontend Specialist - Emergency Response Protocol