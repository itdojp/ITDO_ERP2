#!/usr/bin/env python3
"""
CC03 v41.0 Advanced Monitoring Automation System
Comprehensive infrastructure monitoring, alerting, and self-healing capabilities
"""

import asyncio
import json
import logging
import time
import aiohttp
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
import signal
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_v41.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    duration_minutes: int = 2
    enabled: bool = True

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    query: str
    severity: str  # warning, critical
    duration: str
    description: str
    enabled: bool = True

@dataclass
class SystemAlert:
    """System alert data structure"""
    alert_id: str
    name: str
    severity: str
    message: str
    timestamp: datetime
    metrics: Dict[str, float]
    resolved: bool = False
    auto_healing_attempted: bool = False

@dataclass
class MonitoringMetrics:
    """System monitoring metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    service_status: Dict[str, bool]
    response_times: Dict[str, float]
    error_rates: Dict[str, float]
    database_connections: int
    queue_sizes: Dict[str, int]

class PrometheusClient:
    """Prometheus client for metrics collection"""
    
    def __init__(self, prometheus_url: str):
        self.base_url = prometheus_url.rstrip('/')
        self.session = requests.Session()
        
    def query(self, query: str) -> Dict[str, Any]:
        """Execute Prometheus query"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/query",
                params={'query': query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return {'status': 'error', 'data': {'result': []}}
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = '1m') -> Dict[str, Any]:
        """Execute Prometheus range query"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start.timestamp(),
                    'end': end.timestamp(),
                    'step': step
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus range query failed: {e}")
            return {'status': 'error', 'data': {'result': []}}

class AlertManager:
    """Advanced alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.alert_history: List[SystemAlert] = []
        self.notification_channels = self._setup_notification_channels()
        self.auto_healing_enabled = config.get('auto_healing_enabled', True)
        
    def _setup_notification_channels(self) -> Dict[str, Any]:
        """Setup notification channels"""
        channels = {}
        
        # Email configuration
        if 'email' in self.config:
            channels['email'] = {
                'smtp_server': self.config['email'].get('smtp_server', 'localhost'),
                'smtp_port': self.config['email'].get('smtp_port', 587),
                'username': self.config['email'].get('username', ''),
                'password': self.config['email'].get('password', ''),
                'from_address': self.config['email'].get('from_address', 'alerts@itdo-erp.com'),
                'to_addresses': self.config['email'].get('to_addresses', [])
            }
        
        # Slack configuration
        if 'slack' in self.config:
            channels['slack'] = {
                'webhook_url': self.config['slack'].get('webhook_url', ''),
                'channel': self.config['slack'].get('channel', '#alerts')
            }
        
        return channels
    
    async def process_alert(self, alert: SystemAlert) -> None:
        """Process incoming alert"""
        logger.info(f"Processing alert: {alert.name} - {alert.severity}")
        
        # Check if alert already exists
        if alert.alert_id in self.active_alerts:
            if alert.resolved:
                await self._resolve_alert(alert.alert_id)
            else:
                self.active_alerts[alert.alert_id] = alert
        else:
            if not alert.resolved:
                self.active_alerts[alert.alert_id] = alert
                await self._send_notifications(alert)
                
                # Attempt auto-healing for critical alerts
                if alert.severity == 'critical' and self.auto_healing_enabled:
                    await self._attempt_auto_healing(alert)
        
        # Add to history
        self.alert_history.append(alert)
        
        # Cleanup old history (keep last 1000 alerts)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    async def _resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            
            # Send resolution notification
            alert.message = f"RESOLVED: {alert.message}"
            await self._send_notifications(alert)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert.name}")
    
    async def _send_notifications(self, alert: SystemAlert) -> None:
        """Send alert notifications"""
        try:
            # Send email notification
            if 'email' in self.notification_channels:
                await self._send_email_notification(alert)
            
            # Send Slack notification
            if 'slack' in self.notification_channels:
                await self._send_slack_notification(alert)
                
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    async def _send_email_notification(self, alert: SystemAlert) -> None:
        """Send email notification"""
        try:
            email_config = self.notification_channels['email']
            
            msg = MimeMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(email_config['to_addresses'])
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.name}"
            
            body = f"""
Alert: {alert.name}
Severity: {alert.severity}
Time: {alert.timestamp}
Message: {alert.message}

Metrics:
{json.dumps(alert.metrics, indent=2)}

---
ITDO ERP Monitoring System v41.0
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config['username']:
                    server.starttls()
                    server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                
            logger.info(f"Email notification sent for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _send_slack_notification(self, alert: SystemAlert) -> None:
        """Send Slack notification"""
        try:
            slack_config = self.notification_channels['slack']
            
            color = 'danger' if alert.severity == 'critical' else 'warning'
            if alert.resolved:
                color = 'good'
            
            payload = {
                'channel': slack_config['channel'],
                'username': 'ITDO ERP Monitor',
                'icon_emoji': ':rotating_light:',
                'attachments': [{
                    'color': color,
                    'title': f"{alert.severity.upper()}: {alert.name}",
                    'text': alert.message,
                    'timestamp': int(alert.timestamp.timestamp()),
                    'fields': [
                        {
                            'title': 'Metrics',
                            'value': '\n'.join([f"{k}: {v}" for k, v in alert.metrics.items()]),
                            'short': False
                        }
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_config['webhook_url'], json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert: {alert.name}")
                    else:
                        logger.error(f"Failed to send Slack notification: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _attempt_auto_healing(self, alert: SystemAlert) -> None:
        """Attempt automatic healing for critical alerts"""
        if alert.auto_healing_attempted:
            return
            
        alert.auto_healing_attempted = True
        
        try:
            # Auto-healing actions based on alert type
            if 'high_cpu' in alert.name.lower():
                await self._scale_resources('cpu')
            elif 'high_memory' in alert.name.lower():
                await self._scale_resources('memory')
            elif 'service_down' in alert.name.lower():
                await self._restart_service(alert)
            elif 'disk_space' in alert.name.lower():
                await self._cleanup_disk_space()
            elif 'database' in alert.name.lower():
                await self._optimize_database()
                
            logger.info(f"Auto-healing attempted for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"Auto-healing failed for alert {alert.name}: {e}")
    
    async def _scale_resources(self, resource_type: str) -> None:
        """Scale Kubernetes resources"""
        try:
            if resource_type == 'cpu':
                # Scale up replicas
                cmd = ["kubectl", "scale", "deployment", "backend", "--replicas=3", "-n", "itdo-erp-prod"]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info("Scaled up backend replicas for CPU load")
                
            elif resource_type == 'memory':
                # Apply memory limits patch
                cmd = ["kubectl", "patch", "deployment", "backend", "-n", "itdo-erp-prod", 
                       "-p", '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"2Gi"}}}]}}}}']
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info("Increased memory limits for backend")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scale resources: {e}")
    
    async def _restart_service(self, alert: SystemAlert) -> None:
        """Restart failed service"""
        try:
            # Extract service name from alert
            service_name = self._extract_service_name(alert.message)
            
            if service_name:
                cmd = ["kubectl", "rollout", "restart", "deployment", service_name, "-n", "itdo-erp-prod"]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"Restarted service: {service_name}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart service: {e}")
    
    async def _cleanup_disk_space(self) -> None:
        """Cleanup disk space"""
        try:
            # Clean up old logs
            cmd = ["kubectl", "exec", "-n", "itdo-erp-prod", "deployment/backend", "--", 
                   "sh", "-c", "find /var/log -name '*.log' -mtime +7 -delete"]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Cleaned up old log files")
            
            # Clean up temporary files
            cmd = ["kubectl", "exec", "-n", "itdo-erp-prod", "deployment/backend", "--", 
                   "sh", "-c", "rm -rf /tmp/*"]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Cleaned up temporary files")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup disk space: {e}")
    
    async def _optimize_database(self) -> None:
        """Optimize database performance"""
        try:
            # Run database maintenance
            cmd = ["kubectl", "exec", "-n", "itdo-erp-prod", "statefulset/postgresql", "--", 
                   "psql", "-U", "postgres", "-c", "VACUUM ANALYZE;"]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Optimized database with VACUUM ANALYZE")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to optimize database: {e}")
    
    def _extract_service_name(self, message: str) -> Optional[str]:
        """Extract service name from alert message"""
        # Simple extraction logic - can be enhanced
        if 'backend' in message.lower():
            return 'backend'
        elif 'frontend' in message.lower():
            return 'frontend'
        elif 'database' in message.lower():
            return 'postgresql'
        return None

class MetricsCollector:
    """Advanced metrics collection system"""
    
    def __init__(self, prometheus_client: PrometheusClient):
        self.prometheus = prometheus_client
        self.metrics_cache: Dict[str, Any] = {}
        self.collection_interval = 30  # seconds
        
    async def collect_all_metrics(self) -> MonitoringMetrics:
        """Collect comprehensive system metrics"""
        try:
            timestamp = datetime.now()
            
            # Collect CPU metrics
            cpu_usage = await self._get_cpu_usage()
            
            # Collect memory metrics
            memory_usage = await self._get_memory_usage()
            
            # Collect disk metrics
            disk_usage = await self._get_disk_usage()
            
            # Collect network metrics
            network_io = await self._get_network_io()
            
            # Collect service status
            service_status = await self._get_service_status()
            
            # Collect response times
            response_times = await self._get_response_times()
            
            # Collect error rates
            error_rates = await self._get_error_rates()
            
            # Collect database metrics
            db_connections = await self._get_database_connections()
            
            # Collect queue metrics
            queue_sizes = await self._get_queue_sizes()
            
            metrics = MonitoringMetrics(
                timestamp=timestamp,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                service_status=service_status,
                response_times=response_times,
                error_rates=error_rates,
                database_connections=db_connections,
                queue_sizes=queue_sizes
            )
            
            # Cache metrics
            self.metrics_cache[timestamp.isoformat()] = asdict(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return self._get_default_metrics()
    
    async def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        query = '100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        result = self.prometheus.query(query)
        
        if result['status'] == 'success' and result['data']['result']:
            return float(result['data']['result'][0]['value'][1])
        return 0.0
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        query = '(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100'
        result = self.prometheus.query(query)
        
        if result['status'] == 'success' and result['data']['result']:
            return float(result['data']['result'][0]['value'][1])
        return 0.0
    
    async def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        query = '(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100'
        result = self.prometheus.query(query)
        
        if result['status'] == 'success' and result['data']['result']:
            return float(result['data']['result'][0]['value'][1])
        return 0.0
    
    async def _get_network_io(self) -> Dict[str, float]:
        """Get network I/O metrics"""
        receive_query = 'rate(node_network_receive_bytes_total[5m])'
        transmit_query = 'rate(node_network_transmit_bytes_total[5m])'
        
        receive_result = self.prometheus.query(receive_query)
        transmit_result = self.prometheus.query(transmit_query)
        
        return {
            'receive_bytes_per_sec': float(receive_result['data']['result'][0]['value'][1]) if receive_result['data']['result'] else 0.0,
            'transmit_bytes_per_sec': float(transmit_result['data']['result'][0]['value'][1]) if transmit_result['data']['result'] else 0.0
        }
    
    async def _get_service_status(self) -> Dict[str, bool]:
        """Get service status"""
        query = 'up{job=~"backend|frontend|postgresql|redis"}'
        result = self.prometheus.query(query)
        
        status = {}
        if result['status'] == 'success':
            for item in result['data']['result']:
                job = item['metric'].get('job', 'unknown')
                status[job] = float(item['value'][1]) == 1.0
        
        return status
    
    async def _get_response_times(self) -> Dict[str, float]:
        """Get service response times"""
        query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
        result = self.prometheus.query(query)
        
        response_times = {}
        if result['status'] == 'success':
            for item in result['data']['result']:
                job = item['metric'].get('job', 'unknown')
                response_times[job] = float(item['value'][1])
        
        return response_times
    
    async def _get_error_rates(self) -> Dict[str, float]:
        """Get service error rates"""
        query = 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100'
        result = self.prometheus.query(query)
        
        error_rates = {}
        if result['status'] == 'success':
            for item in result['data']['result']:
                job = item['metric'].get('job', 'unknown')
                error_rates[job] = float(item['value'][1])
        
        return error_rates
    
    async def _get_database_connections(self) -> int:
        """Get database connection count"""
        query = 'pg_stat_activity_count'
        result = self.prometheus.query(query)
        
        if result['status'] == 'success' and result['data']['result']:
            return int(float(result['data']['result'][0]['value'][1]))
        return 0
    
    async def _get_queue_sizes(self) -> Dict[str, int]:
        """Get queue sizes"""
        # Placeholder for queue metrics
        return {'task_queue': 0, 'email_queue': 0}
    
    def _get_default_metrics(self) -> MonitoringMetrics:
        """Get default metrics when collection fails"""
        return MonitoringMetrics(
            timestamp=datetime.now(),
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            network_io={'receive_bytes_per_sec': 0.0, 'transmit_bytes_per_sec': 0.0},
            service_status={},
            response_times={},
            error_rates={},
            database_connections=0,
            queue_sizes={}
        )

class MonitoringDashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.dashboard_data: Dict[str, Any] = {}
        
    async def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data"""
        try:
            # Get current metrics
            metrics = await self.metrics_collector.collect_all_metrics()
            
            # Get active alerts
            active_alerts = [asdict(alert) for alert in self.alert_manager.active_alerts.values()]
            
            # Get alert history (last 24 hours)
            now = datetime.now()
            day_ago = now - timedelta(days=1)
            recent_alerts = [
                asdict(alert) for alert in self.alert_manager.alert_history
                if alert.timestamp >= day_ago
            ]
            
            # Generate dashboard data
            self.dashboard_data = {
                'timestamp': now.isoformat(),
                'system_status': 'healthy' if not active_alerts else 'warning' if any(a['severity'] == 'warning' for a in active_alerts) else 'critical',
                'metrics': asdict(metrics),
                'active_alerts': active_alerts,
                'recent_alerts': recent_alerts,
                'alert_summary': {
                    'total_active': len(active_alerts),
                    'critical_count': len([a for a in active_alerts if a['severity'] == 'critical']),
                    'warning_count': len([a for a in active_alerts if a['severity'] == 'warning']),
                    'last_24h_count': len(recent_alerts)
                },
                'service_health': {
                    'backend': metrics.service_status.get('backend', False),
                    'frontend': metrics.service_status.get('frontend', False),
                    'database': metrics.service_status.get('postgresql', False),
                    'redis': metrics.service_status.get('redis', False)
                },
                'performance_metrics': {
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'avg_response_time': sum(metrics.response_times.values()) / len(metrics.response_times) if metrics.response_times else 0,
                    'avg_error_rate': sum(metrics.error_rates.values()) / len(metrics.error_rates) if metrics.error_rates else 0
                }
            }
            
            return self.dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            return {'error': str(e)}
    
    async def save_dashboard_data(self, file_path: str) -> None:
        """Save dashboard data to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.dashboard_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save dashboard data: {e}")

class MonitoringOrchestrator:
    """Main orchestrator for monitoring system"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.prometheus_client = PrometheusClient(self.config['prometheus_url'])
        self.metrics_collector = MetricsCollector(self.prometheus_client)
        self.alert_manager = AlertManager(self.config['alerting'])
        self.dashboard = MonitoringDashboard(self.metrics_collector, self.alert_manager)
        
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Metric thresholds
        self.thresholds = [
            MetricThreshold('cpu_usage', 70.0, 85.0, 2),
            MetricThreshold('memory_usage', 80.0, 90.0, 2),
            MetricThreshold('disk_usage', 85.0, 95.0, 1),
            MetricThreshold('response_time', 2.0, 5.0, 2),
            MetricThreshold('error_rate', 5.0, 10.0, 2),
            MetricThreshold('database_connections', 80, 100, 2)
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load monitoring configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'prometheus_url': 'http://prometheus-service:9090',
            'collection_interval': 30,
            'alerting': {
                'auto_healing_enabled': True,
                'email': {
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'from_address': 'alerts@itdo-erp.com',
                    'to_addresses': ['admin@itdo-erp.com']
                }
            }
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def start(self) -> None:
        """Start monitoring system"""
        logger.info("Starting CC03 v41.0 Monitoring System...")
        self.running = True
        
        # Start monitoring tasks
        self.tasks = [
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._dashboard_update_loop()),
            asyncio.create_task(self._health_check_loop())
        ]
        
        # Wait for all tasks
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Monitoring system stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = await self.metrics_collector.collect_all_metrics()
                
                # Check thresholds and generate alerts
                await self._check_thresholds(metrics)
                
                # Wait for next collection
                await asyncio.sleep(self.config.get('collection_interval', 30))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _alert_processing_loop(self) -> None:
        """Alert processing loop"""
        while self.running:
            try:
                # Process any pending alerts
                # This would typically read from a queue
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _dashboard_update_loop(self) -> None:
        """Dashboard update loop"""
        while self.running:
            try:
                # Generate dashboard data
                dashboard_data = await self.dashboard.generate_dashboard_data()
                
                # Save to file
                await self.dashboard.save_dashboard_data('/tmp/monitoring_dashboard.json')
                
                # Wait before next update
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(10)
    
    async def _health_check_loop(self) -> None:
        """Health check loop"""
        while self.running:
            try:
                # Check system health
                await self._perform_health_checks()
                
                # Wait before next check
                await asyncio.sleep(300)  # Every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_thresholds(self, metrics: MonitoringMetrics) -> None:
        """Check metric thresholds and generate alerts"""
        try:
            for threshold in self.thresholds:
                if not threshold.enabled:
                    continue
                    
                # Get metric value
                metric_value = self._get_metric_value(metrics, threshold.metric_name)
                if metric_value is None:
                    continue
                
                # Check thresholds
                if metric_value >= threshold.critical_threshold:
                    await self._generate_alert(
                        f"Critical {threshold.metric_name}",
                        'critical',
                        f"{threshold.metric_name} is at {metric_value:.2f} (threshold: {threshold.critical_threshold})",
                        {threshold.metric_name: metric_value}
                    )
                elif metric_value >= threshold.warning_threshold:
                    await self._generate_alert(
                        f"High {threshold.metric_name}",
                        'warning',
                        f"{threshold.metric_name} is at {metric_value:.2f} (threshold: {threshold.warning_threshold})",
                        {threshold.metric_name: metric_value}
                    )
                    
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    def _get_metric_value(self, metrics: MonitoringMetrics, metric_name: str) -> Optional[float]:
        """Get metric value by name"""
        metric_map = {
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage,
            'disk_usage': metrics.disk_usage,
            'database_connections': float(metrics.database_connections),
            'response_time': sum(metrics.response_times.values()) / len(metrics.response_times) if metrics.response_times else 0,
            'error_rate': sum(metrics.error_rates.values()) / len(metrics.error_rates) if metrics.error_rates else 0
        }
        
        return metric_map.get(metric_name)
    
    async def _generate_alert(self, name: str, severity: str, message: str, metrics: Dict[str, float]) -> None:
        """Generate system alert"""
        alert = SystemAlert(
            alert_id=f"{name.lower().replace(' ', '_')}_{int(time.time())}",
            name=name,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics
        )
        
        await self.alert_manager.process_alert(alert)
    
    async def _perform_health_checks(self) -> None:
        """Perform system health checks"""
        try:
            # Check Prometheus connectivity
            result = self.prometheus_client.query('up')
            if result['status'] != 'success':
                await self._generate_alert(
                    "Prometheus Connectivity",
                    'critical',
                    "Cannot connect to Prometheus",
                    {}
                )
            
            # Check service endpoints
            services = ['backend', 'frontend', 'postgresql', 'redis']
            for service in services:
                # This would check actual service health endpoints
                pass
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")

def main():
    """Main function"""
    # Create config file if it doesn't exist
    config_path = '/tmp/monitoring_config.yaml'
    if not os.path.exists(config_path):
        default_config = {
            'prometheus_url': 'http://prometheus-service:9090',
            'collection_interval': 30,
            'alerting': {
                'auto_healing_enabled': True,
                'email': {
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'from_address': 'alerts@itdo-erp.com',
                    'to_addresses': ['admin@itdo-erp.com']
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
    
    # Start monitoring system
    orchestrator = MonitoringOrchestrator(config_path)
    
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        logger.info("Monitoring system stopped by user")
    except Exception as e:
        logger.error(f"Monitoring system failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()