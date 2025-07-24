#!/bin/bash

# Performance Testing Runner for ITDO ERP System
# This script orchestrates various performance testing scenarios

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"
CONFIGS_DIR="${SCRIPT_DIR}/configs"
DATE_STAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if k6 is installed
check_k6() {
    if ! command -v k6 &> /dev/null; then
        print_status $RED "❌ k6 is not installed. Please install k6 first:"
        echo "   curl https://github.com/grafana/k6/releases/download/v0.46.0/k6-v0.46.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1"
        exit 1
    fi
    
    local k6_version=$(k6 version | head -n1)
    print_status $GREEN "✅ k6 found: ${k6_version}"
}

# Function to check if target URL is accessible
check_target() {
    local base_url=${1:-"http://localhost:8000"}
    
    print_status $BLUE "🔍 Checking target accessibility: ${base_url}"
    
    if curl -s -f "${base_url}/health" > /dev/null; then
        print_status $GREEN "✅ Target is accessible"
    else
        print_status $RED "❌ Target is not accessible. Please ensure the application is running."
        exit 1
    fi
}

# Function to run a specific test
run_test() {
    local test_type=$1
    local base_url=$2
    local output_file="${REPORTS_DIR}/${test_type}_${DATE_STAMP}"
    
    print_status $BLUE "🚀 Running ${test_type} test..."
    
    case $test_type in
        "smoke")
            k6 run \
                --env BASE_URL="${base_url}" \
                --out json="${output_file}.json" \
                --out html="${output_file}.html" \
                "${SCRIPT_DIR}/scenarios/api-smoke-test.js"
            ;;
        "load")
            k6 run \
                --env BASE_URL="${base_url}" \
                --out json="${output_file}.json" \
                --out html="${output_file}.html" \
                "${SCRIPT_DIR}/scripts/load-test.js"
            ;;
        "stress")
            k6 run \
                --env BASE_URL="${base_url}" \
                --out json="${output_file}.json" \
                --out html="${output_file}.html" \
                "${SCRIPT_DIR}/scripts/stress-test.js"
            ;;
        "spike")
            k6 run \
                --env BASE_URL="${base_url}" \
                --out json="${output_file}.json" \
                --out html="${output_file}.html" \
                --stage "1m:10,30s:100,2m:100,30s:10,1m:10" \
                "${SCRIPT_DIR}/scripts/load-test.js"
            ;;
        *)
            print_status $RED "❌ Unknown test type: ${test_type}"
            exit 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ ${test_type} test completed successfully"
        print_status $BLUE "📊 Results saved to: ${output_file}.{json,html}"
    else
        print_status $RED "❌ ${test_type} test failed"
        exit 1
    fi
}

# Function to generate summary report
generate_summary() {
    local summary_file="${REPORTS_DIR}/summary_${DATE_STAMP}.md"
    
    print_status $BLUE "📋 Generating test summary..."
    
    cat > "${summary_file}" << EOF
# Performance Test Summary

**Date:** $(date)
**Environment:** ${BASE_URL}

## Test Results

EOF

    # Add results for each test type
    for result_file in "${REPORTS_DIR}"/*_${DATE_STAMP}.json; do
        if [ -f "$result_file" ]; then
            local test_name=$(basename "$result_file" | cut -d'_' -f1)
            echo "### ${test_name^} Test" >> "${summary_file}"
            echo "" >> "${summary_file}"
            
            # Extract key metrics using jq if available
            if command -v jq &> /dev/null; then
                echo "- **Average Response Time:** $(jq -r '.metrics.http_req_duration.avg' "$result_file" 2>/dev/null || echo "N/A") ms" >> "${summary_file}"
                echo "- **95th Percentile:** $(jq -r '.metrics.http_req_duration.p95' "$result_file" 2>/dev/null || echo "N/A") ms" >> "${summary_file}"
                echo "- **Error Rate:** $(jq -r '.metrics.http_req_failed.rate' "$result_file" 2>/dev/null || echo "N/A")" >> "${summary_file}"
                echo "- **Total Requests:** $(jq -r '.metrics.http_reqs.count' "$result_file" 2>/dev/null || echo "N/A")" >> "${summary_file}"
            else
                echo "- **Report File:** $(basename "$result_file")" >> "${summary_file}"
            fi
            echo "" >> "${summary_file}"
        fi
    done
    
    cat >> "${summary_file}" << EOF

## Recommendations

1. **Response Time Analysis:** Check if response times meet SLA requirements
2. **Error Rate Review:** Investigate any errors above acceptable thresholds
3. **Capacity Planning:** Use stress test results for scaling decisions
4. **Bottleneck Identification:** Review detailed metrics for performance bottlenecks

## Files Generated

EOF

    # List all generated files
    for file in "${REPORTS_DIR}"/*_${DATE_STAMP}.*; do
        if [ -f "$file" ]; then
            echo "- $(basename "$file")" >> "${summary_file}"
        fi
    done
    
    print_status $GREEN "✅ Summary report generated: ${summary_file}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [test_type] [base_url]"
    echo ""
    echo "Test types:"
    echo "  smoke   - Quick API validation (2 minutes)"
    echo "  load    - Standard load test (16 minutes)"
    echo "  stress  - High load stress test (16 minutes)"
    echo "  spike   - Traffic spike test (5 minutes)"
    echo "  all     - Run all tests sequentially"
    echo ""
    echo "Examples:"
    echo "  $0 smoke                           # Run smoke test on localhost"
    echo "  $0 load http://localhost:8000      # Run load test on specific URL"
    echo "  $0 all https://api.example.com     # Run all tests"
    echo ""
    echo "Environment variables:"
    echo "  BASE_URL - Default target URL (default: http://localhost:8000)"
}

# Main execution
main() {
    local test_type=${1:-"smoke"}
    local base_url=${2:-${BASE_URL:-"http://localhost:8000"}}
    
    print_status $BLUE "🎯 ITDO ERP Performance Testing Suite"
    print_status $BLUE "======================================"
    
    # Show usage if help requested
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    # Perform pre-flight checks
    check_k6
    check_target "$base_url"
    
    print_status $YELLOW "📝 Test Configuration:"
    echo "   Test Type: $test_type"
    echo "   Target URL: $base_url"
    echo "   Reports Directory: $REPORTS_DIR"
    echo ""
    
    # Run tests
    if [ "$test_type" = "all" ]; then
        print_status $BLUE "🏃‍♂️ Running all test suites..."
        
        run_test "smoke" "$base_url"
        sleep 10
        
        run_test "load" "$base_url"
        sleep 30
        
        run_test "spike" "$base_url"
        sleep 30
        
        # Only run stress test if explicitly requested for 'all'
        read -p "Run stress test? This will apply high load (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_test "stress" "$base_url"
        fi
    else
        run_test "$test_type" "$base_url"
    fi
    
    # Generate summary
    generate_summary
    
    print_status $GREEN "🎉 Performance testing completed!"
    print_status $BLUE "📁 Check the reports directory for detailed results: ${REPORTS_DIR}"
}

# Run main function with all arguments
main "$@"