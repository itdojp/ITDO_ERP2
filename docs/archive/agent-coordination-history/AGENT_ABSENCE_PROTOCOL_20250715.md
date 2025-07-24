# エージェント不在時緊急対応プロトコル

## 🚨 現在の状況

### エージェント応答状況（20:30時点）
- **CC01**: PR #98完了後、1時間以上応答なし
- **CC02**: 緊急活性化プロトコルへの応答なし
- **CC03**: 復活プロトコルへの応答なし

### 判断基準
```yaml
Level 0 (通常): 15分以内の応答
Level 1 (注意): 30分-1時間応答なし
Level 2 (警告): 1-3時間応答なし ← 現在
Level 3 (緊急): 3時間以上応答なし
```

## 🔧 人間開発者による緊急介入

### PR #124の緊急修正手順

#### 1. マージ競合の解決
```bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/auth-edge-cases
git pull origin main

# 競合解決
git status --porcelain | grep "^UU" | awk '{print $2}' | while read file; do
    echo "Resolving conflict in $file"
    # エディタで手動解決またはマージツール使用
done

git add -A
git commit -m "fix: Resolve merge conflicts for PR #124"
```

#### 2. Import文の一括修正
```python
# fix_all_imports.py
import os
import re
from pathlib import Path

def fix_file_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 基本的なtypingインポート
    if any(x in content for x in ['Optional', 'List', 'Dict', 'Any', 'Union']):
        imports_needed = []
        if 'Optional' in content: imports_needed.append('Optional')
        if 'List' in content: imports_needed.append('List')
        if 'Dict' in content: imports_needed.append('Dict')
        if 'Any' in content: imports_needed.append('Any')
        if 'Union' in content: imports_needed.append('Union')
        
        import_line = f"from typing import {', '.join(imports_needed)}"
        
        # 既存のtypingインポートを置換
        if 'from typing import' in content:
            content = re.sub(r'from typing import [^\n]+', import_line, content)
        else:
            # ファイルの先頭に追加
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#'):
                    insert_pos = i
                    break
            lines.insert(insert_pos, import_line)
            content = '\n'.join(lines)
    
    with open(filepath, 'w') as f:
        f.write(content)

# 実行
backend_path = Path('/mnt/c/work/ITDO_ERP2/backend')
for py_file in backend_path.rglob('*.py'):
    if 'venv' not in str(py_file):
        fix_file_imports(py_file)
        print(f"Fixed: {py_file}")
```

#### 3. Role modelの修正
```python
# backend/app/models/role.py
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.permission import Permission
    from app.models.user import User

class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String, nullable=False)
    description: Mapped[Optional[str]] = Column(String, nullable=True)
    organization_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # リレーションシップ
    organization: Mapped["Organization"] = relationship("Organization", back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", 
        secondary="role_permissions",
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        "User", 
        secondary="user_roles", 
        back_populates="roles"
    )
```

### 🚀 自動回復システム

#### エージェント再起動スクリプト
```bash
#!/bin/bash
# restart_agents.sh

restart_agent() {
    local agent_id=$1
    local specialization=$2
    
    echo "🔄 Attempting to restart $agent_id..."
    
    # 既存プロセスの終了
    pkill -f "universal-agent.*$agent_id" || true
    
    # claude-code-clusterでの再起動
    cd /tmp/claude-code-cluster
    source venv/bin/activate
    
    case $agent_id in
        CC01)
            python3 hooks/universal-agent-auto-loop-with-logging.py CC01 itdojp ITDO_ERP2 \
                --specialization "Frontend & Technical Leader" \
                --labels frontend leader \
                --max-iterations 3 \
                --cooldown 300 &
            ;;
        CC02)
            python3 hooks/universal-agent-auto-loop-with-logging.py CC02 itdojp ITDO_ERP2 \
                --specialization "Backend Specialist" \
                --labels backend database \
                --max-iterations 3 \
                --cooldown 300 &
            ;;
        CC03)
            python3 hooks/universal-agent-auto-loop-with-logging.py CC03 itdojp ITDO_ERP2 \
                --specialization "Infrastructure Expert" \
                --labels infrastructure ci-cd \
                --max-iterations 3 \
                --cooldown 300 &
            ;;
    esac
    
    echo "✅ $agent_id restart initiated"
}

# 全エージェント再起動
for agent in CC01 CC02 CC03; do
    restart_agent $agent
    sleep 10
done
```

### 📊 状況監視ダッシュボード

#### リアルタイム監視
```bash
#!/bin/bash
# realtime_dashboard.sh

while true; do
    clear
    echo "=== ITDO_ERP2 Agent Dashboard - $(date) ==="
    echo
    
    # エージェント状態
    echo "📡 Agent Status:"
    for agent in CC01 CC02 CC03; do
        if pgrep -f "universal-agent.*$agent" > /dev/null; then
            echo "  $agent: 🟢 Running"
        else
            echo "  $agent: 🔴 Stopped"
        fi
    done
    echo
    
    # PR #124状態
    echo "📋 PR #124 Status:"
    gh pr view 124 --json state,mergeable,statusCheckRollup -q '. | 
        "  State: " + .state + 
        "\n  Mergeable: " + (.mergeable // "unknown") + 
        "\n  Checks: " + (.statusCheckRollup // []) | length | tostring + " total"'
    echo
    
    # 最近の活動
    echo "⚡ Recent Activity:"
    gh issue list --assignee @me --state all --limit 3 --json number,title,updatedAt \
        -q '.[] | "  #" + (.number | tostring) + ": " + .title + " (" + .updatedAt + ")"'
    echo
    
    # CI/CD状態
    echo "🔧 CI/CD Status:"
    gh run list --limit 3 --json conclusion,name,updatedAt \
        -q '.[] | "  " + .name + ": " + .conclusion + " (" + .updatedAt + ")"'
    
    sleep 30
done
```

## 🎯 緊急対応優先順位

### 1. 即座対応（20:30-21:00）
1. **PR #124修正**: 人間開発者による直接介入
2. **エージェント再起動**: 自動スクリプト実行
3. **監視開始**: ダッシュボード起動

### 2. 短期対応（21:00-22:00）
1. **PR #124マージ**: 修正完了後のマージ
2. **エージェント確認**: 応答状況の確認
3. **夜間自動化**: 自動スクリプト設定

### 3. 継続対応（22:00-06:00）
1. **自動監視**: 夜間監視継続
2. **自動テスト**: 定期実行
3. **レポート生成**: 朝の準備

## 🔔 エスカレーション基準

### Level 2 → Level 3への移行条件
- 3時間以上の完全無応答
- 重要タスクの完全停止
- 技術的問題の自動解決不可

### Level 3対応
1. 人間開発者の完全介入
2. 手動でのタスク完了
3. システム診断と修復

## 📱 緊急連絡体制

### 通知方法
```bash
# 緊急通知スクリプト
send_emergency_notification() {
    local level=$1
    local message=$2
    
    # GitHub Issue作成
    gh issue create \
        --title "🚨 Level $level Emergency: Agent System Alert" \
        --body "$message" \
        --label "emergency,alert,level-$level"
    
    # ログ記録
    echo "[$(date)] Level $level: $message" >> /tmp/emergency.log
}
```

---
**プロトコル発動**: 2025-07-15 20:30
**現在レベル**: Level 2 (警告)
**次回評価**: 2025-07-15 23:30（Level 3判定）
**人間介入**: 推奨