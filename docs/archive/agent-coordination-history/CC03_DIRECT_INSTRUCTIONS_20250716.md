# CC03への直接指示 - 緊急修正

## 🚨 最優先タスク（30分以内完了）

### 1. マージ競合解決
```bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/auth-edge-cases

# backend/app/models/user.pyの編集
# 以下の行を確認して修正:
# - 258-291行目: is_locked()メソッド
# - 311-314行目: UserSessionフィルタ
```

### 2. 具体的な修正内容

#### is_locked()メソッド（258-291行目を以下に置換）
```python
def is_locked(self) -> bool:
    """Check if account is locked."""
    if not self.locked_until:
        return False
    
    now = datetime.now(timezone.utc)
    locked_until = self.locked_until
    
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    
    return now < locked_until
```

#### UserSessionフィルタ（311-314行目）
```python
.filter(
    UserSession.user_id == self.id,
    UserSession.is_active,
    UserSession.expires_at > datetime.now(),
)
```

### 3. 型エラー修正
- **121行目付近**: `return None`が`return user`の後にある場合は削除
- **442-473行目**: get_effective_permissionsメソッド内でpermissionsがlist型として扱われている箇所を修正

### 4. コミット&プッシュ
```bash
git add backend/app/models/user.py
git commit -m "fix: Resolve merge conflicts and type errors in user model

- Fixed is_locked() timezone handling merge conflict
- Fixed UserSession filter merge conflict
- Removed unreachable return statement
- Fixed type inconsistencies in get_effective_permissions"

git push origin feature/auth-edge-cases
```

### 5. CI再実行
```bash
gh pr comment 124 --body "Fixed merge conflicts and type errors. Rerunning CI."
```

## ✅ 完了確認項目
- [ ] マージ競合マーカー（<<<<<<< HEAD）が全て削除されている
- [ ] `grep -n "<<<<<<" backend/app/models/user.py` で何も表示されない
- [ ] `cd backend && uv run python -m py_compile app/models/user.py` でエラーなし

## 📊 成功基準
- CI/CDのTypeScriptエラーが減少
- Backend testが通過開始
- マージ可能状態への移行

---
**締切**: 2025-07-16 06:00
**優先度**: 最高
**期待所要時間**: 20-30分