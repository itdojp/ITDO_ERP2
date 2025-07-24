#!/bin/bash
# Monitor Agent Activity Script

echo "=== Agent Activity Monitor ==="
echo "Current Time: $(date)"
echo ""

# Check recent commits
echo "1. Recent Commits (last 2 hours):"
git log --since="2 hours ago" --oneline --grep="CC0[123]" 2>/dev/null || echo "No agent commits found"
echo ""

# Check for agent files
echo "2. Agent-related files:"
find . -name "*cc01*" -o -name "*cc02*" -o -name "*cc03*" -o -name "*agent*" -type f -mmin -120 2>/dev/null | grep -v ".git" | head -10 || echo "No recent agent files found"
echo ""

# Check GitHub activity
echo "3. Recent GitHub comments:"
gh issue list --state all --limit 5 --json number,title,comments | jq -r '.[] | select(.comments | length > 0) | "\(.number): \(.title) - \(.comments | length) comments"' 2>/dev/null || echo "Could not check GitHub comments"
echo ""

# Check for status files
echo "4. Status files in /tmp:"
ls -la /tmp/*status* /tmp/*agent* /tmp/*cc0* 2>/dev/null || echo "No status files found"
echo ""

# Check branch activity
echo "5. Active branches:"
git branch -a | grep -E "(cc0[123]|agent)" || echo "No agent branches found"
echo ""

echo "=== End of Report ==="