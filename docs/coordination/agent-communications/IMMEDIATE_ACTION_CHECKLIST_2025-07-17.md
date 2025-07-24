# ⚡ 即座実行チェックリスト

**作成日時**: 2025年7月17日 20:55 JST  
**対象**: CC01, CC02, CC03  
**目的**: 10分以内に全エージェント再起動

## 🎯 CC01 即座実行リスト

### ✅ 今すぐ実行 (コピペ可能)
```bash
# 1. 生存確認 (1分)
echo "CC01 restart at $(date)" > frontend/CC01_RESTART.md
git add frontend/CC01_RESTART.md
git commit -m "🎨 CC01: Agent restart confirmation"

# 2. ブランチ作成 (1分)
git checkout main
git pull origin main
git checkout -b feature/issue-174-ui-components-phase1

# 3. 最初のファイル作成 (3分)
mkdir -p frontend/src/components/ui/Button
touch frontend/src/components/ui/Button/Button.tsx
touch frontend/src/components/ui/Button/Button.test.tsx
touch frontend/src/components/ui/Button/index.ts

# 4. 最初のコミット (1分)
git add frontend/src/components/ui/Button/
git commit -m "feat: Initialize Button component structure for Issue #174"

# 5. 実装開始メッセージ
echo "Starting Issue #174 implementation..."
```

### 📝 Button.tsx スターターコード
```typescript
// frontend/src/components/ui/Button/Button.tsx
import React from 'react';

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  loading = false,
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};
```

---

## 🎯 CC02 即座実行リスト

### ✅ 今すぐ実行 (コピペ可能)
```bash
# 1. 生存確認 (1分)
echo "CC02 restart at $(date)" > backend/CC02_RESTART.md
git add backend/CC02_RESTART.md
git commit -m "🔧 CC02: Agent restart confirmation"

# 2. ブランチ作成 (1分)
git checkout main
git pull origin main
git checkout -b feature/issue-46-security-audit

# 3. 最初のファイル作成 (3分)
touch backend/app/models/audit_log.py
touch backend/app/api/v1/audit_logs.py
touch backend/app/schemas/audit_log.py

# 4. 最初のコミット (1分)
git add backend/app/models/audit_log.py backend/app/api/v1/audit_logs.py backend/app/schemas/audit_log.py
git commit -m "feat: Initialize audit log structure for Issue #46"

# 5. 実装開始メッセージ
echo "Starting Issue #46 implementation..."
```

### 📝 audit_log.py スターターコード
```python
# backend/app/models/audit_log.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    status = Column(String(20), default="success")
    details = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
```

---

## 🎯 CC03 即座実行リスト

### ✅ 今すぐ実行 (Read/Write/Edit使用)

#### 1. 生存確認 (Write使用 - 1分)
```yaml
Write ツール使用:
  ファイル: docs/CC03_RESTART.md
  内容: |
    # CC03 Restart Confirmation
    
    Date: 2025-07-17 20:55 JST
    Agent: CC03 (Infrastructure/Testing)
    Status: Active and ready
    
    Starting Issue #173: 自動割り当てシステムの改善
```

#### 2. 現状確認 (Read使用 - 3分)
```yaml
Read ツール使用:
  1. .github/workflows/label-processor.yml
  2. .github/workflows/claude-pm-automation.yml
  3. docs/coordination/README.md
```

#### 3. 改善案作成 (Write使用 - 5分)
```yaml
Write ツール使用:
  ファイル: .github/workflows/improved-label-processor.yml
  内容: |
    name: Improved Label-Based Issue Processor
    
    on:
      issues:
        types: [opened, labeled, unlabeled, reopened]
    
    jobs:
      process-issue:
        runs-on: ubuntu-latest
        steps:
          - name: Check processing eligibility
            id: check
            uses: actions/github-script@v6
            with:
              script: |
                const issue = context.payload.issue;
                const labels = issue.labels.map(l => l.name);
                
                // Processing labels
                const processingLabels = [
                  'claude-code-frontend',
                  'claude-code-backend',
                  'claude-code-infrastructure',
                  'claude-code-testing',
                  'claude-code-security',
                  'claude-code-database'
                ];
                
                // Exclusion labels
                const exclusionLabels = [
                  'work-in-progress',
                  'blocked',
                  'on-hold',
                  'needs-discussion'
                ];
                
                const shouldProcess = processingLabels.some(l => labels.includes(l)) &&
                                    !exclusionLabels.some(l => labels.includes(l));
                
                console.log(`Should process: ${shouldProcess}`);
                return shouldProcess;
```

#### 4. テストケース作成 (Write使用 - 3分)
```yaml
Write ツール使用:
  ファイル: tests/github-actions/test-label-processor.md
  内容: |
    # Label Processor Test Cases
    
    ## Test 1: Processing Label Detection
    - Add 'claude-code-frontend' → Should process
    - Add 'claude-code-backend' → Should process
    
    ## Test 2: Exclusion Label Blocking
    - Add 'blocked' → Should NOT process
    - Add 'work-in-progress' → Should NOT process
    
    ## Test 3: Combined Labels
    - 'claude-code-frontend' + 'blocked' → Should NOT process
    - 'claude-code-backend' + 'enhancement' → Should process
```

---

## 🚀 10分後の期待状態

### ✅ 達成すべきチェックポイント

#### 全エージェント共通
- [ ] 生存確認コミット完了
- [ ] 作業ブランチ作成完了
- [ ] 最初のファイル作成完了
- [ ] 実装開始の準備完了

#### CC01 (21:05までに)
- [ ] Button componentディレクトリ作成
- [ ] 基本的なTypeScript型定義
- [ ] 最初のコンポーネント実装開始

#### CC02 (21:05までに)
- [ ] audit_logモデル作成
- [ ] 基本的なスキーマ定義
- [ ] APIエンドポイント準備

#### CC03 (21:05までに)
- [ ] 現在のワークフロー分析完了
- [ ] 改善案の作成開始
- [ ] テストケース定義

## 📞 トラブルシューティング

### もし応答がない場合
1. **5分待機**: エージェントの自然な反応を待つ
2. **簡略化指示**: より単純なタスクから開始
3. **代替手段**: 別のアプローチを提示

### 技術的問題が発生した場合
1. **エラーログ確認**: 具体的なエラー内容を特定
2. **回避策提示**: 代替実装方法を提案
3. **優先度調整**: ブロッカーのないタスクへ切り替え

---

**⏰ 開始時刻**: 2025年7月17日 20:55 JST  
**⏰ 確認時刻**: 2025年7月17日 21:05 JST (10分後)  
**🎯 成功基準**: 全エージェントが実装を開始している状態