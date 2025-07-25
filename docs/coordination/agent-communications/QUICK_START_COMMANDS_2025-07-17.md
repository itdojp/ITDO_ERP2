# ⚡ クイックスタートコマンド集

**作成時刻**: 2025-07-17 21:15 JST  
**目的**: 即座コピペ実行可能なコマンド集

## 🎨 CC01 - 今すぐコピペ実行

### Step 1: 基本セットアップ (1分)
```bash
# 実行開始宣言
echo "[$(date)] CC01 Starting UI Components Phase 1" >> frontend/CC01_LOG.txt

# ブランチ作成
git checkout main && git pull
git checkout -b feature/issue-174-ui-components-phase1

# ディレクトリ構造作成
mkdir -p frontend/src/components/ui/{Button,Input,Card,common}
mkdir -p frontend/src/components/ui/Button/{__tests__,__stories__}
mkdir -p frontend/src/components/ui/Input/{__tests__,__stories__}
mkdir -p frontend/src/components/ui/Card/{__tests__,__stories__}
mkdir -p frontend/src/types/components
mkdir -p frontend/src/styles/components
```

### Step 2: 最初のファイル作成 (2分)
```bash
# Button Component
cat > frontend/src/components/ui/Button/Button.tsx << 'EOF'
import React from 'react';
import { ButtonProps } from './Button.types';

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary',
  size = 'md',
  ...props 
}) => {
  return (
    <button className={`btn-${variant} btn-${size}`} {...props}>
      {children}
    </button>
  );
};
EOF

# Button Types
cat > frontend/src/components/ui/Button/Button.types.ts << 'EOF'
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}
EOF

# Button Test
cat > frontend/src/components/ui/Button/__tests__/Button.test.tsx << 'EOF'
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Button } from '../Button';

describe('Button', () => {
  it('renders correctly', () => {
    const { getByText } = render(<Button>Click me</Button>);
    expect(getByText('Click me')).toBeInTheDocument();
  });
});
EOF

# 最初のコミット
git add frontend/src/components/ui/Button/
git commit -m "feat: Initialize Button component structure"
```

### Step 3: 並行タスク開始 (同時実行)
```bash
# Design Tokens
cat > frontend/src/styles/design-tokens.css << 'EOF'
:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-secondary: #64748b;
  --color-danger: #ef4444;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  
  /* Typography */
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
}
EOF

# TypeScript Config
cat > frontend/src/types/components/index.ts << 'EOF'
export type Size = 'sm' | 'md' | 'lg';
export type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}
EOF

git add frontend/src/styles/ frontend/src/types/
git commit -m "feat: Add design tokens and base types"
```

---

## 🔧 CC02 - 今すぐコピペ実行

### Step 1: 基本セットアップ (1分)
```bash
# 実行開始宣言
echo "[$(date)] CC02 Starting Security Audit Logs" >> backend/CC02_LOG.txt

# ブランチ作成
git checkout main && git pull
git checkout -b feature/issue-46-security-audit

# ファイル作成
touch backend/app/models/audit_log.py
touch backend/app/schemas/audit_log.py
touch backend/app/api/v1/audit_logs.py
touch backend/app/services/audit_log_service.py
touch backend/tests/unit/models/test_audit_log.py
```

### Step 2: 最初のモデル実装 (2分)
```bash
# Audit Log Model
cat > backend/app/models/audit_log.py << 'EOF'
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default="success")
    details = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
EOF

# Schema
cat > backend/app/schemas/audit_log.py << 'EOF'
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuditLogBase(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    status: str = "success"
    details: Optional[Dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    class Config:
        from_attributes = True
EOF

# 最初のコミット
git add backend/app/models/audit_log.py backend/app/schemas/audit_log.py
git commit -m "feat: Add AuditLog model and schema"
```

### Step 3: 並行タスク開始 (同時実行)
```bash
# Migration作成
cat > backend/alembic/versions/008_add_audit_logs.py << 'EOF'
"""Add audit logs table

Revision ID: 008
Revises: 007
Create Date: 2025-07-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'

def upgrade():
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('idx_audit_action_timestamp', 'audit_logs', ['action', 'timestamp'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])

def downgrade():
    op.drop_table('audit_logs')
EOF

# Performance Middleware
cat > backend/app/middleware/performance.py << 'EOF'
import time
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

async def log_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response
EOF

git add backend/alembic/versions/008_add_audit_logs.py backend/app/middleware/
git commit -m "feat: Add migration and performance middleware"
```

---

## 🏗️ CC03 - 今すぐコピペ実行 (Read/Write/Edit)

### Step 1: Write - 開始宣言 (1分)
```yaml
Write ツール使用:
ファイル: docs/CC03_EXECUTION_START.md
内容: |
  # CC03 Execution Start Log
  
  Date: 2025-07-17 21:15 JST
  Main Task: Issue #173 - Auto Assignment System
  
  ## Execution Plan
  1. Analyze current label processor
  2. Design improved assignment logic
  3. Implement load balancing
  4. Create automated reports
  
  ## Parallel Tasks
  - CI/CD optimization
  - Security scanning enhancement
  - Test coverage improvement
  
  Status: STARTED
```

### Step 2: Read - 現状分析 (2分)
```yaml
Read ツール使用 (順次実行):
1. .github/workflows/label-processor.yml
2. .github/workflows/claude-pm-automation.yml
3. .github/ISSUE_TEMPLATE/
4. docs/coordination/README.md

分析ポイント:
- 現在のラベル処理ロジック
- エージェント割り当て方式
- 優先度設定の有無
- 除外ラベルの扱い
```

### Step 3: Write - 改善案作成 (3分)
```yaml
Write ツール使用:
ファイル: .github/workflows/improved-assignment.yml
内容: |
  name: Improved Auto Assignment System
  
  on:
    issues:
      types: [opened, labeled, unlabeled, reopened]
    schedule:
      - cron: '*/30 * * * *'  # 30分ごとに負荷確認
  
  jobs:
    assign-issue:
      runs-on: ubuntu-latest
      steps:
        - name: Analyze Issue
          id: analyze
          uses: actions/github-script@v6
          with:
            script: |
              const issue = context.payload.issue;
              const labels = issue.labels.map(l => l.name);
              
              // エージェント専門分野マッピング
              const agentSpecialty = {
                'cc01': ['frontend', 'react', 'typescript', 'ui-ux'],
                'cc02': ['backend', 'python', 'fastapi', 'database'],
                'cc03': ['infrastructure', 'testing', 'ci-cd', 'security']
              };
              
              // 優先度マッピング
              const priorityLabels = {
                'critical': 100,
                'high': 75,
                'medium': 50,
                'low': 25
              };
              
              // 除外ラベル
              const exclusionLabels = ['wip', 'blocked', 'on-hold', 'draft'];
              
              // 処理判定
              if (exclusionLabels.some(l => labels.includes(l))) {
                console.log('Issue excluded due to blocking labels');
                return null;
              }
              
              // エージェント選定ロジック
              let bestAgent = null;
              let highestScore = 0;
              
              for (const [agent, specialties] of Object.entries(agentSpecialty)) {
                let score = 0;
                for (const label of labels) {
                  if (specialties.some(s => label.includes(s))) {
                    score += 10;
                  }
                }
                
                // 優先度スコア追加
                for (const [priority, points] of Object.entries(priorityLabels)) {
                  if (labels.includes(priority)) {
                    score += points;
                  }
                }
                
                if (score > highestScore) {
                  highestScore = score;
                  bestAgent = agent;
                }
              }
              
              return { agent: bestAgent, score: highestScore };
              
        - name: Check Agent Load
          id: load
          uses: actions/github-script@v6
          with:
            script: |
              // エージェント別の現在のタスク数を確認
              const issues = await github.rest.issues.listForRepo({
                owner: context.repo.owner,
                repo: context.repo.repo,
                state: 'open',
                labels: 'auto-assigned'
              });
              
              const agentLoad = {
                'cc01': 0,
                'cc02': 0,
                'cc03': 0
              };
              
              for (const issue of issues.data) {
                const agentLabel = issue.labels.find(l => l.name.startsWith('cc0'));
                if (agentLabel) {
                  agentLoad[agentLabel.name]++;
                }
              }
              
              console.log('Current agent load:', agentLoad);
              return agentLoad;
              
        - name: Assign to Agent
          if: steps.analyze.outputs.agent
          uses: actions/github-script@v6
          with:
            script: |
              const selectedAgent = steps.analyze.outputs.agent;
              const agentLoad = steps.load.outputs;
              
              // 負荷分散: 最も負荷の低いエージェントを優先
              if (agentLoad[selectedAgent] > 5) {
                // 代替エージェントを探す
                const alternativeAgent = Object.entries(agentLoad)
                  .sort(([,a], [,b]) => a - b)[0][0];
                selectedAgent = alternativeAgent;
              }
              
              // ラベル追加
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                labels: [selectedAgent, 'auto-assigned']
              });
              
              // コメント追加
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `🤖 Auto-assigned to @${selectedAgent} based on expertise match and current workload.`
              });
```

### Step 4: Write - テストケース (2分)
```yaml
Write ツール使用:
ファイル: tests/workflows/test-auto-assignment.md
内容: |
  # Auto Assignment System Test Cases
  
  ## Test 1: Frontend Issue Assignment
  Labels: ['bug', 'frontend', 'react']
  Expected: Assign to CC01
  
  ## Test 2: Backend Issue Assignment  
  Labels: ['enhancement', 'backend', 'api']
  Expected: Assign to CC02
  
  ## Test 3: Infrastructure Issue Assignment
  Labels: ['infrastructure', 'ci-cd']
  Expected: Assign to CC03
  
  ## Test 4: Load Balancing
  Scenario: CC01 has 6 open issues
  Labels: ['frontend', 'ui']
  Expected: Assign to CC02 or CC03 (lowest load)
  
  ## Test 5: Exclusion Labels
  Labels: ['frontend', 'blocked']
  Expected: No assignment
  
  ## Test 6: Priority Handling
  Labels: ['backend', 'critical']
  Expected: High priority assignment to CC02
```

### Step 5: Write - 自動レポート (2分)
```yaml
Write ツール使用:
ファイル: scripts/generate-assignment-report.js
内容: |
  const fs = require('fs');
  const { Octokit } = require("@octokit/rest");
  
  const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN
  });
  
  async function generateReport() {
    const now = new Date();
    const oneDayAgo = new Date(now - 24 * 60 * 60 * 1000);
    
    // Get all issues
    const issues = await octokit.issues.listForRepo({
      owner: 'itdojp',
      repo: 'ITDO_ERP2',
      state: 'all',
      since: oneDayAgo.toISOString()
    });
    
    // Analyze assignments
    const stats = {
      cc01: { assigned: 0, completed: 0, inProgress: 0 },
      cc02: { assigned: 0, completed: 0, inProgress: 0 },
      cc03: { assigned: 0, completed: 0, inProgress: 0 }
    };
    
    for (const issue of issues.data) {
      const agentLabel = issue.labels.find(l => l.name.match(/^cc0[123]$/));
      if (agentLabel) {
        const agent = agentLabel.name;
        stats[agent].assigned++;
        
        if (issue.state === 'closed') {
          stats[agent].completed++;
        } else {
          stats[agent].inProgress++;
        }
      }
    }
    
    // Generate report
    const report = `# Auto Assignment Daily Report
  
  Date: ${now.toISOString().split('T')[0]}
  
  ## Assignment Statistics
  
  | Agent | Assigned | Completed | In Progress | Completion Rate |
  |-------|----------|-----------|-------------|-----------------|
  | CC01  | ${stats.cc01.assigned} | ${stats.cc01.completed} | ${stats.cc01.inProgress} | ${(stats.cc01.completed / stats.cc01.assigned * 100).toFixed(1)}% |
  | CC02  | ${stats.cc02.assigned} | ${stats.cc02.completed} | ${stats.cc02.inProgress} | ${(stats.cc02.completed / stats.cc02.assigned * 100).toFixed(1)}% |
  | CC03  | ${stats.cc03.assigned} | ${stats.cc03.completed} | ${stats.cc03.inProgress} | ${(stats.cc03.completed / stats.cc03.assigned * 100).toFixed(1)}% |
  
  ## Recommendations
  - Balance load if any agent has >5 in-progress issues
  - Review blocked issues for potential unblocking
  - Celebrate high completion rates!
  `;
    
    fs.writeFileSync(`reports/assignment-report-${now.toISOString().split('T')[0]}.md`, report);
    console.log('Report generated successfully');
  }
  
  generateReport();
```

---

## 🎯 全エージェント共通 - 進捗記録

### 15分ごとの進捗コミット
```bash
# CC01用
echo "[$(date)] Completed Button component base implementation" >> frontend/CC01_LOG.txt
git add . && git commit -m "feat: Progress update - Button component 50% complete"

# CC02用  
echo "[$(date)] Completed AuditLog model and migration" >> backend/CC02_LOG.txt
git add . && git commit -m "feat: Progress update - AuditLog model complete"

# CC03用 (Write使用)
Write: docs/CC03_PROGRESS.md
追記内容: |
  ## $(date)
  - Completed: Label processor analysis
  - In Progress: Load balancing implementation
  - Next: Automated report generation
```

---

**⚡ 開始**: このファイルの該当セクションをコピペして即座に実行開始！

**🔥 並行実行**: メインタスクと並行タスクを同時に進めて効率最大化！

**📊 進捗共有**: 15分ごとに簡単な進捗コミットで状況を可視化！