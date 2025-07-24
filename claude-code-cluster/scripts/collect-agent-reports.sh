#!/bin/bash
# Collect and aggregate agent reports from multiple agents
# Run this on a central machine after agents have generated their reports

set -euo pipefail

REPORT_DIR="/tmp/claude-code-analysis"
AGGREGATE_FILE="${REPORT_DIR}/aggregate_report_$(date +%Y%m%d_%H%M%S).md"

# Create report directory
mkdir -p "${REPORT_DIR}"

# Start aggregate report
cat > "${AGGREGATE_FILE}" << EOF
# Claude Code Multi-Agent Activity Analysis
Generated: $(date)

## Overview
This report aggregates activity data from all Claude Code agents (CC01, CC02, CC03).

EOF

# Function to add agent report
add_agent_report() {
    local agent_name=$1
    local report_file=$2
    
    echo "## Agent: ${agent_name}" >> "${AGGREGATE_FILE}"
    echo "" >> "${AGGREGATE_FILE}"
    
    if [ -f "${report_file}" ]; then
        # Extract key information
        echo "### Status Summary" >> "${AGGREGATE_FILE}"
        grep -E "(✅|❌|Branch:|Modified:|Generated:)" "${report_file}" | head -20 >> "${AGGREGATE_FILE}" || true
        echo "" >> "${AGGREGATE_FILE}"
        
        echo "### Recent Activity" >> "${AGGREGATE_FILE}"
        sed -n '/Recent Project File Changes/,/^$/p' "${report_file}" | tail -n +3 | head -10 >> "${AGGREGATE_FILE}" || true
        echo "" >> "${AGGREGATE_FILE}"
        
        echo "### Git Activity" >> "${AGGREGATE_FILE}"
        sed -n '/Git Activity/,/^$/p' "${report_file}" | tail -n +3 | head -10 >> "${AGGREGATE_FILE}" || true
        echo "" >> "${AGGREGATE_FILE}"
        
        echo "[Full report: ${report_file}]" >> "${AGGREGATE_FILE}"
        echo "" >> "${AGGREGATE_FILE}"
        echo "---" >> "${AGGREGATE_FILE}"
        echo "" >> "${AGGREGATE_FILE}"
    else
        echo "⚠️ No report found for ${agent_name}" >> "${AGGREGATE_FILE}"
        echo "" >> "${AGGREGATE_FILE}"
    fi
}

# Check for agent reports
echo "Searching for agent reports in ${REPORT_DIR}..." 

# Add reports for each agent
for agent in CC01 CC02 CC03; do
    latest_report=$(find "${REPORT_DIR}" -name "agent_${agent}_report_*.txt" -type f -mtime -1 2>/dev/null | sort -r | head -1)
    if [ -n "${latest_report}" ]; then
        echo "Found report for ${agent}: ${latest_report}"
        add_agent_report "${agent}" "${latest_report}"
    else
        echo "No recent report found for ${agent}"
        add_agent_report "${agent}" ""
    fi
done

# Add summary section
cat >> "${AGGREGATE_FILE}" << EOF

## Analysis Summary

### Active Agents
EOF

# Count active agents
active_count=$(grep -c "✅ Claude Code is running" "${REPORT_DIR}"/agent_*_report_*.txt 2>/dev/null || echo "0")
echo "- Active Claude Code processes: ${active_count}" >> "${AGGREGATE_FILE}"

# Get recent commits across all agents
echo "" >> "${AGGREGATE_FILE}"
echo "### Recent Commits (All Agents)" >> "${AGGREGATE_FILE}"
cat "${REPORT_DIR}"/agent_*_report_*.txt 2>/dev/null | grep -E "^[a-f0-9]{7} " | sort -u | head -10 >> "${AGGREGATE_FILE}" || echo "No recent commits found" >> "${AGGREGATE_FILE}"

# Get modified files across all agents
echo "" >> "${AGGREGATE_FILE}"
echo "### Recently Modified Files (All Agents)" >> "${AGGREGATE_FILE}"
cat "${REPORT_DIR}"/agent_*_report_*.txt 2>/dev/null | grep "Modified: " | sort -u | head -20 >> "${AGGREGATE_FILE}" || echo "No recently modified files found" >> "${AGGREGATE_FILE}"

echo "" >> "${AGGREGATE_FILE}"
echo "Report generation complete: ${AGGREGATE_FILE}" >> "${AGGREGATE_FILE}"

# Display summary
echo ""
echo "Aggregate report created: ${AGGREGATE_FILE}"
echo ""
echo "Summary:"
echo "- Reports found: $(find "${REPORT_DIR}" -name "agent_*_report_*.txt" -type f -mtime -1 2>/dev/null | wc -l)"
echo "- Active agents: ${active_count}"
echo ""
echo "To view the full report:"
echo "  cat ${AGGREGATE_FILE}"