# Claude Code Agent Log Analysis Scripts

These scripts help analyze Claude Code agent activity across multiple Ubuntu instances.

## Scripts

### 1. agent-log-analyzer.sh
Run this script on each agent's Ubuntu instance to collect activity data.

**Usage:**
```bash
# Set agent name and run
export AGENT_NAME=CC01  # or CC02, CC03
./agent-log-analyzer.sh
```

**What it collects:**
- Claude Code process status
- Recent session files
- Project file modifications (last 2 hours)
- Git activity (last 24 hours)
- Current git branch and status
- Claude Code command history
- System resource usage
- Network connections to GitHub
- Summary report

**Output:**
- Report saved to: `/tmp/claude-code-analysis/agent_${AGENT_NAME}_report_${TIMESTAMP}.txt`

### 2. collect-agent-reports.sh
Run this script on a central machine to aggregate reports from all agents.

**Usage:**
```bash
# After copying agent reports to /tmp/claude-code-analysis/
./collect-agent-reports.sh
```

**Output:**
- Aggregate report: `/tmp/claude-code-analysis/aggregate_report_${TIMESTAMP}.md`

## Workflow

1. **On each agent machine (CC01, CC02, CC03):**
   ```bash
   cd ~/ITDO_ERP2/claude-code-cluster/scripts
   export AGENT_NAME=CC01  # Set appropriate name
   ./agent-log-analyzer.sh
   ```

2. **Copy reports to central location:**
   ```bash
   # Example: scp from agent machines to central
   scp user@cc01:/tmp/claude-code-analysis/agent_CC01_report_*.txt /tmp/claude-code-analysis/
   scp user@cc02:/tmp/claude-code-analysis/agent_CC02_report_*.txt /tmp/claude-code-analysis/
   scp user@cc03:/tmp/claude-code-analysis/agent_CC03_report_*.txt /tmp/claude-code-analysis/
   ```

3. **Generate aggregate report:**
   ```bash
   ./collect-agent-reports.sh
   ```

## Report Contents

The agent report includes:
- Process status verification
- File modification tracking
- Git activity monitoring
- System resource usage
- Network connection status
- Claude Code session information

## Troubleshooting

- If Claude Code process is not found, check if it's running under a different name
- If project directory is not found, update the script with correct path
- For permission issues, ensure scripts have execute permissions: `chmod +x *.sh`

## Security Note

These scripts only read system information and do not modify any files or settings.
Reports may contain file paths and system information - review before sharing.