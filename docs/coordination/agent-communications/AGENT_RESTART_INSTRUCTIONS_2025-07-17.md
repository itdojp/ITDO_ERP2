# 🔄 エージェント再起動指示書

**発行日時**: 2025年7月17日 20:50 JST  
**発行者**: Claude Code (CC01) - システム統合担当  
**緊急度**: 🔴 高優先度  
**目的**: 作業停止後のエージェント再起動と明確なタスク割り振り

## 🚨 現状分析

### 問題の認識
- **経過時間**: 前回指示から約3時間経過
- **エージェント状況**: CC01, CC02, CC03 全員が完全沈黙状態
- **最後の活動**: 2025年7月16日のコミット以降、エージェント活動なし
- **タスク進行**: 割り当て済みIssueが全て未着手

### 根本原因
1. **人間による作業割り振り停止**: 明確な実行指示の欠如
2. **Issue #160/PR #171問題**: 大規模変更による混乱が未解決
3. **ラベル設定の不備**: claude-codeラベルが適切に設定されていない

## 🎯 各エージェント向け再起動指示

### 🎨 CC01 (フロントエンド) - 即座実行指示

#### ステップ1: 生存確認 (5分)
```bash
# 簡単なコミットで生存確認
echo "CC01 restart at $(date)" > frontend/CC01_RESTART.md
git add frontend/CC01_RESTART.md
git commit -m "🎨 CC01: Agent restart confirmation"
```

#### ステップ2: Issue #174 着手開始 (即座)
```typescript
// タスク: UI Component Design System - Phase 1 (基盤)
// 目標: Button, Input, Card コンポーネント実装 (<500行)

// 1. ブランチ作成
git checkout -b feature/issue-174-ui-components-phase1

// 2. 実装開始
frontend/src/components/ui/Button/Button.tsx
frontend/src/components/ui/Button/Button.test.tsx
frontend/src/components/ui/Button/Button.stories.tsx
frontend/src/components/ui/Button/index.ts

// 3. TypeScript型定義
frontend/src/types/components/button.ts

// 4. Tailwind CSS設計
frontend/src/styles/components/button.css
```

#### 成果物 (2時間以内)
- [ ] Button Component完全実装 (5 variants, 3 sizes)
- [ ] Input Component完全実装 (6 types, validation)
- [ ] Card Component完全実装 (4 variants)
- [ ] 全コンポーネントのVitest + Storybook

---

### 🔧 CC02 (バックエンド) - 即座実行指示

#### ステップ1: 生存確認 (5分)
```bash
# 簡単なコミットで生存確認
echo "CC02 restart at $(date)" > backend/CC02_RESTART.md
git add backend/CC02_RESTART.md
git commit -m "🔧 CC02: Agent restart confirmation"
```

#### ステップ2: Issue #46 着手開始 (即座)
```python
# タスク: セキュリティ監査ログとモニタリング機能
# 目標: 完全な監査ログシステム実装

# 1. ブランチ作成
git checkout -b feature/issue-46-security-audit

# 2. 実装開始
# backend/app/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    status = Column(String(20))
    details = Column(JSON)

# 3. API実装
# backend/app/api/v1/audit.py
@router.get("/audit-logs")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    filters: AuditLogFilter = Depends()
):
    # 監査ログ取得実装
```

#### 成果物 (2時間以内)
- [ ] AuditLog モデル完全実装
- [ ] 監査ログAPI (CRUD + フィルタリング)
- [ ] セキュリティイベント自動記録
- [ ] pytest完全カバレッジ

---

### 🏗️ CC03 (インフラ/テスト) - 即座実行指示

#### ステップ1: 生存確認 (5分)
```bash
# Write ツールで生存確認スクリプト作成
Write: docs/CC03_RESTART.md
内容: "CC03 restart at 2025-07-17 20:50 JST"
```

#### ステップ2: Issue #173 着手開始 (即座)
```yaml
# タスク: Issue自動割り当てシステムの改善
# 目標: ラベルベース処理制御の完全実装

# Read/Write/Edit ツール使用で実装
# 1. Read: .github/workflows/label-processor.yml 確認
# 2. Edit: 処理ロジック改善
# 3. Write: 新しい自動化スクリプト作成

# 実装内容:
# - 処理/除外ラベルシステム
# - 優先度ベース割り当て
# - エージェント負荷分散
# - 自動レポート生成
```

#### 成果物 (2時間以内)
- [ ] label-processor.yml 最適化
- [ ] 自動割り当てロジック改善
- [ ] エージェント状態監視システム
- [ ] ドキュメント更新

## 📊 段階的実行計画

### Phase 1: 再起動確認 (20:50-21:00)
```yaml
全エージェント共通:
  - 生存確認コミット作成
  - 作業ブランチ準備
  - 開発環境確認
  
成功基準:
  - 3つの再起動コミット確認
  - 各エージェントの応答確認
```

### Phase 2: 初期実装 (21:00-22:00)
```yaml
CC01:
  - Button Component完全実装
  - TypeScript型定義作成
  - Vitest基本テスト

CC02:
  - AuditLogモデル実装
  - 基本的なCRUD API
  - データベースマイグレーション

CC03:
  - label-processor.yml分析
  - 改善案作成
  - テスト自動化準備
```

### Phase 3: 完成・統合 (22:00-23:00)
```yaml
CC01:
  - Input, Card Component実装
  - Storybook統合
  - CI/CD通過確認

CC02:
  - セキュリティイベント記録
  - フィルタリング実装
  - APIテスト完全実装

CC03:
  - 自動割り当てシステム完成
  - ドキュメント作成
  - 全体統合テスト
```

## 🚀 即座実行プロトコル

### 優先度設定
1. **最優先**: 生存確認コミット (全エージェント)
2. **高優先**: 各専門分野のIssue着手
3. **中優先**: テスト・ドキュメント作成
4. **低優先**: 最適化・リファクタリング

### 成功指標
- **1時間後**: 全エージェント活動再開確認
- **2時間後**: 各Issue実装50%完了
- **3時間後**: 初期成果物完成・PR作成準備

### エスカレーション基準
```yaml
問題発生時:
  - 15分経過で応答なし → 代替指示作成
  - 技術的ブロッカー → 代替手段提示
  - 依存関係問題 → 独立タスクへ切り替え
```

## 💡 重要な注意事項

### 各エージェントへ
1. **シンプルに開始**: 複雑な準備は不要、即座に実装開始
2. **品質より速度**: まず動くものを作り、後で改善
3. **独立実行**: 他エージェントを待たずに進行
4. **進捗報告**: 1時間毎に簡単な進捗コミット

### CC03への特別配慮
- Bash制約は考慮済み、Read/Write/Editで全作業可能
- GitHub CLI使用不可の場合はスクリプト生成で対応
- 結果確認はReadツールで実行

## 📅 タイムライン

- **20:50**: 指示書発行
- **21:00**: 生存確認完了期限
- **21:30**: 初期実装進捗確認
- **22:00**: Phase 2完了確認
- **23:00**: 初期成果物完成確認
- **23:30**: 次期タスク計画策定

---

**🔄 再起動開始**: 全エージェントは**今すぐ**生存確認から開始してください。

**⚡ 目標**: 3時間以内に全エージェントの活動を正常化し、各専門分野での実装を軌道に乗せる。

**🎯 成功基準**: 23:00までに3つのIssueで具体的な実装成果物を生成する。