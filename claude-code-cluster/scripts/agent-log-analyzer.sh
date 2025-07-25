#!/bin/bash
# Claude Code Agent Log Analyzer
# This script analyzes Claude Code logs on each agent's Ubuntu instance

set -euo pipefail

# Configuration
AGENT_NAME="${AGENT_NAME:-Unknown}"
OUTPUT_DIR="/tmp/claude-code-analysis"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${OUTPUT_DIR}/agent_${AGENT_NAME}_report_${TIMESTAMP}.txt"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to print section headers
print_header() {
    echo "====================================" >> "${REPORT_FILE}"
    echo "$1" >> "${REPORT_FILE}"
    echo "====================================" >> "${REPORT_FILE}"
}

# Start report
echo "Claude Code Agent Activity Report" > "${REPORT_FILE}"
echo "Agent: ${AGENT_NAME}" >> "${REPORT_FILE}"
echo "Generated: $(date)" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 1. Check Claude Code process
print_header "1. Claude Code Process Status"
if pgrep -f "claude" > /dev/null; then
    echo "✅ Claude Code is running" >> "${REPORT_FILE}"
    ps aux | grep -i claude | grep -v grep >> "${REPORT_FILE}" 2>/dev/null || true
else
    echo "❌ Claude Code process not found" >> "${REPORT_FILE}"
fi
echo "" >> "${REPORT_FILE}"

# 2. Check Claude Code session files
print_header "2. Claude Code Session Files"
find ~/.claude* ~/.config -name "*claude*" -type f -mtime -1 2>/dev/null | while read -r file; do
    echo "Found: $file (modified: $(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2))" >> "${REPORT_FILE}"
done || echo "No recent Claude Code files found" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 3. Check recent file modifications in project
print_header "3. Recent Project File Changes (Last 2 Hours)"
cd ~/ITDO_ERP2 2>/dev/null || cd /home/*/ITDO_ERP2 2>/dev/null || {
    echo "Project directory not found" >> "${REPORT_FILE}"
    exit 1
}

find . -type f -mmin -120 -not -path "./.git/*" 2>/dev/null | head -20 | while read -r file; do
    echo "Modified: $file at $(stat -c %y "$file" | cut -d' ' -f1,2)" >> "${REPORT_FILE}"
done || echo "No recent file modifications" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 4. Check Git activity
print_header "4. Git Activity (Last 24 Hours)"
git log --oneline --all --since="24 hours ago" --format="%h %ar: %s" 2>/dev/null | head -10 >> "${REPORT_FILE}" || echo "No recent git commits" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 5. Check current Git branch and status
print_header "5. Current Git Status"
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')" >> "${REPORT_FILE}"
echo "Status:" >> "${REPORT_FILE}"
git status --porcelain 2>/dev/null | head -10 >> "${REPORT_FILE}" || echo "Unable to get git status" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 6. Check Claude Code history/logs
print_header "6. Claude Code Command History"
# Check common locations for Claude Code logs
for log_location in \
    ~/.claude*/logs \
    ~/.config/claude*/logs \
    ~/.local/share/claude* \
    /tmp/claude*
do
    if [ -d "$log_location" ]; then
        echo "Checking $log_location..." >> "${REPORT_FILE}"
        find "$log_location" -name "*.log" -mtime -1 -exec tail -20 {} \; 2>/dev/null >> "${REPORT_FILE}" || true
    fi
done

# Also check shell history for claude commands
if [ -f ~/.bash_history ]; then
    echo -e "\nRecent claude commands from bash history:" >> "${REPORT_FILE}"
    grep -i claude ~/.bash_history 2>/dev/null | tail -10 >> "${REPORT_FILE}" || true
fi
echo "" >> "${REPORT_FILE}"

# 7. System resource usage
print_header "7. System Resource Usage"
echo "Memory:" >> "${REPORT_FILE}"
free -h | head -3 >> "${REPORT_FILE}"
echo -e "\nDisk:" >> "${REPORT_FILE}"
df -h . | head -2 >> "${REPORT_FILE}"
echo -e "\nLoad Average:" >> "${REPORT_FILE}"
uptime >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 8. Network connections (checking for GitHub)
print_header "8. Active Network Connections to GitHub"
netstat -an 2>/dev/null | grep -E "(github|140.82|192.30)" | head -5 >> "${REPORT_FILE}" || echo "No active GitHub connections detected" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# 9. Summary
print_header "9. Summary"
echo "Report generated successfully" >> "${REPORT_FILE}"
echo "Location: ${REPORT_FILE}" >> "${REPORT_FILE}"

# Display report location
echo "Analysis complete. Report saved to: ${REPORT_FILE}"
echo ""
echo "To view the report:"
echo "  cat ${REPORT_FILE}"
echo ""
echo "To share this report, copy ${REPORT_FILE} to the shared repository"

# Optional: Also output to stdout for immediate viewing
cat "${REPORT_FILE}"