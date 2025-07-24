# SLO Management Framework for ITDO ERP v2

## 🎯 Overview

This document defines the Service Level Objective (SLO) Management Framework for ITDO ERP, implementing comprehensive observability, reliability measurement, and automated alerting to ensure optimal service performance and user experience.

## 📊 SLO Framework Principles

### Core Concepts
1. **Service Level Indicators (SLIs)**: Quantitative measures of service performance
2. **Service Level Objectives (SLOs)**: Target values for SLIs over a time window
3. **Error Budgets**: Allowable failure rate derived from SLO targets
4. **Burn Rate**: Rate at which error budget is consumed
5. **Alert Fatigue Prevention**: Multi-burn rate alerting strategy

### Business Alignment
- **User Experience Focus**: SLOs based on user-perceived performance
- **Business Impact**: Metrics tied to business outcomes
- **Proactive Management**: Early warning before SLO violations
- **Continuous Improvement**: Data-driven optimization
- **Team Accountability**: Clear ownership and responsibilities

## 🏗️ SLO Architecture

### SLO Management Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    SLO Dashboard                            │
│              (Grafana + Custom UI)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                SLO Analytics Engine                         │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│     │  Error      │ │  Burn Rate  │ │  Forecasting│        │
│     │  Budget     │ │  Analysis   │ │  Engine     │        │
│     └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  SLI Collection Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Prometheus  │ │    Jaeger   │ │  Custom     │           │
│  │   Metrics   │ │   Tracing   │ │  Collectors │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Service Infrastructure                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Frontend   │ │   Backend   │ │  Database   │           │
│  │  Services   │ │   APIs      │ │  Services   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Service Level Indicators (SLIs)

### API Service SLIs
```yaml
# slo/api-slis.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-slis-config
  namespace: monitoring
data:
  slis.yaml: |
    services:
      backend-api:
        availability:
          description: "Percentage of successful HTTP requests"
          sli_specification: |
            sum(rate(http_requests_total{service="backend-api",code!~"5.."}[5m])) /
            sum(rate(http_requests_total{service="backend-api"}[5m]))
          
        latency:
          description: "95th percentile of request duration"
          sli_specification: |
            histogram_quantile(0.95,
              rate(http_request_duration_seconds_bucket{service="backend-api"}[5m])
            )
        
        throughput:
          description: "Requests per second served successfully"
          sli_specification: |
            sum(rate(http_requests_total{service="backend-api",code!~"5.."}[5m]))
        
        quality:
          description: "Percentage of requests completed without errors"
          sli_specification: |
            sum(rate(http_requests_total{service="backend-api",code!~"[45].."}[5m])) /
            sum(rate(http_requests_total{service="backend-api"}[5m]))
        
        saturation:
          description: "Resource utilization percentage"
          sli_specification: |
            max(
              avg(cpu_usage_percent{service="backend-api"}),
              avg(memory_usage_percent{service="backend-api"})
            )
      
      frontend-app:
        availability:
          description: "Percentage of successful page loads"
          sli_specification: |
            sum(rate(frontend_page_loads_total{result="success"}[5m])) /
            sum(rate(frontend_page_loads_total[5m]))
        
        performance:
          description: "95th percentile of page load time"
          sli_specification: |
            histogram_quantile(0.95,
              rate(frontend_page_load_duration_bucket[5m])
            )
        
        interaction:
          description: "95th percentile of user interaction response time"
          sli_specification: |
            histogram_quantile(0.95,
              rate(frontend_interaction_duration_bucket[5m])
            )
      
      database:
        availability:
          description: "Percentage of successful database queries"
          sli_specification: |
            sum(rate(database_queries_total{result="success"}[5m])) /
            sum(rate(database_queries_total[5m]))
        
        latency:
          description: "95th percentile of query duration"
          sli_specification: |
            histogram_quantile(0.95,
              rate(database_query_duration_seconds_bucket[5m])
            )
        
        saturation:
          description: "Database connection pool utilization"
          sli_specification: |
            avg(database_connection_pool_used / database_connection_pool_max)
```

### Custom SLI Collectors
```python
# slo/collectors/sli_collector.py
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from typing import Dict, List, Any
import logging

class SLICollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registry = CollectorRegistry()
        
        # SLI Metrics
        self.availability_sli = Gauge(
            'sli_availability',
            'Service availability SLI',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        self.latency_sli = Gauge(
            'sli_latency_p95',
            '95th percentile latency SLI',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        self.error_rate_sli = Gauge(
            'sli_error_rate',
            'Error rate SLI',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        self.throughput_sli = Gauge(
            'sli_throughput',
            'Throughput SLI (requests per second)',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        # Business Logic SLIs
        self.business_process_success = Gauge(
            'sli_business_process_success',
            'Business process success rate',
            ['process_name', 'service'],
            registry=self.registry
        )
        
        self.data_freshness = Gauge(
            'sli_data_freshness',
            'Data freshness in seconds',
            ['data_source', 'service'],
            registry=self.registry
        )
    
    async def collect_api_slis(self, service_config: Dict[str, Any]):
        """Collect SLIs for API services"""
        try:
            for service_name, endpoints in service_config.items():
                for endpoint_config in endpoints:
                    endpoint = endpoint_config['path']
                    
                    # Collect availability
                    availability = await self.measure_availability(service_name, endpoint)
                    self.availability_sli.labels(service=service_name, endpoint=endpoint).set(availability)
                    
                    # Collect latency
                    latency_p95 = await self.measure_latency_p95(service_name, endpoint)
                    self.latency_sli.labels(service=service_name, endpoint=endpoint).set(latency_p95)
                    
                    # Collect error rate
                    error_rate = await self.measure_error_rate(service_name, endpoint)
                    self.error_rate_sli.labels(service=service_name, endpoint=endpoint).set(error_rate)
                    
                    # Collect throughput
                    throughput = await self.measure_throughput(service_name, endpoint)
                    self.throughput_sli.labels(service=service_name, endpoint=endpoint).set(throughput)
                    
                    self.logger.info(f"Collected SLIs for {service_name}{endpoint}: "
                                   f"availability={availability:.3f}, latency_p95={latency_p95:.3f}ms, "
                                   f"error_rate={error_rate:.3f}, throughput={throughput:.1f}rps")
        
        except Exception as e:
            self.logger.error(f"Error collecting API SLIs: {e}")
    
    async def collect_business_slis(self):
        """Collect business logic SLIs"""
        try:
            # User registration process
            registration_success = await self.measure_business_process(
                'user_registration', 
                'backend-api'
            )
            self.business_process_success.labels(
                process_name='user_registration',
                service='backend-api'
            ).set(registration_success)
            
            # Task creation process
            task_creation_success = await self.measure_business_process(
                'task_creation',
                'backend-api'
            )
            self.business_process_success.labels(
                process_name='task_creation',
                service='backend-api'
            ).set(task_creation_success)
            
            # Data freshness
            user_data_freshness = await self.measure_data_freshness('user_data', 'database')
            self.data_freshness.labels(
                data_source='user_data',
                service='database'
            ).set(user_data_freshness)
            
            organization_data_freshness = await self.measure_data_freshness('organization_data', 'database')
            self.data_freshness.labels(
                data_source='organization_data',
                service='database'
            ).set(organization_data_freshness)
        
        except Exception as e:
            self.logger.error(f"Error collecting business SLIs: {e}")
    
    async def measure_availability(self, service: str, endpoint: str) -> float:
        """Measure service availability"""
        try:
            # Query Prometheus for success rate
            query = f'''
                sum(rate(http_requests_total{{service="{service}",endpoint="{endpoint}",code!~"5.."}}[5m])) /
                sum(rate(http_requests_total{{service="{service}",endpoint="{endpoint}"}}[5m]))
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring availability for {service}{endpoint}: {e}")
            return 0.0
    
    async def measure_latency_p95(self, service: str, endpoint: str) -> float:
        """Measure 95th percentile latency"""
        try:
            query = f'''
                histogram_quantile(0.95,
                    rate(http_request_duration_seconds_bucket{{service="{service}",endpoint="{endpoint}"}}[5m])
                ) * 1000
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring latency for {service}{endpoint}: {e}")
            return 0.0
    
    async def measure_error_rate(self, service: str, endpoint: str) -> float:
        """Measure error rate"""
        try:
            query = f'''
                sum(rate(http_requests_total{{service="{service}",endpoint="{endpoint}",code=~"[45].."}}[5m])) /
                sum(rate(http_requests_total{{service="{service}",endpoint="{endpoint}"}}[5m]))
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring error rate for {service}{endpoint}: {e}")
            return 0.0
    
    async def measure_throughput(self, service: str, endpoint: str) -> float:
        """Measure throughput (requests per second)"""
        try:
            query = f'''
                sum(rate(http_requests_total{{service="{service}",endpoint="{endpoint}",code!~"5.."}}[5m]))
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring throughput for {service}{endpoint}: {e}")
            return 0.0
    
    async def measure_business_process(self, process_name: str, service: str) -> float:
        """Measure business process success rate"""
        try:
            # This would be customized based on actual business metrics
            query = f'''
                sum(rate(business_process_total{{process="{process_name}",service="{service}",result="success"}}[5m])) /
                sum(rate(business_process_total{{process="{process_name}",service="{service}"}}[5m]))
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring business process {process_name}: {e}")
            return 0.0
    
    async def measure_data_freshness(self, data_source: str, service: str) -> float:
        """Measure data freshness in seconds"""
        try:
            query = f'''
                time() - max(data_last_updated_timestamp{{source="{data_source}",service="{service}"}})
            '''
            
            result = await self.query_prometheus(query)
            return float(result[0]['value'][1]) if result else 0.0
        
        except Exception as e:
            self.logger.error(f"Error measuring data freshness for {data_source}: {e}")
            return 0.0
    
    async def query_prometheus(self, query: str) -> List[Dict]:
        """Query Prometheus API"""
        try:
            prometheus_url = "http://prometheus-server.monitoring.svc.cluster.local:80"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{prometheus_url}/api/v1/query",
                    params={'query': query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('result', [])
                    else:
                        self.logger.warning(f"Prometheus query failed: {response.status}")
                        return []
        
        except Exception as e:
            self.logger.error(f"Error querying Prometheus: {e}")
            return []
    
    async def push_metrics(self):
        """Push SLI metrics to Prometheus"""
        try:
            pushgateway_url = "http://prometheus-pushgateway.monitoring.svc.cluster.local:9091"
            push_to_gateway(
                pushgateway_url,
                job='sli-collector',
                registry=self.registry
            )
            self.logger.info("SLI metrics pushed successfully")
        
        except Exception as e:
            self.logger.error(f"Error pushing SLI metrics: {e}")

# Service configuration
SERVICE_CONFIG = {
    'backend-api': [
        {'path': '/api/v1/health'},
        {'path': '/api/v1/users'},
        {'path': '/api/v1/organizations'},
        {'path': '/api/v1/tasks'},
        {'path': '/api/v1/departments'}
    ],
    'frontend-app': [
        {'path': '/'},
        {'path': '/dashboard'},
        {'path': '/users'},
        {'path': '/organizations'}
    ]
}

async def main():
    logging.basicConfig(level=logging.INFO)
    collector = SLICollector()
    
    while True:
        try:
            await collector.collect_api_slis(SERVICE_CONFIG)
            await collector.collect_business_slis()
            await collector.push_metrics()
            
            # Collect every 30 seconds
            await asyncio.sleep(30)
        
        except Exception as e:
            logging.error(f"Error in SLI collection loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 Service Level Objectives (SLOs)

### SLO Definitions
```yaml
# slo/slo-definitions.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: slo-definitions
  namespace: monitoring
data:
  slos.yaml: |
    slos:
      # API Service SLOs
      backend-api-availability:
        service: "backend-api"
        sli_name: "availability"
        objective: 99.9  # 99.9% availability
        time_window: "30d"
        error_budget: 0.1  # 0.1% error budget (43.2 minutes per month)
        description: "Backend API should be available 99.9% of the time"
        
      backend-api-latency:
        service: "backend-api"
        sli_name: "latency_p95"
        objective: 200  # 95th percentile under 200ms
        time_window: "30d"
        error_budget: 20  # 20% of requests can exceed 200ms
        description: "95% of backend API requests should complete within 200ms"
        
      backend-api-quality:
        service: "backend-api"
        sli_name: "error_rate"
        objective: 0.01  # Less than 1% error rate
        time_window: "30d"
        error_budget: 99  # Up to 1% error rate allowed
        description: "Backend API error rate should be less than 1%"
      
      # Frontend Service SLOs
      frontend-availability:
        service: "frontend-app"
        sli_name: "availability"
        objective: 99.5  # 99.5% availability
        time_window: "30d"
        error_budget: 0.5  # 0.5% error budget
        description: "Frontend should be available 99.5% of the time"
        
      frontend-performance:
        service: "frontend-app"
        sli_name: "page_load_time_p95"
        objective: 2000  # 95th percentile under 2 seconds
        time_window: "30d"
        error_budget: 20  # 20% of page loads can exceed 2 seconds
        description: "95% of page loads should complete within 2 seconds"
      
      # Database Service SLOs
      database-availability:
        service: "database"
        sli_name: "availability"
        objective: 99.95  # 99.95% availability
        time_window: "30d"
        error_budget: 0.05  # 0.05% error budget
        description: "Database should be available 99.95% of the time"
        
      database-latency:
        service: "database"
        sli_name: "query_latency_p95"
        objective: 100  # 95th percentile under 100ms
        time_window: "30d"
        error_budget: 15  # 15% of queries can exceed 100ms
        description: "95% of database queries should complete within 100ms"
      
      # Business Process SLOs
      user-registration-success:
        service: "backend-api"
        sli_name: "business_process_success"
        process: "user_registration"
        objective: 99.0  # 99% success rate
        time_window: "7d"
        error_budget: 1.0  # 1% failure rate allowed
        description: "User registration should succeed 99% of the time"
        
      task-creation-success:
        service: "backend-api"
        sli_name: "business_process_success"
        process: "task_creation"
        objective: 99.5  # 99.5% success rate
        time_window: "7d"
        error_budget: 0.5  # 0.5% failure rate allowed
        description: "Task creation should succeed 99.5% of the time"
      
      # Data Freshness SLOs
      user-data-freshness:
        service: "database"
        sli_name: "data_freshness"
        data_source: "user_data"
        objective: 300  # Data should be no older than 5 minutes
        time_window: "24h"
        error_budget: 20  # 20% of the time data can be stale
        description: "User data should be refreshed within 5 minutes"
```

## 📊 Error Budget Management

### Error Budget Calculator
```python
# slo/error_budget.py
import asyncio
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import aiohttp
import logging

@dataclass
class SLOConfig:
    name: str
    service: str
    sli_name: str
    objective: float
    time_window_days: int
    error_budget_percent: float
    description: str

@dataclass
class ErrorBudgetStatus:
    slo_name: str
    current_sli_value: float
    objective: float
    error_budget_total: float
    error_budget_consumed: float
    error_budget_remaining: float
    burn_rate_1h: float
    burn_rate_6h: float
    burn_rate_24h: float
    status: str  # 'healthy', 'warning', 'critical', 'exhausted'
    time_to_exhaustion: Optional[str]

class ErrorBudgetManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.slo_configs = []
        self.load_slo_configs()
    
    def load_slo_configs(self):
        """Load SLO configurations"""
        # This would typically load from ConfigMap or database
        self.slo_configs = [
            SLOConfig(
                name="backend-api-availability",
                service="backend-api",
                sli_name="availability",
                objective=99.9,
                time_window_days=30,
                error_budget_percent=0.1,
                description="Backend API availability SLO"
            ),
            SLOConfig(
                name="backend-api-latency",
                service="backend-api",
                sli_name="latency_p95",
                objective=200.0,
                time_window_days=30,
                error_budget_percent=20.0,
                description="Backend API latency SLO"
            ),
            SLOConfig(
                name="frontend-availability",
                service="frontend-app",
                sli_name="availability",
                objective=99.5,
                time_window_days=30,
                error_budget_percent=0.5,
                description="Frontend availability SLO"
            )
        ]
    
    async def calculate_error_budget_status(self, slo_config: SLOConfig) -> ErrorBudgetStatus:
        """Calculate current error budget status"""
        try:
            # Get current SLI value
            current_sli = await self.get_current_sli_value(slo_config)
            
            # Calculate error budget metrics
            if slo_config.sli_name in ['availability', 'quality']:
                # For availability/quality SLOs (higher is better)
                error_budget_total = 100.0 - slo_config.objective
                error_budget_consumed = max(0, slo_config.objective - current_sli)
                error_budget_remaining = error_budget_total - error_budget_consumed
            else:
                # For latency SLOs (lower is better)
                if current_sli <= slo_config.objective:
                    error_budget_consumed = 0
                    error_budget_remaining = slo_config.error_budget_percent
                else:
                    excess_latency = (current_sli - slo_config.objective) / slo_config.objective
                    error_budget_consumed = min(slo_config.error_budget_percent, excess_latency * 100)
                    error_budget_remaining = slo_config.error_budget_percent - error_budget_consumed
                error_budget_total = slo_config.error_budget_percent
            
            # Calculate burn rates
            burn_rate_1h = await self.calculate_burn_rate(slo_config, "1h")
            burn_rate_6h = await self.calculate_burn_rate(slo_config, "6h")
            burn_rate_24h = await self.calculate_burn_rate(slo_config, "24h")
            
            # Determine status
            status = self.determine_status(
                error_budget_remaining, 
                error_budget_total, 
                burn_rate_1h, 
                burn_rate_6h
            )
            
            # Calculate time to exhaustion
            time_to_exhaustion = self.calculate_time_to_exhaustion(
                error_budget_remaining, 
                burn_rate_1h
            )
            
            return ErrorBudgetStatus(
                slo_name=slo_config.name,
                current_sli_value=current_sli,
                objective=slo_config.objective,
                error_budget_total=error_budget_total,
                error_budget_consumed=error_budget_consumed,
                error_budget_remaining=error_budget_remaining,
                burn_rate_1h=burn_rate_1h,
                burn_rate_6h=burn_rate_6h,
                burn_rate_24h=burn_rate_24h,
                status=status,
                time_to_exhaustion=time_to_exhaustion
            )
        
        except Exception as e:
            self.logger.error(f"Error calculating error budget for {slo_config.name}: {e}")
            return ErrorBudgetStatus(
                slo_name=slo_config.name,
                current_sli_value=0.0,
                objective=slo_config.objective,
                error_budget_total=0.0,
                error_budget_consumed=0.0,
                error_budget_remaining=0.0,
                burn_rate_1h=0.0,
                burn_rate_6h=0.0,
                burn_rate_24h=0.0,
                status="unknown",
                time_to_exhaustion=None
            )
    
    async def get_current_sli_value(self, slo_config: SLOConfig) -> float:
        """Get current SLI value from Prometheus"""
        try:
            if slo_config.sli_name == "availability":
                query = f'''
                    avg_over_time(sli_availability{{service="{slo_config.service}"}}[{slo_config.time_window_days}d])
                '''
            elif slo_config.sli_name == "latency_p95":
                query = f'''
                    avg_over_time(sli_latency_p95{{service="{slo_config.service}"}}[{slo_config.time_window_days}d])
                '''
            elif slo_config.sli_name == "error_rate":
                query = f'''
                    avg_over_time(sli_error_rate{{service="{slo_config.service}"}}[{slo_config.time_window_days}d])
                '''
            else:
                query = f'''
                    avg_over_time(sli_{slo_config.sli_name}{{service="{slo_config.service}"}}[{slo_config.time_window_days}d])
                '''
            
            result = await self.query_prometheus(query)
            if result and len(result) > 0:
                return float(result[0]['value'][1])
            else:
                self.logger.warning(f"No SLI data found for {slo_config.name}")
                return 0.0
        
        except Exception as e:
            self.logger.error(f"Error getting SLI value for {slo_config.name}: {e}")
            return 0.0
    
    async def calculate_burn_rate(self, slo_config: SLOConfig, time_window: str) -> float:
        """Calculate error budget burn rate for given time window"""
        try:
            if slo_config.sli_name == "availability":
                # For availability, burn rate is the rate of SLO violations
                query = f'''
                    rate(sli_availability_violations_total{{service="{slo_config.service}"}}[{time_window}])
                '''
            elif slo_config.sli_name == "latency_p95":
                # For latency, burn rate is the rate of SLO violations
                query = f'''
                    rate(sli_latency_violations_total{{service="{slo_config.service}"}}[{time_window}])
                '''
            else:
                # Generic violation rate
                query = f'''
                    rate(sli_violations_total{{service="{slo_config.service}",sli="{slo_config.sli_name}"}}[{time_window}])
                '''
            
            result = await self.query_prometheus(query)
            if result and len(result) > 0:
                return float(result[0]['value'][1])
            else:
                return 0.0
        
        except Exception as e:
            self.logger.error(f"Error calculating burn rate for {slo_config.name}: {e}")
            return 0.0
    
    def determine_status(self, remaining: float, total: float, burn_rate_1h: float, burn_rate_6h: float) -> str:
        """Determine error budget status"""
        remaining_percent = (remaining / total) * 100 if total > 0 else 100
        
        if remaining_percent <= 0:
            return "exhausted"
        elif remaining_percent <= 10 or burn_rate_1h > 0.1:
            return "critical"
        elif remaining_percent <= 25 or burn_rate_6h > 0.05:
            return "warning"
        else:
            return "healthy"
    
    def calculate_time_to_exhaustion(self, remaining: float, burn_rate: float) -> Optional[str]:
        """Calculate time until error budget exhaustion"""
        if burn_rate <= 0:
            return None
        
        hours_to_exhaustion = remaining / burn_rate
        
        if hours_to_exhaustion < 1:
            return f"{int(hours_to_exhaustion * 60)} minutes"
        elif hours_to_exhaustion < 24:
            return f"{int(hours_to_exhaustion)} hours"
        else:
            return f"{int(hours_to_exhaustion / 24)} days"
    
    async def query_prometheus(self, query: str) -> List[Dict]:
        """Query Prometheus API"""
        try:
            prometheus_url = "http://prometheus-server.monitoring.svc.cluster.local:80"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{prometheus_url}/api/v1/query",
                    params={'query': query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('result', [])
                    else:
                        return []
        
        except Exception as e:
            self.logger.error(f"Error querying Prometheus: {e}")
            return []
    
    async def get_all_error_budget_status(self) -> List[ErrorBudgetStatus]:
        """Get error budget status for all SLOs"""
        statuses = []
        
        for slo_config in self.slo_configs:
            status = await self.calculate_error_budget_status(slo_config)
            statuses.append(status)
        
        return statuses
    
    async def generate_error_budget_report(self) -> Dict:
        """Generate comprehensive error budget report"""
        try:
            statuses = await self.get_all_error_budget_status()
            
            # Categorize statuses
            healthy = [s for s in statuses if s.status == "healthy"]
            warning = [s for s in statuses if s.status == "warning"]
            critical = [s for s in statuses if s.status == "critical"]
            exhausted = [s for s in statuses if s.status == "exhausted"]
            
            # Calculate overall health score
            if len(statuses) > 0:
                health_score = (len(healthy) / len(statuses)) * 100
            else:
                health_score = 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_health_score": health_score,
                "summary": {
                    "total_slos": len(statuses),
                    "healthy": len(healthy),
                    "warning": len(warning),
                    "critical": len(critical),
                    "exhausted": len(exhausted)
                },
                "slo_statuses": [
                    {
                        "name": s.slo_name,
                        "current_sli": s.current_sli_value,
                        "objective": s.objective,
                        "error_budget_remaining": s.error_budget_remaining,
                        "burn_rate_1h": s.burn_rate_1h,
                        "status": s.status,
                        "time_to_exhaustion": s.time_to_exhaustion
                    } for s in statuses
                ],
                "alerts": self.generate_alerts(statuses)
            }
        
        except Exception as e:
            self.logger.error(f"Error generating error budget report: {e}")
            return {"error": str(e)}
    
    def generate_alerts(self, statuses: List[ErrorBudgetStatus]) -> List[Dict]:
        """Generate alerts based on error budget status"""
        alerts = []
        
        for status in statuses:
            if status.status == "exhausted":
                alerts.append({
                    "severity": "critical",
                    "slo": status.slo_name,
                    "message": f"Error budget exhausted for {status.slo_name}",
                    "action": "Immediate attention required"
                })
            elif status.status == "critical":
                alerts.append({
                    "severity": "warning",
                    "slo": status.slo_name,
                    "message": f"Error budget critically low for {status.slo_name}",
                    "action": f"Estimated exhaustion in {status.time_to_exhaustion}"
                })
            elif status.burn_rate_1h > 0.1:
                alerts.append({
                    "severity": "warning",
                    "slo": status.slo_name,
                    "message": f"High burn rate detected for {status.slo_name}",
                    "action": "Monitor closely for continued degradation"
                })
        
        return alerts

# Usage example
async def main():
    manager = ErrorBudgetManager()
    report = await manager.generate_error_budget_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

## 🚨 Multi-Burn Rate Alerting

### Alerting Rules
```yaml
# slo/alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: slo-alerting-rules
  namespace: monitoring
spec:
  groups:
  - name: slo.error_budget
    interval: 30s
    rules:
    # Fast burn rate alerts (2% budget consumed in 1 hour)
    - alert: ErrorBudgetBurnRateTooHigh
      expr: |
        (
          slo_error_budget_consumed_rate_1h > 0.02
        )
      for: 2m
      labels:
        severity: critical
        category: slo
      annotations:
        summary: "High error budget burn rate for {{ $labels.slo_name }}"
        description: |
          SLO {{ $labels.slo_name }} is consuming error budget at {{ $value | humanizePercentage }} per hour.
          At this rate, the entire error budget will be exhausted in {{ $labels.time_to_exhaustion }}.
        runbook_url: "https://runbooks.company.com/slo-error-budget-burn-rate"
    
    # Medium burn rate alerts (5% budget consumed in 6 hours)
    - alert: ErrorBudgetBurnRateHigh
      expr: |
        (
          slo_error_budget_consumed_rate_6h > 0.05
        )
      for: 15m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "Elevated error budget burn rate for {{ $labels.slo_name }}"
        description: |
          SLO {{ $labels.slo_name }} is consuming error budget at an elevated rate.
          Current 6-hour burn rate: {{ $value | humanizePercentage }}.
        runbook_url: "https://runbooks.company.com/slo-error-budget-burn-rate"
    
    # Error budget exhaustion alerts
    - alert: ErrorBudgetExhausted
      expr: |
        slo_error_budget_remaining <= 0
      for: 0m
      labels:
        severity: critical
        category: slo
      annotations:
        summary: "Error budget exhausted for {{ $labels.slo_name }}"
        description: |
          SLO {{ $labels.slo_name }} has exhausted its error budget.
          Current SLI value: {{ $labels.current_sli_value }}
          SLO objective: {{ $labels.objective }}
        runbook_url: "https://runbooks.company.com/slo-error-budget-exhausted"
    
    # Error budget low alerts (25% remaining)
    - alert: ErrorBudgetLow
      expr: |
        (slo_error_budget_remaining / slo_error_budget_total) < 0.25
      for: 5m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "Low error budget for {{ $labels.slo_name }}"
        description: |
          SLO {{ $labels.slo_name }} has less than 25% error budget remaining.
          Remaining: {{ $value | humanizePercentage }}
        runbook_url: "https://runbooks.company.com/slo-error-budget-low"
    
    # SLI data staleness
    - alert: SLIDataStale
      expr: |
        time() - sli_last_update_timestamp > 300
      for: 5m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "SLI data is stale for {{ $labels.service }}"
        description: |
          SLI data for {{ $labels.service }} hasn't been updated in {{ $value | humanizeDuration }}.
          This may indicate an issue with data collection.
        runbook_url: "https://runbooks.company.com/sli-data-stale"

  - name: slo.sli_violations
    interval: 30s
    rules:
    # Availability SLO violations
    - alert: AvailabilitySLOViolation
      expr: |
        sli_availability < bool(slo_availability_objective)
      for: 5m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "Availability SLO violation for {{ $labels.service }}"
        description: |
          Service {{ $labels.service }} availability is {{ $value | humanizePercentage }}, 
          below the SLO objective of {{ $labels.objective | humanizePercentage }}.
        runbook_url: "https://runbooks.company.com/availability-slo-violation"
    
    # Latency SLO violations
    - alert: LatencySLOViolation
      expr: |
        sli_latency_p95 > slo_latency_objective
      for: 5m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "Latency SLO violation for {{ $labels.service }}"
        description: |
          Service {{ $labels.service }} 95th percentile latency is {{ $value }}ms, 
          above the SLO objective of {{ $labels.objective }}ms.
        runbook_url: "https://runbooks.company.com/latency-slo-violation"
    
    # Error rate SLO violations
    - alert: ErrorRateSLOViolation
      expr: |
        sli_error_rate > slo_error_rate_objective
      for: 5m
      labels:
        severity: warning
        category: slo
      annotations:
        summary: "Error rate SLO violation for {{ $labels.service }}"
        description: |
          Service {{ $labels.service }} error rate is {{ $value | humanizePercentage }}, 
          above the SLO objective of {{ $labels.objective | humanizePercentage }}.
        runbook_url: "https://runbooks.company.com/error-rate-slo-violation"
```

## 📊 SLO Dashboard and Reporting

### Grafana SLO Dashboard
```json
{
  "dashboard": {
    "id": null,
    "title": "ITDO ERP SLO Dashboard",
    "tags": ["slo", "reliability", "error-budget"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Overall SLO Health Score",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(slo_health_score)",
            "legendFormat": "Health Score"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 70},
                {"color": "green", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Error Budget Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "count by (status) (slo_error_budget_status)",
            "legendFormat": "{{status}}"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Budget Burn Rate (1h)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "slo_error_budget_burn_rate_1h",
            "legendFormat": "{{slo_name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit"
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "SLI vs SLO Objectives",
        "type": "table",
        "targets": [
          {
            "expr": "sli_current_value",
            "format": "table"
          },
          {
            "expr": "slo_objective",
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "merge",
            "options": {}
          },
          {
            "id": "organize",
            "options": {
              "columns": [
                {"text": "Service", "value": "service"},
                {"text": "SLI", "value": "sli_name"},
                {"text": "Current", "value": "Value #A"},
                {"text": "Objective", "value": "Value #B"},
                {"text": "Status", "value": "status"}
              ]
            }
          }
        ],
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 5,
        "title": "Error Budget Remaining",
        "type": "bargauge",
        "targets": [
          {
            "expr": "slo_error_budget_remaining_percent",
            "legendFormat": "{{slo_name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 25},
                {"color": "green", "value": 50}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20}
      },
      {
        "id": 6,
        "title": "SLO Violations (24h)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "increase(slo_violations_total[24h])",
            "legendFormat": "{{slo_name}} violations"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 20}
      }
    ],
    "time": {
      "from": "now-7d",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **SLI Collection Setup**
   - Deploy SLI collector services
   - Configure Prometheus metrics
   - Setup basic SLI dashboards
   - Implement data quality monitoring

2. **SLO Definition**
   - Define initial SLOs for critical services
   - Configure SLO storage and tracking
   - Setup basic error budget calculation
   - Create SLO documentation

### Phase 2: Alerting and Automation (Week 3-4)
1. **Multi-Burn Rate Alerting**
   - Implement multi-window alerting
   - Configure alert routing and escalation
   - Setup runbooks and documentation
   - Test alert responsiveness

2. **Error Budget Management**
   - Deploy error budget tracking
   - Implement automated reporting
   - Configure budget consumption alerts
   - Setup trend analysis

### Phase 3: Advanced Analytics (Week 5-6)
1. **SLO Analytics Platform**
   - Deploy comprehensive dashboard
   - Implement trend analysis
   - Setup capacity planning integration
   - Configure business impact correlation

2. **Automated Optimization**
   - Implement SLO-driven scaling
   - Configure quality gates
   - Setup performance optimization
   - Implement cost optimization integration

### Phase 4: Organization Integration (Week 7-8)
1. **Team Integration**
   - Setup team-specific dashboards
   - Implement SLO ownership model
   - Configure review processes
   - Setup training materials

2. **Business Alignment**
   - Implement business impact tracking
   - Configure customer satisfaction correlation
   - Setup executive reporting
   - Implement continuous improvement process

## ✅ Success Metrics

### SLO Coverage
- **Service Coverage**: 100% of critical services have SLOs
- **SLI Quality**: 95% data availability for all SLIs
- **Alert Accuracy**: <5% false positive rate
- **Response Time**: <15 minutes to acknowledge SLO violations

### Error Budget Management
- **Budget Utilization**: Healthy consumption across all services
- **Burn Rate Detection**: 100% detection of fast burn rates
- **Recovery Time**: <2 hours to restore SLO compliance
- **Forecasting Accuracy**: Within 10% of actual consumption

### Team Adoption
- **Dashboard Usage**: 90% of engineering teams use SLO dashboards
- **SLO Reviews**: Monthly SLO review meetings for all services
- **Documentation**: 100% of SLOs have runbooks
- **Training**: 100% of oncall engineers trained on SLO response

---

**Document Status**: Design Phase Complete  
**Next Phase**: Cost Optimization Analysis  
**Implementation Risk**: LOW (Design Only)  
**Production Impact**: NONE