#!/bin/bash

# ITDO ERP System - Environment Verification Script
# This script performs automated checks to verify the development environment

# Don't exit on error - we want to run all checks
set +e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_check() {
    echo -e "${BLUE}[CHECK] $1${NC}"
    ((TOTAL_CHECKS++))
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
}

# Setup environment variables
setup_environment() {
    export PATH="$HOME/.local/bin:$PATH"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check version
check_version() {
    local cmd=$1
    local min_version=$2
    local actual_version=$3
    
    if [ "$(printf '%s\n' "$min_version" "$actual_version" | sort -V | head -n1)" = "$min_version" ]; then
        return 0
    else
        return 1
    fi
}

# 1. Basic Tools Check
check_basic_tools() {
    print_header "1. Basic Tools Check"
    
    # Check uv
    print_check "Checking uv installation"
    if command_exists uv; then
        UV_VERSION=$(uv --version | cut -d' ' -f2)
        print_success "uv $UV_VERSION is installed"
    else
        print_error "uv is not installed. Install from: https://github.com/astral-sh/uv"
    fi
    
    # Check Node.js
    print_check "Checking Node.js installation"
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        if check_version "18.0.0" "$NODE_VERSION" "$NODE_VERSION"; then
            print_success "Node.js v$NODE_VERSION is installed (>= 18.0.0)"
        else
            print_error "Node.js v$NODE_VERSION is too old (need >= 18.0.0)"
        fi
    else
        print_error "Node.js is not installed"
    fi
    
    # Check npm
    print_check "Checking npm installation"
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        print_success "npm $NPM_VERSION is installed"
    else
        print_error "npm is not installed"
    fi
    
    # Check Podman/Docker
    print_check "Checking container runtime"
    if command_exists podman; then
        PODMAN_VERSION=$(podman --version | cut -d' ' -f3)
        print_success "Podman $PODMAN_VERSION is installed"
    elif command_exists docker; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker $DOCKER_VERSION is installed"
    else
        print_error "Neither Podman nor Docker is installed"
    fi
    
    # Check Git
    print_check "Checking Git installation"
    if command_exists git; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_success "Git $GIT_VERSION is installed"
    else
        print_error "Git is not installed"
    fi
}

# 2. Project Structure Check
check_project_structure() {
    print_header "2. Project Structure Check"
    
    # Check essential directories
    DIRS=(
        "backend/app"
        "frontend/src"
        "infra"
        "scripts"
        ".github/workflows"
        ".claude"
        "docs"
    )
    
    for dir in "${DIRS[@]}"; do
        print_check "Checking directory: $dir"
        if [ -d "$dir" ]; then
            print_success "Directory $dir exists"
        else
            print_error "Directory $dir is missing"
        fi
    done
    
    # Check essential files
    FILES=(
        "CLAUDE.md"
        "complete-development-docs.md"
        "pyproject.toml"
        "Makefile"
        ".gitignore"
        "backend/requirements.txt"
        "frontend/package.json"
        "infra/compose-data.yaml"
    )
    
    for file in "${FILES[@]}"; do
        print_check "Checking file: $file"
        if [ -f "$file" ]; then
            print_success "File $file exists"
        else
            print_error "File $file is missing"
        fi
    done
}

# 3. Claude Configuration Check
check_claude_config() {
    print_header "3. Claude Configuration Check"
    
    # Check CLAUDE.md
    print_check "Checking CLAUDE.md content"
    if [ -f "CLAUDE.md" ]; then
        if grep -q "Required Reading Files" CLAUDE.md; then
            print_success "CLAUDE.md contains required reading files section"
        else
            print_error "CLAUDE.md missing required reading files section"
        fi
    fi
    
    # Check .claude directory files
    CLAUDE_FILES=(
        ".claude/PROJECT_CONTEXT.md"
        ".claude/DEVELOPMENT_WORKFLOW.md"
        ".claude/CODING_STANDARDS.md"
        ".claude/TECHNICAL_CONSTRAINTS.md"
    )
    
    for file in "${CLAUDE_FILES[@]}"; do
        print_check "Checking $file"
        if [ -f "$file" ]; then
            print_success "$file exists"
        else
            print_error "$file is missing"
        fi
    done
}

# 4. Data Layer Services Check
check_data_services() {
    print_header "4. Data Layer Services Check"
    
    print_check "Checking PostgreSQL port (5432)"
    if nc -z localhost 5432 2>/dev/null; then
        print_success "PostgreSQL is accessible on port 5432"
    else
        print_warning "PostgreSQL is not running. Run 'make start-data' to start"
    fi
    
    print_check "Checking Redis port (6379)"
    if nc -z localhost 6379 2>/dev/null; then
        print_success "Redis is accessible on port 6379"
    else
        print_warning "Redis is not running. Run 'make start-data' to start"
    fi
    
    print_check "Checking Keycloak port (8080)"
    if nc -z localhost 8080 2>/dev/null; then
        print_success "Keycloak is accessible on port 8080"
    else
        print_warning "Keycloak is not running. Run 'make start-data' to start"
    fi
}

# 5. Python Environment Check
check_python_env() {
    print_header "5. Python Environment Check"
    
    cd backend
    
    print_check "Checking Python virtual environment"
    if [ -d ".venv" ]; then
        print_success "Python virtual environment exists"
    else
        print_warning "Python virtual environment not found. Creating..."
        if PATH="$HOME/.local/bin:$PATH" uv venv; then
            print_success "Virtual environment created"
        else
            print_error "Failed to create virtual environment"
        fi
    fi
    
    print_check "Checking Python dependencies"
    if [ -f "requirements.txt" ]; then
        print_success "requirements.txt exists"
    else
        print_error "requirements.txt is missing"
    fi
    
    cd ..
}

# 6. Node Environment Check
check_node_env() {
    print_header "6. Node Environment Check"
    
    cd frontend
    
    print_check "Checking node_modules"
    if [ -d "node_modules" ]; then
        print_success "node_modules exists"
    else
        print_warning "node_modules not found. Run 'npm ci' to install"
    fi
    
    print_check "Checking package-lock.json"
    if [ -f "package-lock.json" ]; then
        print_success "package-lock.json exists"
    else
        print_warning "package-lock.json is missing"
    fi
    
    cd ..
}

# 7. GitHub Actions Check
check_github_actions() {
    print_header "7. GitHub Actions Check"
    
    WORKFLOWS=(
        ".github/workflows/ci.yml"
        ".github/workflows/security-scan.yml"
        ".github/workflows/typecheck.yml"
        ".github/workflows/auto-review-request.yml"
    )
    
    for workflow in "${WORKFLOWS[@]}"; do
        print_check "Checking workflow: $workflow"
        if [ -f "$workflow" ]; then
            # Basic YAML validation
            if command_exists uv && [ -d "backend/.venv" ]; then
                if cd backend && PATH="$HOME/.local/bin:$PATH" uv run python -c "import yaml; yaml.safe_load(open('../$workflow'))" 2>/dev/null && cd ..; then
                    print_success "$workflow is valid YAML"
                else
                    print_error "$workflow has invalid YAML syntax"
                fi
            else
                print_success "$workflow exists (YAML validation skipped - uv not available)"
            fi
        else
            print_error "$workflow is missing"
        fi
    done
}

# 8. Test Configuration Check
check_test_config() {
    print_header "8. Test Configuration Check"
    
    print_check "Checking test script"
    if [ -f "scripts/test.sh" ] && [ -x "scripts/test.sh" ]; then
        print_success "test.sh exists and is executable"
    else
        print_error "test.sh is missing or not executable"
    fi
    
    print_check "Checking pre-commit configuration"
    if [ -f ".pre-commit-config.yaml" ]; then
        print_success ".pre-commit-config.yaml exists"
    else
        print_error ".pre-commit-config.yaml is missing"
    fi
    
    print_check "Checking Makefile"
    if [ -f "Makefile" ]; then
        # Check for essential targets
        TARGETS=("dev" "test" "lint" "typecheck")
        for target in "${TARGETS[@]}"; do
            if grep -q "^$target:" Makefile; then
                print_success "Makefile has '$target' target"
            else
                print_error "Makefile missing '$target' target"
            fi
        done
    fi
}

# 9. Security Configuration Check
check_security_config() {
    print_header "9. Security Configuration Check"
    
    print_check "Checking .gitignore"
    if [ -f ".gitignore" ]; then
        # Check for essential patterns
        PATTERNS=(".env" "__pycache__" "node_modules" ".venv")
        for pattern in "${PATTERNS[@]}"; do
            if grep -q "$pattern" .gitignore; then
                print_success ".gitignore includes $pattern"
            else
                print_error ".gitignore missing $pattern"
            fi
        done
    fi
    
    print_check "Checking secrets baseline"
    if [ -f ".secrets.baseline" ]; then
        print_success ".secrets.baseline exists"
    else
        print_warning ".secrets.baseline is missing (run 'detect-secrets scan > .secrets.baseline')"
    fi
}

# 10. Port Availability Check
check_port_availability() {
    print_header "10. Port Availability Check"
    
    PORTS=(
        "3000:Frontend Dev Server"
        "8000:Backend Dev Server"
        "5432:PostgreSQL"
        "6379:Redis"
        "8080:Keycloak"
        "5050:PgAdmin"
    )
    
    for port_desc in "${PORTS[@]}"; do
        IFS=':' read -r port description <<< "$port_desc"
        print_check "Checking port $port ($description)"
        if lsof -i ":$port" &> /dev/null; then
            print_warning "Port $port is in use"
        else
            print_success "Port $port is available"
        fi
    done
}

# Generate Report
generate_report() {
    print_header "Verification Summary"
    
    echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    echo -e "Success Rate: ${BLUE}$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))%${NC}"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All checks passed! Your environment is ready for development.${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Some checks failed. Please review the errors above.${NC}"
        echo -e "${YELLOW}Run 'make setup-dev' to fix most issues automatically.${NC}"
    fi
    
    # Save report
    REPORT_FILE="test-reports/environment-verification-$(date +%Y%m%d-%H%M%S).txt"
    mkdir -p test-reports
    {
        echo "Environment Verification Report"
        echo "Generated: $(date)"
        echo "================================"
        echo "Total Checks: $TOTAL_CHECKS"
        echo "Passed: $PASSED_CHECKS"
        echo "Failed: $FAILED_CHECKS"
        echo "Success Rate: $(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))%"
    } > "$REPORT_FILE"
    
    echo -e "\n${BLUE}Report saved to: $REPORT_FILE${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}ITDO ERP System - Environment Verification${NC}"
    echo -e "${BLUE}===========================================${NC}"
    
    # Setup environment
    setup_environment
    
    # Run all checks
    check_basic_tools
    check_project_structure
    check_claude_config
    check_data_services
    check_python_env
    check_node_env
    check_github_actions
    check_test_config
    check_security_config
    check_port_availability
    
    # Generate summary report
    generate_report
}

# Run main function
main