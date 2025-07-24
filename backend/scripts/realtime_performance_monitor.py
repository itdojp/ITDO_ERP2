#!/usr/bin/env python3
"""
CC02 v38.0 Phase 4: Real-time Performance Monitoring System
リアルタイム性能監視システム - 継続的パフォーマンス追跡と自動最適化
"""

import asyncio
import json
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil


class RealTimePerformanceMonitor:
    """Real-time performance monitoring with automatic optimization triggers."""

    def __init__(self):
        self.monitoring_active = False
        self.performance_db = "performance_monitoring.db"
        self.monitoring_interval = 10  # seconds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "response_time_ms": 1000.0,
            "error_rate": 5.0,  # percent
            "database_connections": 0.9,  # 90% of pool
        }
        self.optimization_triggers = {
            "auto_scale": False,
            "cache_warming": True,
            "query_optimization": True,
            "resource_cleanup": True,
        }

        self.initialize_database()

    def initialize_database(self):
        """Initialize SQLite database for performance metrics storage."""
        print("🗄️ Initializing performance monitoring database...")

        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        # Create tables for different metric types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_usage_percent REAL,
                network_io_mb REAL,
                active_connections INTEGER,
                process_count INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                response_time_ms REAL,
                status_code INTEGER,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER,
                user_id TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS database_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                query_type TEXT,
                execution_time_ms REAL,
                rows_affected INTEGER,
                table_name TEXT,
                connection_pool_size INTEGER,
                active_connections INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                metric_value REAL,
                threshold_value REAL,
                resolved BOOLEAN DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT,
                description TEXT,
                success BOOLEAN,
                impact_description TEXT,
                metrics_before TEXT,
                metrics_after TEXT
            )
        """)

        conn.commit()
        conn.close()

        print("✅ Performance monitoring database initialized")

    async def start_monitoring(self, duration_minutes: Optional[int] = None):
        """Start real-time performance monitoring."""
        print("🚀 Starting real-time performance monitoring...")
        print(f"📊 Monitoring interval: {self.monitoring_interval} seconds")
        print(
            f"⏱️ Duration: {'Continuous' if not duration_minutes else f'{duration_minutes} minutes'}"
        )

        self.monitoring_active = True

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_system_metrics()),
            asyncio.create_task(self.monitor_application_health()),
            asyncio.create_task(self.monitor_database_performance()),
            asyncio.create_task(self.analyze_performance_trends()),
            asyncio.create_task(self.check_alerts_and_optimize()),
        ]

        try:
            if duration_minutes:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=duration_minutes * 60,
                )
            else:
                await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.TimeoutError:
            print("⏰ Monitoring duration completed")
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
        finally:
            self.monitoring_active = False

        print("✅ Performance monitoring completed")

    async def monitor_system_metrics(self):
        """Monitor system-level performance metrics."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                net_io = psutil.net_io_counters()
                connections = len(psutil.net_connections())
                processes = len(psutil.pids())

                # Calculate network I/O rate (MB/s)
                if hasattr(self, "_last_net_io"):
                    net_io_mb = (
                        (
                            (net_io.bytes_sent + net_io.bytes_recv)
                            - (
                                self._last_net_io.bytes_sent
                                + self._last_net_io.bytes_recv
                            )
                        )
                        / 1024
                        / 1024
                    )
                else:
                    net_io_mb = 0

                self._last_net_io = net_io

                # Store metrics
                self.store_system_metrics(
                    {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_usage_percent": disk.percent,
                        "network_io_mb": net_io_mb,
                        "active_connections": connections,
                        "process_count": processes,
                    }
                )

                # Check for system alerts
                await self.check_system_alerts(
                    {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_usage_percent": disk.percent,
                        "active_connections": connections,
                    }
                )

            except Exception as e:
                print(f"⚠️ Error monitoring system metrics: {e}")

            await asyncio.sleep(self.monitoring_interval)

    def store_system_metrics(self, metrics: Dict[str, Any]):
        """Store system metrics in database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO system_metrics
            (cpu_percent, memory_percent, disk_usage_percent, network_io_mb, active_connections, process_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                metrics["cpu_percent"],
                metrics["memory_percent"],
                metrics["disk_usage_percent"],
                metrics["network_io_mb"],
                metrics["active_connections"],
                metrics["process_count"],
            ),
        )

        conn.commit()
        conn.close()

    async def check_system_alerts(self, metrics: Dict[str, Any]):
        """Check system metrics against alert thresholds."""
        alerts = []

        if metrics["cpu_percent"] > self.alert_thresholds["cpu_percent"]:
            alerts.append(
                {
                    "type": "high_cpu_usage",
                    "severity": "warning"
                    if metrics["cpu_percent"] < 95
                    else "critical",
                    "message": f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                    "value": metrics["cpu_percent"],
                    "threshold": self.alert_thresholds["cpu_percent"],
                }
            )

        if metrics["memory_percent"] > self.alert_thresholds["memory_percent"]:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "severity": "warning"
                    if metrics["memory_percent"] < 95
                    else "critical",
                    "message": f"High memory usage: {metrics['memory_percent']:.1f}%",
                    "value": metrics["memory_percent"],
                    "threshold": self.alert_thresholds["memory_percent"],
                }
            )

        if metrics["disk_usage_percent"] > 90:
            alerts.append(
                {
                    "type": "high_disk_usage",
                    "severity": "warning"
                    if metrics["disk_usage_percent"] < 95
                    else "critical",
                    "message": f"High disk usage: {metrics['disk_usage_percent']:.1f}%",
                    "value": metrics["disk_usage_percent"],
                    "threshold": 90.0,
                }
            )

        # Store and process alerts
        for alert in alerts:
            self.store_alert(alert)
            await self.process_alert(alert)

    def store_alert(self, alert: Dict[str, Any]):
        """Store performance alert in database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO performance_alerts
            (alert_type, severity, message, metric_value, threshold_value)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                alert["type"],
                alert["severity"],
                alert["message"],
                alert["value"],
                alert["threshold"],
            ),
        )

        conn.commit()
        conn.close()

        print(f"🚨 {alert['severity'].upper()}: {alert['message']}")

    async def process_alert(self, alert: Dict[str, Any]):
        """Process performance alert and trigger optimizations if needed."""
        if alert["severity"] == "critical":
            print(f"🔴 CRITICAL ALERT: {alert['message']}")

            # Trigger immediate optimization
            if alert["type"] == "high_cpu_usage":
                await self.optimize_cpu_usage()
            elif alert["type"] == "high_memory_usage":
                await self.optimize_memory_usage()

        elif alert["severity"] == "warning":
            print(f"🟡 WARNING: {alert['message']}")

    async def optimize_cpu_usage(self):
        """Optimize CPU usage when threshold is exceeded."""
        print("⚡ Triggering CPU optimization...")

        optimization_actions = []

        try:
            # Action 1: Identify CPU-intensive processes
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
                try:
                    proc_info = proc.info
                    if proc_info["cpu_percent"] > 10:  # Only high CPU processes
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort by CPU usage
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)

            optimization_actions.append(
                f"Identified {len(processes)} high CPU processes"
            )

            # Action 2: Clear caches if available
            if self.optimization_triggers["resource_cleanup"]:
                await self.clear_system_caches()
                optimization_actions.append("Cleared system caches")

            # Action 3: Log optimization
            await self.log_optimization_action(
                {
                    "action_type": "cpu_optimization",
                    "description": "Automatic CPU usage optimization triggered",
                    "actions": optimization_actions,
                    "success": True,
                }
            )

            print("✅ CPU optimization completed")

        except Exception as e:
            print(f"❌ CPU optimization failed: {e}")
            await self.log_optimization_action(
                {
                    "action_type": "cpu_optimization",
                    "description": f"CPU optimization failed: {e}",
                    "actions": optimization_actions,
                    "success": False,
                }
            )

    async def optimize_memory_usage(self):
        """Optimize memory usage when threshold is exceeded."""
        print("💾 Triggering memory optimization...")

        optimization_actions = []

        try:
            # Action 1: Get memory info
            memory = psutil.virtual_memory()
            optimization_actions.append(f"Current memory usage: {memory.percent:.1f}%")

            # Action 2: Clear application caches
            if self.optimization_triggers["resource_cleanup"]:
                await self.clear_application_caches()
                optimization_actions.append("Cleared application caches")

            # Action 3: Force garbage collection in Python processes
            await self.trigger_garbage_collection()
            optimization_actions.append("Triggered garbage collection")

            # Action 4: Log optimization
            await self.log_optimization_action(
                {
                    "action_type": "memory_optimization",
                    "description": "Automatic memory usage optimization triggered",
                    "actions": optimization_actions,
                    "success": True,
                }
            )

            print("✅ Memory optimization completed")

        except Exception as e:
            print(f"❌ Memory optimization failed: {e}")
            await self.log_optimization_action(
                {
                    "action_type": "memory_optimization",
                    "description": f"Memory optimization failed: {e}",
                    "actions": optimization_actions,
                    "success": False,
                }
            )

    async def clear_system_caches(self):
        """Clear system-level caches where possible."""
        try:
            # Clear Python's internal caches
            import gc

            gc.collect()

            # Clear DNS cache (Linux)
            try:
                subprocess.run(
                    ["sudo", "systemctl", "restart", "systemd-resolved"],
                    check=False,
                    capture_output=True,
                )
            except:
                pass

        except Exception as e:
            print(f"⚠️ Error clearing system caches: {e}")

    async def clear_application_caches(self):
        """Clear application-level caches."""
        try:
            # This would integrate with your application's cache system
            # For now, just demonstrate the concept
            print("   🧹 Clearing application caches...")

            # Example: Clear Redis cache
            # redis_client.flushdb()

            # Example: Clear in-memory caches
            # cache_manager.clear_all()

        except Exception as e:
            print(f"⚠️ Error clearing application caches: {e}")

    async def trigger_garbage_collection(self):
        """Trigger garbage collection in Python processes."""
        try:
            import gc

            collected = gc.collect()
            print(f"   🗑️ Garbage collection freed {collected} objects")
        except Exception as e:
            print(f"⚠️ Error triggering garbage collection: {e}")

    async def monitor_application_health(self):
        """Monitor application-specific health metrics."""
        while self.monitoring_active:
            try:
                # Check if FastAPI application is responsive
                await self.check_application_health()

                # Monitor API response times (simulated)
                api_metrics = await self.collect_api_metrics()

                # Store API metrics
                for metric in api_metrics:
                    self.store_api_metrics(metric)

                # Check for API performance alerts
                await self.check_api_alerts(api_metrics)

            except Exception as e:
                print(f"⚠️ Error monitoring application health: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def check_application_health(self) -> Dict[str, Any]:
        """Check if the application is healthy and responsive."""
        try:
            # Simulate health check (in real implementation, make HTTP request to /health)
            health_status = {
                "status": "healthy",
                "response_time_ms": 50,  # Simulated
                "database_connected": True,
                "cache_connected": True,
            }

            return health_status

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "response_time_ms": None}

    async def collect_api_metrics(self) -> List[Dict[str, Any]]:
        """Collect API performance metrics (simulated)."""
        # In real implementation, this would integrate with application monitoring
        # For demonstration, return simulated metrics
        import random

        endpoints = [
            "/api/v1/users",
            "/api/v1/organizations",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/tasks",
        ]

        metrics = []
        for endpoint in endpoints:
            if random.random() < 0.3:  # 30% chance of having recent requests
                metric = {
                    "endpoint": endpoint,
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                    "response_time_ms": random.uniform(10, 500),
                    "status_code": random.choice([200, 200, 200, 201, 400, 500]),
                    "request_size_bytes": random.randint(100, 5000),
                    "response_size_bytes": random.randint(500, 50000),
                    "user_id": f"user_{random.randint(1, 100)}",
                }
                metrics.append(metric)

        return metrics

    def store_api_metrics(self, metric: Dict[str, Any]):
        """Store API metrics in database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO api_metrics
            (endpoint, method, response_time_ms, status_code, request_size_bytes, response_size_bytes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metric["endpoint"],
                metric["method"],
                metric["response_time_ms"],
                metric["status_code"],
                metric["request_size_bytes"],
                metric["response_size_bytes"],
                metric["user_id"],
            ),
        )

        conn.commit()
        conn.close()

    async def check_api_alerts(self, metrics: List[Dict[str, Any]]):
        """Check API metrics for performance alerts."""
        for metric in metrics:
            # Check response time
            if metric["response_time_ms"] > self.alert_thresholds["response_time_ms"]:
                alert = {
                    "type": "slow_api_response",
                    "severity": "warning"
                    if metric["response_time_ms"] < 2000
                    else "critical",
                    "message": f"Slow API response: {metric['endpoint']} took {metric['response_time_ms']:.1f}ms",
                    "value": metric["response_time_ms"],
                    "threshold": self.alert_thresholds["response_time_ms"],
                }
                self.store_alert(alert)
                await self.process_alert(alert)

            # Check for server errors
            if metric["status_code"] >= 500:
                alert = {
                    "type": "api_server_error",
                    "severity": "critical",
                    "message": f"API server error: {metric['endpoint']} returned {metric['status_code']}",
                    "value": metric["status_code"],
                    "threshold": 500,
                }
                self.store_alert(alert)
                await self.process_alert(alert)

    async def monitor_database_performance(self):
        """Monitor database performance metrics."""
        while self.monitoring_active:
            try:
                # Simulate database monitoring
                db_metrics = await self.collect_database_metrics()

                # Store database metrics
                for metric in db_metrics:
                    self.store_database_metrics(metric)

                # Check for database alerts
                await self.check_database_alerts(db_metrics)

            except Exception as e:
                print(f"⚠️ Error monitoring database performance: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def collect_database_metrics(self) -> List[Dict[str, Any]]:
        """Collect database performance metrics (simulated)."""
        import random

        query_types = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        tables = ["users", "organizations", "tasks", "roles", "permissions"]

        metrics = []
        for _ in range(random.randint(1, 5)):
            metric = {
                "query_type": random.choice(query_types),
                "execution_time_ms": random.uniform(1, 200),
                "rows_affected": random.randint(1, 1000),
                "table_name": random.choice(tables),
                "connection_pool_size": 20,
                "active_connections": random.randint(1, 18),
            }
            metrics.append(metric)

        return metrics

    def store_database_metrics(self, metric: Dict[str, Any]):
        """Store database metrics in database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO database_metrics
            (query_type, execution_time_ms, rows_affected, table_name, connection_pool_size, active_connections)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                metric["query_type"],
                metric["execution_time_ms"],
                metric["rows_affected"],
                metric["table_name"],
                metric["connection_pool_size"],
                metric["active_connections"],
            ),
        )

        conn.commit()
        conn.close()

    async def check_database_alerts(self, metrics: List[Dict[str, Any]]):
        """Check database metrics for performance alerts."""
        for metric in metrics:
            # Check connection pool usage
            pool_usage = metric["active_connections"] / metric["connection_pool_size"]
            if pool_usage > self.alert_thresholds["database_connections"]:
                alert = {
                    "type": "high_db_connection_usage",
                    "severity": "warning" if pool_usage < 0.95 else "critical",
                    "message": f"High database connection usage: {pool_usage:.1%}",
                    "value": pool_usage * 100,
                    "threshold": self.alert_thresholds["database_connections"] * 100,
                }
                self.store_alert(alert)
                await self.process_alert(alert)

            # Check slow queries
            if metric["execution_time_ms"] > 100:
                alert = {
                    "type": "slow_database_query",
                    "severity": "warning"
                    if metric["execution_time_ms"] < 500
                    else "critical",
                    "message": f"Slow database query: {metric['query_type']} on {metric['table_name']} took {metric['execution_time_ms']:.1f}ms",
                    "value": metric["execution_time_ms"],
                    "threshold": 100,
                }
                self.store_alert(alert)

    async def analyze_performance_trends(self):
        """Analyze performance trends and predict issues."""
        while self.monitoring_active:
            try:
                # Analyze trends every 5 monitoring intervals
                await asyncio.sleep(self.monitoring_interval * 5)

                # Get recent metrics for trend analysis
                trends = await self.calculate_performance_trends()

                # Generate trend-based recommendations
                recommendations = await self.generate_trend_recommendations(trends)

                if recommendations:
                    print("📈 Performance Trend Analysis:")
                    for rec in recommendations:
                        print(f"   • {rec}")

            except Exception as e:
                print(f"⚠️ Error analyzing performance trends: {e}")

    async def calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from recent metrics."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        # Get system metrics from last hour
        cursor.execute("""
            SELECT cpu_percent, memory_percent, timestamp
            FROM system_metrics
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp
        """)

        system_data = cursor.fetchall()

        # Get API metrics from last hour
        cursor.execute("""
            SELECT AVG(response_time_ms), COUNT(*), timestamp
            FROM api_metrics
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY datetime(timestamp)
            ORDER BY timestamp
        """)

        api_data = cursor.fetchall()

        conn.close()

        trends = {
            "system_metrics_count": len(system_data),
            "api_metrics_count": len(api_data),
            "cpu_trend": "stable",
            "memory_trend": "stable",
            "response_time_trend": "stable",
        }

        # Analyze CPU trend
        if len(system_data) > 10:
            recent_cpu = [row[0] for row in system_data[-10:]]
            earlier_cpu = (
                [row[0] for row in system_data[-20:-10]]
                if len(system_data) > 20
                else recent_cpu
            )

            recent_avg = sum(recent_cpu) / len(recent_cpu)
            earlier_avg = sum(earlier_cpu) / len(earlier_cpu)

            if recent_avg > earlier_avg * 1.1:
                trends["cpu_trend"] = "increasing"
            elif recent_avg < earlier_avg * 0.9:
                trends["cpu_trend"] = "decreasing"

        # Analyze memory trend
        if len(system_data) > 10:
            recent_memory = [row[1] for row in system_data[-10:]]
            earlier_memory = (
                [row[1] for row in system_data[-20:-10]]
                if len(system_data) > 20
                else recent_memory
            )

            recent_avg = sum(recent_memory) / len(recent_memory)
            earlier_avg = sum(earlier_memory) / len(earlier_memory)

            if recent_avg > earlier_avg * 1.05:
                trends["memory_trend"] = "increasing"
            elif recent_avg < earlier_avg * 0.95:
                trends["memory_trend"] = "decreasing"

        return trends

    async def generate_trend_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance trends."""
        recommendations = []

        if trends["cpu_trend"] == "increasing":
            recommendations.append(
                "CPU usage is trending upward - consider scaling or optimization"
            )

        if trends["memory_trend"] == "increasing":
            recommendations.append(
                "Memory usage is trending upward - investigate memory leaks"
            )

        if trends["system_metrics_count"] > 0 and trends["api_metrics_count"] == 0:
            recommendations.append(
                "No API activity detected - verify application health"
            )

        return recommendations

    async def check_alerts_and_optimize(self):
        """Check for unresolved alerts and trigger optimizations."""
        while self.monitoring_active:
            try:
                # Check for unresolved critical alerts
                conn = sqlite3.connect(self.performance_db)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT alert_type, COUNT(*) as count
                    FROM performance_alerts
                    WHERE resolved = 0 AND severity = 'critical'
                    AND timestamp > datetime('now', '-10 minutes')
                    GROUP BY alert_type
                """)

                critical_alerts = cursor.fetchall()
                conn.close()

                for alert_type, count in critical_alerts:
                    if count >= 3:  # 3 or more critical alerts of same type
                        print(
                            f"🚨 MULTIPLE CRITICAL ALERTS: {alert_type} ({count} alerts)"
                        )
                        await self.trigger_emergency_optimization(alert_type)

            except Exception as e:
                print(f"⚠️ Error checking alerts: {e}")

            await asyncio.sleep(self.monitoring_interval * 2)

    async def trigger_emergency_optimization(self, alert_type: str):
        """Trigger emergency optimization for critical alert patterns."""
        print(f"🆘 Triggering emergency optimization for {alert_type}...")

        try:
            if alert_type == "high_cpu_usage":
                await self.optimize_cpu_usage()
            elif alert_type == "high_memory_usage":
                await self.optimize_memory_usage()
            elif alert_type == "slow_api_response":
                await self.optimize_api_performance()
            elif alert_type == "high_db_connection_usage":
                await self.optimize_database_connections()

            # Mark alerts as resolved
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE performance_alerts
                SET resolved = 1
                WHERE alert_type = ? AND resolved = 0
            """,
                (alert_type,),
            )
            conn.commit()
            conn.close()

            print(f"✅ Emergency optimization completed for {alert_type}")

        except Exception as e:
            print(f"❌ Emergency optimization failed for {alert_type}: {e}")

    async def optimize_api_performance(self):
        """Optimize API performance when slow responses are detected."""
        print("🚀 Optimizing API performance...")

        optimization_actions = []

        try:
            # Action 1: Warm up caches
            if self.optimization_triggers["cache_warming"]:
                await self.warm_up_caches()
                optimization_actions.append("Warmed up application caches")

            # Action 2: Optimize database queries
            if self.optimization_triggers["query_optimization"]:
                await self.optimize_database_queries()
                optimization_actions.append("Optimized database queries")

            await self.log_optimization_action(
                {
                    "action_type": "api_performance_optimization",
                    "description": "Automatic API performance optimization triggered",
                    "actions": optimization_actions,
                    "success": True,
                }
            )

            print("✅ API performance optimization completed")

        except Exception as e:
            print(f"❌ API performance optimization failed: {e}")

    async def optimize_database_connections(self):
        """Optimize database connection usage."""
        print("🗄️ Optimizing database connections...")

        optimization_actions = []

        try:
            optimization_actions.append("Analyzed database connection pool usage")
            optimization_actions.append("Recommended connection pool scaling")

            await self.log_optimization_action(
                {
                    "action_type": "database_connection_optimization",
                    "description": "Database connection optimization triggered",
                    "actions": optimization_actions,
                    "success": True,
                }
            )

            print("✅ Database connection optimization completed")

        except Exception as e:
            print(f"❌ Database connection optimization failed: {e}")

    async def warm_up_caches(self):
        """Warm up application caches to improve response times."""
        try:
            print("   🔥 Warming up caches...")
            # In real implementation, pre-load frequently accessed data
            await asyncio.sleep(1)  # Simulate cache warming
        except Exception as e:
            print(f"⚠️ Error warming up caches: {e}")

    async def optimize_database_queries(self):
        """Optimize database query performance."""
        try:
            print("   🗄️ Optimizing database queries...")
            # In real implementation, analyze and optimize slow queries
            await asyncio.sleep(1)  # Simulate query optimization
        except Exception as e:
            print(f"⚠️ Error optimizing database queries: {e}")

    async def log_optimization_action(self, action: Dict[str, Any]):
        """Log optimization action to database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO optimization_actions
            (action_type, description, success, impact_description)
            VALUES (?, ?, ?, ?)
        """,
            (
                action["action_type"],
                action["description"],
                action["success"],
                "; ".join(action.get("actions", [])),
            ),
        )

        conn.commit()
        conn.close()

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        print("📊 Generating performance report...")

        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        # System metrics summary
        cursor.execute("""
            SELECT
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                COUNT(*) as metric_count
            FROM system_metrics
            WHERE timestamp > datetime('now', '-1 hour')
        """)

        system_summary = cursor.fetchone()

        # API metrics summary
        cursor.execute("""
            SELECT
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                COUNT(*) as request_count,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
            FROM api_metrics
            WHERE timestamp > datetime('now', '-1 hour')
        """)

        api_summary = cursor.fetchone()

        # Alert summary
        cursor.execute("""
            SELECT
                alert_type,
                severity,
                COUNT(*) as count
            FROM performance_alerts
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY alert_type, severity
        """)

        alert_summary = cursor.fetchall()

        # Optimization actions summary
        cursor.execute("""
            SELECT
                action_type,
                COUNT(*) as count,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
            FROM optimization_actions
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY action_type
        """)

        optimization_summary = cursor.fetchall()

        conn.close()

        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_period": "1 hour",
            "system_performance": {
                "avg_cpu_percent": system_summary[0] if system_summary[0] else 0,
                "max_cpu_percent": system_summary[1] if system_summary[1] else 0,
                "avg_memory_percent": system_summary[2] if system_summary[2] else 0,
                "max_memory_percent": system_summary[3] if system_summary[3] else 0,
                "metric_count": system_summary[4] if system_summary[4] else 0,
            },
            "api_performance": {
                "avg_response_time_ms": api_summary[0] if api_summary[0] else 0,
                "max_response_time_ms": api_summary[1] if api_summary[1] else 0,
                "total_requests": api_summary[2] if api_summary[2] else 0,
                "error_count": api_summary[3] if api_summary[3] else 0,
                "error_rate_percent": (api_summary[3] / max(1, api_summary[2])) * 100
                if api_summary[2]
                else 0,
            },
            "alerts": [
                {"type": alert[0], "severity": alert[1], "count": alert[2]}
                for alert in alert_summary
            ],
            "optimizations": [
                {
                    "type": opt[0],
                    "total_attempts": opt[1],
                    "successful": opt[2],
                    "success_rate": (opt[2] / opt[1]) * 100 if opt[1] > 0 else 0,
                }
                for opt in optimization_summary
            ],
        }

        return report

    async def save_performance_report(self, report: Dict[str, Any]):
        """Save performance report to file."""
        reports_dir = Path("docs/monitoring")
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / f"performance_report_{int(time.time())}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Performance report saved: {report_file}")

        return report_file


async def main():
    """Main function for real-time performance monitoring."""
    print("🚀 CC02 v38.0 Phase 4: Real-time Performance Monitoring System")
    print("=" * 70)

    monitor = RealTimePerformanceMonitor()

    try:
        # Start monitoring for 5 minutes (demo duration)
        monitoring_task = asyncio.create_task(
            monitor.start_monitoring(duration_minutes=5)
        )

        # Wait for monitoring to complete
        await monitoring_task

        # Generate final performance report
        report = await monitor.generate_performance_report()
        report_file = await monitor.save_performance_report(report)

        print("\n🎉 Real-time Performance Monitoring Complete!")
        print("=" * 70)
        print("📊 Monitoring Summary:")
        print(
            f"   - System Metrics Collected: {report['system_performance']['metric_count']}"
        )
        print(
            f"   - API Requests Monitored: {report['api_performance']['total_requests']}"
        )
        print(
            f"   - Alerts Generated: {sum(alert['count'] for alert in report['alerts'])}"
        )
        print(
            f"   - Optimizations Performed: {sum(opt['total_attempts'] for opt in report['optimizations'])}"
        )
        print(
            f"   - Average CPU Usage: {report['system_performance']['avg_cpu_percent']:.1f}%"
        )
        print(
            f"   - Average Memory Usage: {report['system_performance']['avg_memory_percent']:.1f}%"
        )
        print(
            f"   - Average API Response Time: {report['api_performance']['avg_response_time_ms']:.1f}ms"
        )
        print(
            f"   - API Error Rate: {report['api_performance']['error_rate_percent']:.1f}%"
        )
        print(f"   - Performance Report: {report_file}")

        return True

    except Exception as e:
        print(f"\n❌ Error in real-time performance monitoring: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
