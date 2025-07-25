# 🚨 緊急：マージコンフリクト解決手順

## 🎯 10分で解決する手順

### Step 1: 影響範囲の確認（1分）
```bash
# Backend (CC02担当)
cd /mnt/c/work/ITDO_ERP2/backend
echo "Backend conflicts: $(grep -r '<<<<<<< HEAD' app/ tests/ 2>/dev/null | wc -l)"

# Frontend (CC01担当)  
cd /mnt/c/work/ITDO_ERP2/frontend
echo "Frontend conflicts: $(grep -r '<<<<<<< HEAD' src/ 2>/dev/null | wc -l)"
```

### Step 2: 自動解決スクリプト（5分）

#### Backend用（app/ディレクトリ）
```bash
#!/bin/bash
# save as fix_conflicts_backend.sh

cd /mnt/c/work/ITDO_ERP2/backend

# Find all Python files with conflicts
for file in $(grep -rl "<<<<<<< HEAD" app/ tests/); do
    echo "Fixing: $file"
    # Remove conflict markers and keep the main branch version
    sed -i '/<<<<<<< HEAD/,/=======/d' "$file"
    sed -i '/>>>>>>> origin\/main/d' "$file"
done

# Verify
echo "Remaining conflicts: $(grep -r '<<<<<<< HEAD' app/ tests/ | wc -l)"
```

#### より安全な方法（推奨）
```bash
# ファイルごとに確認しながら解決
git status | grep "both modified" | awk '{print $3}' | while read file; do
    echo "Resolving: $file"
    # mainブランチのバージョンを採用
    git checkout --theirs "$file"
    git add "$file"
done
```

### Step 3: 結果確認（2分）
```bash
# Syntax errorが消えたか確認
uv run python -m py_compile app/**/*.py

# Ruffでチェック
uv run ruff check . --select E999 | wc -l
# 0になっていればOK
```

### Step 4: コミット（2分）
```bash
git add -A
git commit -m "fix: Resolve all merge conflicts - adopt main branch changes

- Fixed $(grep -r '<<<<<<< HEAD' . | wc -l) conflict markers
- Restored syntax validity to all Python files
- Ready for Code Quality improvements"

git push
```

## ⚠️ 注意事項

1. **バックアップ推奨**
   ```bash
   git stash
   # または
   cp -r app/ app_backup/
   ```

2. **段階的実行**
   - まず1ファイルで試す
   - 問題なければ全体に適用

3. **テスト実行**
   ```bash
   uv run pytest tests/test_main.py -v
   ```

## 🎯 期待される結果

Before:
- Errors: 3,023個
- Syntax Errors: 2,843個

After:
- Errors: ~180個
- Syntax Errors: 0個

---

**緊急度**: 最高
**担当**: CC02（Backend）、CC01（Frontend）
**期限**: 30分以内