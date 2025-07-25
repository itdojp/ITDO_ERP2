#!/bin/bash
# ITDO ERP v2 - Kubernetes Deployment Script
# CC03 v48.0 Business-Aligned Infrastructure

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    fi
    
    # Check helm (optional but recommended)
    if ! command -v helm &> /dev/null; then
        warn "helm is not installed. Some components may need manual installation."
    fi
    
    log "Prerequisites check completed ✓"
}

# Apply namespace configurations
apply_namespaces() {
    log "Creating namespaces..."
    kubectl apply -f namespace.yaml
    
    # Wait for namespaces to be ready
    kubectl wait --for=condition=Active namespace/itdo-erp-prod --timeout=60s
    kubectl wait --for=condition=Active namespace/itdo-erp-monitoring --timeout=60s
    kubectl wait --for=condition=Active namespace/itdo-erp-data --timeout=60s
    
    log "Namespaces created successfully ✓"
}

# Apply storage classes
apply_storage() {
    log "Creating storage classes..."
    kubectl apply -f storage-classes.yaml
    log "Storage classes created successfully ✓"
}

# Apply secrets and config maps
apply_configs() {
    log "Creating configuration and secrets..."
    
    # Apply ConfigMaps first
    kubectl apply -f configmap.yaml
    
    # Apply Secrets (these should be replaced with proper secret management)
    warn "Applying template secrets. In production, use proper secret management!"
    kubectl apply -f secrets.yaml
    
    log "Configuration and secrets applied successfully ✓"
}

# Deploy data layer (PostgreSQL and Redis)
deploy_data_layer() {
    log "Deploying data layer..."
    
    # Deploy PostgreSQL cluster
    log "Deploying PostgreSQL cluster..."
    kubectl apply -f postgresql-cluster.yaml
    
    # Deploy Redis cluster
    log "Deploying Redis cluster..."
    kubectl apply -f redis-cluster.yaml
    
    # Wait for data layer to be ready
    log "Waiting for data layer to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=postgresql --timeout=300s -n itdo-erp-data
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=redis --timeout=300s -n itdo-erp-data
    
    log "Data layer deployed successfully ✓"
}

# Deploy application layer
deploy_applications() {
    log "Deploying applications..."
    
    # Deploy backend
    log "Deploying backend application..."
    kubectl apply -f backend-deployment.yaml
    
    # Deploy frontend
    log "Deploying frontend application..."
    kubectl apply -f frontend-deployment.yaml
    
    # Wait for applications to be ready
    log "Waiting for applications to be ready..."
    kubectl wait --for=condition=Available deployment/itdo-erp-backend --timeout=300s -n itdo-erp-prod
    kubectl wait --for=condition=Available deployment/itdo-erp-frontend --timeout=300s -n itdo-erp-prod
    
    log "Applications deployed successfully ✓"
}

# Deploy ingress and SSL
deploy_ingress() {
    log "Deploying ingress and SSL..."
    
    # Install cert-manager if not exists
    if ! kubectl get namespace cert-manager &> /dev/null; then
        log "Installing cert-manager..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
        kubectl wait --for=condition=Available deployment/cert-manager --timeout=300s -n cert-manager
        kubectl wait --for=condition=Available deployment/cert-manager-cainjector --timeout=300s -n cert-manager
        kubectl wait --for=condition=Available deployment/cert-manager-webhook --timeout=300s -n cert-manager
    fi
    
    # Apply certificate management
    kubectl apply -f cert-manager.yaml
    
    # Apply ingress controller
    kubectl apply -f ingress-nginx.yaml
    
    # Wait for ingress to be ready
    kubectl wait --for=condition=Available deployment/nginx-ingress-controller --timeout=300s -n ingress-nginx
    
    log "Ingress and SSL deployed successfully ✓"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    kubectl apply -f monitoring-stack.yaml
    
    # Wait for monitoring components to be ready
    log "Waiting for monitoring stack to be ready..."
    kubectl wait --for=condition=Available deployment/prometheus --timeout=300s -n itdo-erp-monitoring
    kubectl wait --for=condition=Available deployment/grafana --timeout=300s -n itdo-erp-monitoring
    kubectl wait --for=condition=Available deployment/loki --timeout=300s -n itdo-erp-monitoring
    
    log "Monitoring stack deployed successfully ✓"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check all pods are running
    log "Checking pod status..."
    kubectl get pods --all-namespaces -o wide
    
    # Check services
    log "Checking services..."
    kubectl get services --all-namespaces
    
    # Check ingress
    log "Checking ingress..."
    kubectl get ingress --all-namespaces
    
    # Health checks
    log "Performing health checks..."
    
    # Check if backend is responding
    BACKEND_IP=$(kubectl get service itdo-erp-backend-service -n itdo-erp-prod -o jsonpath='{.spec.clusterIP}')
    if kubectl run health-check --image=curlimages/curl --rm -i --restart=Never -- curl -f http://$BACKEND_IP:8000/api/v1/health; then
        log "Backend health check passed ✓"
    else
        warn "Backend health check failed"
    fi
    
    # Check if frontend is responding
    FRONTEND_IP=$(kubectl get service itdo-erp-frontend-service -n itdo-erp-prod -o jsonpath='{.spec.clusterIP}')
    if kubectl run health-check-frontend --image=curlimages/curl --rm -i --restart=Never -- curl -f http://$FRONTEND_IP:8080/health; then
        log "Frontend health check passed ✓"
    else
        warn "Frontend health check failed"
    fi
    
    log "Deployment verification completed ✓"
}

# Print deployment summary
print_summary() {
    log "🎉 ITDO ERP v2 Kubernetes Deployment Completed!"
    echo
    echo -e "${BLUE}=== Deployment Summary ===${NC}"
    echo -e "${GREEN}✓ Namespaces created${NC}"
    echo -e "${GREEN}✓ Storage classes configured${NC}"
    echo -e "${GREEN}✓ Data layer deployed (PostgreSQL + Redis)${NC}"
    echo -e "${GREEN}✓ Applications deployed (Backend + Frontend)${NC}"
    echo -e "${GREEN}✓ SSL/TLS certificates configured${NC}"
    echo -e "${GREEN}✓ Load balancer and ingress configured${NC}"
    echo -e "${GREEN}✓ Monitoring stack deployed${NC}"
    echo
    echo -e "${BLUE}=== Access Information ===${NC}"
    echo "🌐 Main Application: https://itdo-erp.com"
    echo "📊 Monitoring Dashboard: https://monitoring.itdo-erp.com/grafana"
    echo "📈 Prometheus: https://monitoring.itdo-erp.com/prometheus"
    echo
    echo -e "${BLUE}=== Next Steps ===${NC}"
    echo "1. Configure DNS to point to the load balancer IP"
    echo "2. Update SSL certificates with actual domain certificates"
    echo "3. Configure monitoring alerts and notifications"
    echo "4. Set up backup and disaster recovery procedures"
    echo "5. Configure CI/CD pipelines for automated deployments"
    echo
    echo -e "${YELLOW}⚠️  Security Notice:${NC}"
    echo "   - Replace template secrets with actual secure values"
    echo "   - Configure proper RBAC policies"
    echo "   - Enable network policies for production"
    echo "   - Configure backup encryption and retention policies"
    echo
}

# Cleanup function
cleanup() {
    if [[ ${1:-} == "all" ]]; then
        warn "Performing complete cleanup..."
        kubectl delete -f monitoring-stack.yaml --ignore-not-found=true
        kubectl delete -f ingress-nginx.yaml --ignore-not-found=true
        kubectl delete -f cert-manager.yaml --ignore-not-found=true
        kubectl delete -f frontend-deployment.yaml --ignore-not-found=true
        kubectl delete -f backend-deployment.yaml --ignore-not-found=true
        kubectl delete -f redis-cluster.yaml --ignore-not-found=true
        kubectl delete -f postgresql-cluster.yaml --ignore-not-found=true
        kubectl delete -f secrets.yaml --ignore-not-found=true
        kubectl delete -f configmap.yaml --ignore-not-found=true
        kubectl delete -f storage-classes.yaml --ignore-not-found=true
        kubectl delete -f namespace.yaml --ignore-not-found=true
        log "Cleanup completed"
    else
        log "Use '$0 cleanup all' to perform complete cleanup"
    fi
}

# Main deployment function
main() {
    case ${1:-deploy} in
        "deploy")
            log "Starting ITDO ERP v2 Kubernetes deployment..."
            check_prerequisites
            apply_namespaces
            apply_storage
            apply_configs
            deploy_data_layer
            deploy_applications
            deploy_ingress
            deploy_monitoring
            verify_deployment
            print_summary
            ;;
        "cleanup")
            cleanup ${2:-}
            ;;
        "verify")
            verify_deployment
            ;;
        "help")
            echo "Usage: $0 [deploy|cleanup|verify|help]"
            echo "  deploy  - Deploy the complete ITDO ERP v2 stack"
            echo "  cleanup - Remove all deployed resources (use 'cleanup all')"
            echo "  verify  - Verify the current deployment"
            echo "  help    - Show this help message"
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Script execution
main "$@"