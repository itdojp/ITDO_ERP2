# Agent Self-Management Commands

## 🔧 Essential Commands for Autonomous Operation

### Daily Startup Sequence
```bash
# 1. Environment Setup
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster
./start-agent-sonnet.sh [CC01|CC02|CC03]

# 2. Project Navigation
cd /mnt/c/work/ITDO_ERP2

# 3. Status Check
make status
git status
gh pr list --repo itdojp/ITDO_ERP2 --state open
gh issue list --repo itdojp/ITDO_ERP2 --state open --label "claude-code-task"
```

### Task Discovery Commands
```bash
# Find your next task (by priority)
gh issue list --repo itdojp/ITDO_ERP2 --state open --label "cc01" --limit 5    # For CC01
gh issue list --repo itdojp/ITDO_ERP2 --state open --label "cc02" --limit 5    # For CC02
gh issue list --repo itdojp/ITDO_ERP2 --state open --label "cc03" --limit 5    # For CC03

# Check critical PRs
gh pr list --repo itdojp/ITDO_ERP2 --state open --json number,title,statusCheckRollup

# Find failing tests
gh run list --repo itdojp/ITDO_ERP2 --status failure --limit 5
```

### Self-Monitoring Commands
```bash
# Check CI/CD status
gh run list --repo itdojp/ITDO_ERP2 --limit 10

# Monitor your PRs
gh pr list --repo itdojp/ITDO_ERP2 --author "@me" --state open

# Check test coverage
cd backend && uv run pytest --cov=app --cov-report=term-missing
cd frontend && npm run coverage
```

### Autonomous Decision Making
```bash
# Decision Tree: What should I work on?

# 1. Check for failing tests first
if gh run list --repo itdojp/ITDO_ERP2 --status failure --limit 1 | grep -q "backend-test"; then
    echo "Priority 1: Fix failing backend tests"
    # Work on test fixes
fi

# 2. Check for open PRs needing attention
if gh pr list --repo itdojp/ITDO_ERP2 --state open --review-requested "@me" | grep -q "OPEN"; then
    echo "Priority 2: Review requested PRs"
    # Handle PR reviews
fi

# 3. Check for assigned issues
if gh issue list --repo itdojp/ITDO_ERP2 --assignee "@me" --state open | grep -q "OPEN"; then
    echo "Priority 3: Work on assigned issues"
    # Work on assigned issues
fi
```

### Progress Reporting Commands
```bash
# Create progress report
gh issue comment [ISSUE_NUMBER] --body "
## 📊 Progress Update - $(date)

**Status**: [IN_PROGRESS|COMPLETED|BLOCKED]
**Time Spent**: [X] hours
**Completed**: [List achievements]
**Next Steps**: [Planned actions]
**Blockers**: [Any issues requiring escalation]

**Autonomous Actions Taken**: [Self-directed decisions]
"

# Update task status
gh issue edit [ISSUE_NUMBER] --add-label "in-progress"
gh issue edit [ISSUE_NUMBER] --remove-label "in-progress" --add-label "completed"
```

### Quality Assurance Commands
```bash
# Run full test suite
make test

# Check code quality
make lint
make typecheck

# Security scan
make security-scan

# Performance check
cd backend && uv run pytest tests/performance/
cd frontend && npm run test:performance
```

### Cross-Agent Coordination Commands
```bash
# Notify other agents
gh issue comment [ISSUE_NUMBER] --body "@CC01 @CC02 @CC03 [Your message]"

# Check team status
gh issue list --repo itdojp/ITDO_ERP2 --state open --label "claude-code-task" --json number,title,assignees,labels

# Coordinate on shared tasks
gh pr comment [PR_NUMBER] --body "
## 🤝 Cross-Agent Coordination

**From**: [CC01|CC02|CC03]
**To**: [Target agents]
**Context**: [Shared task context]
**Request**: [Specific coordination needed]
"
```

### Emergency Response Commands
```bash
# System health check
make status
podman ps --all
curl -f http://localhost:8000/health || echo "Backend down"
curl -f http://localhost:3000 || echo "Frontend down"

# Emergency escalation
escalate "Critical system failure" "Current status" "Attempted fixes"

# Rollback command
git reset --hard HEAD~1
git push --force-with-lease origin [branch-name]
```

### Self-Learning Commands
```bash
# Analyze past performance
gh issue list --repo itdojp/ITDO_ERP2 --state closed --assignee "@me" --limit 10
gh pr list --repo itdojp/ITDO_ERP2 --state merged --author "@me" --limit 10

# Review successful patterns
git log --oneline --author="$(git config user.name)" --since="1 week ago"

# Knowledge update
gh issue create --repo itdojp/ITDO_ERP2 --title "📚 Knowledge Update: [Topic]" --body "
## Learning Summary

**Topic**: [What was learned]
**Source**: [Where knowledge was gained]
**Application**: [How it will be applied]
**Sharing**: [Knowledge shared with team]
"
```

## 🎯 Autonomous Task Templates

### New Task Discovery Template
```bash
#!/bin/bash
# Auto-discover next task

echo "🔍 Discovering next task..."

# Check for failures first
FAILURES=$(gh run list --repo itdojp/ITDO_ERP2 --status failure --limit 1)
if [ -n "$FAILURES" ]; then
    echo "❌ Found failing tests - Priority 1"
    # Handle failures
    exit 0
fi

# Check for assigned issues
ASSIGNED=$(gh issue list --repo itdojp/ITDO_ERP2 --assignee "@me" --state open --limit 1)
if [ -n "$ASSIGNED" ]; then
    echo "📋 Found assigned issue - Priority 2"
    # Handle assigned work
    exit 0
fi

# Check for relevant label issues
RELEVANT=$(gh issue list --repo itdojp/ITDO_ERP2 --state open --label "claude-code-task" --limit 1)
if [ -n "$RELEVANT" ]; then
    echo "🎯 Found relevant task - Priority 3"
    # Handle relevant work
    exit 0
fi

echo "✅ No urgent tasks found - Enter maintenance mode"
```

### Progress Tracking Template
```bash
#!/bin/bash
# Track and report progress

CURRENT_TIME=$(date)
WORK_START_TIME="$1"  # Pass start time as parameter

echo "📊 Progress Tracking - $CURRENT_TIME"

# Calculate work duration
if [ -n "$WORK_START_TIME" ]; then
    DURATION=$(($(date +%s) - $(date -d "$WORK_START_TIME" +%s)))
    echo "⏱️ Work Duration: $((DURATION / 3600)) hours $((DURATION % 3600 / 60)) minutes"
fi

# Check current status
git status --porcelain | wc -l | xargs echo "📝 Modified files:"
git log --oneline --since="$WORK_START_TIME" --author="$(git config user.name)" | wc -l | xargs echo "💾 Commits made:"

# Report to GitHub
gh issue comment $CURRENT_ISSUE --body "
## 📈 Autonomous Progress Report

**Timestamp**: $CURRENT_TIME
**Duration**: [Calculated above]
**Status**: [AUTO-DETECTED]
**Next Action**: [AUTO-SELECTED]
"
```

## 🚨 Emergency Protocols

### System Recovery Commands
```bash
# Full system restart
make stop-data
make start-data
make dev &

# Database recovery
make stop-data
rm -rf data/postgres/*
make start-data
cd backend && uv run python -m app.db.init_db

# Clean environment reset
git clean -fdx
git reset --hard HEAD
make setup-dev
```

### Escalation Triggers
```bash
# Auto-escalation conditions
if [ "$TASK_DURATION" -gt 1800 ]; then  # 30 minutes
    escalate "Task duration exceeded" "Working on $CURRENT_TASK" "Tried standard approaches"
fi

if [ "$ERROR_COUNT" -gt 3 ]; then  # 3 consecutive errors
    escalate "Multiple errors encountered" "Error pattern: $ERROR_PATTERN" "Attempted error resolution"
fi

if [ "$COMPLEXITY_SCORE" -gt 7 ]; then  # High complexity
    escalate "High complexity task" "Complex architectural decision needed" "Analyzed requirements"
fi
```

---

**Usage**: Copy and customize these commands for your specific agent role
**Maintenance**: Update commands as tools and processes evolve
**Support**: Use escalation for complex scenarios

🤖 Designed for Maximum Agent Autonomy