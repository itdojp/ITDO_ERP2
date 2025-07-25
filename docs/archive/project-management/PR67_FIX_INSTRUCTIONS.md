# PR #67 修正手順書

## 概要
PR #67はRuffの警告修正とコードクリーンアップを行うPRですが、例外クラス名の変更（NotFound → NotFoundError）がメインブランチと競合しているため、CIがfailしています。この手順書に従って修正してください。

## 現在の状況
- PR番号: #67
- ブランチ名: `feature/issue-64-cleanup-and-ruff-fixes`
- 状態: Draft
- 問題: 例外クラス名にErrorサフィックスを追加したが、メインブランチは元の名前を使用している

## 修正手順

### 1. ブランチの確認と切り替え
```bash
# 現在のブランチを確認
git branch

# PR #67のブランチに切り替え
git checkout feature/issue-64-cleanup-and-ruff-fixes

# 最新の状態を取得
git fetch origin
git pull origin feature/issue-64-cleanup-and-ruff-fixes
```

### 2. 例外クラス名を元に戻す

#### 2.1 app/core/exceptions.pyの修正
以下の例外クラス名から"Error"サフィックスを削除してください：

**変更前（現在）:**
- `NotFoundError` → `NotFound`
- `TaskNotFoundError` → `TaskNotFound`
- `ProjectNotFoundError` → `ProjectNotFound`
- `UserNotFoundError` → `UserNotFound`
- `OrganizationNotFoundError` → `OrganizationNotFound`
- その他の `*Error` という名前の例外クラスがあれば同様に修正

**注意:** 以下のクラスは元から"Error"が付いているので変更しない：
- `AuthenticationError`
- `ExpiredTokenError`
- `InvalidTokenError`
- `AuthorizationError`
- `ValidationError`
- `DependencyError`
- `CircularDependencyError`
- `DatabaseError`
- `DuplicateError`

### 3. インポート文の修正

以下のファイルで例外クラスのインポート文を修正してください：

#### 3.1 確認が必要なファイル
```bash
# grepコマンドで影響を受けるファイルを確認
cd /mnt/c/work/ITDO_ERP2/backend
rg "from app\.core\.exceptions import.*NotFoundError" --type py
rg "from app\.core\.exceptions import.*TaskNotFoundError" --type py
rg "from app\.core\.exceptions import.*ProjectNotFoundError" --type py
rg "from app\.core\.exceptions import.*UserNotFoundError" --type py
rg "from app\.core\.exceptions import.*OrganizationNotFoundError" --type py
```

#### 3.2 修正が必要な主要ファイル
- `app/services/task.py`
- `app/services/auth.py`
- `app/services/user.py`（存在する場合）
- `app/services/project.py`（存在する場合）
- `app/services/organization.py`（存在する場合）
- `app/api/v1/endpoints/tasks.py`（存在する場合）
- `app/api/v1/endpoints/users.py`（存在する場合）
- `app/api/v1/endpoints/projects.py`（存在する場合）
- `tests/test_task_management/unit/test_task_service.py`
- `tests/unit/test_security.py`
- その他テストファイル

#### 3.3 インポート文の修正例
```python
# 修正前
from app.core.exceptions import TaskNotFoundError, UserNotFoundError

# 修正後
from app.core.exceptions import TaskNotFound, UserNotFound
```

### 4. 例外の使用箇所を修正

#### 4.1 raiseステートメントの修正
```python
# 修正前
raise TaskNotFoundError(task_id=task_id)

# 修正後
raise TaskNotFound(task_id=task_id)
```

#### 4.2 except節の修正
```python
# 修正前
except TaskNotFoundError:
    # 処理

# 修正後
except TaskNotFound:
    # 処理
```

#### 4.3 isinstance()チェックの修正
```python
# 修正前
if isinstance(e, TaskNotFoundError):
    # 処理

# 修正後
if isinstance(e, TaskNotFound):
    # 処理
```

### 5. テストの実行と確認

#### 5.1 全テストを実行
```bash
cd /mnt/c/work/ITDO_ERP2/backend
uv run pytest -v
```

#### 5.2 型チェックを実行
```bash
cd /mnt/c/work/ITDO_ERP2/backend
uv run mypy app/
```

#### 5.3 Ruffチェックを実行
```bash
cd /mnt/c/work/ITDO_ERP2/backend
uv run ruff check .
uv run ruff format . --check
```

### 6. コミットとプッシュ

#### 6.1 変更をステージング
```bash
git add -A
git status  # 変更内容を確認
```

#### 6.2 コミット
```bash
git commit -m "fix: Revert exception names to original (remove Error suffix)

- Reverted NotFoundError back to NotFound
- Reverted TaskNotFoundError back to TaskNotFound
- Reverted ProjectNotFoundError back to ProjectNotFound
- Reverted UserNotFoundError back to UserNotFound
- Reverted OrganizationNotFoundError back to OrganizationNotFound
- Updated all imports and usages accordingly
- Kept all other Ruff fixes and cleanups

This change resolves conflicts with the main branch while maintaining
all other code improvements from the cleanup effort."
```

#### 6.3 プッシュ
```bash
git push origin feature/issue-64-cleanup-and-ruff-fixes
```

### 7. PRをDraftから通常のPRに変更

GitHubでPR #67を開き、以下の手順でDraftを解除：

1. PR #67のページを開く
2. 右側の"Ready for review"ボタンをクリック
3. PR descriptionを更新（必要に応じて）：
   ```
   ## 概要
   Issue #64: Ruffの警告修正とコードクリーンアップ
   
   ## 変更内容
   - ✅ Ruffの警告をすべて修正
   - ✅ 不要なインポートを削除
   - ✅ コードフォーマットを統一
   - ✅ 例外クラス名を元の命名規則に維持（メインブランチとの互換性のため）
   
   ## テスト
   - ✅ 全ユニットテストがパス
   - ✅ 型チェック（mypy）がパス
   - ✅ Ruffチェックがパス
   ```

### 8. CIの確認

1. GitHub ActionsでCIが正常に実行されることを確認
2. すべてのチェックが緑色になることを確認
3. 問題があれば、エラーログを確認して追加修正

## 重要な注意事項

1. **他のRuff修正は維持する**: 例外名以外のRuff修正（インポート整理、フォーマット等）はそのまま維持してください
2. **テストの確認**: 変更後、必ずすべてのテストが通ることを確認してください
3. **型チェック**: mypyでエラーが出ないことを確認してください
4. **競合の解決**: もしメインブランチとの競合が発生した場合は、例外名は常に"Error"サフィックスなしの元の名前を使用してください

## トラブルシューティング

### テストが失敗する場合
```bash
# 特定のテストのみ実行して詳細を確認
uv run pytest -v tests/test_task_management/unit/test_task_service.py -k "特定のテスト名"
```

### 型チェックエラーが出る場合
```bash
# 特定のファイルのみチェック
uv run mypy app/services/task.py
```

### インポートエラーが残っている場合
```bash
# 全体を検索して見逃しを確認
rg "NotFoundError|TaskNotFoundError|ProjectNotFoundError|UserNotFoundError|OrganizationNotFoundError" --type py
```

## 完了チェックリスト

- [ ] feature/issue-64-cleanup-and-ruff-fixesブランチに切り替え済み
- [ ] app/core/exceptions.pyの例外名を元に戻した
- [ ] すべてのインポート文を修正した
- [ ] すべての例外使用箇所を修正した
- [ ] 全テストがパスする
- [ ] mypyチェックがパスする
- [ ] Ruffチェックがパスする
- [ ] 変更をコミット・プッシュした
- [ ] PRをDraftから通常のPRに変更した
- [ ] GitHub ActionsのCIが成功した

以上の手順に従って修正を行ってください。不明な点があれば、コメントで質問してください。