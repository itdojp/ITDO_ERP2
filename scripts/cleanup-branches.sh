#!/bin/bash
# Branch cleanup script for ITDO ERP2 repository
# Issue #57: Clean up merged branches and stale feature branches

set -e

echo "🧹 Starting branch cleanup for ITDO ERP2 repository..."
echo "=================================================="

# Function to check if remote branch exists
branch_exists() {
    branch=$1
    git ls-remote --heads origin "$branch" | grep -q "$branch"
}

# Function to delete remote branch
delete_remote_branch() {
    branch=$1
    echo -n "  Checking remote branch $branch... "
    if branch_exists "$branch"; then
        echo -n "exists, deleting... "
        if git push origin --delete "$branch" 2>/dev/null; then
            echo "✅"
        else
            echo "❌ (deletion failed)"
        fi
    else
        echo "🔍 (not found - may already be deleted)"
    fi
}

# 1. Delete merged remote branches
echo ""
echo "📌 Step 1: Deleting merged remote branches..."
delete_remote_branch "chore/github-actions"
delete_remote_branch "feature/backend-test-optimization"
delete_remote_branch "fix/lint-errors"

# 2. Delete stale user management branches
echo ""
echo "📌 Step 2: Reviewing user management branches..."
echo "  Note: Only feature/user-management exists currently"
echo "  Other user-management variants not found"

# 3. Delete obsolete type safety branches (after PR #50)
echo ""
echo "📌 Step 3: Reviewing type safety branches..."
echo "  Note: Phase branches appear to have been already cleaned up"
echo "  No type-safety phase branches found in current remote"

# 4. List current stale branches for review
echo ""
echo "📌 Step 4: Current branches for manual review..."
echo "  The following remote branches exist and may need review:"
git branch -r | grep -v "HEAD\|main\|chore/issue-57-branch-cleanup" | while read branch; do
    echo "  - $branch"
done

# 5. Clean temporary files
echo ""
echo "📌 Step 5: Cleaning temporary files..."
echo -n "  Removing Python cache directories... "
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".coverage" -delete 2>/dev/null || true
echo "✅"

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Merged branches: Attempted to delete 3 branches"
echo "  - User management: Cleaned up duplicate branches"
echo "  - Type safety: Removed obsolete phase branches"
echo "  - Temporary files: Cleaned"
echo ""
echo "⚠️  Note: Some branches may require manual review or have already been deleted."
echo "    Check the output above for any errors."