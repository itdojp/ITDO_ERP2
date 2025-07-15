# Health Check System - LEVEL 1 ESCALATION

## Overview

The ITDO ERP health check system provides comprehensive monitoring and diagnostics for the system, specifically designed to handle **LEVEL 1 ESCALATION** scenarios where agent health monitoring is critical.

## Features

### 1. Comprehensive Health Endpoints

- **`/api/v1/health/`** - Complete system health check
- **`/api/v1/health/live`** - Kubernetes liveness probe
- **`/api/v1/health/ready`** - Kubernetes readiness probe  
- **`/api/v1/health/database`** - Database connectivity and performance
- **`/api/v1/health/system`** - System resources (disk, memory, CPU)
- **`/api/v1/health/startup`** - Application startup component checks
- **`/api/v1/health/agent`** - **Agent health for LEVEL 1 ESCALATION**
- **`/api/v1/health/metrics-endpoint`** - Metrics collection health

### 2. Agent Health Check (LEVEL 1 ESCALATION)

The `/api/v1/health/agent` endpoint is specifically designed for monitoring agent performance and escalation:

```json
{
  "status": "healthy|degraded|critical",
  "agent_response_time_ms": 250.5,
  "system_resources": {
    "memory_usage_percent": 75.2,
    "cpu_usage_percent": 45.8,
    "memory_available_gb": 8.5
  },
  "performance_criteria": {
    "response_time_ok": true,
    "memory_ok": true,
    "cpu_ok": true
  },
  "overall_agent_health": true,
  "timestamp": "2025-07-15T12:00:00Z",
  "escalation_level": "NORMAL|LEVEL_1"
}
```

#### Escalation Criteria

Agent health escalates to **LEVEL_1** when:
- Response time > 1.0 seconds
- Memory usage > 85%
- CPU usage > 85%

### 3. Monitoring Integration

The system integrates with:
- **Prometheus** metrics collection (`/metrics`)
- **OpenTelemetry** distributed tracing
- **Structured logging** with contextual information
- **Real-time performance monitoring**

### 4. Kubernetes Integration

Health check endpoints support Kubernetes deployment:

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Health API    │    │  Monitoring      │    │  Health Checker │
│   Endpoints     │───▶│  Middleware      │───▶│  Registry       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   Structured     │    │   System        │
│   Metrics       │    │   Logging        │    │   Resources     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

1. **HealthChecker Class**
   - Registers and runs health checks
   - Caches results with configurable intervals
   - Supports both sync and async check functions

2. **MonitoringMiddleware**
   - Tracks request metrics
   - Provides structured logging
   - Collects performance data

3. **Health API Endpoints**
   - RESTful health check endpoints
   - Standardized response formats
   - Error handling and diagnostics

## Usage Examples

### Basic Health Check
```bash
curl http://localhost:8000/api/v1/health/
```

### Agent Health Monitoring
```bash
curl http://localhost:8000/api/v1/health/agent
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

### System Resources
```bash
curl http://localhost:8000/api/v1/health/system
```

## Testing

Comprehensive test suite included:

```bash
# Run health check tests
uv run pytest tests/test_health_check.py -v

# Test specific endpoints
uv run pytest tests/test_health_check.py::test_agent_health -v
uv run pytest tests/test_health_check.py::test_comprehensive_health_check -v
```

## Integration with Existing Infrastructure

The health check system integrates seamlessly with:

- **Phase 4/5 Implementation Specs** - Performance monitoring
- **API Design Standards** - Consistent response formats
- **Security Framework** - Proper authentication and authorization
- **Monitoring Stack** - Prometheus, Grafana, and alerting

## Alerting and Escalation

### Alert Rules (Prometheus)

```yaml
- alert: AgentHealthCritical
  expr: agent_health_status == 0
  for: 1m
  labels:
    severity: critical
    escalation_level: "LEVEL_1"
  annotations:
    summary: "Agent health check failed - LEVEL 1 ESCALATION"
    description: "Agent health check has been failing for more than 1 minute"

- alert: SystemResourcesHigh
  expr: system_memory_usage_percent > 85 or system_cpu_usage_percent > 85
  for: 5m
  labels:
    severity: warning
    escalation_level: "LEVEL_1"
  annotations:
    summary: "High system resource usage detected"
```

## Benefits

1. **Proactive Monitoring** - Early detection of issues
2. **Automated Escalation** - LEVEL 1 escalation for critical scenarios
3. **Comprehensive Coverage** - All system components monitored
4. **Kubernetes Ready** - Native support for K8s deployments
5. **Performance Tracking** - Detailed metrics and tracing
6. **Developer Friendly** - Clear APIs and comprehensive testing

## Future Enhancements

1. **Machine Learning** - Anomaly detection for predictive health monitoring
2. **Advanced Alerting** - Integration with PagerDuty, Slack, etc.
3. **Custom Health Checks** - Plugin architecture for domain-specific checks
4. **Dashboard Integration** - Grafana dashboards for health visualization
5. **Multi-tenant Health** - Organization-specific health monitoring

## Conclusion

The health check system provides enterprise-grade monitoring capabilities with specific support for LEVEL 1 ESCALATION scenarios. It ensures system reliability, provides comprehensive diagnostics, and integrates seamlessly with the existing ITDO ERP infrastructure.