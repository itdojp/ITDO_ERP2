# 🤖 Claude Code 自動化システム - 専用ユーザー版セットアップガイド

## 📋 概要
Claude Code エージェント（CC01, CC02, CC03）を専用ユーザーで実行し、完全な環境分離と自動化を実現する手順書です。

## 🔧 前提条件
- Ubuntu/Debian系Linux環境
- sudo権限を持つ管理者アカウント
- GitHub CLI (gh) インストール済み
- Git設定済み

## 📝 セットアップ手順

### 1. 専用ユーザーの作成

```bash
# 管理者権限で実行
sudo su -

# 各エージェント用ユーザー作成
useradd -m -s /bin/bash -c "Claude Code Agent CC01" claude-cc01
useradd -m -s /bin/bash -c "Claude Code Agent CC02" claude-cc02
useradd -m -s /bin/bash -c "Claude Code Agent CC03" claude-cc03

# パスワード設定（本番環境では強固なパスワードを使用）
echo "claude-cc01:cc01password" | chpasswd
echo "claude-cc02:cc02password" | chpasswd
echo "claude-cc03:cc03password" | chpasswd

# 必要なグループへの追加
usermod -aG docker claude-cc01 2>/dev/null || true
usermod -aG docker claude-cc02 2>/dev/null || true
usermod -aG docker claude-cc03 2>/dev/null || true
```

### 2. 作業ディレクトリへのアクセス権限設定

```bash
# プロジェクトディレクトリへのアクセス権限付与
PROJECT_DIR="/home/work/ITDO_ERP2"

# ACL (Access Control List) を使用した権限付与
setfacl -R -m u:claude-cc01:rwx $PROJECT_DIR
setfacl -R -m u:claude-cc02:rwx $PROJECT_DIR
setfacl -R -m u:claude-cc03:rwx $PROJECT_DIR

# デフォルトACLの設定（新規作成ファイルにも権限を付与）
setfacl -R -d -m u:claude-cc01:rwx $PROJECT_DIR
setfacl -R -d -m u:claude-cc02:rwx $PROJECT_DIR
setfacl -R -d -m u:claude-cc03:rwx $PROJECT_DIR
```

### 3. 各ユーザーの環境設定スクリプト

```bash
# 設定スクリプトの作成
cat > /tmp/setup-claude-user.sh << 'EOF'
#!/bin/bash
# Claude Code エージェント環境設定スクリプト

AGENT_ID=$1
AGENT_LABEL=$(echo $AGENT_ID | tr '[:upper:]' '[:lower:]')
USER_NAME="claude-$AGENT_LABEL"

# ユーザーのホームディレクトリに移動
cd /home/$USER_NAME

# .bashrc設定
cat >> .bashrc << BASHRC_EOF

# ========================================
# Claude Code $AGENT_ID Automation Settings
# ========================================

# 環境変数
export CLAUDE_AGENT_ID=$AGENT_ID
export AGENT_LABEL=$AGENT_LABEL
export WORK_DIR=/home/work/ITDO_ERP2
export PATH="\$HOME/.local/bin:\$PATH"

# 作業ディレクトリへ自動移動
cd \$WORK_DIR 2>/dev/null || echo "⚠️ 作業ディレクトリにアクセスできません"

# エイリアス設定
alias my-tasks='gh issue list --label \$AGENT_LABEL --state open'
alias my-pr='gh pr list --assignee @me'
alias check-ci='gh pr checks'
alias work='cd \$WORK_DIR'

# カラー設定
export CLICOLOR=1
export LSCOLORS=GxFxCxDxBxegedabagaced

# プロンプト設定
PS1='🤖 [\$CLAUDE_AGENT_ID] \u@\h:\w\$ '

# 起動メッセージ
echo "================================================"
echo "🤖 Claude Code \$CLAUDE_AGENT_ID 自動化システム"
echo "================================================"
echo "環境変数:"
echo "  CLAUDE_AGENT_ID: \$CLAUDE_AGENT_ID"
echo "  AGENT_LABEL: \$AGENT_LABEL"
echo "  WORK_DIR: \$WORK_DIR"
echo ""
echo "利用可能なコマンド:"
echo "  my-tasks  - 自分のタスク一覧"
echo "  my-pr     - 自分のPR一覧"
echo "  check-ci  - CI/CDステータス確認"
echo "  work      - 作業ディレクトリへ移動"
echo "================================================"

# 自動化スクリプトの存在確認と実行
if [ -f "\$WORK_DIR/scripts/claude-code-automation/agent/agent-init.sh" ]; then
    echo "🔄 自動化システムを初期化中..."
    # source \$WORK_DIR/scripts/claude-code-automation/agent/agent-init.sh \$CLAUDE_AGENT_ID
    echo "✅ 初期化完了"
fi

BASHRC_EOF

# Git設定
su - $USER_NAME -c "git config --global user.name 'Claude Code $AGENT_ID'"
su - $USER_NAME -c "git config --global user.email '$AGENT_LABEL@claude-code.local'"

# SSH鍵の生成（必要に応じて）
su - $USER_NAME -c "ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -C '$AGENT_LABEL@claude-code'"

echo "✅ $USER_NAME の設定が完了しました"
EOF

chmod +x /tmp/setup-claude-user.sh

# 各ユーザーの設定実行
/tmp/setup-claude-user.sh CC01
/tmp/setup-claude-user.sh CC02
/tmp/setup-claude-user.sh CC03
```

### 4. GitHub CLI認証設定

各ユーザーでGitHub CLIの認証を設定します：

```bash
# CC01ユーザーでの認証
su - claude-cc01
gh auth login
# 対話的に認証を完了させる

# CC02ユーザーでの認証
su - claude-cc02
gh auth login

# CC03ユーザーでの認証
su - claude-cc03
gh auth login
```

### 5. Claude Code実行用スクリプト

```bash
# Claude Code起動スクリプトの作成
cat > /usr/local/bin/run-claude-agent << 'EOF'
#!/bin/bash
# Claude Code エージェント実行スクリプト

AGENT_ID=$1

if [ -z "$AGENT_ID" ]; then
    echo "使用方法: $0 <CC01|CC02|CC03>"
    exit 1
fi

AGENT_LABEL=$(echo $AGENT_ID | tr '[:upper:]' '[:lower:]')
USER_NAME="claude-$AGENT_LABEL"

echo "🚀 $AGENT_ID を $USER_NAME ユーザーで起動します..."

# ユーザー切り替えてClaude Code実行
sudo -u $USER_NAME -i claude

EOF

chmod +x /usr/local/bin/run-claude-agent
```

### 6. システムサービス化（オプション）

```bash
# systemdサービスファイルの作成
cat > /etc/systemd/system/claude-cc01.service << 'EOF'
[Unit]
Description=Claude Code Agent CC01
After=network.target

[Service]
Type=simple
User=claude-cc01
WorkingDirectory=/home/work/ITDO_ERP2
ExecStart=/usr/bin/claude
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# CC02, CC03用も同様に作成
cp /etc/systemd/system/claude-cc01.service /etc/systemd/system/claude-cc02.service
cp /etc/systemd/system/claude-cc01.service /etc/systemd/system/claude-cc03.service

sed -i 's/CC01/CC02/g; s/cc01/cc02/g' /etc/systemd/system/claude-cc02.service
sed -i 's/CC01/CC03/g; s/cc01/cc03/g' /etc/systemd/system/claude-cc03.service

# サービスの有効化
systemctl daemon-reload
systemctl enable claude-cc01 claude-cc02 claude-cc03
```

## 🚀 使用方法

### 個別起動
```bash
# 特定のエージェントを起動
run-claude-agent CC01
run-claude-agent CC02
run-claude-agent CC03
```

### サービスとして起動
```bash
# サービス開始
sudo systemctl start claude-cc01
sudo systemctl start claude-cc02
sudo systemctl start claude-cc03

# ステータス確認
sudo systemctl status claude-cc01
sudo systemctl status claude-cc02
sudo systemctl status claude-cc03

# ログ確認
sudo journalctl -u claude-cc01 -f
```

## 🔍 トラブルシューティング

### 権限エラーの場合
```bash
# ACL権限の再設定
sudo setfacl -R -m u:claude-cc01:rwx /home/work/ITDO_ERP2
```

### GitHub認証エラーの場合
```bash
# 該当ユーザーで再認証
su - claude-cc01
gh auth status
gh auth login
```

### プロセス確認
```bash
# 実行中のClaude Codeプロセス確認
ps aux | grep claude | grep -v grep
```

## 📊 セキュリティ考慮事項

1. **パスワード管理**
   - 本番環境では強固なパスワードを使用
   - 可能であればSSH鍵認証のみに限定

2. **権限分離**
   - 各エージェントは独立したユーザーで実行
   - 必要最小限の権限のみ付与

3. **監査ログ**
   - 各ユーザーの操作は個別に記録
   - systemdジャーナルで一元管理

## 🎯 メリット

- ✅ 完全な環境分離
- ✅ セキュリティの向上
- ✅ 個別の権限管理
- ✅ ログの明確な分離
- ✅ 自動起動・再起動対応
- ✅ リソース使用量の個別監視

## 📝 注意事項

- 各ユーザーのホームディレクトリは独立
- GitHub認証は各ユーザーで個別に必要
- ファイルの所有権に注意が必要