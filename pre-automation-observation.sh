#!/bin/bash
# 自動化実装前の観察スクリプト

echo "================================================"
echo "自動化システム実装前の環境観察"
echo "実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

echo -e "\n[1] プロセス状況確認"
echo "----------------------------------------"
echo "# Claude関連プロセス:"
ps aux | grep -E "(claude|Claude|agent-work|sleep 900)" | grep -v grep || echo "  該当プロセスなし"

echo -e "\n# bashプロセス（エージェントのシェル）:"
ps aux | grep bash | grep -v grep | tail -5

echo -e "\n[2] 環境変数の痕跡確認"
echo "----------------------------------------"
echo "# .bashrcの確認:"
grep -E "(CLAUDE|AGENT)" ~/.bashrc 2>/dev/null || echo "  CLAUDE/AGENT関連の設定なし"

echo -e "\n# .bash_historyから履歴確認:"
grep -E "(agent-init|my-tasks|CLAUDE)" ~/.bash_history 2>/dev/null | tail -5 || echo "  関連コマンド履歴なし"

echo -e "\n[3] 状態ファイルの確認"
echo "----------------------------------------"
echo "# ホームディレクトリ:"
ls -la ~/ | grep -E "(claude|agent|state)" || echo "  関連ファイルなし"

echo "# /tmpディレクトリ:"
ls -la /tmp/ | grep -E "(claude|agent)" 2>/dev/null || echo "  関連ファイルなし"

echo -e "\n[4] 作業ディレクトリの状態"
echo "----------------------------------------"
echo "# スクリプトの存在と権限:"
ls -la /mnt/c/work/ITDO_ERP2/scripts/claude-code-automation/agent/ 2>/dev/null | grep -E "(init|work|health)" || echo "  スクリプトディレクトリが見つかりません"

echo -e "\n[5] GitHub CLI の状態"
echo "----------------------------------------"
echo "# 認証状態:"
gh auth status 2>&1 || echo "  GitHub CLI未認証"

echo "# 設定確認:"
gh config list 2>/dev/null || echo "  設定情報なし"

echo -e "\n[6] システムリソース"
echo "----------------------------------------"
echo "# メモリ使用状況:"
free -h | grep -E "(total|Mem|Swap)"

echo "# ディスク使用状況:"
df -h | grep -E "(/mnt/c|Filesystem)"

echo -e "\n[7] ネットワーク接続"
echo "----------------------------------------"
echo "# GitHub API接続テスト:"
curl -s -o /dev/null -w "GitHub API応答時間: %{time_total}秒\n" https://api.github.com || echo "  接続失敗"

echo -e "\n[8] 最近のGit活動"
echo "----------------------------------------"
cd /mnt/c/work/ITDO_ERP2 2>/dev/null && {
    echo "# 最新5件のコミット:"
    git log --oneline -5
    
    echo -e "\n# 現在のブランチ:"
    git branch --show-current
    
    echo -e "\n# 変更されたファイル:"
    git status --short
} || echo "  Gitリポジトリにアクセスできません"

echo -e "\n[9] エージェント痕跡の総合診断"
echo "----------------------------------------"
AGENT_TRACES=0

# プロセスチェック
ps aux | grep -E "(agent-work|sleep 900)" | grep -v grep > /dev/null && ((AGENT_TRACES++))

# 環境変数チェック
[ ! -z "$CLAUDE_AGENT_ID" ] && ((AGENT_TRACES++))

# 状態ファイルチェック
[ -f ~/.claude-agent-state ] && ((AGENT_TRACES++))

# 履歴チェック
grep -q "agent-init" ~/.bash_history 2>/dev/null && ((AGENT_TRACES++))

echo "検出された痕跡: $AGENT_TRACES/4"
if [ $AGENT_TRACES -eq 0 ]; then
    echo "➜ 診断: 自動化システムは一度も実行されていません"
elif [ $AGENT_TRACES -lt 3 ]; then
    echo "➜ 診断: 部分的に実行された形跡がありますが、完全ではありません"
else
    echo "➜ 診断: 自動化システムが実行された形跡があります"
fi

echo -e "\n================================================"
echo "観察完了"
echo "================================================"