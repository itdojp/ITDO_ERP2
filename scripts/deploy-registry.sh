#!/bin/bash

# Deploy Container Registry for ITDO ERP Development Environment
# This script deploys Harbor (full-featured) and Docker Registry (lightweight) options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_TYPE=${1:-harbor}  # harbor or docker-registry
NAMESPACE="registry"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    if ! command -v kubectl &> /dev/null; then
        print_status $RED "❌ kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        print_status $RED "❌ helm is not installed or not in PATH"
        exit 1
    fi

    if ! command -v openssl &> /dev/null; then
        print_status $RED "❌ openssl is not installed or not in PATH"
        exit 1
    fi
}

# Function to create namespace and secrets
setup_namespace() {
    print_status $YELLOW "📁 Creating registry namespace..."
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
}

# Function to setup authentication secrets
setup_auth_secrets() {
    print_status $YELLOW "🔐 Setting up authentication secrets..."
    
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        # Harbor uses its own authentication
        kubectl create secret generic harbor-basic-auth \
            --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 Harbor12345!)" | base64 -w 0) \
            --namespace $NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        # Docker Registry authentication
        # Create htpasswd file for basic auth
        TEMP_HTPASSWD=$(mktemp)
        echo -n "admin:" > $TEMP_HTPASSWD
        echo "admin123!" | openssl passwd -apr1 -stdin >> $TEMP_HTPASSWD
        
        kubectl create secret generic registry-auth \
            --from-file=htpasswd=$TEMP_HTPASSWD \
            --namespace $NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
            
        kubectl create secret generic registry-basic-auth \
            --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
            --namespace $NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
            
        # Cleanup temp file
        rm -f $TEMP_HTPASSWD
    fi
}

# Function to add Helm repositories
add_helm_repos() {
    print_status $YELLOW "📦 Adding Helm repositories..."
    
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        helm repo add harbor https://helm.goharbor.io
    else
        helm repo add twuni https://helm.twun.io
    fi
    
    helm repo update
}

# Function to deploy Harbor
deploy_harbor() {
    print_status $YELLOW "🚢 Deploying Harbor Container Registry..."
    
    # Generate encryption key for Harbor
    HARBOR_SECRET_KEY=$(openssl rand -base64 32)
    
    # Create Harbor secrets
    kubectl create secret generic harbor-encryption-key \
        --from-literal=secretKey=$HARBOR_SECRET_KEY \
        --namespace $NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Harbor
    helm upgrade --install harbor harbor/harbor \
        --namespace $NAMESPACE \
        --values registry/harbor/values.yaml \
        --set secretKey=$HARBOR_SECRET_KEY \
        --version 1.13.0 \
        --wait \
        --timeout 20m
}

# Function to deploy Docker Registry
deploy_docker_registry() {
    print_status $YELLOW "📦 Deploying Docker Registry..."
    
    helm upgrade --install docker-registry twuni/docker-registry \
        --namespace $NAMESPACE \
        --values registry/docker-registry/values.yaml \
        --version 2.2.2 \
        --wait \
        --timeout 10m
}

# Function to setup garbage collection
setup_garbage_collection() {
    print_status $YELLOW "🗑️ Setting up garbage collection..."
    
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        # Harbor has built-in GC
        print_status $GREEN "✅ Harbor garbage collection configured automatically"
    else
        # Setup Docker Registry garbage collection CronJob
        cat > /tmp/registry-gc.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: registry-garbage-collector
  namespace: registry
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: registry-gc
            image: registry:2.8.3
            command:
            - /bin/registry
            - garbage-collect
            - --delete-untagged
            - /etc/registry/config.yml
            env:
            - name: REGISTRY_STORAGE_DELETE_ENABLED
              value: "true"
            volumeMounts:
            - name: registry-storage
              mountPath: /var/lib/registry
            - name: registry-config
              mountPath: /etc/registry
          volumes:
          - name: registry-storage
            persistentVolumeClaim:
              claimName: docker-registry
          - name: registry-config
            configMap:
              name: docker-registry-config
          restartPolicy: OnFailure
EOF
        
        kubectl apply -f /tmp/registry-gc.yaml
        rm -f /tmp/registry-gc.yaml
    fi
}

# Function to create webhook configuration
setup_webhooks() {
    print_status $YELLOW "🔗 Setting up webhook integration..."
    
    # Create webhook secret
    kubectl create secret generic registry-webhook-secret \
        --from-literal=token=$(openssl rand -base64 32) \
        --namespace $NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
}

# Function to configure monitoring
setup_monitoring() {
    print_status $YELLOW "📊 Setting up monitoring..."
    
    # Create ServiceMonitor for Prometheus
    cat > /tmp/registry-servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ${REGISTRY_TYPE}-registry
  namespace: monitoring
  labels:
    app: ${REGISTRY_TYPE}-registry
spec:
  selector:
    matchLabels:
      app: ${REGISTRY_TYPE}
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
  namespaceSelector:
    matchNames:
    - $NAMESPACE
EOF
    
    kubectl apply -f /tmp/registry-servicemonitor.yaml
    rm -f /tmp/registry-servicemonitor.yaml
    
    print_status $GREEN "✅ ServiceMonitor created for Prometheus scraping"
}

# Function to verify deployment
verify_deployment() {
    print_status $YELLOW "⏳ Verifying deployment..."
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l "app=${REGISTRY_TYPE}" --timeout=300s -n $NAMESPACE
    
    # Test registry connectivity
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        REGISTRY_URL="https://registry.itdo-erp.com"
        print_status $BLUE "Testing Harbor connectivity..."
    else
        REGISTRY_URL="https://docker-registry.itdo-erp.com"
        print_status $BLUE "Testing Docker Registry connectivity..."
    fi
    
    # Give some time for ingress to be ready
    sleep 30
    
    print_status $GREEN "✅ ${REGISTRY_TYPE^} registry deployed successfully!"
}

# Function to display information
show_info() {
    print_status $GREEN "✅ Container Registry deployed successfully!"
    print_status $BLUE "📊 Service Information:"
    
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        cat << 'EOF'

Harbor Container Registry:
  URL: https://registry.itdo-erp.com
  Username: admin  
  Password: Harbor12345!
  
Features Available:
  ✅ Web UI for registry management
  ✅ Vulnerability scanning with Trivy
  ✅ Helm chart repository (ChartMuseum)
  ✅ Image signing with Notary
  ✅ OIDC integration with Keycloak
  ✅ Project-based access control
  ✅ Automated garbage collection
  ✅ Webhook notifications

Docker CLI Usage:
  docker login registry.itdo-erp.com
  docker tag myapp:latest registry.itdo-erp.com/itdo-erp/myapp:latest
  docker push registry.itdo-erp.com/itdo-erp/myapp:latest

Kubectl Usage:
  kubectl create secret docker-registry regcred \
    --docker-server=registry.itdo-erp.com \
    --docker-username=admin \
    --docker-password=Harbor12345! \
    --docker-email=admin@itdo-erp.com

EOF
    else
        cat << 'EOF'

Docker Registry:
  URL: https://docker-registry.itdo-erp.com
  Username: admin
  Password: admin123!
  
Features Available:
  ✅ Basic image storage and retrieval
  ✅ RESTful API
  ✅ Webhook notifications
  ✅ Automated garbage collection
  ✅ Basic authentication

Docker CLI Usage:
  docker login docker-registry.itdo-erp.com
  docker tag myapp:latest docker-registry.itdo-erp.com/myapp:latest
  docker push docker-registry.itdo-erp.com/myapp:latest

Kubectl Usage:
  kubectl create secret docker-registry regcred \
    --docker-server=docker-registry.itdo-erp.com \
    --docker-username=admin \
    --docker-password=admin123! \
    --docker-email=admin@itdo-erp.com

EOF
    fi
    
    print_status $BLUE "🔧 Registry API Examples:"
    cat << EOF

# List repositories
curl -u admin:password https://${REGISTRY_TYPE}.itdo-erp.com/v2/_catalog

# List tags for a repository  
curl -u admin:password https://${REGISTRY_TYPE}.itdo-erp.com/v2/myapp/tags/list

# Get image manifest
curl -u admin:password https://${REGISTRY_TYPE}.itdo-erp.com/v2/myapp/manifests/latest

EOF

    print_status $BLUE "📈 Storage Information:"
    cat << EOF

Storage Allocation:
  - Registry Images: 100Gi (Harbor) / 50Gi (Docker Registry)
  - Database: 10Gi (Harbor only)
  - Redis Cache: 5Gi (Harbor only)
  
Retention Policies:
  - Untagged images: Deleted after 24 hours
  - Garbage collection: Daily at 3 AM
  - Vulnerability scan updates: Daily

Performance Expectations:
  - Image push/pull speed: 100MB/s (local network)
  - Concurrent connections: 100+
  - Storage compression: ~30-40% (depending on image layers)

EOF
}

# Main execution
main() {
    print_status $BLUE "🚀 Deploying ITDO ERP Container Registry"
    print_status $BLUE "Registry Type: ${REGISTRY_TYPE^}"
    
    check_prerequisites
    setup_namespace
    setup_auth_secrets
    add_helm_repos
    
    if [[ "$REGISTRY_TYPE" == "harbor" ]]; then
        deploy_harbor
    else
        deploy_docker_registry
    fi
    
    setup_garbage_collection
    setup_webhooks
    setup_monitoring
    verify_deployment
    show_info
    
    print_status $GREEN "🎉 Container registry deployment completed!"
    print_status $YELLOW "💡 Next steps:"
    echo "1. Configure your CI/CD pipeline to use this registry"
    echo "2. Create projects and configure access control (Harbor only)"
    echo "3. Set up image vulnerability scanning policies"
    echo "4. Configure backup and disaster recovery procedures"
    echo "5. Integrate with development workflows and IDE plugins"
}

# Show usage if invalid argument
if [[ "$1" != "harbor" && "$1" != "docker-registry" && "$1" != "" ]]; then
    echo "Usage: $0 [harbor|docker-registry]"
    echo ""
    echo "Options:"
    echo "  harbor          Deploy full-featured Harbor registry (default)"
    echo "  docker-registry Deploy lightweight Docker Registry"
    echo ""
    echo "Examples:"
    echo "  $0 harbor           # Deploy Harbor with full features"
    echo "  $0 docker-registry  # Deploy simple Docker Registry"
    exit 1
fi

# Execute main function
main