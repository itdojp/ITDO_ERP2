#!/bin/bash
# Claude Code エージェント用 Code Quality 自動チェックスクリプト

set -e

echo "🤖 Claude Code Quality Check Starting..."
echo "======================================="

# 現在のブランチを確認
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# 未コミットの変更を確認
CHANGED_FILES=$(git diff --name-only)
if [ -z "$CHANGED_FILES" ]; then
    echo "✅ No uncommitted changes found"
else
    echo "📝 Changed files:"
    echo "$CHANGED_FILES"
fi

# Python Quality Check
if [ -d "backend" ]; then
    echo -e "\n🐍 Python Code Quality Check..."
    cd backend
    
    # Ruff check
    echo "Running ruff check..."
    if uv run ruff check . --fix; then
        echo "✅ Ruff check passed"
    else
        echo "⚠️  Ruff found issues, attempting unsafe fixes..."
        uv run ruff check . --fix --unsafe-fixes
    fi
    
    # Ruff format
    echo "Running ruff format..."
    uv run ruff format .
    echo "✅ Formatting completed"
    
    # Type check (non-blocking)
    echo "Running mypy..."
    uv run mypy app/ || echo "⚠️  Type checking has warnings (non-blocking)"
    
    cd ..
fi

# TypeScript Quality Check
if [ -d "frontend" ]; then
    echo -e "\n📘 TypeScript Code Quality Check..."
    cd frontend
    
    # ESLint
    echo "Running ESLint..."
    npm run lint:fix || echo "⚠️  ESLint found issues"
    
    # TypeScript check
    echo "Running TypeScript check..."
    npm run typecheck || echo "⚠️  TypeScript check has issues"
    
    cd ..
fi

# Pre-commit check
echo -e "\n🔍 Running pre-commit checks..."
if command -v pre-commit &> /dev/null; then
    uv run pre-commit run --all-files || {
        echo "⚠️  Pre-commit checks failed, but continuing..."
        echo "Run 'uv run pre-commit run --all-files' to see details"
    }
else
    echo "⚠️  pre-commit not installed"
fi

# Summary
echo -e "\n📊 Summary"
echo "=========="

# Count remaining issues
if [ -d "backend" ]; then
    cd backend
    PYTHON_ERRORS=$(uv run ruff check . 2>/dev/null | grep -E "^\w+:" | wc -l || echo "0")
    echo "🐍 Python errors remaining: $PYTHON_ERRORS"
    cd ..
fi

if [ -d "frontend" ]; then
    cd frontend
    TS_ERRORS=$(npm run lint 2>&1 | grep -E "error" | wc -l || echo "0")
    echo "📘 TypeScript errors remaining: $TS_ERRORS"
    cd ..
fi

echo -e "\n✅ Code Quality Check Complete!"
echo "Next steps:"
echo "1. Review any remaining issues"
echo "2. Commit your changes: git add -A && git commit -m 'fix: Apply code quality improvements'"
echo "3. Create PR: gh pr create --title 'fix: Code quality improvements'"