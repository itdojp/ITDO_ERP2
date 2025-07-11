# Claude Code Automation Tools

## 📋 概要

Claude Codeエージェントの管理と自動化のためのツール集です。将来的に独立したリポジトリとして分離することを前提に設計されています。

## 🗂️ ディレクトリ構造

```
claude-code-automation/
├── agent/              # エージェント側で使用するスクリプト
│   ├── agent-init.sh   # エージェント初期化
│   ├── agent-work.sh   # 自動作業実行
│   └── auto-fix-ci.sh  # CI/CD自動修正
├── pm/                 # PM側で使用するスクリプト
│   ├── distribute-tasks.sh  # タスク配布
│   └── agent-status.sh      # 状態確認
├── docs/               # ドキュメント
│   ├── AGENT_AUTOMATION_GUIDE.md
│   ├── AGENT_STARTUP_PROMPT.md
│   └── MULTI_AGENT_COORDINATION.md
├── config/             # 設定ファイル（将来用）
└── README.md           # このファイル
```

## 🚀 クイックスタート

### PM側（タスク管理者）

```bash
# タスク配布
./scripts/claude-code-automation/pm/distribute-tasks.sh

# 状態確認
./scripts/claude-code-automation/pm/agent-status.sh
```

### エージェント側（Claude Code）

```bash
# 初期化（セッション開始時）
source ./scripts/claude-code-automation/agent/agent-init.sh CC01

# 自動作業実行
./scripts/claude-code-automation/agent/agent-work.sh

# CI/CD修正
./scripts/claude-code-automation/agent/auto-fix-ci.sh [PR番号]
```

## 📦 将来の分離計画

このツールセットは将来的に `claude-code-automation` という独立したリポジトリとして分離される予定です。

### 分離時の構成案

```
github.com/[organization]/claude-code-automation/
├── src/
│   ├── agent/
│   ├── pm/
│   └── common/
├── docs/
├── examples/
├── tests/
└── README.md
```

### 移行手順（将来）

1. 新リポジトリ作成
2. このディレクトリの内容をコピー
3. プロジェクト固有の部分を汎用化
4. パッケージとして公開

## 🔧 カスタマイズ

プロジェクト固有の設定は `config/` ディレクトリに配置予定：

- `config/project.conf` - プロジェクト設定
- `config/agents.json` - エージェント定義
- `config/templates/` - タスクテンプレート

## 📝 ライセンス

現在はITDO ERP2プロジェクトの一部として管理されています。
分離時に適切なライセンスを設定予定。

---

*Version: 0.1.0 (Integrated with ITDO ERP2)*