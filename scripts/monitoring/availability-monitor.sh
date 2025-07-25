#!/bin/bash
# CC03 v58.0 - Production Availability Monitoring Script
# Target: 99.9% Availability (8.77 hours downtime/year maximum)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/itdo-erp/availability-monitor.log"
METRICS_FILE="/var/log/itdo-erp/availability-metrics.json"
ALERT_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
CHECK_INTERVAL=${CHECK_INTERVAL:-30}  # seconds
AVAILABILITY_TARGET=99.9
MAX_RESPONSE_TIME=5000  # milliseconds

# Service endpoints
FRONTEND_URL="${FRONTEND_URL:-https://itdo-erp.com}"
API_URL="${API_URL:-https://api.itdo-erp.com}"
AUTH_URL="${AUTH_URL:-https://auth.itdo-erp.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Initialize metrics file
init_metrics() {
    if [ ! -f "$METRICS_FILE" ]; then
        cat > "$METRICS_FILE" << EOF
{
  "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_checks": 0,
  "successful_checks": 0,
  "failed_checks": 0,
  "downtime_seconds": 0,
  "current_availability": 100.0,
  "services": {
    "frontend": {
      "status": "unknown",
      "response_time": 0,
      "last_check": "",
      "uptime_checks": 0,
      "failed_checks": 0
    },
    "api": {
      "status": "unknown", 
      "response_time": 0,
      "last_check": "",
      "uptime_checks": 0,
      "failed_checks": 0
    },
    "auth": {
      "status": "unknown",
      "response_time": 0,
      "last_check": "",
      "uptime_checks": 0,
      "failed_checks": 0
    }
  },
  "last_incident": null,
  "recovery_time": null
}
EOF
    fi
}

# Check service health
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout=10
    
    info "Checking $service_name at $url"
    
    # Measure response time
    local start_time=$(date +%s%3N)
    local http_code
    local response_time
    
    if http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout "$url" 2>/dev/null); then
        local end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))
        
        if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 301 ] || [ "$http_code" -eq 302 ]; then
            if [ "$response_time" -lt "$MAX_RESPONSE_TIME" ]; then
                log "✅ $service_name: UP (${response_time}ms, HTTP $http_code)"
                update_metrics "$service_name" "up" "$response_time"
                return 0
            else
                warn "⚠️ $service_name: SLOW (${response_time}ms, HTTP $http_code)"
                update_metrics "$service_name" "slow" "$response_time" 
                return 1
            fi
        else
            error "❌ $service_name: ERROR (HTTP $http_code)"
            update_metrics "$service_name" "down" "$response_time"
            return 1
        fi
    else
        error "❌ $service_name: UNREACHABLE"
        update_metrics "$service_name" "down" 0
        return 1
    fi
}

# Update metrics
update_metrics() {
    local service="$1"
    local status="$2"
    local response_time="$3"
    local current_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Use jq to update metrics (install if not available)
    if ! command -v jq &> /dev/null; then
        warn "jq not installed, installing..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    # Update service-specific metrics
    tmp_file=$(mktemp)
    jq --arg service "$service" \
       --arg status "$status" \
       --arg response_time "$response_time" \
       --arg current_time "$current_time" \
       '.services[$service].status = $status |
        .services[$service].response_time = ($response_time | tonumber) |
        .services[$service].last_check = $current_time |
        .total_checks += 1 |
        if $status == "up" then
          .successful_checks += 1 |
          .services[$service].uptime_checks += 1
        else
          .failed_checks += 1 |
          .services[$service].failed_checks += 1
        end |
        .current_availability = ((.successful_checks / .total_checks) * 100)' \
        "$METRICS_FILE" > "$tmp_file" && mv "$tmp_file" "$METRICS_FILE"
}

# Send alert
send_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    if [ -n "$ALERT_WEBHOOK" ]; then
        local color="warning"
        [ "$severity" = "critical" ] && color="danger"
        [ "$severity" = "info" ] && color="good"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"ITDO ERP Production Alert\",
                    \"text\": \"$message\",
                    \"footer\": \"Availability Monitor\",
                    \"ts\": $(date +%s)
                }]
            }" \
            "$ALERT_WEBHOOK" 2>/dev/null || warn "Failed to send alert"
    fi
    
    # Log locally
    case "$severity" in
        "critical") error "$message" ;;
        "warning") warn "$message" ;;
        *) info "$message" ;;
    esac
}

# Check availability threshold
check_availability_threshold() {
    local current_availability
    current_availability=$(jq -r '.current_availability' "$METRICS_FILE")
    
    if (( $(echo "$current_availability < $AVAILABILITY_TARGET" | bc -l) )); then
        local downtime_minutes
        downtime_minutes=$(jq -r '.failed_checks * ('$CHECK_INTERVAL' / 60)' "$METRICS_FILE")
        
        send_alert "🚨 CRITICAL: Availability dropped to ${current_availability}% (Target: ${AVAILABILITY_TARGET}%). Estimated downtime: ${downtime_minutes} minutes." "critical"
        
        # Trigger recovery procedures
        trigger_recovery
    elif (( $(echo "$current_availability < 99.5" | bc -l) )); then
        send_alert "⚠️ WARNING: Availability at ${current_availability}% (Target: ${AVAILABILITY_TARGET}%)" "warning"
    fi
}

# Trigger recovery procedures
trigger_recovery() {
    info "🔧 Triggering automated recovery procedures..."
    
    # Restart services if available
    if command -v docker-compose &> /dev/null && [ -f "/opt/itdo-erp/compose-prod.yaml" ]; then
        info "🔄 Restarting production services..."
        cd /opt/itdo-erp
        docker-compose -f compose-prod.yaml restart
        sleep 60  # Wait for services to stabilize
    fi
    
    # Run health checks
    info "🏥 Running post-recovery health checks..."
    run_health_checks
}

# Generate availability report
generate_report() {
    local current_availability
    local total_checks
    local failed_checks
    local uptime_hours
    
    current_availability=$(jq -r '.current_availability' "$METRICS_FILE")
    total_checks=$(jq -r '.total_checks' "$METRICS_FILE")
    failed_checks=$(jq -r '.failed_checks' "$METRICS_FILE")
    
    # Calculate uptime in hours
    local start_time
    start_time=$(jq -r '.start_time' "$METRICS_FILE")
    local current_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local uptime_seconds
    uptime_seconds=$(( $(date -d "$current_time" +%s) - $(date -d "$start_time" +%s) ))
    uptime_hours=$(echo "scale=2; $uptime_seconds / 3600" | bc -l)
    
    cat << EOF

📊 AVAILABILITY REPORT
=====================
Current Availability: ${current_availability}%
Target Availability: ${AVAILABILITY_TARGET}%
Total Checks: ${total_checks}
Failed Checks: ${failed_checks}
Monitoring Duration: ${uptime_hours} hours

Service Status:
$(jq -r '.services | to_entries[] | "- \(.key): \(.value.status) (\(.value.response_time)ms)"' "$METRICS_FILE")

Last Updated: $(date)
EOF
}

# Run comprehensive health checks
run_health_checks() {
    local all_services_up=true
    
    # Check all services
    check_service "frontend" "$FRONTEND_URL" || all_services_up=false
    check_service "api" "$API_URL/api/v1/health" || all_services_up=false  
    check_service "auth" "$AUTH_URL/health" || all_services_up=false
    
    # Update overall status
    if [ "$all_services_up" = true ]; then
        info "✅ All services operational"
    else
        warn "⚠️ Some services are experiencing issues"
    fi
    
    # Check availability threshold
    check_availability_threshold
    
    return 0
}

# Main monitoring loop
main() {
    info "🚀 Starting ITDO ERP Availability Monitor (Target: ${AVAILABILITY_TARGET}%)"
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$METRICS_FILE")"
    
    # Initialize metrics
    init_metrics
    
    # Send startup notification
    send_alert "🚀 Availability monitoring started. Target: ${AVAILABILITY_TARGET}%" "info"
    
    # Main monitoring loop
    while true; do
        run_health_checks
        
        # Generate report every hour (3600 seconds / CHECK_INTERVAL)
        local check_count
        check_count=$(jq -r '.total_checks' "$METRICS_FILE")
        if (( check_count % (3600 / CHECK_INTERVAL) == 0 )) && [ "$check_count" -gt 0 ]; then
            generate_report
        fi
        
        sleep "$CHECK_INTERVAL"
    done
}

# Signal handlers
trap 'info "🛑 Availability monitor stopped"; exit 0' SIGTERM SIGINT

# Install dependencies if missing
install_dependencies() {
    if ! command -v bc &> /dev/null; then
        info "Installing bc calculator..."
        sudo apt-get update && sudo apt-get install -y bc
    fi
    
    if ! command -v jq &> /dev/null; then
        info "Installing jq JSON processor..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
}

# Check if running as daemon
if [ "${1:-}" = "daemon" ]; then
    install_dependencies
    main
elif [ "${1:-}" = "check" ]; then
    install_dependencies
    init_metrics
    run_health_checks
    generate_report
elif [ "${1:-}" = "report" ]; then
    init_metrics
    generate_report
else
    echo "Usage: $0 {daemon|check|report}"
    echo "  daemon - Run continuous monitoring"
    echo "  check  - Run single health check"
    echo "  report - Generate availability report"
    exit 1
fi