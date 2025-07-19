# 夜間自律作業計画 - 2025-07-15 20:30

## 🌙 夜間作業概要

エージェントの応答が低下している現状を踏まえ、自律的に実行可能な夜間作業計画を策定します。

## 🤖 自動化可能タスク

### 1. CI/CD監視とレポート

#### 自動監視スクリプト
```bash
#!/bin/bash
# night_monitor.sh

LOG_FILE="/tmp/night_monitor_$(date +%Y%m%d).log"

monitor_ci_status() {
    while true; do
        echo "$(date): Checking CI/CD status..." >> $LOG_FILE
        
        # PR #124のステータス確認
        gh pr view 124 --json statusCheckRollup -q '.statusCheckRollup' >> $LOG_FILE
        
        # 失敗したチェックの詳細
        gh pr checks 124 --watch >> $LOG_FILE 2>&1
        
        # 30分ごとに確認
        sleep 1800
    done
}

# バックグラウンドで実行
nohup monitor_ci_status &
```

### 2. テスト自動実行

#### Backend テスト自動化
```bash
#!/bin/bash
# auto_test_backend.sh

cd /mnt/c/work/ITDO_ERP2/backend

run_tests() {
    echo "$(date): Running backend tests..."
    
    # 仮想環境の確認と起動
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # テスト実行と結果保存
    python -m pytest tests/ -v --tb=short > /tmp/backend_test_$(date +%Y%m%d_%H%M%S).log 2>&1
}

# 1時間ごとに実行
while true; do
    run_tests
    sleep 3600
done
```

#### Frontend テスト自動化
```bash
#!/bin/bash
# auto_test_frontend.sh

cd /mnt/c/work/ITDO_ERP2/frontend

run_frontend_tests() {
    echo "$(date): Running frontend tests..."
    
    # 依存関係の確認
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # テスト実行
    npm test -- --run > /tmp/frontend_test_$(date +%Y%m%d_%H%M%S).log 2>&1
    
    # TypeScriptチェック
    npm run typecheck > /tmp/typescript_check_$(date +%Y%m%d_%H%M%S).log 2>&1
}

# 1時間ごとに実行
while true; do
    run_frontend_tests
    sleep 3600
done
```

### 3. 自動修正スクリプト

#### Import文の自動修正
```python
#!/usr/bin/env python3
# auto_fix_imports.py

import os
import re
from pathlib import Path

def fix_imports(file_path):
    """Pythonファイルのimport文を自動修正"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # typingインポートの修正
    if 'Optional' in content and 'from typing import' in content:
        if 'Optional' not in re.findall(r'from typing import ([^\\n]+)', content)[0]:
            content = re.sub(
                r'from typing import ([^\\n]+)',
                r'from typing import \\1, Optional',
                content
            )
    
    # List, Dictの追加
    typing_imports = {'List', 'Dict', 'Optional', 'Any', 'Union'}
    used_types = set()
    
    for type_name in typing_imports:
        if type_name in content:
            used_types.add(type_name)
    
    if used_types:
        import_line = f"from typing import {', '.join(sorted(used_types))}"
        if 'from typing import' not in content:
            content = import_line + '\\n' + content
        else:
            content = re.sub(
                r'from typing import [^\\n]+',
                import_line,
                content
            )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed imports in {file_path}")

# 全Pythonファイルを処理
backend_dir = Path('/mnt/c/work/ITDO_ERP2/backend')
for py_file in backend_dir.rglob('*.py'):
    try:
        fix_imports(py_file)
    except Exception as e:
        print(f"Error fixing {py_file}: {e}")
```

### 4. マージ競合の準備

#### 競合ファイルリスト作成
```bash
#!/bin/bash
# prepare_merge_conflicts.sh

cd /mnt/c/work/ITDO_ERP2
git checkout feature/auth-edge-cases

# 競合ファイルのリスト作成
git diff --name-only --diff-filter=U > /tmp/conflict_files.txt

# 各ファイルの競合詳細を保存
while read file; do
    echo "=== Conflict in $file ===" >> /tmp/conflict_details.txt
    git diff $file >> /tmp/conflict_details.txt
    echo "" >> /tmp/conflict_details.txt
done < /tmp/conflict_files.txt

echo "Conflict analysis saved to /tmp/conflict_details.txt"
```

## 🔄 claude-code-cluster夜間自動ループ

### 1. 監視専用エージェント起動
```bash
cd /tmp/claude-code-cluster
source venv/bin/activate

# 夜間監視エージェント
nohup python3 hooks/universal-agent-auto-loop-with-logging.py NIGHT01 itdojp ITDO_ERP2 \
  --specialization "Night Shift Monitor" \
  --labels monitoring night automation \
  --keywords monitor test fix automate \
  --max-iterations 20 \
  --cooldown 900 \
  > /tmp/night_agent.log 2>&1 &
```

### 2. テスト修正エージェント
```bash
# テスト自動修正エージェント
nohup python3 hooks/universal-agent-auto-loop-with-logging.py NIGHT02 itdojp ITDO_ERP2 \
  --specialization "Test Fix Specialist" \
  --labels testing fix backend frontend \
  --keywords test pytest jest typescript \
  --max-iterations 10 \
  --cooldown 1200 \
  > /tmp/test_fix_agent.log 2>&1 &
```

## 📊 夜間レポート生成

### 自動レポート生成スクリプト
```bash
#!/bin/bash
# generate_night_report.sh

REPORT_FILE="/tmp/night_report_$(date +%Y%m%d).md"

cat > $REPORT_FILE << EOF
# 夜間作業レポート - $(date +"%Y-%m-%d %H:%M")

## CI/CD Status
$(gh pr view 124 --json statusCheckRollup -q '.statusCheckRollup' | jq .)

## Test Results Summary
### Backend Tests
$(tail -20 /tmp/backend_test_*.log 2>/dev/null | grep -E "(PASSED|FAILED|ERROR)")

### Frontend Tests  
$(tail -20 /tmp/frontend_test_*.log 2>/dev/null | grep -E "(PASS|FAIL)")

## Automated Fixes
- Import statements: $(find /mnt/c/work/ITDO_ERP2/backend -name "*.py" -mtime -0.5 | wc -l) files updated
- Merge conflicts: $(wc -l < /tmp/conflict_files.txt) files identified

## Agent Activity
$(python3 /tmp/claude-code-cluster/hooks/view-command-logs.py --limit 10)

## Next Actions Required
1. Review and merge PR #124
2. Resolve remaining $(wc -l < /tmp/conflict_files.txt) merge conflicts
3. Verify all tests passing

Generated at: $(date)
EOF

echo "Night report generated: $REPORT_FILE"
```

## 🌅 明朝の準備

### 1. 優先タスクリスト生成
```bash
#!/bin/bash
# prepare_morning_tasks.sh

TASK_FILE="/tmp/morning_tasks_$(date +%Y%m%d).md"

cat > $TASK_FILE << 'EOF'
# Morning Priority Tasks - $(date +%Y-%m-%d)

## 🔴 Critical (対応必須)
1. [ ] PR #124のマージ完了
2. [ ] エージェント健康チェック
3. [ ] 夜間テスト結果の確認

## 🟡 High Priority
1. [ ] Issue #132 Level 1 Escalation解決
2. [ ] Backend test全パス確認
3. [ ] CI/CD安定性向上

## 🟢 Normal Priority
1. [ ] 新しいIssueのトリアージ
2. [ ] コードレビュー
3. [ ] ドキュメント更新

## エージェント割り当て案
- CC01: Frontend + PR #124最終確認
- CC02: Backend修正 + テスト
- CC03: CI/CD + Infrastructure

## 成功指標
- PR #124: マージ完了
- CI/CD: 95%以上成功率
- エージェント: 3体稼働
EOF

echo "Morning tasks prepared: $TASK_FILE"
```

### 2. エージェント起動準備
```bash
#!/bin/bash
# prepare_agent_startup.sh

# 起動スクリプト準備
cat > /tmp/start_all_agents.sh << 'EOF'
#!/bin/bash
echo "🌅 Starting morning agent activation..."

# CC01起動
echo "Starting CC01..."
# CC01起動コマンド

# CC02起動
echo "Starting CC02..."
# CC02起動コマンド

# CC03起動
echo "Starting CC03..."
# CC03起動コマンド

echo "✅ All agents activation initiated"
EOF

chmod +x /tmp/start_all_agents.sh
```

## 🔔 アラート設定

### 緊急アラート条件
```bash
#!/bin/bash
# emergency_alert.sh

check_emergency() {
    # PR #124が朝6時までにマージされていない場合
    PR_STATE=$(gh pr view 124 --json state -q '.state')
    if [ "$PR_STATE" != "MERGED" ] && [ $(date +%H) -ge 06 ]; then
        echo "🚨 EMERGENCY: PR #124 not merged by 6 AM"
        # アラート送信
    fi
    
    # テスト失敗が継続している場合
    if grep -q "FAILED" /tmp/backend_test_*.log; then
        echo "🚨 EMERGENCY: Backend tests still failing"
        # アラート送信
    fi
}

# 30分ごとにチェック
while true; do
    check_emergency
    sleep 1800
done
```

## 📋 実行手順

### 1. 即座実行（20:45）
```bash
# 自動修正スクリプトの実行
python3 auto_fix_imports.py

# 夜間監視の開始
nohup ./night_monitor.sh &

# 自動テストの開始
nohup ./auto_test_backend.sh &
nohup ./auto_test_frontend.sh &
```

### 2. 定期実行（21:00-06:00）
```bash
# cronジョブ設定
crontab -e
# 以下を追加
0 * * * * /mnt/c/work/ITDO_ERP2/generate_night_report.sh
*/30 * * * * /mnt/c/work/ITDO_ERP2/emergency_alert.sh
0 6 * * * /mnt/c/work/ITDO_ERP2/prepare_morning_tasks.sh
```

### 3. 明朝確認（06:00）
- 夜間レポートの確認
- エージェント起動準備
- 優先タスクの実行開始

---
**夜間作業開始**: 2025-07-15 20:45
**自動監視期間**: 21:00 - 06:00
**明朝レビュー**: 2025-07-16 06:00
**緊急連絡**: 重大問題発生時のみ