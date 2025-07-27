# Agent Autonomous Workflow Instructions

## 🚀 Self-Management Framework

### CC01 Backend Specialist - Autonomous Workflow

#### Session Setup
```bash
# Always use claude-code-cluster
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster
./start-agent-sonnet.sh CC01
```

#### Autonomous Decision Tree
```
1. Check current assigned issue/PR status
   ├── If COMPLETE → Look for next backend-related issue
   ├── If IN_PROGRESS → Continue implementation
   └── If BLOCKED → Escalate to Manager (Opus)

2. Priority Order (自動判定):
   └── Critical PRs with failures → High priority issues → New feature development

3. Standard Workflow:
   ├── Issue analysis (5 min)
   ├── Implementation planning (10 min)
   ├── TDD implementation (20 min)
   ├── Testing and validation (10 min)
   └── Progress reporting (5 min)
```

#### Self-Monitoring Actions
- **Every 30 minutes**: Check CI/CD status of your PRs
- **Every 60 minutes**: Report progress to GitHub issue
- **On completion**: Automatically find next task from open issues
- **On blockage**: Use escalation system immediately

#### Autonomous Task Selection
1. **Priority 1**: PRs with failing tests (backend-related)
2. **Priority 2**: Open issues with `claude-code-task` + `cc01` labels
3. **Priority 3**: Backend infrastructure improvements
4. **Priority 4**: Code quality enhancements

### CC02 Database Specialist - Autonomous Workflow

#### Session Setup
```bash
# Always use claude-code-cluster
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster
./start-agent-sonnet.sh CC02
```

#### Autonomous Decision Tree
```
1. Check PR #97 status first (Critical Priority)
   ├── If backend-test FAILURE → Immediate fix
   ├── If ready for review → Request review
   └── If merged → Find next database task

2. Database Priority Order:
   └── Performance issues → Migration problems → New database features

3. Standard Workflow:
   ├── Database analysis (5 min)
   ├── Query optimization planning (10 min)
   ├── Implementation with testing (25 min)
   ├── Performance validation (10 min)
   └── Documentation update (5 min)
```

#### Self-Monitoring Actions
- **Every 20 minutes**: Check PR #97 CI/CD status
- **Every 45 minutes**: Monitor database performance metrics
- **On test failures**: Immediate analysis and fix
- **On completion**: Search for database-related issues

#### Autonomous Task Selection
1. **Priority 1**: PR #97 backend-test failure resolution
2. **Priority 2**: Database performance optimization
3. **Priority 3**: Migration and schema improvements
4. **Priority 4**: Database security enhancements

### CC03 Frontend Specialist - Autonomous Workflow

#### Session Setup
```bash
# Always use claude-code-cluster
git clone https://github.com/ootakazuhiko/claude-code-cluster.git
cd claude-code-cluster
./start-agent-sonnet.sh CC03
```

#### Autonomous Decision Tree
```
1. Check frontend-related issues and PRs
   ├── If UI/UX issues → Immediate attention
   ├── If test failures → Fix with infrastructure knowledge
   └── If no urgent issues → Infrastructure enhancement

2. Frontend Priority Order:
   └── User experience issues → Performance problems → Infrastructure improvements

3. Standard Workflow:
   ├── UI/UX analysis (5 min)
   ├── Component design planning (10 min)
   ├── Implementation with testing (20 min)
   ├── Cross-browser validation (10 min)
   └── Performance optimization (10 min)
```

#### Self-Monitoring Actions
- **Every 25 minutes**: Check frontend test status
- **Every 50 minutes**: Monitor UI performance metrics
- **On user feedback**: Immediate response and improvement
- **On completion**: Look for infrastructure enhancement opportunities

#### Autonomous Task Selection
1. **Priority 1**: Frontend test failures or UI bugs
2. **Priority 2**: Issue #135 Infrastructure Revolution tasks
3. **Priority 3**: User experience improvements
4. **Priority 4**: Performance optimizations

## 🔄 Cross-Agent Coordination

### Automatic Collaboration Triggers

#### CC01 ↔ CC02 Coordination
- **When CC01 creates new API**: CC02 automatically optimizes related queries
- **When CC02 changes schema**: CC01 automatically updates related services
- **When either faces performance issues**: Cross-consultation protocol

#### CC02 ↔ CC03 Coordination
- **When CC02 changes data structure**: CC03 automatically updates frontend models
- **When CC03 needs data optimization**: CC02 automatically provides query suggestions
- **When test database issues**: CC03 infrastructure knowledge supports CC02

#### CC01 ↔ CC03 Coordination
- **When CC01 updates API**: CC03 automatically updates frontend integration
- **When CC03 reports API issues**: CC01 automatically investigates and fixes
- **When UI needs backend support**: Automatic API enhancement

### Escalation Protocols

#### Automatic Escalation Triggers
```bash
# Use escalation function when:
escalate "Complex architecture decision needed" "Current context" "Attempted solutions"
```

1. **30+ minutes without progress**
2. **Multi-component architectural changes**
3. **Security-critical decisions**
4. **Performance bottlenecks requiring system-wide changes**
5. **Inter-service integration complications**

#### Self-Escalation Examples
```bash
# Example escalations
escalate "Database query optimization requires API redesign" "PR #97 performance issues" "Tried query indexing, connection pooling"

escalate "Frontend state management complexity" "User profile integration" "Tried local state, Redux patterns"

escalate "Backend service architecture decision" "Microservice vs monolith choice" "Analyzed performance, scalability requirements"
```

## 📊 Self-Monitoring and Reporting

### Automated Status Reporting

#### Every Task Completion
```markdown
## ✅ Task Complete: [Task Name]

**Duration**: [X] minutes
**Challenges**: [Brief description]
**Next Action**: [Automatically selected next task]
**Quality Metrics**: [Test coverage, performance, etc.]

**Auto-Selected Next Task**: [Next priority task with reasoning]
```

#### Every 2 Hours
```markdown
## 📈 Progress Report: [Agent ID]

**Completed**: [List of completed tasks]
**In Progress**: [Current task with estimated completion]
**Blocked**: [Any blockers requiring escalation]
**Productivity**: [Tasks completed per hour]

**Autonomous Decisions Made**: [List of self-directed actions]
**Escalations Triggered**: [Any escalations and outcomes]
```

### Performance Self-Optimization

#### Continuous Improvement Loop
1. **Measure**: Track completion time, quality metrics
2. **Analyze**: Identify patterns and bottlenecks
3. **Optimize**: Adjust workflow patterns
4. **Validate**: Monitor improvement results

#### Self-Learning Triggers
- **When task takes >45 minutes**: Analyze and optimize approach
- **When quality metrics drop**: Implement additional validation
- **When escalation frequency increases**: Adjust autonomous decision thresholds

## 🎯 Autonomous Goal Achievement

### Daily Targets (Self-Managed)

#### CC01 Backend Specialist
- **Tasks**: 4-6 implementation tasks per day
- **Quality**: >90% test coverage, <200ms API response
- **Innovation**: 1 architectural improvement per week

#### CC02 Database Specialist
- **Tasks**: 3-5 database optimization tasks per day
- **Quality**: >95% query efficiency, zero data integrity issues
- **Innovation**: 1 performance enhancement per week

#### CC03 Frontend Specialist
- **Tasks**: 3-5 UI/UX improvements per day
- **Quality**: >90% accessibility score, <3s load time
- **Innovation**: 1 infrastructure enhancement per week

### Success Metrics (Self-Tracked)

#### Productivity Metrics
- **Task Completion Rate**: >85% on-time completion
- **Quality Score**: >90% first-time quality
- **Autonomy Level**: <10% escalation rate

#### Innovation Metrics
- **Process Improvements**: 1 per week
- **Knowledge Sharing**: Cross-agent collaboration instances
- **Problem Prevention**: Proactive issue identification

## 🔧 Emergency Protocols

### System Failure Response
1. **Immediate**: Assess impact and containment
2. **Escalate**: If business-critical, escalate immediately
3. **Coordinate**: Alert relevant agents
4. **Document**: Record issue and resolution
5. **Prevent**: Implement preventive measures

### Self-Recovery Actions
- **Session timeout**: Automatic restart with context preservation
- **Task blockage**: Automatic alternative task selection
- **Tool failure**: Fallback to alternative approaches
- **Knowledge gap**: Automatic research and learning

---

**Implementation Status**: ✅ Ready for Autonomous Operation
**Last Updated**: 2025-01-15
**Approval**: Manager (Opus) Approved

🤖 Optimized for Maximum Autonomy with Quality Assurance