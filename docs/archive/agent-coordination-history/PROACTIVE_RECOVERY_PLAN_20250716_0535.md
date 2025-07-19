# プロアクティブ回復計画 - 2025-07-16 05:35

## 🚀 段階的回復シナリオ

### Phase 1: CC03主導修正（05:35-06:00）

#### 自動修正スクリプト（CC03サポート用）
```python
#!/usr/bin/env python3
# auto_fix_user_model.py

import re
from pathlib import Path

def fix_merge_conflicts():
    """user.pyのマージ競合を自動解決"""
    file_path = Path("/mnt/c/work/ITDO_ERP2/backend/app/models/user.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # マージ競合パターン
    conflict_pattern = r'<<<<<<< HEAD.*?=======.*?>>>>>>> origin/main'
    
    # is_locked()メソッドの統合版
    unified_is_locked = '''    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        
        # 統一されたタイムゾーン処理
        now = datetime.now(timezone.utc)
        locked_until = self.locked_until
        
        # locked_untilがnaiveの場合、UTCとして扱う
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        
        return now < locked_until'''
    
    # マージ競合を解決
    content = re.sub(
        r'<<<<<<< HEAD.*?def is_locked.*?>>>>>>> origin/main',
        unified_is_locked,
        content,
        flags=re.DOTALL
    )
    
    # UserSessionフィルタの競合解決
    content = re.sub(
        r'<<<<<<< HEAD.*?UserSession\.expires_at.*?>>>>>>> origin/main',
        '                UserSession.expires_at > datetime.now(),',
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Merge conflicts resolved")

def fix_type_errors():
    """型エラーの修正"""
    file_path = Path("/mnt/c/work/ITDO_ERP2/backend/app/models/user.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Line 121付近の不要なreturn文を探して削除
    for i in range(120, 140):
        if i < len(lines) and lines[i].strip() == "return None":
            # create_userメソッド内の不要なreturn文
            if i > 0 and "return user" in lines[i-1]:
                lines[i] = ""  # 削除
                print(f"✅ Removed unreachable return at line {i+1}")
    
    with open(file_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    print("Starting automatic fixes...")
    fix_merge_conflicts()
    fix_type_errors()
    print("✅ All fixes applied")
```

### Phase 2: 並列タスク実行（06:00-06:30）

#### タスク分配スクリプト
```bash
#!/bin/bash
# distribute_tasks.sh

# CC03: バックエンド修正継続
cat > /tmp/cc03_tasks.md << EOF
## CC03 継続タスク (06:00-06:30)
1. [ ] CI環境変数の追加（.github/workflows/*.yml）
2. [ ] backend型チェック完全通過確認
3. [ ] テストの再実行と結果確認
EOF

# CC01: フロントエンド確認（CC03の修正後）
cat > /tmp/cc01_tasks.md << EOF
## CC01 復帰タスク (06:00-06:30)
1. [ ] TypeScript型エラーの確認と修正
2. [ ] フロントエンドビルドの確認
3. [ ] E2Eテスト準備状況の確認
EOF

# CC02: インフラ支援（必要に応じて）
cat > /tmp/cc02_tasks.md << EOF
## CC02 支援タスク (06:00-06:30)
1. [ ] Dockerイメージのビルド確認
2. [ ] 依存関係の更新確認
3. [ ] セキュリティスキャン結果の確認
EOF
```

### Phase 3: 統合テスト（06:30-07:00）

#### 自動統合テストスクリプト
```python
#!/usr/bin/env python3
# integration_test_runner.py

import subprocess
import time
from datetime import datetime

class IntegrationTestRunner:
    def __init__(self):
        self.results = {
            "backend": None,
            "frontend": None,
            "e2e": None,
            "ci_checks": None
        }
        
    def run_backend_tests(self):
        """バックエンドテスト実行"""
        print("🔧 Running backend tests...")
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/", "-v", "--tb=short"],
            cwd="/mnt/c/work/ITDO_ERP2/backend",
            capture_output=True,
            text=True
        )
        self.results["backend"] = result.returncode == 0
        return self.results["backend"]
    
    def run_frontend_tests(self):
        """フロントエンドテスト実行"""
        print("🎨 Running frontend tests...")
        result = subprocess.run(
            ["npm", "test", "--", "--run"],
            cwd="/mnt/c/work/ITDO_ERP2/frontend",
            capture_output=True,
            text=True
        )
        self.results["frontend"] = result.returncode == 0
        return self.results["frontend"]
    
    def check_ci_status(self):
        """CI状態確認"""
        print("📊 Checking CI status...")
        result = subprocess.run(
            ["gh", "pr", "checks", "124"],
            capture_output=True,
            text=True
        )
        failures = result.stdout.count("fail")
        self.results["ci_checks"] = failures == 0
        return self.results["ci_checks"]
    
    def generate_report(self):
        """統合レポート生成"""
        report = f"""
# Integration Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Test Results
- Backend: {'✅ PASS' if self.results['backend'] else '❌ FAIL'}
- Frontend: {'✅ PASS' if self.results['frontend'] else '❌ FAIL'}
- CI Checks: {'✅ PASS' if self.results['ci_checks'] else '❌ FAIL'}

## Overall Status
{'🎉 All tests passed!' if all(self.results.values()) else '⚠️ Some tests failed'}
"""
        return report
    
    def run_all(self):
        """全テスト実行"""
        self.run_backend_tests()
        self.run_frontend_tests()
        self.check_ci_status()
        return self.generate_report()

if __name__ == "__main__":
    runner = IntegrationTestRunner()
    report = runner.run_all()
    print(report)
    
    # GitHubへの報告
    if all(runner.results.values()):
        subprocess.run([
            "gh", "pr", "comment", "124",
            "--body", "✅ All integration tests passed! Ready for merge."
        ])
```

## 🔄 継続的改善プロセス

### 1. 問題パターン学習
```yaml
learned_patterns:
  merge_conflicts:
    - is_locked()メソッドのタイムゾーン処理
    - UserSessionのexpires_atフィルタ
  type_errors:
    - 到達不可能なreturn文
    - permissions属性の型不一致
  ci_failures:
    - 環境変数の不足
    - タイムゾーン設定
```

### 2. 予防策の実装
```bash
#!/bin/bash
# preventive_checks.sh

# プルリクエスト作成前のチェック
pre_pr_check() {
    echo "🔍 Running pre-PR checks..."
    
    # 1. マージ競合の事前確認
    git fetch origin main
    git merge origin/main --no-commit --no-ff
    if [ $? -ne 0 ]; then
        echo "⚠️ Potential merge conflicts detected"
        git merge --abort
    fi
    
    # 2. 型チェック
    cd backend && uv run mypy app/ --strict
    cd ../frontend && npm run typecheck
    
    # 3. ローカルテスト
    cd ../backend && uv run pytest tests/unit/ -x
    cd ../frontend && npm test -- --run
}
```

### 3. エージェント協調改善
```markdown
## エージェント役割最適化

### CC01 (Frontend Leader)
- PRレビューの最終確認
- フロントエンド品質保証
- 他エージェントの調整

### CC02 (Backend Specialist)
- データベース関連の修正
- APIエンドポイントの実装
- パフォーマンス最適化

### CC03 (Infrastructure Expert)
- CI/CD修正と最適化
- 環境設定の管理
- 自動化スクリプトの作成
```

## 📱 通知とモニタリング

### リアルタイム通知システム
```python
#!/usr/bin/env python3
# realtime_notifier.py

import subprocess
import json
from datetime import datetime

def check_and_notify():
    """状態チェックと通知"""
    # PR状態取得
    pr_status = subprocess.run(
        ["gh", "pr", "view", "124", "--json", "state,mergeable"],
        capture_output=True,
        text=True
    )
    
    if pr_status.returncode == 0:
        data = json.loads(pr_status.stdout)
        
        # マージ可能になった場合
        if data.get("mergeable") == "MERGEABLE":
            notify("🎉 PR #124 is now mergeable!")
            
            # エージェントへの通知
            subprocess.run([
                "gh", "issue", "create",
                "--title", "PR #124 Ready for Merge",
                "--body", "CC01, CC02, CC03: PR #124 is ready for final review and merge.",
                "--label", "urgent,merge-ready"
            ])

def notify(message):
    """通知送信"""
    print(f"[{datetime.now()}] {message}")
    # 追加の通知チャンネル（Slack, Discord等）への送信

if __name__ == "__main__":
    check_and_notify()
```

---
**計画作成**: 2025-07-16 05:35
**Phase 1開始**: 即座
**完全回復目標**: 07:00
**次回評価**: 06:00