# 自動化監視・アラートシステム セットアップ

## 🎯 目的

CC01, CC02, CC03の状況を自動的に監視し、問題を早期発見・対応するシステムの構築

## 📊 監視項目

### 1. エージェント健康状態
```yaml
基本メトリクス:
  - 応答時間
  - 稼働率
  - エラー発生率
  - タスク完了率

高度メトリクス:
  - メモリ使用量
  - CPU使用率
  - 作業効率
  - 品質スコア
```

### 2. プロジェクト進捗
```yaml
開発メトリクス:
  - PR成功率
  - CI/CD成功率
  - Test coverage
  - Build time

品質メトリクス:
  - Code quality score
  - Bug発生率
  - Performance metrics
  - Security score
```

## 🔧 監視スクリプト

### 1. エージェント状態監視
```bash
#!/bin/bash
# agent_monitor.sh

SCRIPT_DIR="/mnt/c/work/ITDO_ERP2"
LOG_FILE="/tmp/agent_monitor.log"

check_agent_status() {
    local agent_id=$1
    local last_activity=$(gh issue list --assignee @me --state closed --limit 1 --json closedAt -q '.[0].closedAt' 2>/dev/null)
    
    if [ -z "$last_activity" ]; then
        echo "❌ $agent_id: No recent activity" >> $LOG_FILE
        return 1
    else
        echo "✅ $agent_id: Active (last: $last_activity)" >> $LOG_FILE
        return 0
    fi
}

monitor_agents() {
    echo "🔍 Agent Status Check - $(date)" >> $LOG_FILE
    
    # CC01監視
    if ! check_agent_status "CC01"; then
        send_alert "CC01" "No recent activity detected"
    fi
    
    # CC02監視
    if ! check_agent_status "CC02"; then
        send_alert "CC02" "Extended absence detected"
    fi
    
    # CC03監視
    if ! check_agent_status "CC03"; then
        send_alert "CC03" "Response timeout detected"
    fi
}

send_alert() {
    local agent=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "🚨 ALERT [$timestamp] $agent: $message" >> $LOG_FILE
    
    # GitHub Issueアラート
    gh issue create \
        --title "🚨 Agent Alert: $agent" \
        --body "**Alert Time**: $timestamp
**Agent**: $agent
**Issue**: $message
**Action Required**: Investigation needed

**Monitoring System**: Automated alert" \
        --label "alert,monitoring,$agent" 2>/dev/null
}

# 実行
monitor_agents
```

### 2. プロジェクト状態監視
```bash
#!/bin/bash
# project_monitor.sh

PROJECT_DIR="/mnt/c/work/ITDO_ERP2"
LOG_FILE="/tmp/project_monitor.log"

check_ci_status() {
    local success_rate=$(gh run list --limit 10 --json conclusion -q 'map(select(.conclusion == "success")) | length')
    local total_runs=10
    local rate=$((success_rate * 100 / total_runs))
    
    echo "🔧 CI/CD Success Rate: $rate% ($success_rate/$total_runs)" >> $LOG_FILE
    
    if [ $rate -lt 70 ]; then
        send_project_alert "CI/CD" "Success rate below threshold: $rate%"
    fi
}

check_pr_status() {
    local open_prs=$(gh pr list --state open --json number -q 'length')
    local draft_prs=$(gh pr list --state open --draft --json number -q 'length')
    
    echo "📋 Open PRs: $open_prs (Draft: $draft_prs)" >> $LOG_FILE
    
    if [ $open_prs -gt 20 ]; then
        send_project_alert "PR" "Too many open PRs: $open_prs"
    fi
}

check_issue_status() {
    local open_issues=$(gh issue list --state open --json number -q 'length')
    local high_priority=$(gh issue list --state open --label "priority:high" --json number -q 'length')
    
    echo "📝 Open Issues: $open_issues (High Priority: $high_priority)" >> $LOG_FILE
    
    if [ $high_priority -gt 10 ]; then
        send_project_alert "Issues" "Too many high priority issues: $high_priority"
    fi
}

send_project_alert() {
    local component=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "🚨 PROJECT ALERT [$timestamp] $component: $message" >> $LOG_FILE
}

# 実行
cd $PROJECT_DIR
echo "📊 Project Status Check - $(date)" >> $LOG_FILE
check_ci_status
check_pr_status
check_issue_status
```

### 3. パフォーマンス監視
```bash
#!/bin/bash
# performance_monitor.sh

METRICS_FILE="/tmp/performance_metrics.json"
LOG_FILE="/tmp/performance_monitor.log"

collect_metrics() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # システムメトリクス
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    # GitHub APIレート制限
    local rate_limit=$(gh api rate_limit --jq '.rate.remaining')
    
    # メトリクス記録
    cat >> $METRICS_FILE << EOF
{
  "timestamp": "$timestamp",
  "cpu_usage": $cpu_usage,
  "memory_usage": $memory_usage,
  "disk_usage": $disk_usage,
  "github_rate_limit": $rate_limit
}
EOF
    
    echo "📈 Performance Metrics [$timestamp] CPU: $cpu_usage%, Memory: $memory_usage%, Disk: $disk_usage%, GitHub API: $rate_limit" >> $LOG_FILE
    
    # アラート判定
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        send_performance_alert "CPU" "High CPU usage: $cpu_usage%"
    fi
    
    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        send_performance_alert "Memory" "High memory usage: $memory_usage%"
    fi
    
    if [ $rate_limit -lt 100 ]; then
        send_performance_alert "GitHub API" "Low rate limit: $rate_limit"
    fi
}

send_performance_alert() {
    local component=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "🚨 PERFORMANCE ALERT [$timestamp] $component: $message" >> $LOG_FILE
}

# 実行
collect_metrics
```

## 📱 アラート通知システム

### 1. Slack通知（オプション）
```bash
#!/bin/bash
# slack_notifier.sh

SLACK_WEBHOOK_URL="your-slack-webhook-url"

send_slack_alert() {
    local message=$1
    local color=$2
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"🤖 ITDO_ERP2 Agent Alert\",
                \"text\": \"$message\",
                \"footer\": \"Agent Monitoring System\",
                \"ts\": $(date +%s)
            }]
        }" \
        $SLACK_WEBHOOK_URL
}

# 使用例
# send_slack_alert "CC01 high load detected" "warning"
```

### 2. メール通知（オプション）
```bash
#!/bin/bash
# email_notifier.sh

send_email_alert() {
    local subject=$1
    local message=$2
    local to_email=$3
    
    echo "$message" | mail -s "$subject" "$to_email"
}

# 使用例
# send_email_alert "Agent Alert" "CC01 requires attention" "admin@example.com"
```

## 🔄 自動実行設定

### 1. Cron設定
```bash
# crontab -e で以下を追加

# 5分ごとのエージェント監視
*/5 * * * * /mnt/c/work/ITDO_ERP2/agent_monitor.sh

# 15分ごとのプロジェクト監視
*/15 * * * * /mnt/c/work/ITDO_ERP2/project_monitor.sh

# 30分ごとのパフォーマンス監視
*/30 * * * * /mnt/c/work/ITDO_ERP2/performance_monitor.sh

# 1時間ごとのレポート生成
0 * * * * /mnt/c/work/ITDO_ERP2/generate_report.sh
```

### 2. Systemd設定（オプション）
```ini
# /etc/systemd/system/agent-monitor.service
[Unit]
Description=Agent Monitoring Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/mnt/c/work/ITDO_ERP2
ExecStart=/mnt/c/work/ITDO_ERP2/agent_monitor.sh
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

## 📊 ダッシュボード

### 1. 簡易ダッシュボード
```bash
#!/bin/bash
# dashboard.sh

generate_dashboard() {
    echo "🎯 ITDO_ERP2 Agent Dashboard - $(date)"
    echo "=" | head -c 50; echo
    
    # エージェント状態
    echo "🤖 Agent Status:"
    echo "  CC01: $(check_agent_health CC01)"
    echo "  CC02: $(check_agent_health CC02)"
    echo "  CC03: $(check_agent_health CC03)"
    echo
    
    # プロジェクト状態
    echo "📊 Project Status:"
    echo "  Open PRs: $(gh pr list --state open --json number -q 'length')"
    echo "  Open Issues: $(gh issue list --state open --json number -q 'length')"
    echo "  CI Success Rate: $(calculate_ci_success_rate)"
    echo
    
    # 最新アクティビティ
    echo "⚡ Recent Activity:"
    gh issue list --state closed --limit 3 --json title,closedAt -q '.[] | "  - " + .title + " (closed: " + .closedAt + ")"'
    echo
    
    # システムメトリクス
    echo "💻 System Metrics:"
    echo "  CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
    echo "  Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "  Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"
}

check_agent_health() {
    local agent=$1
    # 実装：エージェントの健康状態チェック
    echo "Active" # プレースホルダー
}

calculate_ci_success_rate() {
    local success=$(gh run list --limit 10 --json conclusion -q 'map(select(.conclusion == "success")) | length')
    echo "$((success * 10))%"
}

# 実行
generate_dashboard
```

### 2. HTML ダッシュボード
```html
<!DOCTYPE html>
<html>
<head>
    <title>ITDO_ERP2 Agent Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status-good { color: green; }
        .status-warning { color: orange; }
        .status-error { color: red; }
        .metrics { display: flex; gap: 20px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🤖 ITDO_ERP2 Agent Dashboard</h1>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Agent Status</h3>
            <div id="agent-status">Loading...</div>
        </div>
        
        <div class="metric-card">
            <h3>Project Metrics</h3>
            <div id="project-metrics">Loading...</div>
        </div>
        
        <div class="metric-card">
            <h3>System Health</h3>
            <div id="system-health">Loading...</div>
        </div>
    </div>
    
    <script>
        // JavaScript for real-time updates
        function updateDashboard() {
            // 実装：APIからデータを取得してダッシュボードを更新
        }
        
        setInterval(updateDashboard, 30000); // 30秒ごとに更新
    </script>
</body>
</html>
```

## 🚀 claude-code-cluster統合

### 1. 自動監視の統合
```bash
# claude-code-cluster監視との統合
cd /tmp/claude-code-cluster
source venv/bin/activate

# 監視用エージェントの起動
python3 hooks/universal-agent-auto-loop-with-logging.py MONITOR itdojp ITDO_ERP2 \
  --specialization "Monitoring & Alert Specialist" \
  --labels monitoring alert system \
  --keywords monitor alert health status \
  --max-iterations 1000 \
  --cooldown 300
```

### 2. ログ統合
```bash
# 監視ログとエージェントログの統合
python3 hooks/view-command-logs.py --agent MONITOR-ITDO_ERP2 --follow
```

---
**監視システム設定完了**: _______________
**次回メンテナンス**: _______________
**アラート閾値**: CPU 80%, Memory 85%, GitHub API 100req