#!/bin/bash

# Claude Code Usage Monitor Script
# This script helps monitor and optimize Claude Code usage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Claude Code Usage Monitor ===${NC}"
echo ""

# Function to check directory size
check_size() {
    local dir=$1
    local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    echo "$size"
}

# Function to clean cache directories
clean_caches() {
    echo -e "${YELLOW}Cleaning cache directories...${NC}"
    
    local dirs=(
        ".pytest_cache"
        ".mypy_cache"
        ".ruff_cache"
        "htmlcov"
        ".coverage"
        "__pycache__"
        "node_modules/.cache"
    )
    
    local total_before=$(du -sh . 2>/dev/null | cut -f1)
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "  Removing $dir..."
            rm -rf "$dir"
        fi
    done
    
    # Find and remove all __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Find and remove all .pyc files
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    local total_after=$(du -sh . 2>/dev/null | cut -f1)
    
    echo -e "${GREEN}✓ Cache cleanup complete${NC}"
    echo "  Before: $total_before"
    echo "  After:  $total_after"
}

# Function to analyze large files
analyze_large_files() {
    echo -e "${YELLOW}Analyzing large files...${NC}"
    echo "Files larger than 1MB:"
    find . -type f -size +1M -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' | sort -hr | head -20
}

# Function to check git status
check_git_status() {
    echo -e "${YELLOW}Checking git status...${NC}"
    local untracked=$(git ls-files --others --exclude-standard | wc -l)
    local modified=$(git diff --name-only | wc -l)
    
    echo "  Untracked files: $untracked"
    echo "  Modified files: $modified"
    
    if [ $untracked -gt 50 ]; then
        echo -e "${RED}  ⚠️  High number of untracked files detected${NC}"
    fi
}

# Function to generate optimization report
generate_report() {
    echo -e "${BLUE}=== Optimization Report ===${NC}"
    echo ""
    
    # Check if .claudeignore exists
    if [ -f ".claudeignore" ]; then
        echo -e "${GREEN}✓ .claudeignore file exists${NC}"
    else
        echo -e "${RED}✗ .claudeignore file missing${NC}"
        echo "  Recommendation: Create .claudeignore to exclude unnecessary files"
    fi
    
    # Check project size
    local total_size=$(du -sh . 2>/dev/null | cut -f1)
    echo ""
    echo "Total project size: $total_size"
    
    # Size recommendations
    if [[ "$total_size" =~ ([0-9]+)M ]]; then
        local size_mb=${BASH_REMATCH[1]}
        if [ $size_mb -gt 200 ]; then
            echo -e "${RED}  ⚠️  Project size is large (>200MB)${NC}"
            echo "  Recommendation: Review and exclude unnecessary files"
        elif [ $size_mb -gt 100 ]; then
            echo -e "${YELLOW}  ⚠️  Project size is moderate (>100MB)${NC}"
            echo "  Recommendation: Consider optimizing further"
        else
            echo -e "${GREEN}  ✓ Project size is optimal (<100MB)${NC}"
        fi
    fi
    
    # Check for common issues
    echo ""
    echo -e "${YELLOW}Checking for common issues...${NC}"
    
    # Check for .venv directory
    if [ -d ".venv" ] && ! grep -q "^\.venv" .gitignore 2>/dev/null; then
        echo -e "${RED}  ⚠️  .venv directory not in .gitignore${NC}"
    fi
    
    # Check for node_modules
    if [ -d "node_modules" ] && ! grep -q "^node_modules" .gitignore 2>/dev/null; then
        echo -e "${RED}  ⚠️  node_modules directory not in .gitignore${NC}"
    fi
}

# Function to show usage tips
show_tips() {
    echo ""
    echo -e "${BLUE}=== Claude Code Usage Tips ===${NC}"
    echo ""
    echo "1. Session Management:"
    echo "   - Use /compact every 2-4 hours"
    echo "   - Start new sessions after major milestones"
    echo "   - Check usage with /cost regularly"
    echo ""
    echo "2. Query Optimization:"
    echo "   - Be specific and concise"
    echo "   - Break complex tasks into smaller ones"
    echo "   - Avoid broad, open-ended requests"
    echo ""
    echo "3. Project Structure:"
    echo "   - Keep codebase under 100MB"
    echo "   - Use .claudeignore for exclusions"
    echo "   - Clean caches regularly"
    echo ""
    echo "4. Cost Monitoring:"
    echo "   - Daily: Check /cost"
    echo "   - Weekly: Review patterns"
    echo "   - Monthly: Optimize workflow"
}

# Main menu
show_menu() {
    echo ""
    echo "Select an option:"
    echo "1) Quick analysis"
    echo "2) Clean caches"
    echo "3) Analyze large files"
    echo "4) Full optimization report"
    echo "5) Show optimization tips"
    echo "6) Exit"
    echo ""
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1)
            echo ""
            check_git_status
            echo ""
            echo "Total size: $(check_size .)"
            ;;
        2)
            echo ""
            clean_caches
            ;;
        3)
            echo ""
            analyze_large_files
            ;;
        4)
            echo ""
            check_git_status
            echo ""
            analyze_large_files
            echo ""
            generate_report
            ;;
        5)
            show_tips
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
}

# Main loop
while true; do
    show_menu
    echo ""
    read -p "Press Enter to continue..."
    clear
    echo -e "${BLUE}=== Claude Code Usage Monitor ===${NC}"
done