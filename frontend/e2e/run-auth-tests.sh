#!/bin/bash

# E2E Authentication Tests Runner

echo "🧪 Running E2E Authentication Tests"
echo "=================================="

# Set up environment
export NODE_ENV=test
export API_URL=http://localhost:8000
export FRONTEND_URL=http://localhost:3000

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run test with timing
run_test() {
    local test_name=$1
    local test_file=$2
    
    echo -e "\n${YELLOW}Running: $test_name${NC}"
    start_time=$(date +%s)
    
    if npx playwright test "$test_file" --reporter=list; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✓ $test_name passed (${duration}s)${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
}

# Check if services are running
echo "Checking services..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}Backend is not running. Please start it first.${NC}"
    exit 1
fi

if ! curl -s http://localhost:3000 > /dev/null; then
    echo -e "${RED}Frontend is not running. Please start it first.${NC}"
    exit 1
fi

echo -e "${GREEN}Services are running${NC}"

# Install Playwright browsers if needed
echo "Ensuring Playwright browsers are installed..."
npx playwright install

# Run tests
echo -e "\n${YELLOW}Starting test execution...${NC}"

total_tests=0
passed_tests=0

# Run each test suite
test_suites=(
    "Login Tests:tests/auth/auth-login.spec.ts"
    "MFA Verification:tests/auth/auth-mfa.spec.ts"
    "Registration:tests/auth/auth-register.spec.ts"
    "Password Reset:tests/auth/auth-password-reset.spec.ts"
    "MFA Setup:tests/auth/auth-mfa-setup.spec.ts"
    "Session Management:tests/auth/auth-session-management.spec.ts"
    "Complete Flow:tests/auth/auth-complete-flow.spec.ts"
)

for suite in "${test_suites[@]}"; do
    IFS=':' read -r name file <<< "$suite"
    ((total_tests++))
    
    if run_test "$name" "$file"; then
        ((passed_tests++))
    fi
done

# Generate summary
echo -e "\n=================================="
echo "📊 Test Summary"
echo "=================================="
echo "Total test suites: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    echo "View detailed reports in: test-results/"
    exit 1
fi