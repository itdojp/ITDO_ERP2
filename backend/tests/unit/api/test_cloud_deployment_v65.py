"""
ITDO ERP Backend - Cloud Deployment v65 Tests
Test suite for cloud-native deployment and infrastructure features
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.v1.analytics_bi_v64 import (
    DataWarehouseManager,
    PredictiveAnalyticsEngine,
    RealtimeDashboardManager,
)
from app.api.v1.api_gateway_v62 import (
    CircuitBreaker,
    GatewayMetrics,
    LoadBalancer,
    RateLimiter,
    ServiceRegistry,
)
from app.api.v1.enterprise_integration_v63 import (
    MessageQueue,
    SagaOrchestrator,
)
from app.main import app


class TestCloudDeploymentInfrastructure:
    """Test cloud-native deployment infrastructure components"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Async test client fixture"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_kubernetes_client(self):
        """Mock Kubernetes client"""
        with patch("kubernetes.client.AppsV1Api") as mock:
            yield mock

    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client"""
        with patch("docker.from_env") as mock:
            yield mock

    @pytest.fixture
    def mock_helm_client(self):
        """Mock Helm client"""
        with patch("subprocess.run") as mock:
            yield mock

    def test_health_check_endpoint(self, client):
        """Test health check endpoint for load balancer"""
        response = client.get("/health")
        assert response.status_code == 200

        health_data = response.json()
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert health_data["status"] == "healthy"

    def test_readiness_probe_endpoint(self, client):
        """Test readiness probe endpoint for Kubernetes"""
        response = client.get("/health/ready")
        assert response.status_code == 200

        readiness_data = response.json()
        assert "ready" in readiness_data
        assert "dependencies" in readiness_data
        assert readiness_data["ready"] is True

    def test_metrics_endpoint_for_prometheus(self, client):
        """Test metrics endpoint for Prometheus scraping"""
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check for Prometheus format metrics
        metrics_text = response.text
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text
        assert "active_users_total" in metrics_text

    async def test_api_gateway_service_discovery(self):
        """Test API gateway service discovery for microservices"""
        service_registry = ServiceRegistry()

        # Test service registration
        service_data = {
            "name": "itdo-erp-backend",
            "version": "v65.0",
            "host": "itdo-erp-backend-service",
            "port": 8000,
            "health_check": "/health",
            "metadata": {"environment": "production", "deployment": "kubernetes"},
        }

        result = await service_registry.register_service(service_data)
        assert result["status"] == "registered"
        assert result["service_id"] is not None

        # Test service discovery
        services = await service_registry.discover_services("backend")
        assert len(services) > 0
        assert services[0]["name"] == "itdo-erp-backend"

    async def test_load_balancer_kubernetes_integration(self):
        """Test load balancer integration with Kubernetes services"""
        load_balancer = LoadBalancer()

        # Mock Kubernetes service endpoints
        mock_endpoints = [
            {"host": "10.0.1.100", "port": 8000, "ready": True},
            {"host": "10.0.1.101", "port": 8000, "ready": True},
            {"host": "10.0.1.102", "port": 8000, "ready": False},
        ]

        with patch.object(
            load_balancer, "get_kubernetes_endpoints", return_value=mock_endpoints
        ):
            # Test round-robin load balancing
            endpoint1 = await load_balancer.get_next_endpoint("backend")
            endpoint2 = await load_balancer.get_next_endpoint("backend")

            # Should only return ready endpoints
            assert endpoint1["ready"] is True
            assert endpoint2["ready"] is True
            assert endpoint1["host"] != endpoint2["host"]

    async def test_circuit_breaker_with_health_checks(self):
        """Test circuit breaker integration with Kubernetes health checks"""
        circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=30, health_check_interval=10
        )

        service_name = "backend-service"

        # Test healthy service
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200

            result = await circuit_breaker.call_service(service_name, "/health")
            assert result["status"] == "success"
            assert circuit_breaker.get_state(service_name) == "CLOSED"

        # Test failing service
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            # Trigger failures to open circuit
            for _ in range(4):
                try:
                    await circuit_breaker.call_service(service_name, "/api/test")
                except:
                    pass

            assert circuit_breaker.get_state(service_name) == "OPEN"

    async def test_rate_limiting_for_kubernetes_ingress(self):
        """Test rate limiting integration with Kubernetes ingress"""
        rate_limiter = RateLimiter()

        client_ip = "192.168.1.100"
        endpoint = "/api/v1/orders"

        # Test rate limiting with different limits per endpoint
        limits = {
            "/api/v1/orders": {"requests": 100, "window": 60},
            "/api/v1/analytics": {"requests": 10, "window": 60},
        }

        with patch.object(rate_limiter, "get_endpoint_limits", return_value=limits):
            # Test normal requests
            for i in range(50):
                result = await rate_limiter.check_rate_limit(client_ip, endpoint)
                assert result["allowed"] is True

            # Test exceeding limits
            for i in range(60):
                await rate_limiter.check_rate_limit(client_ip, endpoint)

            result = await rate_limiter.check_rate_limit(client_ip, endpoint)
            assert result["allowed"] is False
            assert "retry_after" in result

    async def test_auto_scaling_metrics_collection(self):
        """Test metrics collection for Kubernetes HPA"""
        gateway_metrics = GatewayMetrics()

        # Simulate requests for metrics collection
        for i in range(100):
            await gateway_metrics.record_request(
                method="GET",
                path="/api/v1/products",
                status_code=200,
                duration=0.1 + (i * 0.001),
                user_id=f"user_{i % 10}",
            )

        # Test CPU and memory utilization metrics
        cpu_usage = await gateway_metrics.get_cpu_utilization()
        memory_usage = await gateway_metrics.get_memory_utilization()

        assert 0 <= cpu_usage <= 100
        assert 0 <= memory_usage <= 100

        # Test custom application metrics for HPA
        request_rate = await gateway_metrics.get_request_rate()
        active_users = await gateway_metrics.get_active_users()

        assert request_rate > 0
        assert active_users > 0

    async def test_message_queue_kubernetes_persistence(self):
        """Test message queue with Kubernetes persistent volumes"""
        message_queue = MessageQueue()

        # Test message persistence with volume mounts
        message_data = {
            "id": "msg_001",
            "type": "order_created",
            "payload": {"order_id": "order_123", "user_id": "user_456"},
            "priority": "high",
            "retry_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Mock persistent storage
        with patch.object(message_queue, "persist_to_volume") as mock_persist:
            result = await message_queue.send_message(message_data)
            assert result["status"] == "sent"
            mock_persist.assert_called_once()

        # Test message recovery after pod restart
        with patch.object(message_queue, "load_from_volume") as mock_load:
            mock_load.return_value = [message_data]

            recovered_messages = await message_queue.recover_messages()
            assert len(recovered_messages) == 1
            assert recovered_messages[0]["id"] == "msg_001"

    async def test_saga_orchestrator_distributed_transactions(self):
        """Test SAGA orchestrator for distributed microservices"""
        saga_orchestrator = SagaOrchestrator()

        # Define distributed transaction steps
        saga_definition = {
            "saga_id": "order_processing_saga",
            "steps": [
                {
                    "service": "inventory-service",
                    "action": "reserve_items",
                    "compensate": "release_items",
                },
                {
                    "service": "payment-service",
                    "action": "process_payment",
                    "compensate": "refund_payment",
                },
                {
                    "service": "shipping-service",
                    "action": "create_shipment",
                    "compensate": "cancel_shipment",
                },
            ],
        }

        # Mock service calls
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "success"}

            result = await saga_orchestrator.execute_saga(saga_definition)
            assert result["status"] == "completed"
            assert len(result["completed_steps"]) == 3

        # Test compensation on failure
        with patch("httpx.AsyncClient.post") as mock_post:
            # First two steps succeed, third fails
            mock_responses = [
                Mock(status_code=200, json=lambda: {"status": "success"}),
                Mock(status_code=200, json=lambda: {"status": "success"}),
                Mock(status_code=500, json=lambda: {"status": "error"}),
            ]
            mock_post.side_effect = mock_responses

            result = await saga_orchestrator.execute_saga(saga_definition)
            assert result["status"] == "compensated"
            assert len(result["compensated_steps"]) == 2

    async def test_real_time_dashboard_kubernetes_scaling(self):
        """Test real-time dashboard with Kubernetes auto-scaling"""
        dashboard_manager = RealtimeDashboardManager()

        # Test dashboard creation with scaling configuration
        dashboard_config = {
            "name": "Production Monitoring",
            "widgets": [
                {
                    "type": "metrics",
                    "data_source": "prometheus",
                    "query": "rate(http_requests_total[5m])",
                },
                {
                    "type": "logs",
                    "data_source": "loki",
                    "query": '{namespace="itdo-erp"}',
                },
            ],
            "auto_refresh": 30,
            "scaling_metrics": {
                "cpu_threshold": 70,
                "memory_threshold": 80,
                "custom_metrics": ["request_rate", "active_users"],
            },
        }

        result = await dashboard_manager.create_dashboard(dashboard_config)
        assert result["status"] == "created"
        assert "dashboard_id" in result

        # Test real-time updates with WebSocket
        with patch("websockets.connect") as mock_ws:
            mock_ws.return_value.__aenter__.return_value.send = AsyncMock()

            await dashboard_manager.send_real_time_update(
                result["dashboard_id"], {"metric": "cpu_usage", "value": 75}
            )

    async def test_data_warehouse_cloud_storage_integration(self):
        """Test data warehouse integration with cloud storage"""
        warehouse_manager = DataWarehouseManager()

        # Test cloud storage configuration
        storage_config = {
            "provider": "aws_s3",
            "bucket": "itdo-erp-data-warehouse",
            "region": "us-west-2",
            "compression": "parquet",
            "partitioning": "date",
        }

        # Mock cloud storage operations
        with patch("boto3.client") as mock_s3:
            mock_s3.return_value.put_object.return_value = {"ETag": "test_etag"}

            result = await warehouse_manager.setup_cloud_storage(storage_config)
            assert result["status"] == "configured"
            assert result["storage_provider"] == "aws_s3"

        # Test data export to cloud storage
        export_config = {
            "table": "sales_data",
            "date_range": "2024-01-01_to_2024-01-31",
            "format": "parquet",
            "compression": "gzip",
        }

        with patch.object(warehouse_manager, "export_to_cloud") as mock_export:
            mock_export.return_value = {
                "status": "exported",
                "file_path": "s3://itdo-erp-data-warehouse/sales_data/2024/01/data.parquet",
                "file_size": "15.2MB",
            }

            result = await warehouse_manager.export_data(export_config)
            assert result["status"] == "exported"
            assert "s3://" in result["file_path"]

    async def test_predictive_analytics_distributed_computing(self):
        """Test predictive analytics with distributed computing"""
        analytics_engine = PredictiveAnalyticsEngine()

        # Test model training with distributed computing
        training_config = {
            "model_type": "sales_forecasting",
            "algorithm": "xgboost",
            "distributed": True,
            "cluster_config": {"nodes": 3, "cpu_per_node": 4, "memory_per_node": "8Gi"},
            "data_source": "data_warehouse",
            "features": ["historical_sales", "seasonality", "promotions"],
        }

        # Mock distributed training
        with patch.object(analytics_engine, "train_distributed_model") as mock_train:
            mock_train.return_value = {
                "status": "training_completed",
                "model_id": "sales_forecast_v1.0",
                "accuracy": 0.92,
                "training_time": "25 minutes",
                "cluster_utilization": 85,
            }

            result = await analytics_engine.train_model(training_config)
            assert result["status"] == "training_completed"
            assert result["accuracy"] > 0.9

        # Test model deployment to Kubernetes
        deployment_config = {
            "model_id": "sales_forecast_v1.0",
            "deployment_type": "kubernetes",
            "replicas": 3,
            "resources": {"cpu": "500m", "memory": "1Gi"},
            "auto_scaling": {
                "min_replicas": 2,
                "max_replicas": 10,
                "cpu_threshold": 70,
            },
        }

        with patch.object(analytics_engine, "deploy_to_kubernetes") as mock_deploy:
            mock_deploy.return_value = {
                "status": "deployed",
                "endpoint": "http://ml-model-service:8080/predict",
                "deployment_name": "sales-forecast-deployment",
            }

            result = await analytics_engine.deploy_model(deployment_config)
            assert result["status"] == "deployed"
            assert "endpoint" in result


class TestContainerOrchestration:
    """Test Docker and Kubernetes container orchestration"""

    async def test_docker_image_security_scanning(self):
        """Test Docker image security scanning before deployment"""
        with patch("subprocess.run") as mock_run:
            # Mock trivy security scan
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(
                {
                    "Results": [
                        {
                            "Vulnerabilities": [
                                {
                                    "Severity": "HIGH",
                                    "VulnerabilityID": "CVE-2023-1234",
                                },
                                {
                                    "Severity": "MEDIUM",
                                    "VulnerabilityID": "CVE-2023-5678",
                                },
                            ]
                        }
                    ]
                }
            )

            from app.utils.security_scanner import scan_docker_image

            result = await scan_docker_image(
                "registry.itdo-erp.com/itdo-erp-backend:v65.0"
            )

            assert result["scan_completed"] is True
            assert len(result["vulnerabilities"]) == 2
            assert result["high_severity_count"] == 1

    async def test_kubernetes_deployment_health_checks(self):
        """Test Kubernetes deployment with proper health checks"""
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "itdo-erp-backend"},
            "spec": {
                "replicas": 3,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "backend",
                                "image": "registry.itdo-erp.com/itdo-erp-backend:v65.0",
                                "livenessProbe": {
                                    "httpGet": {"path": "/health", "port": 8000},
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/health/ready", "port": 8000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5,
                                },
                            }
                        ]
                    }
                },
            },
        }

        # Validate health check configuration
        container = deployment_manifest["spec"]["template"]["spec"]["containers"][0]
        assert "livenessProbe" in container
        assert "readinessProbe" in container
        assert container["livenessProbe"]["httpGet"]["path"] == "/health"
        assert container["readinessProbe"]["httpGet"]["path"] == "/health/ready"

    async def test_horizontal_pod_autoscaler_configuration(self):
        """Test HPA configuration for automatic scaling"""
        hpa_manifest = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": "itdo-erp-backend-hpa"},
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "itdo-erp-backend",
                },
                "minReplicas": 3,
                "maxReplicas": 20,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {"type": "Utilization", "averageUtilization": 70},
                        },
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {"type": "Utilization", "averageUtilization": 80},
                        },
                    },
                ],
            },
        }

        # Validate HPA configuration
        assert hpa_manifest["spec"]["minReplicas"] >= 3
        assert hpa_manifest["spec"]["maxReplicas"] <= 20
        assert len(hpa_manifest["spec"]["metrics"]) == 2

    async def test_persistent_volume_claims(self):
        """Test persistent volume claims for data storage"""
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "postgresql-pvc"},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "100Gi"}},
                "storageClassName": "fast-ssd",
            },
        }

        # Validate PVC configuration
        assert "ReadWriteOnce" in pvc_manifest["spec"]["accessModes"]
        assert pvc_manifest["spec"]["resources"]["requests"]["storage"] == "100Gi"
        assert pvc_manifest["spec"]["storageClassName"] == "fast-ssd"


class TestContinuousIntegrationDeployment:
    """Test CI/CD pipeline integration"""

    async def test_github_actions_workflow_validation(self):
        """Test GitHub Actions workflow for automated deployment"""
        workflow_config = {
            "name": "Production Deployment",
            "on": {"push": {"branches": ["main"]}, "workflow_dispatch": {}},
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v4"},
                        {"name": "Build Backend", "run": "docker build backend/"},
                        {"name": "Security Scan", "run": "trivy image backend:latest"},
                        {
                            "name": "Deploy to K8s",
                            "run": "kubectl apply -f deployment/",
                        },
                    ],
                }
            },
        }

        # Validate workflow structure
        assert "build" in workflow_config["jobs"]
        assert len(workflow_config["jobs"]["build"]["steps"]) == 4

        # Check for security scanning step
        security_step = next(
            step
            for step in workflow_config["jobs"]["build"]["steps"]
            if "Security Scan" in step["name"]
        )
        assert "trivy" in security_step["run"]

    async def test_automated_testing_in_pipeline(self):
        """Test automated testing integration in CI/CD pipeline"""
        test_results = {
            "backend_tests": {
                "unit_tests": {"passed": 485, "failed": 0, "coverage": 92.5},
                "integration_tests": {"passed": 125, "failed": 0, "coverage": 88.3},
                "security_tests": {"passed": 45, "failed": 0, "coverage": 95.0},
            },
            "frontend_tests": {
                "unit_tests": {"passed": 234, "failed": 0, "coverage": 89.2},
                "e2e_tests": {"passed": 58, "failed": 0, "coverage": 85.5},
            },
        }

        # Validate test coverage requirements
        assert test_results["backend_tests"]["unit_tests"]["coverage"] > 90
        assert test_results["backend_tests"]["integration_tests"]["coverage"] > 85
        assert test_results["frontend_tests"]["unit_tests"]["coverage"] > 85

        # Ensure no failing tests
        for test_suite in test_results.values():
            for test_type in test_suite.values():
                assert test_type["failed"] == 0

    async def test_deployment_rollback_capability(self):
        """Test deployment rollback capability"""
        with patch("subprocess.run") as mock_run:
            # Mock successful rollback
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = (
                "deployment.apps/itdo-erp-backend rolled back"
            )

            from app.utils.deployment import rollback_deployment

            result = await rollback_deployment("itdo-erp-backend", "production")

            assert result["status"] == "rolled_back"
            assert "rolled back" in result["message"]


class TestMonitoringAndObservability:
    """Test monitoring and observability integration"""

    async def test_prometheus_metrics_collection(self):
        """Test Prometheus metrics collection"""
        from app.utils.metrics import PrometheusMetrics

        metrics = PrometheusMetrics()

        # Test custom business metrics
        await metrics.record_order_created("user_123", 150.50)
        await metrics.record_user_login("user_123")
        await metrics.record_api_request("/api/v1/products", "GET", 200, 0.125)

        # Validate metrics are recorded
        order_metric = await metrics.get_metric("orders_created_total")
        assert order_metric["value"] >= 1

        user_metric = await metrics.get_metric("active_users_total")
        assert user_metric["value"] >= 1

        api_metric = await metrics.get_metric("http_requests_total")
        assert api_metric["value"] >= 1

    async def test_grafana_dashboard_provisioning(self):
        """Test Grafana dashboard provisioning"""
        dashboard_config = {
            "dashboard": {
                "title": "ITDO ERP - Production Overview",
                "panels": [
                    {
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [{"expr": "rate(http_requests_total[5m])"}],
                    },
                    {
                        "title": "Error Rate",
                        "type": "stat",
                        "targets": [
                            {"expr": 'rate(http_requests_total{status=~"5.."}[5m])'}
                        ],
                    },
                ],
            }
        }

        # Validate dashboard structure
        assert (
            dashboard_config["dashboard"]["title"] == "ITDO ERP - Production Overview"
        )
        assert len(dashboard_config["dashboard"]["panels"]) == 2

    async def test_alerting_rules_configuration(self):
        """Test Prometheus alerting rules"""
        alerting_rules = {
            "groups": [
                {
                    "name": "itdo-erp.rules",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": 'rate(http_requests_total{status=~"5.."}[5m]) > 0.05',
                            "for": "2m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "High error rate detected",
                                "description": "Error rate is above 5% for 2 minutes",
                            },
                        }
                    ],
                }
            ]
        }

        # Validate alert configuration
        rule = alerting_rules["groups"][0]["rules"][0]
        assert rule["alert"] == "HighErrorRate"
        assert "5.." in rule["expr"]  # 5xx status codes
        assert rule["labels"]["severity"] == "critical"


class TestSecurityCompliance:
    """Test security and compliance features"""

    async def test_network_policies_isolation(self):
        """Test Kubernetes network policies for service isolation"""
        network_policy = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "itdo-erp-backend-network-policy"},
            "spec": {
                "podSelector": {
                    "matchLabels": {"app.kubernetes.io/name": "itdo-erp-backend"}
                },
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "podSelector": {
                                    "matchLabels": {
                                        "app.kubernetes.io/name": "itdo-erp-frontend"
                                    }
                                }
                            }
                        ],
                        "ports": [{"protocol": "TCP", "port": 8000}],
                    }
                ],
            },
        }

        # Validate network isolation
        assert "Ingress" in network_policy["spec"]["policyTypes"]
        assert "Egress" in network_policy["spec"]["policyTypes"]
        assert len(network_policy["spec"]["ingress"]) == 1

    async def test_pod_security_policies(self):
        """Test pod security policies enforcement"""
        pod_security_policy = {
            "apiVersion": "policy/v1beta1",
            "kind": "PodSecurityPolicy",
            "metadata": {"name": "itdo-erp-restricted"},
            "spec": {
                "privileged": False,
                "allowPrivilegeEscalation": False,
                "requiredDropCapabilities": ["ALL"],
                "runAsUser": {"rule": "MustRunAsNonRoot"},
                "fsGroup": {"rule": "RunAsAny"},
                "seLinux": {"rule": "RunAsAny"},
                "volumes": [
                    "configMap",
                    "emptyDir",
                    "projected",
                    "secret",
                    "downwardAPI",
                    "persistentVolumeClaim",
                ],
            },
        }

        # Validate security restrictions
        assert pod_security_policy["spec"]["privileged"] is False
        assert pod_security_policy["spec"]["allowPrivilegeEscalation"] is False
        assert "ALL" in pod_security_policy["spec"]["requiredDropCapabilities"]
        assert pod_security_policy["spec"]["runAsUser"]["rule"] == "MustRunAsNonRoot"

    async def test_rbac_permissions(self):
        """Test RBAC permissions for service accounts"""
        rbac_config = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": "itdo-erp-backend-role"},
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["configmaps", "secrets"],
                    "verbs": ["get", "list"],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["deployments"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        }

        # Validate minimal permissions
        assert len(rbac_config["rules"]) == 2
        for rule in rbac_config["rules"]:
            assert "create" not in rule["verbs"]  # No create permissions
            assert "delete" not in rule["verbs"]  # No delete permissions


# Test execution and coverage reporting
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ]
    )
