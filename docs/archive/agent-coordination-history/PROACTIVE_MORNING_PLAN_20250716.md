# プロアクティブ朝の作業計画 - 2025-07-16

## 🌅 朝の自動実行タスク

### 1. エージェント健康チェックスクリプト
```bash
#!/bin/bash
# agent_health_check.sh

echo "=== Agent Health Check - $(date) ==="

check_agent() {
    local agent=$1
    echo -n "$agent: "
    
    # プロセス確認
    if pgrep -f "universal-agent.*$agent" > /dev/null; then
        echo "🟢 Running"
    else
        echo "🔴 Stopped - Attempting restart..."
        # 自動再起動試行
        cd /tmp/claude-code-cluster
        source venv/bin/activate
        python3 hooks/universal-agent-auto-loop-with-logging.py $agent itdojp ITDO_ERP2 \
            --max-iterations 1 \
            --cooldown 60 &
        echo "  ↳ Restart initiated"
    fi
}

# 全エージェントチェック
for agent in CC01 CC02 CC03; do
    check_agent $agent
done

# PR状態確認
echo -e "\n=== PR #124 Status ==="
gh pr view 124 --json state,mergeable -q 'State: .state, Mergeable: .mergeable'

# 失敗チェック数
echo -e "\n=== Failed Checks ==="
gh pr checks 124 | grep -c "fail" || echo "0 failures"
```

### 2. 自動Import修正実行
```python
#!/usr/bin/env python3
# morning_auto_fix.py

import os
import re
from pathlib import Path
import subprocess

def fix_task_service_imports():
    """task.pyのimport修正"""
    file_path = Path("/mnt/c/work/ITDO_ERP2/backend/app/services/task.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Line 36付近でOptional, Dictが未定義
    import_added = False
    for i, line in enumerate(lines):
        if i == 35 and 'from typing import' not in ''.join(lines[:40]):
            # import文を挿入
            lines.insert(4, "from typing import Optional, Dict, Any\n")
            import_added = True
            break
    
    if import_added:
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print(f"✅ Fixed imports in {file_path}")
    else:
        print(f"ℹ️ Imports already present in {file_path}")

def run_quick_test():
    """修正後の簡易テスト"""
    os.chdir("/mnt/c/work/ITDO_ERP2/backend")
    result = subprocess.run(
        ["python", "-m", "py_compile", "app/services/task.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Syntax check passed")
    else:
        print(f"❌ Syntax error: {result.stderr}")

if __name__ == "__main__":
    print("Starting morning auto-fix...")
    fix_task_service_imports()
    run_quick_test()
```

### 3. CI/CD復旧スクリプト
```bash
#!/bin/bash
# ci_recovery.sh

echo "=== CI/CD Recovery Script - $(date) ==="

# 1. 最新の変更を取得
cd /mnt/c/work/ITDO_ERP2
git fetch origin

# 2. マージ競合の自動解決試行
if git merge origin/main --no-commit --no-ff; then
    echo "✅ Merge successful"
else
    echo "⚠️ Merge conflicts detected"
    
    # 競合ファイルリスト
    git diff --name-only --diff-filter=U > /tmp/conflicts.txt
    
    # 各競合ファイルに対して
    while read file; do
        echo "Conflict in: $file"
        # 安全な自動解決を試行（mainを優先）
        git checkout --theirs "$file" 2>/dev/null || echo "  ↳ Manual resolution required"
    done < /tmp/conflicts.txt
fi

# 3. テスト実行
echo -e "\n=== Running Tests ==="
cd backend
uv run pytest tests/unit/ -v --tb=short | tail -20

cd ../frontend
npm test -- --run 2>&1 | tail -20
```

## 🤖 エージェント段階復帰計画

### Phase 1: 最小稼働（05:00-06:00）
```yaml
目標: 1エージェントの復活
手段:
  - CC01単独起動
  - 1タスク限定実行
  - 30分間隔監視
```

### Phase 2: 部分稼働（06:00-09:00）
```yaml
目標: 2エージェント稼働
手段:
  - CC01 + CC03稼働
  - PR #124対応専念
  - 人間サポート体制
```

### Phase 3: 通常復帰（09:00-12:00）
```yaml
目標: 全エージェント稼働
手段:
  - CC02復活
  - 通常タスク再開
  - 自律運用移行
```

## 📱 自動通知システム

### Slack/Discord通知スクリプト
```python
#!/usr/bin/env python3
# morning_notifications.py

import subprocess
import json
from datetime import datetime

def get_system_status():
    """システム状態を取得"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "agents": {},
        "pr_124": {},
        "alerts": []
    }
    
    # エージェント状態
    for agent in ["CC01", "CC02", "CC03"]:
        result = subprocess.run(
            ["pgrep", "-f", f"universal-agent.*{agent}"],
            capture_output=True
        )
        status["agents"][agent] = "Running" if result.returncode == 0 else "Stopped"
    
    # PR状態
    pr_result = subprocess.run(
        ["gh", "pr", "view", "124", "--json", "state,mergeable"],
        capture_output=True,
        text=True
    )
    if pr_result.returncode == 0:
        status["pr_124"] = json.loads(pr_result.stdout)
    
    # アラート判定
    if all(v == "Stopped" for v in status["agents"].values()):
        status["alerts"].append("🚨 All agents are down!")
    
    if status["pr_124"].get("mergeable") == "CONFLICTING":
        status["alerts"].append("⚠️ PR #124 has merge conflicts!")
    
    return status

def send_notification(status):
    """通知送信（実装は環境に応じて）"""
    print("=== Morning Status Report ===")
    print(json.dumps(status, indent=2))
    
    # GitHub Issueでの通知例
    if status["alerts"]:
        alert_text = "\n".join(status["alerts"])
        subprocess.run([
            "gh", "issue", "comment", "132",
            "--body", f"Morning Alert ({status['timestamp']}):\n{alert_text}"
        ])

if __name__ == "__main__":
    status = get_system_status()
    send_notification(status)
```

## 🎯 成功指標と継続戦略

### 朝の成功指標（06:00評価）
- [ ] 最低1エージェント稼働
- [ ] PR #124進捗あり
- [ ] 新規エラーなし

### 午前の成功指標（09:00評価）
- [ ] 2エージェント以上稼働
- [ ] PR #124マージ可能状態
- [ ] CI/CD 80%以上通過

### 正午の成功指標（12:00評価）
- [ ] 全エージェント稼働
- [ ] PR #124完了
- [ ] 通常運用復帰

## 🔄 継続的改善

### 1. ログ分析自動化
```bash
# analyze_logs.sh
#!/bin/bash

LOG_DIR="/tmp/claude-code-cluster/logs"
REPORT="/tmp/morning_log_analysis.txt"

echo "=== Log Analysis Report - $(date) ===" > $REPORT

# エラーパターン検出
echo -e "\n## Error Patterns:" >> $REPORT
grep -i "error\|exception\|failed" $LOG_DIR/*.log | \
    awk -F: '{print $1}' | sort | uniq -c | sort -nr >> $REPORT

# 実行統計
echo -e "\n## Execution Stats:" >> $REPORT
for agent in CC01 CC02 CC03; do
    count=$(grep -c "Executing task" $LOG_DIR/*$agent*.log 2>/dev/null || echo 0)
    echo "$agent: $count tasks executed" >> $REPORT
done

cat $REPORT
```

### 2. 予防的メンテナンス
```yaml
daily_maintenance:
  - ログローテーション
  - 一時ファイルクリーンアップ
  - メモリ使用量チェック
  - プロセス健全性確認
```

---
**計画作成**: 2025-07-16 04:45
**実行開始**: 2025-07-16 05:00
**評価時刻**: 06:00, 09:00, 12:00
**目標**: 段階的な通常運用復帰