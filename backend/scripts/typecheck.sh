#!/bin/bash
# Type checking helper script for developers

set -e

echo "🔍 Running type safety checks..."
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")/.."

# Function to count errors
count_errors() {
    local output="$1"
    echo "$output" | grep -c "error:" || echo "0"
}

# Run mypy
echo "Running mypy type checking..."
if output=$(uv run mypy . --show-error-codes --show-column-numbers --pretty 2>&1); then
    echo -e "${GREEN}✅ Type check passed!${NC}"
    TYPE_ERRORS=0
else
    TYPE_ERRORS=$(count_errors "$output")
    echo -e "${RED}❌ Type check failed with $TYPE_ERRORS errors${NC}"
    echo "$output"
fi

# Count type: ignore comments
echo ""
echo "Checking type: ignore usage..."
TYPE_IGNORES=$(grep -r "type: ignore" app tests --include="*.py" 2>/dev/null | wc -l || echo "0")
if [ "$TYPE_IGNORES" -gt 20 ]; then
    echo -e "${YELLOW}⚠️  Found $TYPE_IGNORES type: ignore comments (threshold: 20)${NC}"
else
    echo -e "${GREEN}✅ Found $TYPE_IGNORES type: ignore comments${NC}"
fi

# Count Any usage
echo ""
echo "Checking Any type usage..."
ANY_USAGE=$(grep -r "\bAny\b" app tests --include="*.py" 2>/dev/null | grep -v "from typing import" | wc -l || echo "0")
if [ "$ANY_USAGE" -gt 10 ]; then
    echo -e "${YELLOW}⚠️  Found $ANY_USAGE uses of Any type (threshold: 10)${NC}"
else
    echo -e "${GREEN}✅ Found $ANY_USAGE uses of Any type${NC}"
fi

# Generate detailed report if requested
if [ "$1" == "--report" ]; then
    echo ""
    echo "Generating detailed HTML report..."
    uv run mypy . --html-report mypy-report
    echo -e "${GREEN}✅ Report generated at: mypy-report/index.html${NC}"
fi

# Summary
echo ""
echo "================================"
echo "Summary:"
echo "- Type errors: $TYPE_ERRORS"
echo "- Type ignores: $TYPE_IGNORES"
echo "- Any usage: $ANY_USAGE"

if [ "$TYPE_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ All type checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Type errors must be fixed${NC}"
    exit 1
fi