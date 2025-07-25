"""
Tests for API Integration Platform - CC02 v64.0 Day 9
Comprehensive test suite for API gateway, external integrations, webhooks, and data synchronization
"""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.api_integration import (
    APIGateway,
    ExternalIntegration,
    DataSyncJob,
    WebhookEndpoint,
    WebhookDelivery,
    APIKey,
    APIUsageLog,
    DataMapping,
    IntegrationHealth,
    IntegrationType,
    AuthenticationType,
    ConnectionStatus,
    SyncDirection,
    SyncStatus,
    WebhookStatus,
)
from app.schemas.api_integration import (
    APIGatewayCreate,
    ExternalIntegrationCreate,
    WebhookEndpointCreate,
    APIKeyCreate,
    DataMappingCreate,
    IntegrationHealthCheck,
)
from app.services.api_integration_service import (
    APIGatewayService,
    ExternalIntegrationService,
    WebhookService,
    APIKeyService,
    IntegrationHealthService,
)


class TestAPIGatewayService:
    """Test suite for API Gateway service."""
    
    @pytest.fixture
    async def gateway_service(self, db_session: AsyncSession):
        """Create API gateway service instance."""
        return APIGatewayService(db_session)
    
    @pytest.fixture
    async def sample_gateway_data(self):
        """Create sample gateway data for testing."""
        return APIGatewayCreate(
            name="Test API Gateway",
            description="Test gateway for integration testing",
            base_url="https://api.test.com",
            public_url="https://public.api.test.com",
            supported_protocols=["https", "http"],
            default_protocol="https",
            authentication_required=True,
            default_auth_type=AuthenticationType.API_KEY,
            cors_enabled=True,
            cors_origins=["https://app.test.com"],
            rate_limit_enabled=True,
            default_rate_limit=1000,
            burst_limit=100
        )
    
    async def test_create_gateway(
        self,
        gateway_service: APIGatewayService,
        sample_gateway_data: APIGatewayCreate,
        test_organization
    ):
        """Test creating API gateway."""
        gateway = await gateway_service.create_gateway(
            sample_gateway_data, test_organization.id, "user-001"
        )
        
        assert gateway.name == "Test API Gateway"
        assert gateway.base_url == "https://api.test.com"
        assert gateway.organization_id == test_organization.id
        assert gateway.status == ConnectionStatus.ACTIVE
        assert gateway.gateway_id.startswith("gw_")
    
    async def test_get_gateway(
        self,
        gateway_service: APIGatewayService,
        sample_gateway_data: APIGatewayCreate,
        test_organization
    ):
        """Test getting API gateway by ID."""
        created_gateway = await gateway_service.create_gateway(
            sample_gateway_data, test_organization.id, "user-001"
        )
        
        retrieved_gateway = await gateway_service.get_gateway(
            created_gateway.gateway_id, test_organization.id
        )
        
        assert retrieved_gateway is not None
        assert retrieved_gateway.id == created_gateway.id
        assert retrieved_gateway.name == created_gateway.name
    
    async def test_list_gateways(
        self,
        gateway_service: APIGatewayService,
        sample_gateway_data: APIGatewayCreate,
        test_organization
    ):
        """Test listing API gateways."""
        # Create multiple gateways
        gateway1 = await gateway_service.create_gateway(
            sample_gateway_data, test_organization.id, "user-001"
        )
        
        gateway2_data = sample_gateway_data.model_copy()
        gateway2_data.name = "Test Gateway 2"
        gateway2_data.base_url = "https://api2.test.com"
        
        gateway2 = await gateway_service.create_gateway(
            gateway2_data, test_organization.id, "user-001"
        )
        
        gateways = await gateway_service.list_gateways(test_organization.id)
        
        assert len(gateways) >= 2
        gateway_names = [g.name for g in gateways]
        assert "Test API Gateway" in gateway_names
        assert "Test Gateway 2" in gateway_names
    
    @patch('httpx.AsyncClient.get')
    async def test_health_check_gateway_success(
        self,
        mock_get,
        gateway_service: APIGatewayService,
        sample_gateway_data: APIGatewayCreate,
        test_organization
    ):
        """Test successful gateway health check."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_get.return_value = mock_response
        
        gateway = await gateway_service.create_gateway(
            sample_gateway_data, test_organization.id, "user-001"
        )
        
        health_data = await gateway_service.health_check_gateway(
            gateway.gateway_id, test_organization.id
        )
        
        assert health_data["status"] == "healthy"
        assert health_data["response_time_ms"] == 150.0
        assert health_data["status_code"] == 200
    
    @patch('httpx.AsyncClient.get')
    async def test_health_check_gateway_failure(
        self,
        mock_get,
        gateway_service: APIGatewayService,
        sample_gateway_data: APIGatewayCreate,
        test_organization
    ):
        """Test failed gateway health check."""
        # Mock failed HTTP response
        mock_get.side_effect = Exception("Connection timeout")
        
        gateway = await gateway_service.create_gateway(
            sample_gateway_data, test_organization.id, "user-001"
        )
        
        health_data = await gateway_service.health_check_gateway(
            gateway.gateway_id, test_organization.id
        )
        
        assert health_data["status"] == "error"
        assert "Connection timeout" in health_data["error"]


class TestExternalIntegrationService:
    """Test suite for External Integration service."""
    
    @pytest.fixture
    async def integration_service(self, db_session: AsyncSession):
        """Create external integration service instance."""
        return ExternalIntegrationService(db_session)
    
    @pytest.fixture
    async def sample_integration_data(self):
        """Create sample integration data for testing."""
        return ExternalIntegrationCreate(
            name="Salesforce CRM",
            description="Integration with Salesforce CRM system",
            integration_type=IntegrationType.REST_API,
            provider="salesforce",
            endpoint_url="https://api.salesforce.com/v1",
            auth_type=AuthenticationType.OAUTH2,
            auth_config={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "scope": "api"
            },
            sync_enabled=True,
            sync_direction=SyncDirection.BIDIRECTIONAL,
            sync_frequency_minutes=60
        )
    
    async def test_create_integration(
        self,
        integration_service: ExternalIntegrationService,
        sample_integration_data: ExternalIntegrationCreate,
        test_organization
    ):
        """Test creating external integration."""
        integration = await integration_service.create_integration(
            sample_integration_data, test_organization.id, "user-001"
        )
        
        assert integration.name == "Salesforce CRM"
        assert integration.integration_type == IntegrationType.REST_API
        assert integration.provider == "salesforce"
        assert integration.organization_id == test_organization.id
        assert integration.integration_id.startswith("int_")
    
    async def test_get_integration(
        self,
        integration_service: ExternalIntegrationService,
        sample_integration_data: ExternalIntegrationCreate,
        test_organization
    ):
        """Test getting external integration by ID."""
        created_integration = await integration_service.create_integration(
            sample_integration_data, test_organization.id, "user-001"
        )
        
        retrieved_integration = await integration_service.get_integration(
            created_integration.integration_id, test_organization.id
        )
        
        assert retrieved_integration is not None
        assert retrieved_integration.id == created_integration.id
        assert retrieved_integration.name == created_integration.name
    
    @patch('httpx.AsyncClient.get')
    async def test_test_integration_connection_success(
        self,
        mock_get,
        integration_service: ExternalIntegrationService,
        sample_integration_data: ExternalIntegrationCreate,
        test_organization
    ):
        """Test successful integration connection test."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.25
        mock_get.return_value = mock_response
        
        integration = await integration_service.create_integration(
            sample_integration_data, test_organization.id, "user-001"
        )
        
        connection_data = await integration_service.test_integration_connection(
            integration.integration_id, test_organization.id
        )
        
        assert connection_data["status"] == "connected"
        assert connection_data["response_time_ms"] == 250.0
        assert connection_data["status_code"] == 200
    
    async def test_trigger_sync_job(
        self,
        integration_service: ExternalIntegrationService,
        sample_integration_data: ExternalIntegrationCreate,
        test_organization
    ):
        """Test triggering data synchronization job."""
        integration = await integration_service.create_integration(
            sample_integration_data, test_organization.id, "user-001"
        )
        
        sync_job = await integration_service.trigger_sync_job(
            integration.integration_id,
            test_organization.id,
            "Test Sync Job",
            SyncDirection.INBOUND,
            {"entity_type": "contacts", "limit": 1000}
        )
        
        assert sync_job.job_name == "Test Sync Job"
        assert sync_job.sync_direction == SyncDirection.INBOUND
        assert sync_job.integration_id == integration.id
        assert sync_job.status == SyncStatus.PENDING
        assert sync_job.job_id.startswith("sync_")


class TestWebhookService:
    """Test suite for Webhook service."""
    
    @pytest.fixture
    async def webhook_service(self, db_session: AsyncSession):
        """Create webhook service instance."""
        return WebhookService(db_session)
    
    @pytest.fixture
    async def sample_webhook_data(self):
        """Create sample webhook data for testing."""
        return WebhookEndpointCreate(
            name="Order Created Webhook",
            description="Webhook triggered when a new order is created",
            endpoint_url="https://external.system.com/webhooks/order-created",
            http_method="POST",
            content_type="application/json",
            trigger_events=["order.created", "order.updated"],
            auth_type=AuthenticationType.BEARER_TOKEN,
            auth_config={"token": "webhook_secret_token"},
            custom_headers={"X-Source": "ERP-System"},
            timeout_seconds=30,
            retry_enabled=True,
            max_retries=3
        )
    
    async def test_create_webhook(
        self,
        webhook_service: WebhookService,
        sample_webhook_data: WebhookEndpointCreate,
        test_organization
    ):
        """Test creating webhook endpoint."""
        webhook = await webhook_service.create_webhook(
            sample_webhook_data, test_organization.id, "user-001"
        )
        
        assert webhook.name == "Order Created Webhook"
        assert webhook.endpoint_url == "https://external.system.com/webhooks/order-created"
        assert webhook.organization_id == test_organization.id
        assert webhook.webhook_id.startswith("wh_")
        assert webhook.secret_key is not None  # Should be auto-generated
    
    async def test_get_webhook(
        self,
        webhook_service: WebhookService,
        sample_webhook_data: WebhookEndpointCreate,
        test_organization
    ):
        """Test getting webhook endpoint by ID."""
        created_webhook = await webhook_service.create_webhook(
            sample_webhook_data, test_organization.id, "user-001"
        )
        
        retrieved_webhook = await webhook_service.get_webhook(
            created_webhook.webhook_id, test_organization.id
        )
        
        assert retrieved_webhook is not None
        assert retrieved_webhook.id == created_webhook.id
        assert retrieved_webhook.name == created_webhook.name
    
    @patch('httpx.AsyncClient.request')
    async def test_deliver_webhook_success(
        self,
        mock_request,
        webhook_service: WebhookService,
        sample_webhook_data: WebhookEndpointCreate,
        test_organization
    ):
        """Test successful webhook delivery."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"status": "received"}'
        mock_request.return_value = mock_response
        
        webhook = await webhook_service.create_webhook(
            sample_webhook_data, test_organization.id, "user-001"
        )
        
        delivery = await webhook_service.deliver_webhook(
            webhook.webhook_id,
            test_organization.id,
            "order.created",
            "order-123",
            {"order_id": "123", "amount": 99.99}
        )
        
        assert delivery.event_type == "order.created"
        assert delivery.event_id == "order-123"
        assert delivery.delivery_id.startswith("del_")
        assert delivery.request_payload == {"order_id": "123", "amount": 99.99}
    
    @patch('httpx.AsyncClient.request')
    async def test_deliver_webhook_failure(
        self,
        mock_request,
        webhook_service: WebhookService,
        sample_webhook_data: WebhookEndpointCreate,
        test_organization
    ):
        """Test failed webhook delivery."""
        # Mock failed HTTP request
        mock_request.side_effect = Exception("Connection refused")
        
        webhook = await webhook_service.create_webhook(
            sample_webhook_data, test_organization.id, "user-001"
        )
        
        delivery = await webhook_service.deliver_webhook(
            webhook.webhook_id,
            test_organization.id,
            "order.created",
            "order-123",
            {"order_id": "123", "amount": 99.99}
        )
        
        assert delivery.event_type == "order.created"
        assert delivery.delivery_id.startswith("del_")


class TestAPIKeyService:
    """Test suite for API Key service."""
    
    @pytest.fixture
    async def api_key_service(self, db_session: AsyncSession):
        """Create API key service instance."""
        return APIKeyService(db_session)
    
    @pytest.fixture
    async def sample_gateway(self, db_session: AsyncSession, test_organization):
        """Create sample API gateway for testing."""
        gateway = APIGateway(
            gateway_id="gw_test123",
            organization_id=test_organization.id,
            name="Test Gateway",
            base_url="https://api.test.com",
            supported_protocols=["https"],
            created_by="user-001"
        )
        db_session.add(gateway)
        await db_session.commit()
        await db_session.refresh(gateway)
        return gateway
    
    @pytest.fixture
    async def sample_api_key_data(self, sample_gateway):
        """Create sample API key data for testing."""
        return APIKeyCreate(
            gateway_id=sample_gateway.id,
            name="Test API Key",
            description="API key for testing purposes",
            key_prefix="tk",
            scopes=["read", "write"],
            permissions={"orders": ["read", "write"], "customers": ["read"]},
            rate_limit_requests=1000,
            rate_limit_window_seconds=3600,
            owner_type="user",
            owner_id="user-001"
        )
    
    async def test_create_api_key(
        self,
        api_key_service: APIKeyService,
        sample_api_key_data: APIKeyCreate,
        test_organization
    ):
        """Test creating API key."""
        api_key = await api_key_service.create_api_key(
            sample_api_key_data, test_organization.id, "user-001"
        )
        
        assert api_key.name == "Test API Key"
        assert api_key.key_value.startswith("tk_")
        assert api_key.scopes == ["read", "write"]
        assert api_key.organization_id == test_organization.id
        assert api_key.key_id.startswith("ak_")
        assert api_key.is_active is True
    
    async def test_get_api_key(
        self,
        api_key_service: APIKeyService,
        sample_api_key_data: APIKeyCreate,
        test_organization
    ):
        """Test getting API key by value."""
        created_key = await api_key_service.create_api_key(
            sample_api_key_data, test_organization.id, "user-001"
        )
        
        retrieved_key = await api_key_service.get_api_key(created_key.key_value)
        
        assert retrieved_key is not None
        assert retrieved_key.id == created_key.id
        assert retrieved_key.name == created_key.name
    
    async def test_validate_api_key_with_scopes(
        self,
        api_key_service: APIKeyService,
        sample_api_key_data: APIKeyCreate,
        test_organization
    ):
        """Test validating API key with required scopes."""
        created_key = await api_key_service.create_api_key(
            sample_api_key_data, test_organization.id, "user-001"
        )
        
        # Test with valid scopes
        validated_key = await api_key_service.validate_api_key(
            created_key.key_value, ["read"]
        )
        assert validated_key is not None
        
        # Test with invalid scopes
        invalid_key = await api_key_service.validate_api_key(
            created_key.key_value, ["admin"]
        )
        assert invalid_key is None
    
    async def test_rotate_api_key(
        self,
        api_key_service: APIKeyService,
        sample_api_key_data: APIKeyCreate,
        test_organization
    ):
        """Test rotating API key."""
        created_key = await api_key_service.create_api_key(
            sample_api_key_data, test_organization.id, "user-001"
        )
        
        original_key_value = created_key.key_value
        
        rotated_key = await api_key_service.rotate_api_key(
            created_key.key_id, test_organization.id
        )
        
        assert rotated_key.key_value != original_key_value
        assert rotated_key.key_value.startswith("tk_")
        assert rotated_key.last_rotation_at is not None
    
    async def test_log_api_usage(
        self,
        api_key_service: APIKeyService,
        sample_api_key_data: APIKeyCreate,
        test_organization
    ):
        """Test logging API usage."""
        created_key = await api_key_service.create_api_key(
            sample_api_key_data, test_organization.id, "user-001"
        )
        
        usage_log = await api_key_service.log_api_usage(
            api_key=created_key,
            request_id="req-123",
            method="GET",
            endpoint="/api/v1/orders",
            path="/api/v1/orders?limit=10",
            client_ip="192.168.1.100",
            status_code=200,
            response_time_ms=150,
            organization_id=test_organization.id,
            user_id="user-001"
        )
        
        assert usage_log.request_id == "req-123"
        assert usage_log.method == "GET"
        assert usage_log.endpoint == "/api/v1/orders"
        assert usage_log.status_code == 200
        assert usage_log.response_time_ms == 150
        assert usage_log.log_id.startswith("log_")


class TestIntegrationHealthService:
    """Test suite for Integration Health service."""
    
    @pytest.fixture
    async def health_service(self, db_session: AsyncSession):
        """Create integration health service instance."""
        return IntegrationHealthService(db_session)
    
    @pytest.fixture
    async def sample_integration(self, db_session: AsyncSession, test_organization):
        """Create sample integration for health testing."""
        integration = ExternalIntegration(
            integration_id="int_health_test",
            organization_id=test_organization.id,
            name="Health Test Integration",
            integration_type=IntegrationType.REST_API,
            provider="test_provider",
            endpoint_url="https://api.healthtest.com",
            auth_type=AuthenticationType.NONE,
            auth_config={},
            created_by="user-001"
        )
        db_session.add(integration)
        await db_session.commit()
        await db_session.refresh(integration)
        return integration
    
    @patch('httpx.AsyncClient.get')
    async def test_perform_health_check_success(
        self,
        mock_get,
        health_service: IntegrationHealthService,
        sample_integration: ExternalIntegration,
        test_organization
    ):
        """Test successful integration health check."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        health_check = await health_service.perform_health_check(
            sample_integration.integration_id,
            test_organization.id,
            "connectivity"
        )
        
        assert health_check.integration_id == sample_integration.integration_id
        assert health_check.is_healthy is True
        assert health_check.connection_successful is True
        assert health_check.health_score > 0
        assert health_check.health_id.startswith("health_")
    
    @patch('httpx.AsyncClient.get')
    async def test_perform_health_check_failure(
        self,
        mock_get,
        health_service: IntegrationHealthService,
        sample_integration: ExternalIntegration,
        test_organization
    ):
        """Test failed integration health check."""
        # Mock failed HTTP request
        mock_get.side_effect = Exception("Connection timeout")
        
        health_check = await health_service.perform_health_check(
            sample_integration.integration_id,
            test_organization.id,
            "connectivity"
        )
        
        assert health_check.integration_id == sample_integration.integration_id
        assert health_check.is_healthy is False
        assert health_check.connection_successful is False
        assert health_check.health_score == 0.0
        assert len(health_check.issues_detected) > 0
        assert health_check.severity_level == "critical"
    
    async def test_get_integration_health_summary(
        self,
        health_service: IntegrationHealthService,
        sample_integration: ExternalIntegration,
        test_organization,
        db_session: AsyncSession
    ):
        """Test getting integration health summary."""
        # Create some health check records
        health1 = IntegrationHealth(
            health_id="h1",
            integration_id=sample_integration.integration_id,
            organization_id=test_organization.id,
            check_timestamp=datetime.now(),
            check_type="connectivity",
            is_healthy=True,
            health_score=95.0,
            connection_successful=True,
            severity_level="info"
        )
        
        health2 = IntegrationHealth(
            health_id="h2",
            integration_id=sample_integration.integration_id,
            organization_id=test_organization.id,
            check_timestamp=datetime.now(),
            check_type="connectivity",
            is_healthy=False,
            health_score=30.0,
            connection_successful=False,
            severity_level="critical",
            issues_detected=["Connection timeout"]
        )
        
        db_session.add(health1)
        db_session.add(health2)
        await db_session.commit()
        
        summary = await health_service.get_integration_health_summary(
            test_organization.id, 7
        )
        
        assert summary["total_integrations"] >= 1
        assert "healthy_integrations" in summary
        assert "unhealthy_integrations" in summary
        assert "average_health_score" in summary
        assert "critical_issues" in summary


class TestAPIIntegrationEndpoints:
    """Test suite for API Integration endpoints."""
    
    async def test_create_api_gateway_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test API gateway creation endpoint."""
        gateway_data = {
            "name": "Test Gateway API",
            "description": "Gateway created via API",
            "base_url": "https://api.test-endpoint.com",
            "supported_protocols": ["https"],
            "authentication_required": True,
            "default_auth_type": "api_key",
            "rate_limit_enabled": True,
            "default_rate_limit": 1000
        }
        
        response = await async_client.post(
            "/api/v1/api-integration/gateways",
            json=gateway_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Gateway API"
        assert data["base_url"] == "https://api.test-endpoint.com"
        assert data["gateway_id"].startswith("gw_")
    
    async def test_list_api_gateways_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test API gateway listing endpoint."""
        response = await async_client.get(
            "/api/v1/api-integration/gateways",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_create_external_integration_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test external integration creation endpoint."""
        integration_data = {
            "name": "Test External Integration",
            "description": "Integration created via API",
            "integration_type": "rest_api",
            "provider": "test_provider",
            "endpoint_url": "https://external.api.test.com",
            "auth_type": "api_key",
            "auth_config": {"api_key": "test_key"},
            "sync_enabled": True,
            "sync_direction": "bidirectional"
        }
        
        response = await async_client.post(
            "/api/v1/api-integration/integrations",
            json=integration_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test External Integration"
        assert data["integration_type"] == "rest_api"
        assert data["integration_id"].startswith("int_")
    
    async def test_create_webhook_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test webhook endpoint creation."""
        webhook_data = {
            "name": "Test Webhook",
            "description": "Webhook created via API",
            "endpoint_url": "https://webhook.test.com/receive",
            "http_method": "POST",
            "trigger_events": ["order.created", "order.updated"],
            "auth_type": "none",
            "timeout_seconds": 30,
            "retry_enabled": True,
            "max_retries": 3
        }
        
        response = await async_client.post(
            "/api/v1/api-integration/webhooks",
            json=webhook_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Webhook"
        assert data["endpoint_url"] == "https://webhook.test.com/receive"
        assert data["webhook_id"].startswith("wh_")
    
    async def test_health_check_endpoint(
        self,
        async_client: AsyncClient
    ):
        """Test API integration platform health check."""
        response = await async_client.get("/api/v1/api-integration/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "CC02 v64.0"
        assert data["system"] == "API Integration Platform"
    
    async def test_metrics_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test system metrics endpoint."""
        response = await async_client.get(
            "/api/v1/api-integration/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "active_gateways" in data
        assert "total_integrations" in data
        assert "total_webhooks" in data
        assert "requests_today" in data
    
    async def test_usage_analytics_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test usage analytics endpoint."""
        response = await async_client.get(
            "/api/v1/api-integration/analytics/usage?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert "total_requests" in data
        assert "success_rate" in data
        assert "top_integrations" in data


# Performance and Load Testing
class TestPerformance:
    """Performance tests for API integration platform."""
    
    @pytest.mark.asyncio
    async def test_bulk_webhook_delivery_performance(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test performance of bulk webhook deliveries."""
        import time
        
        # Create webhook endpoint first
        webhook_data = {
            "name": "Performance Test Webhook",
            "endpoint_url": "https://httpbin.org/post",
            "trigger_events": ["test.event"],
            "auth_type": "none"
        }
        
        webhook_response = await async_client.post(
            "/api/v1/api-integration/webhooks",
            json=webhook_data,
            headers=auth_headers
        )
        webhook_id = webhook_response.json()["webhook_id"]
        
        # Perform bulk deliveries
        delivery_data = {
            "event_type": "test.event",
            "event_id": "bulk-test",
            "payload": {"test": True, "batch_size": 100}
        }
        
        start_time = time.time()
        
        # Simulate 50 concurrent webhook deliveries
        tasks = []
        for i in range(50):
            delivery_data["event_id"] = f"bulk-test-{i}"
            tasks.append(
                async_client.post(
                    f"/api/v1/api-integration/webhooks/{webhook_id}/deliver",
                    json=delivery_data,
                    headers=auth_headers
                )
            )
        
        # Execute all deliveries concurrently
        import asyncio
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance - should complete within 30 seconds
        assert processing_time < 30.0, f"Bulk webhook delivery took {processing_time} seconds, should be < 30"
        
        # Count successful deliveries
        successful_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert successful_count >= 40, f"Only {successful_count} out of 50 deliveries were successful"


# Integration Tests
class TestIntegration:
    """Integration tests for complete API integration workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_integration_workflow(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test complete API integration workflow."""
        # 1. Create API Gateway
        gateway_service = APIGatewayService(db_session)
        gateway_data = APIGatewayCreate(
            name="Integration Test Gateway",
            base_url="https://api.integration-test.com",
            supported_protocols=["https"],
            authentication_required=True
        )
        gateway = await gateway_service.create_gateway(
            gateway_data, test_organization.id, "user-001"
        )
        
        # 2. Create External Integration
        integration_service = ExternalIntegrationService(db_session)
        integration_data = ExternalIntegrationCreate(
            name="Test CRM Integration",
            integration_type=IntegrationType.REST_API,
            provider="test_crm",
            endpoint_url="https://crm.test.com/api",
            auth_type=AuthenticationType.API_KEY,
            auth_config={"api_key": "test_key"},
            gateway_id=gateway.id
        )
        integration = await integration_service.create_integration(
            integration_data, test_organization.id, "user-001"
        )
        
        # 3. Create Webhook
        webhook_service = WebhookService(db_session)
        webhook_data = WebhookEndpointCreate(
            name="CRM Integration Webhook",
            endpoint_url="https://webhook.test.com/crm",
            trigger_events=["contact.created"],
            auth_type=AuthenticationType.NONE,
            integration_id=integration.id
        )
        webhook = await webhook_service.create_webhook(
            webhook_data, test_organization.id, "user-001"
        )
        
        # 4. Create API Key
        api_key_service = APIKeyService(db_session)
        api_key_data = APIKeyCreate(
            gateway_id=gateway.id,
            name="Integration Test Key",
            scopes=["read", "write"],
            permissions={"contacts": ["read", "write"]},
            owner_type="integration",
            owner_id=integration.integration_id
        )
        api_key = await api_key_service.create_api_key(
            api_key_data, test_organization.id, "user-001"
        )
        
        # 5. Trigger Sync Job
        sync_job = await integration_service.trigger_sync_job(
            integration.integration_id,
            test_organization.id,
            "Integration Test Sync",
            SyncDirection.BIDIRECTIONAL,
            {"entity_type": "contacts"}
        )
        
        # 6. Perform Health Check
        health_service = IntegrationHealthService(db_session)
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            health_check = await health_service.perform_health_check(
                integration.integration_id, test_organization.id
            )
        
        # Verify complete workflow
        assert gateway.gateway_id.startswith("gw_")
        assert integration.integration_id.startswith("int_")
        assert webhook.webhook_id.startswith("wh_")
        assert api_key.key_id.startswith("ak_")
        assert sync_job.job_id.startswith("sync_")
        assert health_check.health_id.startswith("health_")
        
        # Verify relationships
        assert integration.gateway_id == gateway.id
        assert webhook.integration_id == integration.id
        assert api_key.gateway_id == gateway.id


# Fixtures
@pytest.fixture
async def test_organization(db_session: AsyncSession):
    """Create test organization."""
    from app.models.organization import Organization
    
    org = Organization(
        name="API Integration Test Org",
        code="APITEST",
        created_by=1
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test-integration-token"}


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client