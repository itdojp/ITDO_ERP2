#!/bin/bash

# Deploy Distributed Tracing Infrastructure for ITDO ERP
# This script deploys Jaeger, OpenTelemetry Collector, and Tempo

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

print_status $BLUE "🚀 Deploying ITDO ERP Distributed Tracing Infrastructure"

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

# Create tracing namespace
print_status $YELLOW "📁 Creating tracing namespace..."
kubectl create namespace tracing --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
print_status $YELLOW "📦 Adding required Helm repositories..."
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create authentication secrets
print_status $YELLOW "🔐 Creating authentication secrets..."

# Basic auth secret for Jaeger UI
kubectl create secret generic jaeger-basic-auth \
    --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
    --namespace tracing \
    --dry-run=client -o yaml | kubectl apply -f -

# Basic auth secret for Tempo UI
kubectl create secret generic tempo-basic-auth \
    --from-literal=auth=$(echo -n "admin:$(openssl passwd -apr1 admin123!)" | base64 -w 0) \
    --namespace tracing \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy OpenTelemetry Collector (DaemonSet)
print_status $YELLOW "📡 Deploying OpenTelemetry Collector..."
helm upgrade --install otel-collector open-telemetry/opentelemetry-collector \
    --namespace tracing \
    --values tracing/otel-collector/values.yaml \
    --version 0.72.0 \
    --wait \
    --timeout 10m

# Deploy Jaeger
print_status $YELLOW "🔍 Deploying Jaeger..."
helm upgrade --install jaeger jaegertracing/jaeger \
    --namespace tracing \
    --values tracing/jaeger/values.yaml \
    --version 0.71.14 \
    --wait \
    --timeout 15m

# Deploy Tempo (alternative tracing backend)
print_status $YELLOW "⏱️ Deploying Grafana Tempo..."
helm upgrade --install tempo grafana/tempo \
    --namespace tracing \
    --values tracing/tempo/values.yaml \
    --version 1.7.0 \
    --wait \
    --timeout 10m

# Wait for all deployments to be ready
print_status $YELLOW "⏳ Waiting for all deployments to be ready..."

# Wait for OpenTelemetry Collector DaemonSet
kubectl rollout status daemonset/otel-collector -n tracing --timeout=300s

# Wait for Jaeger components
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jaeger --timeout=300s -n tracing

# Wait for Tempo
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=tempo --timeout=300s -n tracing

# Create Elasticsearch index templates for Jaeger traces
print_status $YELLOW "📋 Configuring Elasticsearch for Jaeger traces..."
kubectl exec -n logging elasticsearch-master-0 -- curl -X PUT "localhost:9200/_index_template/jaeger-traces" \
  -H "Content-Type: application/json" \
  -u "elastic:elastic-production-password" \
  -d '{
    "index_patterns": ["jaeger-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "refresh_interval": "10s",
        "codec": "best_compression"
      },
      "mappings": {
        "properties": {
          "timestamp": {
            "type": "date_nanos"
          },
          "traceID": {
            "type": "keyword"
          },
          "spanID": {
            "type": "keyword"
          },
          "operationName": {
            "type": "keyword"
          },
          "duration": {
            "type": "long"
          },
          "tags": {
            "type": "nested",
            "properties": {
              "key": {"type": "keyword"},
              "value": {"type": "keyword"}
            }
          },
          "process": {
            "properties": {
              "serviceName": {
                "type": "keyword"
              },
              "tags": {
                "type": "nested",
                "properties": {
                  "key": {"type": "keyword"},
                  "value": {"type": "keyword"}
                }
              }
            }
          }
        }
      }
    }
  }' || true

# Create service mappings for better trace correlation
print_status $YELLOW "🔗 Creating service mappings..."
kubectl exec -n logging elasticsearch-master-0 -- curl -X PUT "localhost:9200/_index_template/jaeger-service" \
  -H "Content-Type: application/json" \
  -u "elastic:elastic-production-password" \
  -d '{
    "index_patterns": ["jaeger-service-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
      },
      "mappings": {
        "properties": {
          "timestamp": {
            "type": "date"
          },
          "serviceName": {
            "type": "keyword"
          },
          "operationName": {
            "type": "keyword"
          }
        }
      }
    }
  }' || true

# Configure Grafana datasource for Tempo (if Grafana is available)
print_status $YELLOW "📊 Configuring Grafana datasources..."
if kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana &> /dev/null; then
    cat > /tmp/tempo-datasource.json << 'EOF'
{
  "name": "Tempo",
  "type": "tempo",
  "access": "proxy",
  "url": "http://tempo-query-frontend.tracing.svc.cluster.local:3100",
  "basicAuth": false,
  "isDefault": false,
  "jsonData": {
    "tracesToLogs": {
      "datasourceUid": "loki",
      "tags": [
        "job",
        "instance",
        "pod",
        "namespace"
      ],
      "mappedTags": [
        {
          "key": "service.name",
          "value": "service"
        }
      ],
      "mapTagNamesEnabled": false,
      "spanStartTimeShift": "1h",
      "spanEndTimeShift": "1h",
      "filterByTraceID": false,
      "filterBySpanID": false
    },
    "tracesToMetrics": {
      "datasourceUid": "prometheus",
      "tags": [
        {
          "key": "service.name",
          "value": "service"
        }
      ],
      "queries": [
        {
          "name": "Sample query",
          "query": "sum(rate(traces_spanmetrics_latency_bucket{service=\"$service\"}[5m]))"
        }
      ]
    },
    "nodeGraph": {
      "enabled": true
    }
  }
}
EOF

    # Add Tempo datasource to Grafana
    kubectl create configmap tempo-datasource \
        --from-file=/tmp/tempo-datasource.json \
        --namespace monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    kubectl label configmap tempo-datasource \
        grafana_datasource=1 \
        --namespace monitoring
        
    # Cleanup temp file
    rm -f /tmp/tempo-datasource.json
    
    print_status $GREEN "✅ Tempo datasource configured in Grafana"
else
    print_status $YELLOW "⚠️ Grafana not found, skipping datasource configuration"
fi

# Create sample tracing configuration for applications
print_status $YELLOW "📝 Creating application tracing configuration..."
kubectl create configmap app-tracing-config \
    --from-literal=OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.tracing.svc.cluster.local:4317 \
    --from-literal=OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger-collector.tracing.svc.cluster.local:14268/api/traces \
    --from-literal=OTEL_SERVICE_NAME=itdo-erp \
    --from-literal=OTEL_RESOURCE_ATTRIBUTES=service.version=v2.0,environment=production \
    --from-literal=JAEGER_AGENT_HOST=otel-collector.tracing.svc.cluster.local \
    --from-literal=JAEGER_AGENT_PORT=6831 \
    --from-literal=JAEGER_SAMPLER_TYPE=probabilistic \
    --from-literal=JAEGER_SAMPLER_PARAM=0.1 \
    --namespace production \
    --dry-run=client -o yaml | kubectl apply -f -

# Get service information
print_status $GREEN "✅ Distributed tracing infrastructure deployed successfully!"
print_status $BLUE "📊 Service Information:"

echo ""
echo "Jaeger UI: https://jaeger.itdo-erp.com"
echo "  - Username: admin"
echo "  - Password: admin123!"
echo ""
echo "Tempo UI: https://tempo.itdo-erp.com"
echo "  - Username: admin"
echo "  - Password: admin123!"
echo ""
echo "OpenTelemetry Collector Endpoints:"
echo "  - OTLP gRPC: otel-collector.tracing.svc.cluster.local:4317"
echo "  - OTLP HTTP: otel-collector.tracing.svc.cluster.local:4318"
echo "  - Jaeger gRPC: otel-collector.tracing.svc.cluster.local:14250"
echo "  - Jaeger Thrift: otel-collector.tracing.svc.cluster.local:6831"
echo "  - Zipkin: otel-collector.tracing.svc.cluster.local:9411"

# Display integration guide
print_status $BLUE "🔧 Application Integration Guide:"
cat << 'EOF'

# Python FastAPI Integration:
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://otel-collector.tracing.svc.cluster.local:4317",
    insecure=True
)

# Add span processor
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# React Frontend Integration:
npm install @opentelemetry/api @opentelemetry/sdk-web @opentelemetry/auto-instrumentations-web

import { WebSDK } from '@opentelemetry/sdk-web';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-otlp-http';

const sdk = new WebSDK({
  resource: {
    attributes: {
      'service.name': 'itdo-erp-frontend',
      'service.version': '2.0.0',
    },
  },
  traceExporter: new OTLPTraceExporter({
    url: 'https://otel-collector.itdo-erp.com/v1/traces',
  }),
  instrumentations: [getWebAutoInstrumentations()],
});

sdk.start();

EOF

print_status $BLUE "📈 Performance Configuration:"
cat << 'EOF'

# Sampling Configuration:
- Probabilistic sampling: 10% (configurable)
- Tail-based sampling for errors and high latency
- Full sampling for error traces
- Intelligent sampling based on trace characteristics

# Storage Configuration:
- Jaeger: 30-day retention in Elasticsearch
- Tempo: 10-day retention with local storage
- Compressed storage with best_compression codec

# Performance Expectations:
- Trace ingestion: 1000 spans/second per collector
- Query latency: <2 seconds for trace lookup
- Storage overhead: ~5MB per 1000 spans

EOF

print_status $GREEN "🎉 Distributed tracing deployment completed!"
print_status $YELLOW "💡 Next steps:"
echo "1. Instrument your applications with OpenTelemetry SDKs"
echo "2. Configure sampling rates based on your traffic patterns"  
echo "3. Set up custom dashboards in Grafana for trace analysis"
echo "4. Configure alerting for high error rates or latency"
echo "5. Correlate traces with logs and metrics for comprehensive observability"