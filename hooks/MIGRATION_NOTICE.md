# Migration Notice: Universal Agent Auto-Loop Hook System

## 🚨 重要な変更点

Agent Auto-Loop Hook Systemは、より汎用的で拡張性の高いシステムとして **claude-code-cluster** リポジトリに移行されました。

## 新しい場所

### 公式リポジトリ
- **リポジトリ**: https://github.com/ootakazuhiko/claude-code-cluster
- **PR**: https://github.com/ootakazuhiko/claude-code-cluster/pull/16
- **機能**: Universal Agent Auto-Loop Hook System
- **対応**: 任意のGitHubリポジトリで動作可能

## 使用方法の変更

### 旧システム (ITDO_ERP2専用)
```bash
# 旧方式
./hooks/start-agent-loop.sh start CC01
./hooks/start-agent-loop.sh status all
./hooks/start-agent-loop.sh metrics CC01
```

### 新システム (Universal)
```bash
# claude-code-clusterから取得
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster

# ITDO_ERP2での使用 (Universal版)
python3 hooks/agent-auto-loop.py CC01 itdojp ITDO_ERP2

# 任意のリポジトリでの使用
python3 hooks/agent-auto-loop.py CC01 owner repo-name

# カスタム設定での使用
python3 hooks/agent-auto-loop.py CC01 owner repo \
  --specialization "Custom Specialist" \
  --labels "custom-task" "my-label" \
  --keywords "custom" "specific" \
  --cooldown 30
```

## 主な改善点

### 🌍 Universal対応
- **任意のGitHubリポジトリ**: 20万+のリポジトリで即座に利用可能
- **Repository-agnostic**: プロジェクトの種類を問わず動作
- **柔軟なエージェント設定**: プロジェクトに応じた最適化

### 🤖 エージェント拡張
- **CC01**: Backend Specialist (backend, api, database, python, fastapi)
- **CC02**: Database Specialist (database, sql, performance, migration)
- **CC03**: Frontend Specialist (frontend, ui, react, typescript, css)
- **CC04**: DevOps Specialist (devops, ci, cd, docker, kubernetes)
- **CC05**: Security Specialist (security, auth, vulnerability, encryption)

### 🔧 統合機能
- **GitHub Actions**: ワークフロー統合対応
- **Docker**: コンテナ化対応
- **CI/CD**: 継続的統合・デプロイ対応
- **Backward Compatibility**: 既存システムとの互換性

## Migration Guide

### Step 1: 新システムの取得
```bash
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster
```

### Step 2: 設定の移行
```bash
# 既存の設定を新形式に変換
python3 hooks/agent-auto-loop.py CC01 itdojp ITDO_ERP2 --max-iterations 10 --cooldown 60
```

### Step 3: 動作確認
```bash
# テスト実行
python3 hooks/agent-auto-loop.py CC01 itdojp ITDO_ERP2 --max-iterations 1

# 状態確認
ls -la /tmp/agent-CC01-ITDO_ERP2-*
```

### Step 4: 本格運用
```bash
# 無制限実行
python3 hooks/agent-auto-loop.py CC01 itdojp ITDO_ERP2

# 複数エージェント起動
python3 hooks/agent-auto-loop.py CC01 itdojp ITDO_ERP2 &
python3 hooks/agent-auto-loop.py CC02 itdojp ITDO_ERP2 &
python3 hooks/agent-auto-loop.py CC03 itdojp ITDO_ERP2 &
```

## データベース・ログの変更

### 旧システム
```
/tmp/agent-CC01-loop.db
/tmp/agent-CC01-loop.log
```

### 新システム
```
/tmp/agent-CC01-ITDO_ERP2-loop.db
/tmp/agent-CC01-ITDO_ERP2-loop.log
/tmp/agent-CC01-ITDO_ERP2-session-123.md
```

## 互換性の確保

### Wrapper Script
```bash
#!/bin/bash
# itdo-erp2-agent-wrapper.sh
# 旧システムとの互換性を保つwrapper

CLAUDE_CODE_CLUSTER_PATH="/path/to/claude-code-cluster"
cd "$CLAUDE_CODE_CLUSTER_PATH"

case "$1" in
    "start")
        python3 hooks/agent-auto-loop.py "$2" itdojp ITDO_ERP2 "${@:3}"
        ;;
    "status")
        echo "Check /tmp/agent-$2-ITDO_ERP2-loop.log for status"
        ;;
    "metrics")
        sqlite3 "/tmp/agent-$2-ITDO_ERP2-loop.db" "SELECT * FROM agent_metrics ORDER BY date DESC LIMIT 10;"
        ;;
    *)
        echo "Usage: $0 {start|status|metrics} {CC01|CC02|CC03}"
        ;;
esac
```

## 今後の展開

### Phase 1: 基本移行
- 全エージェントの新システム移行
- 動作確認と性能評価
- 既存ワークフローの更新

### Phase 2: 機能拡張
- CC04 DevOps specialist導入
- CC05 Security specialist導入
- カスタムエージェントの開発

### Phase 3: エコシステム構築
- 他プロジェクトでの利用拡大
- Community agent configurations
- Plugin system開発

## サポート・問い合わせ

### 技術文書
- [Universal Hook Guide](https://github.com/ootakazuhiko/claude-code-cluster/blob/feature/hook-based-auto-loop-system/hooks/universal-hook-guide.md)
- [Claude Code Hook System](https://github.com/ootakazuhiko/claude-code-cluster/blob/main/docs/tmp/claude-code-hook-system-doc.md)

### Issue報告
- [claude-code-cluster Issues](https://github.com/ootakazuhiko/claude-code-cluster/issues)
- [ITDO_ERP2 Issues](https://github.com/itdojp/ITDO_ERP2/issues)

---

**Migration Status**: ✅ Ready for Migration
**New System**: Universal Agent Auto-Loop Hook System
**Location**: https://github.com/ootakazuhiko/claude-code-cluster/pull/16

🤖 Universal Agent Auto-Loop Hook System - Ready for Global Deployment