#!/bin/bash
# Branch cleanup script for ITDO ERP2 repository
# Issue #57: Clean up merged branches and stale feature branches

set -e

echo "🧹 Starting branch cleanup for ITDO ERP2 repository..."
echo "=================================================="

# Function to delete remote branch
delete_remote_branch() {
    branch=$1
    echo -n "  Deleting remote branch $branch... "
    if git push origin --delete "$branch" 2>/dev/null; then
        echo "✅"
    else
        echo "❌ (may already be deleted or protected)"
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
echo "📌 Step 2: Cleaning up stale user management branches..."
echo "  Keeping only feature/user-management (most recent)"
delete_remote_branch "feature/user-management-clean"
delete_remote_branch "feature/user-management-v2"

# 3. Delete obsolete type safety branches (after PR #50)
echo ""
echo "📌 Step 3: Cleaning up obsolete type safety branches..."
echo "  PR #50 has been merged, removing phase branches"
delete_remote_branch "feature/type-safety-phase1"
delete_remote_branch "feature/type-safety-phase2"
delete_remote_branch "feature/type-safety-phase3"
delete_remote_branch "feature/type-safety-phase4"
delete_remote_branch "feature/type-safety-phase5"
delete_remote_branch "fix/type-safety"

# 4. Review other stale branches
echo ""
echo "📌 Step 4: Other stale branches for review..."
echo "  The following branches need manual review:"
echo "  - origin/feature/dashboard-progress"
echo "  - origin/feature/keycloak-integration"
echo "  - origin/feature/organization-management"
echo "  - origin/feature/task-management"
echo "  - origin/feature/type-safe-task-management"
echo "  - origin/feature/user-management"

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