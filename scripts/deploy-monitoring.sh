#!/bin/bash

# Deploy Monitoring Infrastructure for ITDO ERP
# This script deploys Prometheus, Grafana, and related monitoring components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_status $BLUE "🚀 Deploying ITDO ERP Monitoring Infrastructure"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_status $RED "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    print_status $RED "❌ helm is not installed or not in PATH"
    exit 1
fi

# Create monitoring namespace
print_status $YELLOW "📁 Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Add Prometheus Helm repository
print_status $YELLOW "📦 Adding Prometheus Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deploy kube-prometheus-stack
print_status $YELLOW "🔧 Deploying kube-prometheus-stack..."
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --values monitoring/kube-prometheus-stack/values.yaml \
    --version 55.5.0 \
    --wait \
    --timeout 10m

# Deploy database exporters
print_status $YELLOW "📊 Deploying database exporters..."
kubectl apply -f monitoring/exporters/postgres-exporter.yaml
kubectl apply -f monitoring/exporters/redis-exporter.yaml

# Create ConfigMap for custom dashboard
print_status $YELLOW "📈 Installing custom dashboards..."
kubectl create configmap itdo-erp-overview-dashboard \
    --from-file=monitoring/dashboards/itdo-erp-overview.json \
    --namespace monitoring \
    --dry-run=client -o yaml | kubectl apply -f -

# Label the ConfigMap for Grafana sidecar
kubectl label configmap itdo-erp-overview-dashboard \
    grafana_dashboard=1 \
    --namespace monitoring

# Create basic auth secret for Prometheus
print_status $YELLOW "🔐 Creating authentication secrets..."
kubectl create secret generic prometheus-basic-auth \
    --from-literal=auth=$(echo -n "admin:admin123!" | base64) \
    --namespace monitoring \
    --dry-run=client -o yaml | kubectl apply -f -

# Wait for deployments to be ready
print_status $YELLOW "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/kube-prometheus-stack-grafana -n monitoring
kubectl wait --for=condition=available --timeout=300s deployment/postgres-exporter -n monitoring
kubectl wait --for=condition=available --timeout=300s deployment/redis-exporter -n monitoring

# Get service information
print_status $GREEN "✅ Monitoring stack deployed successfully!"
print_status $BLUE "📊 Service Information:"

echo "Grafana URL: https://grafana.itdo-erp.com"
echo "  - Username: admin"
echo "  - Password: admin123!"
echo ""
echo "Prometheus URL: https://prometheus.itdo-erp.com"
echo "  - Username: admin" 
echo "  - Password: admin123!"
echo ""
echo "AlertManager URL: https://alertmanager.itdo-erp.com"

# Display some useful monitoring queries
print_status $BLUE "🔍 Useful Monitoring Queries:"
cat << EOF

# API Request Rate
sum(rate(http_requests_total{job="backend-api-metrics"}[5m]))

# API Error Rate  
sum(rate(http_requests_total{job="backend-api-metrics",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="backend-api-metrics"}[5m]))

# API 95th Percentile Latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="backend-api-metrics"}[5m])) by (le))

# Database Connections
pg_stat_activity_count

# Redis Memory Usage
redis_memory_used_bytes / redis_config_maxmemory

EOF

print_status $GREEN "🎉 Monitoring infrastructure deployment completed!"
print_status $YELLOW "💡 Next steps:"
echo "1. Configure your application to expose metrics on /metrics endpoint"
echo "2. Update DNS records to point to the ingress controllers"
echo "3. Configure AlertManager with your notification channels"
echo "4. Set up dashboards in Grafana for your specific metrics"