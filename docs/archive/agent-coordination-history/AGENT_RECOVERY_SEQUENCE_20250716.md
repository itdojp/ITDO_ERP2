# エージェント回復シーケンス - 2025-07-16

## 🔄 段階的回復プロトコル

### Phase 0: 緊急診断（04:45-05:00）
```bash
#!/bin/bash
# emergency_diagnosis.sh

echo "=== Emergency Agent Diagnosis ==="

# 1. プロセス確認
echo -e "\n## Running Processes:"
ps aux | grep -E "(universal-agent|claude)" | grep -v grep

# 2. 最終ログ確認
echo -e "\n## Last Log Entries:"
for agent in CC01 CC02 CC03; do
    echo "--- $agent ---"
    log_file="/tmp/claude-code-cluster/logs/*$agent*.log"
    if ls $log_file 1> /dev/null 2>&1; then
        tail -5 $log_file | grep -E "(ERROR|WARN|SUCCESS)"
    else
        echo "No log file found"
    fi
done

# 3. システムリソース
echo -e "\n## System Resources:"
free -h
df -h /tmp
```

### Phase 1: 最小限起動（05:00-05:30）

#### CC01単独起動（リーダー優先）
```bash
cd /tmp/claude-code-cluster
source venv/bin/activate

# 最小構成でCC01を起動
python3 hooks/universal-agent-auto-loop-with-logging.py CC01 itdojp ITDO_ERP2 \
  --specialization "Minimal Emergency Mode" \
  --max-iterations 1 \
  --cooldown 300 \
  --labels "emergency minimal pr-124-fix" \
  --task "Fix import errors in task.py only" &

# 起動確認（30秒待機）
sleep 30
pgrep -f "universal-agent.*CC01" && echo "✅ CC01 started" || echo "❌ CC01 failed"
```

### Phase 2: ペア稼働（05:30-06:00）

#### CC01 + CC03起動
```bash
# CC01が稼働していることを確認後
if pgrep -f "universal-agent.*CC01" > /dev/null; then
    echo "Starting CC03 as support..."
    
    python3 hooks/universal-agent-auto-loop-with-logging.py CC03 itdojp ITDO_ERP2 \
      --specialization "CI/CD Support Mode" \
      --max-iterations 2 \
      --cooldown 300 \
      --labels "support ci-cd pr-124" \
      --task "Monitor and fix CI/CD issues" &
fi
```

### Phase 3: 完全復帰（06:00-07:00）

#### 全エージェント起動
```bash
# start_all_agents_gradual.sh
#!/bin/bash

start_agent() {
    local agent=$1
    local role=$2
    local priority=$3
    
    echo "Starting $agent with $role role..."
    
    cd /tmp/claude-code-cluster
    source venv/bin/activate
    
    python3 hooks/universal-agent-auto-loop-with-logging.py $agent itdojp ITDO_ERP2 \
      --specialization "$role" \
      --max-iterations 5 \
      --cooldown 180 \
      --labels "$priority" &
    
    sleep 10
}

# 優先順位付き起動
start_agent "CC01" "Frontend Leader & Coordinator" "high-priority leader"
sleep 30  # リーダー安定待ち

start_agent "CC03" "Infrastructure & CI/CD" "high-priority infrastructure"
sleep 30  # インフラ安定待ち

start_agent "CC02" "Backend Development" "normal-priority backend"
```

## 🏥 エージェント健康管理

### 継続的監視スクリプト
```python
#!/usr/bin/env python3
# agent_health_monitor.py

import subprocess
import time
import json
from datetime import datetime

class AgentHealthMonitor:
    def __init__(self):
        self.agents = ["CC01", "CC02", "CC03"]
        self.health_status = {}
        self.restart_attempts = {}
        
    def check_agent_process(self, agent):
        """エージェントプロセスの確認"""
        result = subprocess.run(
            ["pgrep", "-f", f"universal-agent.*{agent}"],
            capture_output=True
        )
        return result.returncode == 0
    
    def check_agent_activity(self, agent):
        """エージェントの活動確認"""
        # 最新のIssue/PR活動をチェック
        result = subprocess.run(
            ["gh", "issue", "list", "--assignee", agent, "--limit", "1", "--json", "updatedAt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip() != "[]":
            data = json.loads(result.stdout)
            # 1時間以内の活動があるか
            return len(data) > 0
        return False
    
    def restart_agent(self, agent):
        """エージェントの再起動"""
        if self.restart_attempts.get(agent, 0) >= 3:
            print(f"⚠️ {agent}: Max restart attempts reached")
            return False
            
        print(f"🔄 Restarting {agent}...")
        subprocess.run([
            "python3", "/tmp/claude-code-cluster/hooks/universal-agent-auto-loop-with-logging.py",
            agent, "itdojp", "ITDO_ERP2",
            "--max-iterations", "3",
            "--cooldown", "300"
        ], cwd="/tmp/claude-code-cluster")
        
        self.restart_attempts[agent] = self.restart_attempts.get(agent, 0) + 1
        return True
    
    def monitor_loop(self):
        """監視ループ"""
        while True:
            print(f"\n=== Health Check - {datetime.now().strftime('%H:%M:%S')} ===")
            
            for agent in self.agents:
                process_running = self.check_agent_process(agent)
                activity_recent = self.check_agent_activity(agent)
                
                if process_running and activity_recent:
                    status = "🟢 Healthy"
                elif process_running and not activity_recent:
                    status = "🟡 Idle"
                else:
                    status = "🔴 Down"
                    self.restart_agent(agent)
                
                self.health_status[agent] = status
                print(f"{agent}: {status}")
            
            # 5分ごとにチェック
            time.sleep(300)

if __name__ == "__main__":
    monitor = AgentHealthMonitor()
    monitor.monitor_loop()
```

## 🎯 回復成功指標

### 各フェーズの確認項目

#### Phase 1成功基準
- [ ] CC01プロセス起動確認
- [ ] エラーログなし
- [ ] 簡単なタスク実行可能

#### Phase 2成功基準
- [ ] CC01 + CC03稼働中
- [ ] PR #124に対する活動確認
- [ ] CI/CDエラー減少

#### Phase 3成功基準
- [ ] 全エージェント稼働
- [ ] 通常タスク処理再開
- [ ] 自律的な協調動作

## 🔧 トラブルシューティング

### よくある問題と対処

#### 1. エージェントが即座に停止する
```bash
# メモリ不足の確認
free -h

# ディスク容量確認
df -h /tmp

# Python環境確認
cd /tmp/claude-code-cluster
source venv/bin/activate
python --version
pip list | grep -E "(anthropic|aiohttp)"
```

#### 2. GitHub認証エラー
```bash
# GitHub CLI認証確認
gh auth status

# 必要に応じて再認証
gh auth login
```

#### 3. 依存関係エラー
```bash
cd /tmp/claude-code-cluster
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---
**プロトコル作成**: 2025-07-16 04:45
**実行開始**: 2025-07-16 05:00
**完全復帰目標**: 2025-07-16 07:00