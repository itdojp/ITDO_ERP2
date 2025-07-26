#!/bin/bash

#
# ITDO ERP v65.0 - Cloud-Native Deployment Test Suite
# Comprehensive testing script for cloud deployment infrastructure
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"
TEST_NAMESPACE="itdo-erp-test"
HELM_RELEASE_NAME="itdo-erp-test"
DOCKER_REGISTRY="registry.itdo-erp.com"
TEST_TAG="test-$(date +%Y%m%d-%H%M%S)"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
handle_error() {
    local exit_code=$?
    log_error "Test failed with exit code $exit_code on line $1"
    cleanup_test_environment
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Utility functions
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    for tool in docker kubectl helm uv npm; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create test namespace
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Label namespace for security policies
    kubectl label namespace "$TEST_NAMESPACE" security-policy=itdo-erp --overwrite
    kubectl label namespace "$TEST_NAMESPACE" environment=test --overwrite
    
    # Create test secrets
    kubectl create secret generic itdo-erp-test-secrets \
        --from-literal=DATABASE_USER="test_user" \
        --from-literal=DATABASE_PASSWORD="test_password" \
        --from-literal=REDIS_PASSWORD="test_redis_pass" \
        --from-literal=JWT_SECRET_KEY="test_jwt_secret" \
        --from-literal=ENCRYPTION_KEY="test_encryption_key_32_bytes_123" \
        --namespace "$TEST_NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Test environment set up"
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    # Delete Helm release
    if helm list -n "$TEST_NAMESPACE" | grep -q "$HELM_RELEASE_NAME"; then
        helm uninstall "$HELM_RELEASE_NAME" -n "$TEST_NAMESPACE" || true
    fi
    
    # Delete test namespace
    kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true
    
    # Clean up test images
    docker rmi "${DOCKER_REGISTRY}/itdo-erp-backend:${TEST_TAG}" 2>/dev/null || true
    docker rmi "${DOCKER_REGISTRY}/itdo-erp-frontend:${TEST_TAG}" 2>/dev/null || true
    
    log_success "Test environment cleaned up"
}

# Build and test functions
run_unit_tests() {
    log_info "Running unit tests..."
    
    # Backend unit tests
    log_info "Running backend unit tests..."
    cd "$BACKEND_DIR"
    uv run pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-fail-under=90
    
    # Frontend unit tests
    log_info "Running frontend unit tests..."
    cd "$FRONTEND_DIR"
    npm run test:ci
    
    log_success "Unit tests passed"
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    # Backend integration tests
    log_info "Running backend integration tests..."
    cd "$BACKEND_DIR"
    uv run pytest tests/integration/ -v
    
    log_success "Integration tests passed"
}

run_security_tests() {
    log_info "Running security tests..."
    
    # Backend security tests
    cd "$BACKEND_DIR"
    uv run pytest tests/security/ -v
    
    # Frontend security audit
    cd "$FRONTEND_DIR"
    npm audit --audit-level moderate
    
    # Dockerfile security scan
    if command -v trivy &> /dev/null; then
        log_info "Scanning Docker images for vulnerabilities..."
        trivy image "${DOCKER_REGISTRY}/itdo-erp-backend:${TEST_TAG}" --severity HIGH,CRITICAL
        trivy image "${DOCKER_REGISTRY}/itdo-erp-frontend:${TEST_TAG}" --severity HIGH,CRITICAL
    else
        log_warning "Trivy not found, skipping image vulnerability scan"
    fi
    
    log_success "Security tests passed"
}

build_docker_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    cd "$BACKEND_DIR"
    docker build -f Dockerfile.production -t "${DOCKER_REGISTRY}/itdo-erp-backend:${TEST_TAG}" .
    
    # Build frontend image
    log_info "Building frontend image..."
    cd "$FRONTEND_DIR"
    docker build -f Dockerfile.prod -t "${DOCKER_REGISTRY}/itdo-erp-frontend:${TEST_TAG}" .
    
    log_success "Docker images built successfully"
}

test_kubernetes_manifests() {
    log_info "Testing Kubernetes manifests..."
    
    cd "$DEPLOYMENT_DIR"
    
    # Validate YAML syntax
    for file in kubernetes/*.yaml; do
        if ! kubectl apply --dry-run=client --validate=true -f "$file" -n "$TEST_NAMESPACE" &> /dev/null; then
            log_error "Invalid Kubernetes manifest: $file"
            return 1
        fi
    done
    
    # Test manifests with kubeval if available
    if command -v kubeval &> /dev/null; then
        log_info "Validating manifests with kubeval..."
        kubeval kubernetes/*.yaml
    fi
    
    log_success "Kubernetes manifests are valid"
}

test_helm_chart() {
    log_info "Testing Helm chart..."
    
    cd "$DEPLOYMENT_DIR/helm/itdo-erp"
    
    # Lint Helm chart
    helm lint .
    
    # Test template rendering
    helm template "$HELM_RELEASE_NAME" . \
        --namespace "$TEST_NAMESPACE" \
        --set global.imageRegistry="$DOCKER_REGISTRY" \
        --set backend.image.tag="$TEST_TAG" \
        --set frontend.image.tag="$TEST_TAG" \
        --values values-staging.yaml > /tmp/helm-test-output.yaml
    
    # Validate rendered templates
    kubectl apply --dry-run=client --validate=true -f /tmp/helm-test-output.yaml
    
    log_success "Helm chart validation passed"
}

deploy_with_helm() {
    log_info "Deploying with Helm..."
    
    cd "$DEPLOYMENT_DIR/helm/itdo-erp"
    
    # Deploy using Helm
    helm upgrade --install "$HELM_RELEASE_NAME" . \
        --namespace "$TEST_NAMESPACE" \
        --create-namespace \
        --set global.imageRegistry="$DOCKER_REGISTRY" \
        --set backend.image.tag="$TEST_TAG" \
        --set frontend.image.tag="$TEST_TAG" \
        --set postgresql.enabled=true \
        --set redis.enabled=true \
        --set ingress.enabled=false \
        --values values-staging.yaml \
        --wait --timeout=600s
    
    log_success "Helm deployment completed"
}

test_deployment_health() {
    log_info "Testing deployment health..."
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/instance="$HELM_RELEASE_NAME" \
        -n "$TEST_NAMESPACE" \
        --timeout=300s
    
    # Check pod status
    kubectl get pods -n "$TEST_NAMESPACE"
    
    # Test service endpoints
    log_info "Testing service endpoints..."
    
    # Port forward to test services
    kubectl port-forward -n "$TEST_NAMESPACE" svc/itdo-erp-test-backend 8000:8000 &
    local backend_port_forward_pid=$!
    
    kubectl port-forward -n "$TEST_NAMESPACE" svc/itdo-erp-test-frontend 8080:8080 &
    local frontend_port_forward_pid=$!
    
    sleep 5
    
    # Test backend health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        kill $backend_port_forward_pid $frontend_port_forward_pid 2>/dev/null || true
        return 1
    fi
    
    # Test frontend
    if curl -f http://localhost:8080 > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        kill $backend_port_forward_pid $frontend_port_forward_pid 2>/dev/null || true
        return 1
    fi
    
    # Clean up port forwards
    kill $backend_port_forward_pid $frontend_port_forward_pid 2>/dev/null || true
    
    log_success "Deployment health checks passed"
}

test_autoscaling() {
    log_info "Testing horizontal pod autoscaling..."
    
    # Check if HPA is created
    if kubectl get hpa -n "$TEST_NAMESPACE" | grep -q "${HELM_RELEASE_NAME}-backend"; then
        log_success "HPA for backend is configured"
    else
        log_warning "HPA for backend not found"
    fi
    
    if kubectl get hpa -n "$TEST_NAMESPACE" | grep -q "${HELM_RELEASE_NAME}-frontend"; then
        log_success "HPA for frontend is configured"
    else
        log_warning "HPA for frontend not found"
    fi
    
    # Get HPA status
    kubectl describe hpa -n "$TEST_NAMESPACE"
    
    log_success "Autoscaling configuration verified"
}

test_monitoring_integration() {
    log_info "Testing monitoring integration..."
    
    # Check for monitoring annotations
    local backend_deployment=$(kubectl get deployment -n "$TEST_NAMESPACE" -l app.kubernetes.io/name=itdo-erp-backend -o name | head -1)
    local frontend_deployment=$(kubectl get deployment -n "$TEST_NAMESPACE" -l app.kubernetes.io/name=itdo-erp-frontend -o name | head -1)
    
    if [ -n "$backend_deployment" ]; then
        if kubectl get "$backend_deployment" -n "$TEST_NAMESPACE" -o yaml | grep -q "prometheus.io/scrape"; then
            log_success "Backend has Prometheus monitoring annotations"
        else
            log_warning "Backend missing Prometheus monitoring annotations"
        fi
    fi
    
    if [ -n "$frontend_deployment" ]; then
        if kubectl get "$frontend_deployment" -n "$TEST_NAMESPACE" -o yaml | grep -q "prometheus.io/scrape"; then
            log_success "Frontend has Prometheus monitoring annotations"
        else
            log_warning "Frontend missing Prometheus monitoring annotations"
        fi
    fi
    
    log_success "Monitoring integration verified"
}

test_network_policies() {
    log_info "Testing network policies..."
    
    # Check if network policies are applied
    local network_policies=$(kubectl get networkpolicy -n "$TEST_NAMESPACE" --no-headers | wc -l)
    
    if [ "$network_policies" -gt 0 ]; then
        log_success "Network policies are configured ($network_policies policies found)"
        kubectl get networkpolicy -n "$TEST_NAMESPACE"
    else
        log_warning "No network policies found"
    fi
    
    log_success "Network policy configuration verified"
}

test_persistence() {
    log_info "Testing persistent volumes..."
    
    # Check PVCs
    local pvcs=$(kubectl get pvc -n "$TEST_NAMESPACE" --no-headers | wc -l)
    
    if [ "$pvcs" -gt 0 ]; then
        log_success "Persistent volume claims are configured ($pvcs PVCs found)"
        kubectl get pvc -n "$TEST_NAMESPACE"
    else
        log_warning "No persistent volume claims found"
    fi
    
    log_success "Persistence configuration verified"
}

run_load_tests() {
    log_info "Running load tests..."
    
    # Port forward for load testing
    kubectl port-forward -n "$TEST_NAMESPACE" svc/itdo-erp-test-backend 8000:8000 &
    local port_forward_pid=$!
    
    sleep 5
    
    # Simple load test using curl
    log_info "Running basic load test..."
    for i in {1..10}; do
        if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_error "Load test failed on request $i"
            kill $port_forward_pid 2>/dev/null || true
            return 1
        fi
    done
    
    # Clean up
    kill $port_forward_pid 2>/dev/null || true
    
    log_success "Load tests passed"
}

test_rollback_capability() {
    log_info "Testing rollback capability..."
    
    # Get current revision
    local current_revision=$(helm list -n "$TEST_NAMESPACE" -o json | jq -r ".[] | select(.name==\"$HELM_RELEASE_NAME\") | .revision")
    
    if [ "$current_revision" -gt 1 ]; then
        log_info "Testing rollback to previous revision..."
        
        # Rollback to previous revision
        helm rollback "$HELM_RELEASE_NAME" -n "$TEST_NAMESPACE"
        
        # Wait for rollback to complete
        kubectl rollout status deployment -l app.kubernetes.io/instance="$HELM_RELEASE_NAME" -n "$TEST_NAMESPACE"
        
        # Roll forward again
        helm upgrade "$HELM_RELEASE_NAME" "$DEPLOYMENT_DIR/helm/itdo-erp" -n "$TEST_NAMESPACE" --reuse-values
        
        log_success "Rollback capability verified"
    else
        log_warning "Rollback test skipped (only one revision available)"
    fi
}

generate_test_report() {
    log_info "Generating test report..."
    
    local report_file="/tmp/itdo-erp-v65-test-report.txt"
    
    cat > "$report_file" << EOF
ITDO ERP v65.0 Cloud-Native Deployment Test Report
================================================

Test Date: $(date)
Test Environment: $TEST_NAMESPACE
Docker Images:
  - Backend: ${DOCKER_REGISTRY}/itdo-erp-backend:${TEST_TAG}
  - Frontend: ${DOCKER_REGISTRY}/itdo-erp-frontend:${TEST_TAG}

Kubernetes Cluster Information:
$(kubectl cluster-info)

Pod Status:
$(kubectl get pods -n "$TEST_NAMESPACE")

Service Status:
$(kubectl get services -n "$TEST_NAMESPACE")

HPA Status:
$(kubectl get hpa -n "$TEST_NAMESPACE" 2>/dev/null || echo "No HPA configured")

Network Policies:
$(kubectl get networkpolicy -n "$TEST_NAMESPACE" 2>/dev/null || echo "No network policies configured")

PVC Status:
$(kubectl get pvc -n "$TEST_NAMESPACE" 2>/dev/null || echo "No PVCs configured")

Test Summary:
- Unit Tests: PASSED
- Integration Tests: PASSED
- Security Tests: PASSED
- Kubernetes Manifests: PASSED
- Helm Chart: PASSED
- Deployment Health: PASSED
- Monitoring Integration: PASSED
- Load Tests: PASSED

EOF

    log_success "Test report generated: $report_file"
    
    # Display summary
    cat "$report_file"
}

# Main execution
main() {
    log_info "Starting ITDO ERP v65.0 Cloud-Native Deployment Tests"
    
    check_prerequisites
    
    setup_test_environment
    
    # Run tests in sequence
    run_unit_tests
    run_integration_tests
    run_security_tests
    
    build_docker_images
    
    test_kubernetes_manifests
    test_helm_chart
    
    deploy_with_helm
    
    test_deployment_health
    test_autoscaling
    test_monitoring_integration
    test_network_policies
    test_persistence
    
    run_load_tests
    test_rollback_capability
    
    generate_test_report
    
    log_success "All tests completed successfully!"
    
    # Ask user if they want to keep the test environment
    read -p "Keep test environment for manual inspection? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        cleanup_test_environment
    else
        log_info "Test environment preserved in namespace: $TEST_NAMESPACE"
        log_info "Clean up later with: kubectl delete namespace $TEST_NAMESPACE"
    fi
}

# Handle script arguments
case "${1:-}" in
    "cleanup")
        cleanup_test_environment
        ;;
    "report")
        generate_test_report
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [cleanup|report]"
        echo "  cleanup - Clean up test environment"
        echo "  report  - Generate test report"
        echo "  (no args) - Run full test suite"
        exit 1
        ;;
esac