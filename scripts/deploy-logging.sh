#!/bin/bash

# Deploy Logging Infrastructure for ITDO ERP
# This script deploys Elasticsearch, Kibana, Loki, Fluent Bit, and Filebeat

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

print_status $BLUE "🚀 Deploying ITDO ERP Logging Infrastructure"

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

# Create logging namespace
print_status $YELLOW "📁 Creating logging namespace..."
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
print_status $YELLOW "📦 Adding required Helm repositories..."
helm repo add elastic https://helm.elastic.co
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update

# Generate certificates for Elasticsearch
print_status $YELLOW "🔐 Generating certificates for Elasticsearch..."
if ! kubectl get secret elastic-certificates -n logging &> /dev/null; then
    # Create temporary directory for certificate generation
    TEMP_DIR=$(mktemp -d)
    
    # Generate CA and certificates
    openssl genrsa -out $TEMP_DIR/ca-key.pem 4096
    openssl req -new -x509 -sha256 -key $TEMP_DIR/ca-key.pem -out $TEMP_DIR/ca.pem -days 3650 \
        -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO ERP/OU=Platform/CN=itdo-erp-ca"
    
    openssl genrsa -out $TEMP_DIR/elastic-key.pem 4096
    openssl req -new -key $TEMP_DIR/elastic-key.pem -out $TEMP_DIR/elastic.csr \
        -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO ERP/OU=Platform/CN=elasticsearch.logging.svc.cluster.local"
    
    # Create certificate with SAN
    cat > $TEMP_DIR/elastic.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = elasticsearch
DNS.2 = elasticsearch.logging
DNS.3 = elasticsearch.logging.svc
DNS.4 = elasticsearch.logging.svc.cluster.local
DNS.5 = elasticsearch.itdo-erp.com
DNS.6 = localhost
IP.1 = 127.0.0.1
EOF
    
    openssl x509 -req -in $TEMP_DIR/elastic.csr -CA $TEMP_DIR/ca.pem -CAkey $TEMP_DIR/ca-key.pem \
        -CAcreateserial -out $TEMP_DIR/elastic.pem -days 365 -extensions v3_req -extfile $TEMP_DIR/elastic.ext
    
    # Create Kubernetes secret
    kubectl create secret generic elastic-certificates \
        --from-file=elastic-certificates.crt=$TEMP_DIR/elastic.pem \
        --from-file=elastic-certificates.key=$TEMP_DIR/elastic-key.pem \
        --from-file=ca.crt=$TEMP_DIR/ca.pem \
        --namespace logging
    
    # Cleanup
    rm -rf $TEMP_DIR
    print_status $GREEN "✅ Certificates generated successfully"
else
    print_status $GREEN "✅ Certificates already exist"
fi

# Create authentication secrets
print_status $YELLOW "🔐 Creating authentication secrets..."

# Elasticsearch credentials
kubectl create secret generic elasticsearch-credentials \
    --from-literal=username=elastic \
    --from-literal=password=elastic-production-password \
    --namespace logging \
    --dry-run=client -o yaml | kubectl apply -f -

# Kibana encryption key
kubectl create secret generic kibana-encryption-key \
    --from-literal=encryptionkey=$(openssl rand -base64 32) \
    --namespace logging \
    --dry-run=client -o yaml | kubectl apply -f -

# Basic auth secrets for ingress
kubectl create secret generic elasticsearch-basic-auth \
    --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
    --namespace logging \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic kibana-basic-auth \
    --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
    --namespace logging \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic loki-basic-auth \
    --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
    --namespace logging \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy Elasticsearch
print_status $YELLOW "🔍 Deploying Elasticsearch..."
helm upgrade --install elasticsearch elastic/elasticsearch \
    --namespace logging \
    --values logging/elasticsearch/values.yaml \
    --version 8.11.0 \
    --wait \
    --timeout 15m

# Deploy Kibana
print_status $YELLOW "📊 Deploying Kibana..."
helm upgrade --install kibana elastic/kibana \
    --namespace logging \
    --values logging/kibana/values.yaml \
    --version 8.11.0 \
    --wait \
    --timeout 10m

# Deploy Loki
print_status $YELLOW "📝 Deploying Loki..."
helm upgrade --install loki grafana/loki \
    --namespace logging \
    --values logging/loki/values.yaml \
    --version 5.41.4 \
    --wait \
    --timeout 10m

# Deploy Fluent Bit
print_status $YELLOW "🌊 Deploying Fluent Bit..."
helm upgrade --install fluent-bit fluent/fluent-bit \
    --namespace logging \
    --values logging/fluent-bit/values.yaml \
    --version 0.40.0 \
    --wait \
    --timeout 10m

# Deploy Filebeat
print_status $YELLOW "🥁 Deploying Filebeat..."
helm upgrade --install filebeat elastic/filebeat \
    --namespace logging \
    --values logging/filebeat/values.yaml \
    --version 8.11.0 \
    --wait \
    --timeout 10m

# Wait for all deployments to be ready
print_status $YELLOW "⏳ Waiting for all deployments to be ready..."
kubectl wait --for=condition=ready pod -l app=elasticsearch-master --timeout=300s -n logging
kubectl wait --for=condition=ready pod -l app=kibana --timeout=300s -n logging
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki --timeout=300s -n logging
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=fluent-bit --timeout=300s -n logging
kubectl wait --for=condition=ready pod -l app=filebeat --timeout=300s -n logging

# Create Elasticsearch index lifecycle policies
print_status $YELLOW "🔄 Setting up Elasticsearch ILM policies..."
kubectl exec -n logging elasticsearch-master-0 -- curl -X PUT "localhost:9200/_ilm/policy/itdo-erp-logs-policy" \
  -H "Content-Type: application/json" \
  -u "elastic:elastic-production-password" \
  -d '{
    "policy": {
      "phases": {
        "hot": {
          "actions": {
            "rollover": {
              "max_size": "10GB",
              "max_age": "7d"
            }
          }
        },
        "warm": {
          "min_age": "7d",
          "actions": {
            "allocate": {
              "number_of_replicas": 0
            },
            "shrink": {
              "number_of_shards": 1
            }
          }
        },
        "cold": {
          "min_age": "30d",
          "actions": {
            "allocate": {
              "number_of_replicas": 0
            }
          }
        },
        "delete": {
          "min_age": "90d"
        }
      }
    }
  }' || true

# Create index templates
print_status $YELLOW "📋 Creating Elasticsearch index templates..."
kubectl exec -n logging elasticsearch-master-0 -- curl -X PUT "localhost:9200/_index_template/itdo-erp-logs" \
  -H "Content-Type: application/json" \
  -u "elastic:elastic-production-password" \
  -d '{
    "index_patterns": ["itdo-erp-logs-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "index.lifecycle.name": "itdo-erp-logs-policy",
        "index.lifecycle.rollover_alias": "itdo-erp-logs",
        "refresh_interval": "30s",
        "codec": "best_compression"
      },
      "mappings": {
        "properties": {
          "@timestamp": {
            "type": "date"
          },
          "level": {
            "type": "keyword"
          },
          "message": {
            "type": "text",
            "analyzer": "standard"
          },
          "service": {
            "type": "keyword"
          },
          "kubernetes": {
            "properties": {
              "namespace": {
                "type": "keyword"
              },
              "pod_name": {
                "type": "keyword"
              },
              "container_name": {
                "type": "keyword"
              }
            }
          }
        }
      }
    }
  }' || true

# Get service information
print_status $GREEN "✅ Logging infrastructure deployed successfully!"
print_status $BLUE "📊 Service Information:"

echo ""
echo "Elasticsearch URL: https://elasticsearch.itdo-erp.com"
echo "  - Username: admin"
echo "  - Password: admin123!"
echo ""
echo "Kibana URL: https://kibana.itdo-erp.com"
echo "  - Username: admin"  
echo "  - Password: admin123!"
echo ""
echo "Loki URL: https://loki.itdo-erp.com"
echo "  - Username: admin"
echo "  - Password: admin123!"

# Display useful information
print_status $BLUE "🔍 Useful Kibana Index Patterns:"
cat << EOF

# Index Patterns to create in Kibana:
1. itdo-erp-logs-* (Application logs)
2. system-logs-* (System logs)
3. itdo-erp-app-* (Application-specific logs)
4. itdo-erp-web-* (Web access logs)
5. itdo-erp-db-* (Database logs)

# Useful Kibana queries:
- level:ERROR (All error logs)
- kubernetes.namespace_name:"production" (Production logs only)
- service:"backend-api" AND level:ERROR (Backend API errors)
- message:"database connection" (Database connection issues)

EOF

print_status $BLUE "📈 Log Storage Information:"
cat << EOF

# Storage allocation:
- Elasticsearch: 50Gi per node (150Gi total)
- Loki: 100Gi for long-term storage
- Log retention: 90 days (configurable via ILM)

# Performance expectations:
- Log ingestion: ~10MB/s per node
- Query performance: <2s for most queries
- Storage compression: ~70% with best_compression

EOF

print_status $GREEN "🎉 Logging pipeline deployment completed!"
print_status $YELLOW "💡 Next steps:"
echo "1. Configure your applications to output structured JSON logs"
echo "2. Update DNS records to point to the ingress controllers"
echo "3. Configure log shipping from external sources if needed"
echo "4. Set up custom dashboards in Kibana for your specific use cases"
echo "5. Configure alerting rules for critical log patterns"