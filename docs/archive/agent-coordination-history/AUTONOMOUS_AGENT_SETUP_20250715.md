# 自律エージェントセットアップガイド 2025-07-15

## 🎯 目的

CC01, CC02, CC03の自律的な作業継続を実現するため、claude-code-clusterの自動ループシステムを活用します。

## 🚀 セットアップ手順

### 1. 環境準備

```bash
# claude-code-clusterディレクトリに移動
cd /tmp/claude-code-cluster

# Python仮想環境をアクティベート
source venv/bin/activate

# 最新版を取得
git pull origin main

# 依存関係を更新
pip install -r requirements.txt
```

### 2. ログディレクトリの準備

```bash
# ログディレクトリを作成
mkdir -p /tmp/claude-code-logs
chmod 755 /tmp/claude-code-logs

# ITDO_ERP2専用ログディレクトリ
mkdir -p /tmp/claude-code-logs/itdo-erp2
chmod 755 /tmp/claude-code-logs/itdo-erp2
```

### 3. エージェント起動スクリプト

#### CC01: Frontend & Technical Leader
```bash
#!/bin/bash
# CC01 自律エージェント起動スクリプト

cd /tmp/claude-code-cluster
source venv/bin/activate

python3 hooks/universal-agent-auto-loop-with-logging.py CC01 itdojp ITDO_ERP2 \
  --specialization "Frontend & Technical Leader" \
  --labels frontend authentication testing leadership ui-ux \
  --keywords frontend react typescript authentication testing leadership ui ux \
  --max-iterations 5 \
  --cooldown 300 \
  --log-level INFO \
  --priority-labels claude-code-task,frontend,cc01 \
  --working-directory /mnt/c/work/ITDO_ERP2/frontend &

CC01_PID=$!
echo "CC01 started with PID: $CC01_PID"
echo $CC01_PID > /tmp/claude-code-logs/cc01.pid
```

#### CC02: Backend & Database Specialist
```bash
#!/bin/bash
# CC02 自律エージェント起動スクリプト

cd /tmp/claude-code-cluster
source venv/bin/activate

python3 hooks/universal-agent-auto-loop-with-logging.py CC02 itdojp ITDO_ERP2 \
  --specialization "Backend & Database Specialist" \
  --labels backend database api sqlalchemy fastapi \
  --keywords backend python fastapi sqlalchemy postgresql redis database api \
  --max-iterations 5 \
  --cooldown 300 \
  --log-level INFO \
  --priority-labels claude-code-task,backend,cc02 \
  --working-directory /mnt/c/work/ITDO_ERP2/backend &

CC02_PID=$!
echo "CC02 started with PID: $CC02_PID"
echo $CC02_PID > /tmp/claude-code-logs/cc02.pid
```

#### CC03: Infrastructure & CI/CD Expert
```bash
#!/bin/bash
# CC03 自律エージェント起動スクリプト

cd /tmp/claude-code-cluster
source venv/bin/activate

python3 hooks/universal-agent-auto-loop-with-logging.py CC03 itdojp ITDO_ERP2 \
  --specialization "Infrastructure & CI/CD Expert" \
  --labels infrastructure ci-cd testing deployment docker \
  --keywords infrastructure ci cd testing deployment docker podman pipeline \
  --max-iterations 5 \
  --cooldown 300 \
  --log-level INFO \
  --priority-labels claude-code-task,infrastructure,cc03 \
  --working-directory /mnt/c/work/ITDO_ERP2 &

CC03_PID=$!
echo "CC03 started with PID: $CC03_PID"
echo $CC03_PID > /tmp/claude-code-logs/cc03.pid
```

### 4. 統合管理スクリプト

```bash
#!/bin/bash
# 全エージェント管理スクリプト

SCRIPT_DIR="/tmp/claude-code-cluster"
LOG_DIR="/tmp/claude-code-logs"

start_all() {
    echo "🚀 Starting all agents..."
    
    # CC01 start
    bash start_cc01.sh
    sleep 5
    
    # CC02 start
    bash start_cc02.sh
    sleep 5
    
    # CC03 start
    bash start_cc03.sh
    sleep 5
    
    echo "✅ All agents started"
    status_all
}

stop_all() {
    echo "🛑 Stopping all agents..."
    
    # Kill agents by PID
    for pid_file in $LOG_DIR/*.pid; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo "Stopped agent with PID: $PID"
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Kill any remaining processes
    pkill -f "universal-agent-auto-loop-with-logging.py"
    
    echo "✅ All agents stopped"
}

status_all() {
    echo "📊 Agent Status:"
    
    for agent in CC01 CC02 CC03; do
        PID_FILE="$LOG_DIR/${agent,,}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "✅ $agent: Running (PID: $PID)"
            else
                echo "❌ $agent: Not running (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            echo "❌ $agent: Not running"
        fi
    done
}

logs_all() {
    echo "📋 Starting log monitoring..."
    cd $SCRIPT_DIR
    source venv/bin/activate
    python3 hooks/view-command-logs.py --follow
}

stats_all() {
    echo "📈 Agent Statistics:"
    cd $SCRIPT_DIR
    source venv/bin/activate
    python3 hooks/view-command-logs.py --stats
}

case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    status)
        status_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    logs)
        logs_all
        ;;
    stats)
        stats_all
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|logs|stats}"
        exit 1
        ;;
esac
```

## 📊 モニタリングとアラート

### 1. リアルタイムモニタリング

```bash
# 全エージェントのリアルタイムログ
cd /tmp/claude-code-cluster
source venv/bin/activate
python3 hooks/view-command-logs.py --follow

# 特定エージェントの監視
python3 hooks/view-command-logs.py --agent CC01-ITDO_ERP2 --follow

# 統計情報の表示
python3 hooks/view-command-logs.py --stats
```

### 2. パフォーマンス監視

```bash
# システムリソース監視
top -p $(pgrep -f "universal-agent-auto-loop")

# メモリ使用量確認
ps aux | grep "universal-agent-auto-loop" | awk '{print $6}' | paste -sd+ | bc

# ディスク使用量確認
du -sh /tmp/claude-code-logs/
```

### 3. アラート設定

```bash
#!/bin/bash
# 簡単なアラートスクリプト

check_agents() {
    STOPPED_AGENTS=""
    
    for agent in CC01 CC02 CC03; do
        PID_FILE="/tmp/claude-code-logs/${agent,,}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ! kill -0 "$PID" 2>/dev/null; then
                STOPPED_AGENTS="$STOPPED_AGENTS $agent"
            fi
        else
            STOPPED_AGENTS="$STOPPED_AGENTS $agent"
        fi
    done
    
    if [ -n "$STOPPED_AGENTS" ]; then
        echo "🚨 ALERT: Agents stopped:$STOPPED_AGENTS at $(date)"
        # ここでSlack通知やメール送信を追加可能
    fi
}

# 5分ごとにチェック
while true; do
    check_agents
    sleep 300
done
```

## 🔧 トラブルシューティング

### 1. エージェントが起動しない

```bash
# ログの確認
cd /tmp/claude-code-cluster
source venv/bin/activate
python3 hooks/view-command-logs.py --limit 20

# プロセスの確認
ps aux | grep "universal-agent-auto-loop"

# 手動テスト
python3 hooks/universal-agent-auto-loop-with-logging.py --help
```

### 2. ログが記録されない

```bash
# ログディレクトリの権限確認
ls -la /tmp/claude-code-logs/
chmod 755 /tmp/claude-code-logs/

# SQLiteデータベースの確認
sqlite3 /tmp/claude-code-logs/agent-*/command_history.db ".tables"
```

### 3. 高負荷時の対応

```bash
# クールダウン時間の調整
# --cooldown 300 を --cooldown 600 に変更

# 並行数の削減
# --max-iterations 5 を --max-iterations 3 に変更
```

## 📋 運用ベストプラクティス

### 1. 段階的起動
- 最初はCC01のみ起動
- 安定動作確認後、CC02を追加
- 最後にCC03を追加

### 2. 定期的なメンテナンス
- 1時間ごとのstatus確認
- 4時間ごとのログローテーション
- 1日ごとのstatistics確認

### 3. 緊急時対応
- 全エージェント停止: `bash manage_agents.sh stop`
- 個別エージェント停止: `kill $(cat /tmp/claude-code-logs/cc01.pid)`
- 緊急再起動: `bash manage_agents.sh restart`

---
**セットアップ完了時刻**: _______________
**次回メンテナンス**: _______________