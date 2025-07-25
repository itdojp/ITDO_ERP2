# Agent Sonnet Configuration System - 移行完了

## 重要な変更
Agent Sonnet Configuration Systemは、ITDO_ERP2プロジェクト固有の機能ではなく、Claude開発基盤の共通システムとして `claude-code-cluster` リポジトリに移行されました。

## 新しい場所
- **リポジトリ**: https://github.com/ootakazuhiko/claude-code-cluster
- **PR**: https://github.com/ootakazuhiko/claude-code-cluster/pull/15
- **Issue**: https://github.com/ootakazuhiko/claude-code-cluster/issues/14

## 使用方法
ITDO_ERP2プロジェクトでAgent Sonnet systemを使用する場合は、claude-code-clusterから取得してください：

```bash
# claude-code-clusterから取得
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster

# エージェント起動
./start-agent-sonnet.sh CC01  # Backend
./start-agent-sonnet.sh CC02  # Database
./start-agent-sonnet.sh CC03  # Frontend
```

## 関連リンク
- [claude-code-cluster PR #15](https://github.com/ootakazuhiko/claude-code-cluster/pull/15)
- [ITDO_ERP2 Issue #145](https://github.com/itdojp/ITDO_ERP2/issues/145) - 実装記録

## 移行理由
1. **共通基盤**: 複数プロジェクトで使用可能
2. **保守性**: 中央集権的管理
3. **再利用性**: 他のクラウド開発プロジェクトでも利用可能

---
🤖 Generated with Claude Code (Manager Mode: Opus)