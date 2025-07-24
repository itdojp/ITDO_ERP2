"""
Integration System API Tests - CC02 v31.0 Phase 2

Comprehensive test suite for integration API including:
- External System Integration & API Management
- Data Synchronization & ETL Pipelines
- Third-Party Service Connectors
- Webhook & Event-Driven Integration
- API Gateway & Rate Limiting
- Data Transformation & Mapping
- Integration Monitoring & Health Checks
- Message Queuing & Async Processing
- Authentication & Security Management
- Integration Analytics & Performance Tracking
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.integration_extended import (
    DataMapping,
    DataTransformation,
    ExternalSystem,
    IntegrationConnector,
    IntegrationExecution,
    IntegrationMessage,
    SyncStatus,
    WebhookEndpoint,
)

client = TestClient(app)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def sample_external_system_data():
    """Sample external system data for testing."""
    return {
        "organization_id": "test-org-123",
        "name": "Salesforce CRM",
        "code": "SALESFORCE_CRM",
        "description": "Salesforce CRM integration",
        "integration_type": "api",
        "base_url": "https://api.salesforce.com",
        "api_version": "v1",
        "endpoint_prefix": "/services/data",
        "connection_config": {"host": "api.salesforce.com", "port": 443, "ssl": True},
        "auth_type": "oauth2",
        "auth_config": {"client_id": "test_client_id", "scope": "api"},
        "credentials": {"access_token": "test_token"},
        "rate_limit_requests": 1000,
        "rate_limit_period": 3600,
        "timeout_seconds": 30,
        "retry_attempts": 3,
        "is_active": True,
        "vendor": "Salesforce",
        "version": "v55.0",
        "created_by": "user-123",
    }


@pytest.fixture
def sample_connector_data():
    """Sample connector data for testing."""
    return {
        "organization_id": "test-org-123",
        "external_system_id": "system-123",
        "name": "Contact Sync Connector",
        "code": "CONTACT_SYNC",
        "description": "Synchronize contacts from Salesforce",
        "operation_type": "read",
        "endpoint_url": "https://api.salesforce.com/services/data/v55.0/sobjects/Contact",
        "http_method": "GET",
        "request_headers": {"Accept": "application/json"},
        "request_parameters": {"limit": "1000"},
        "data_format": "json",
        "sync_direction": "inbound",
        "entity_type": "contacts",
        "is_scheduled": True,
        "schedule_cron": "0 */6 * * *",
        "batch_size": 100,
        "parallel_workers": 1,
        "timeout_seconds": 300,
        "max_retries": 3,
        "is_active": True,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_data_mapping_data():
    """Sample data mapping data for testing."""
    return {
        "organization_id": "test-org-123",
        "connector_id": "connector-123",
        "name": "Contact Field Mapping",
        "description": "Map Salesforce contact fields to internal format",
        "entity_type": "contacts",
        "sync_direction": "inbound",
        "source_schema": {
            "Id": "string",
            "FirstName": "string",
            "LastName": "string",
            "Email": "string",
        },
        "target_schema": {
            "id": "string",
            "first_name": "string",
            "last_name": "string",
            "email": "string",
        },
        "field_mappings": {
            "Id": "id",
            "FirstName": "first_name",
            "LastName": "last_name",
            "Email": "email",
        },
        "transformation_rules": [
            {"field": "email", "type": "validation", "rule": "email_format"}
        ],
        "validation_rules": {
            "required_fields": ["id", "email"],
            "unique_fields": ["id", "email"],
        },
        "enable_validation": True,
        "use_bulk_operations": True,
        "chunk_size": 1000,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_transformation_data():
    """Sample transformation data for testing."""
    return {
        "organization_id": "test-org-123",
        "connector_id": "connector-123",
        "name": "Contact Name Transformation",
        "description": "Transform contact names to proper case",
        "transformation_type": "data_conversion",
        "input_schema": {"first_name": "string", "last_name": "string"},
        "output_schema": {
            "first_name": "string",
            "last_name": "string",
            "full_name": "string",
        },
        "transformation_script": """
def transform(data):
    data['first_name'] = data['first_name'].title()
    data['last_name'] = data['last_name'].title()
    data['full_name'] = f"{data['first_name']} {data['last_name']}"
    return data
        """,
        "transformation_config": {"case_style": "title"},
        "language": "python",
        "execution_timeout": 300,
        "memory_limit_mb": 512,
        "error_handling_strategy": "skip",
        "max_error_rate": 5.0,
        "is_active": True,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_webhook_data():
    """Sample webhook data for testing."""
    return {
        "organization_id": "test-org-123",
        "name": "Salesforce Webhook",
        "description": "Webhook for Salesforce notifications",
        "endpoint_url": "/webhooks/salesforce",
        "allowed_methods": ["POST"],
        "content_types": ["application/json"],
        "max_body_size_mb": 10,
        "enable_signature_verification": True,
        "allowed_ips": ["127.0.0.1"],
        "require_authentication": False,
        "rate_limit_per_minute": 100,
        "processing_script": "print('Webhook received')",
        "processing_config": {"action": "log_and_forward"},
        "enable_async_processing": True,
        "response_template": '{"status": "received"}',
        "success_status_code": 200,
        "is_active": True,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "organization_id": "test-org-123",
        "message_type": "data_sync",
        "payload": {
            "action": "sync_contacts",
            "connector_id": "connector-123",
            "batch_size": 100,
        },
        "headers": {"Content-Type": "application/json"},
        "source_system": "salesforce",
        "target_system": "internal",
        "routing_key": "sync.contacts",
        "queue_name": "integration_queue",
        "priority": 5,
        "max_attempts": 3,
        "processing_timeout": 300,
        "delay_seconds": 0,
    }


# =============================================================================
# External System API Tests
# =============================================================================


class TestExternalSystemAPI:
    """Test cases for external system API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_external_system")
    def test_create_external_system_success(
        self, mock_create, sample_external_system_data
    ):
        """Test successful external system creation."""
        # Mock service response
        mock_system = ExternalSystem(**sample_external_system_data)
        mock_system.id = "system-123"
        mock_system.created_at = datetime.now()
        mock_create.return_value = mock_system

        response = client.post(
            "/api/v1/integration_v31/external-systems", json=sample_external_system_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "system-123"
        assert response.json()["name"] == "Salesforce CRM"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.create_external_system")
    def test_create_external_system_validation_error(
        self, mock_create, sample_external_system_data
    ):
        """Test external system creation with validation error."""
        mock_create.side_effect = ValueError("Duplicate system code")

        response = client.post(
            "/api/v1/integration_v31/external-systems", json=sample_external_system_data
        )

        assert response.status_code == 400
        assert "Duplicate system code" in response.json()["detail"]

    @patch("app.crud.integration_v31.integration_service.list_external_systems")
    def test_list_external_systems_success(self, mock_list):
        """Test successful external system listing."""
        mock_list.return_value = {
            "external_systems": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/external-systems?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.get_external_system")
    def test_get_external_system_success(self, mock_get, sample_external_system_data):
        """Test successful external system retrieval."""
        mock_system = ExternalSystem(**sample_external_system_data)
        mock_system.id = "system-123"
        mock_get.return_value = mock_system

        response = client.get("/api/v1/integration_v31/external-systems/system-123")

        assert response.status_code == 200
        assert response.json()["id"] == "system-123"
        mock_get.assert_called_once_with(mock_get.call_args[0][0], "system-123")

    @patch("app.crud.integration_v31.integration_service.get_external_system")
    def test_get_external_system_not_found(self, mock_get):
        """Test external system retrieval when not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/integration_v31/external-systems/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "External system not found"

    @patch("app.crud.integration_v31.integration_service.test_system_connection")
    def test_test_system_connection_success(self, mock_test):
        """Test successful system connection testing."""
        mock_test.return_value = {
            "system_id": "system-123",
            "status": "success",
            "response_code": 200,
            "response_time_ms": 150.5,
            "test_type": "basic",
        }

        test_request = {"test_type": "basic", "timeout": 30}
        response = client.post(
            "/api/v1/integration_v31/external-systems/system-123/test-connection",
            json=test_request,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["response_code"] == 200
        mock_test.assert_called_once()


# =============================================================================
# Integration Connector API Tests
# =============================================================================


class TestIntegrationConnectorAPI:
    """Test cases for integration connector API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_connector")
    def test_create_connector_success(self, mock_create, sample_connector_data):
        """Test successful connector creation."""
        mock_connector = IntegrationConnector(**sample_connector_data)
        mock_connector.id = "connector-123"
        mock_connector.created_at = datetime.now()
        mock_create.return_value = mock_connector

        response = client.post(
            "/api/v1/integration_v31/connectors", json=sample_connector_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "connector-123"
        assert response.json()["name"] == "Contact Sync Connector"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.list_connectors")
    def test_list_connectors_with_filters(self, mock_list):
        """Test connector listing with filters."""
        mock_list.return_value = {
            "connectors": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/connectors"
            "?organization_id=test-org-123"
            "&sync_direction=inbound"
            "&is_active=true"
        )

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.execute_connector")
    def test_execute_connector_success(self, mock_execute):
        """Test successful connector execution."""
        mock_execution = IntegrationExecution(
            id="exec-123",
            organization_id="test-org-123",
            connector_id="connector-123",
            execution_type="manual",
            status=SyncStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=5000,
            records_processed=100,
            records_created=50,
            records_updated=30,
            records_skipped=20,
        )
        mock_execute.return_value = mock_execution

        exec_request = {
            "execution_type": "manual",
            "triggered_by": "user-123",
            "dry_run": False,
        }
        response = client.post(
            "/api/v1/integration_v31/connectors/connector-123/execute",
            json=exec_request,
        )

        assert response.status_code == 200
        assert response.json()["id"] == "exec-123"
        assert response.json()["status"] == "completed"
        assert response.json()["records_processed"] == 100
        mock_execute.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.list_connector_executions")
    def test_list_connector_executions_success(self, mock_list):
        """Test successful connector execution listing."""
        mock_list.return_value = {
            "executions": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/connectors/connector-123/executions"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()


# =============================================================================
# Data Mapping API Tests
# =============================================================================


class TestDataMappingAPI:
    """Test cases for data mapping API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_data_mapping")
    def test_create_data_mapping_success(self, mock_create, sample_data_mapping_data):
        """Test successful data mapping creation."""
        mock_mapping = DataMapping(**sample_data_mapping_data)
        mock_mapping.id = "mapping-123"
        mock_mapping.created_at = datetime.now()
        mock_create.return_value = mock_mapping

        response = client.post(
            "/api/v1/integration_v31/data-mappings", json=sample_data_mapping_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "mapping-123"
        assert response.json()["name"] == "Contact Field Mapping"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.list_data_mappings")
    def test_list_data_mappings_success(self, mock_list):
        """Test successful data mapping listing."""
        mock_list.return_value = {
            "mappings": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/data-mappings?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()


# =============================================================================
# Data Transformation API Tests
# =============================================================================


class TestDataTransformationAPI:
    """Test cases for data transformation API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_transformation")
    def test_create_transformation_success(
        self, mock_create, sample_transformation_data
    ):
        """Test successful transformation creation."""
        mock_transformation = DataTransformation(**sample_transformation_data)
        mock_transformation.id = "transform-123"
        mock_transformation.created_at = datetime.now()
        mock_create.return_value = mock_transformation

        response = client.post(
            "/api/v1/integration_v31/transformations", json=sample_transformation_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "transform-123"
        assert response.json()["name"] == "Contact Name Transformation"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.apply_data_transformation")
    def test_execute_transformation_success(self, mock_execute):
        """Test successful transformation execution."""
        mock_execute.return_value = {
            "transformation_id": "transform-123",
            "status": "success",
            "input_count": 2,
            "output_count": 2,
            "output_data": [
                {"first_name": "John", "last_name": "Doe", "full_name": "John Doe"},
                {"first_name": "Jane", "last_name": "Smith", "full_name": "Jane Smith"},
            ],
            "errors": [],
            "execution_time_ms": 150,
        }

        exec_request = {
            "input_data": [
                {"first_name": "john", "last_name": "doe"},
                {"first_name": "jane", "last_name": "smith"},
            ],
            "execution_config": {},
            "dry_run": False,
        }
        response = client.post(
            "/api/v1/integration_v31/transformations/transform-123/execute",
            json=exec_request,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["output_count"] == 2
        assert len(response.json()["output_data"]) == 2
        mock_execute.assert_called_once()


# =============================================================================
# Webhook API Tests
# =============================================================================


class TestWebhookAPI:
    """Test cases for webhook API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_webhook_endpoint")
    def test_create_webhook_success(self, mock_create, sample_webhook_data):
        """Test successful webhook creation."""
        mock_webhook = WebhookEndpoint(**sample_webhook_data)
        mock_webhook.id = "webhook-123"
        mock_webhook.created_at = datetime.now()
        mock_create.return_value = mock_webhook

        response = client.post(
            "/api/v1/integration_v31/webhooks", json=sample_webhook_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "webhook-123"
        assert response.json()["name"] == "Salesforce Webhook"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.process_webhook_request")
    def test_process_webhook_request_success(self, mock_process):
        """Test successful webhook request processing."""
        mock_process.return_value = {
            "status": "received",
            "message": "Webhook processed successfully",
            "processed_at": datetime.now().isoformat(),
        }

        webhook_request = {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "X-Signature": "sha256=test_signature",
            },
            "query_parameters": {},
            "body": '{"event": "contact.created", "data": {"id": "123"}}',
            "content_type": "application/json",
            "client_ip": "127.0.0.1",
            "user_agent": "Salesforce-Webhook/1.0",
        }
        response = client.post(
            "/api/v1/integration_v31/webhooks/process/salesforce", json=webhook_request
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"
        mock_process.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.list_webhook_endpoints")
    def test_list_webhooks_success(self, mock_list):
        """Test successful webhook listing."""
        mock_list.return_value = {
            "webhooks": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/webhooks?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()


# =============================================================================
# Message Queue API Tests
# =============================================================================


class TestMessageQueueAPI:
    """Test cases for message queue API endpoints."""

    @patch("app.crud.integration_v31.integration_service.create_integration_message")
    def test_create_message_success(self, mock_create, sample_message_data):
        """Test successful message creation."""
        mock_message = IntegrationMessage(**sample_message_data)
        mock_message.id = "message-123"
        mock_message.message_id = "sync_contacts_20240123_001"
        mock_message.status = "pending"
        mock_message.created_at = datetime.now()
        mock_create.return_value = mock_message

        response = client.post(
            "/api/v1/integration_v31/messages", json=sample_message_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "message-123"
        assert response.json()["message_type"] == "data_sync"
        assert response.json()["status"] == "pending"
        mock_create.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.process_pending_messages")
    def test_process_pending_messages_success(self, mock_process):
        """Test successful pending message processing."""
        mock_process.return_value = {
            "processed": 5,
            "successful": 4,
            "failed": 1,
            "expired": 0,
            "messages": [
                {"message_id": "msg1", "status": "completed", "attempt_count": 1},
                {"message_id": "msg2", "status": "completed", "attempt_count": 1},
                {"message_id": "msg3", "status": "completed", "attempt_count": 1},
                {"message_id": "msg4", "status": "completed", "attempt_count": 1},
                {"message_id": "msg5", "status": "failed", "attempt_count": 3},
            ],
        }

        response = client.post(
            "/api/v1/integration_v31/messages/process?organization_id=test-org-123&limit=10"
        )

        assert response.status_code == 200
        assert response.json()["processed"] == 5
        assert response.json()["successful"] == 4
        assert response.json()["failed"] == 1
        assert len(response.json()["messages"]) == 5
        mock_process.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.list_integration_messages")
    def test_list_messages_success(self, mock_list):
        """Test successful message listing."""
        mock_list.return_value = {
            "messages": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/integration_v31/messages?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()


# =============================================================================
# Analytics & Health API Tests
# =============================================================================


class TestAnalyticsHealthAPI:
    """Test cases for analytics and health API endpoints."""

    @patch("app.crud.integration_v31.integration_service.get_integration_health")
    def test_get_integration_health_success(self, mock_health):
        """Test successful integration health retrieval."""
        mock_health.return_value = {
            "overall_health_score": 85.5,
            "status": "healthy",
            "external_systems": {
                "total": 5,
                "active": 4,
                "connected": 4,
                "connection_rate": 80.0,
            },
            "connectors": {"total": 12, "active": 10},
            "executions_24h": {
                "total": 150,
                "successful": 142,
                "failed": 8,
                "success_rate": 94.67,
            },
            "performance": {
                "average_response_time_ms": 250.5,
                "pending_messages": 5,
                "failed_messages": 2,
            },
            "checked_at": datetime.now().isoformat(),
        }

        response = client.get(
            "/api/v1/integration_v31/health?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["overall_health_score"] == 85.5
        assert response.json()["status"] == "healthy"
        assert response.json()["external_systems"]["total"] == 5
        assert response.json()["executions_24h"]["success_rate"] == 94.67
        mock_health.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.get_integration_analytics")
    def test_get_integration_analytics_success(self, mock_analytics):
        """Test successful integration analytics retrieval."""
        mock_analytics.return_value = {
            "organization_id": "test-org-123",
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 1, 31),
            "total_systems": 5,
            "active_systems": 4,
            "connected_systems": 4,
            "total_connectors": 12,
            "active_connectors": 10,
            "total_executions": 1500,
            "successful_executions": 1425,
            "failed_executions": 75,
            "success_rate": 95.0,
            "total_records_processed": 50000,
            "records_created": 20000,
            "records_updated": 25000,
            "records_deleted": 5000,
            "average_execution_time_ms": 2500.0,
            "average_response_time_ms": 300.0,
            "top_errors": [
                {"error": "Connection timeout", "count": 25},
                {"error": "Authentication failed", "count": 15},
            ],
            "error_trends": [
                {"date": "2024-01-01", "errors": 5},
                {"date": "2024-01-02", "errors": 3},
            ],
            "generated_at": datetime.now(),
        }

        analytics_request = {
            "organization_id": "test-org-123",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "system_ids": ["system-123"],
            "include_details": True,
        }
        response = client.post(
            "/api/v1/integration_v31/analytics", json=analytics_request
        )

        assert response.status_code == 200
        assert response.json()["organization_id"] == "test-org-123"
        assert response.json()["success_rate"] == 95.0
        assert response.json()["total_records_processed"] == 50000
        assert len(response.json()["top_errors"]) == 2
        mock_analytics.assert_called_once()


# =============================================================================
# Bulk Operations API Tests
# =============================================================================


class TestBulkOperationsAPI:
    """Test cases for bulk operations API endpoints."""

    @patch("app.crud.integration_v31.integration_service.bulk_execute_connectors")
    def test_bulk_execute_connectors_success(self, mock_bulk_execute):
        """Test successful bulk connector execution."""
        mock_bulk_execute.return_value = {
            "execution_id": "bulk-exec-123",
            "total_requested": 3,
            "successful": 2,
            "failed": 1,
            "execution_results": [
                {"connector_id": "conn-1", "status": "completed", "duration_ms": 2000},
                {"connector_id": "conn-2", "status": "completed", "duration_ms": 1500},
                {
                    "connector_id": "conn-3",
                    "status": "failed",
                    "error": "Connection timeout",
                },
            ],
            "errors": [{"connector_id": "conn-3", "error": "Connection timeout"}],
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
            "total_duration_ms": 5000,
        }

        bulk_request = {
            "connector_ids": ["conn-1", "conn-2", "conn-3"],
            "execution_type": "manual",
            "triggered_by": "user-123",
            "parallel_execution": True,
        }
        response = client.post(
            "/api/v1/integration_v31/connectors/bulk-execute", json=bulk_request
        )

        assert response.status_code == 200
        assert response.json()["total_requested"] == 3
        assert response.json()["successful"] == 2
        assert response.json()["failed"] == 1
        assert len(response.json()["execution_results"]) == 3
        mock_bulk_execute.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.bulk_health_check_systems")
    def test_bulk_health_check_success(self, mock_bulk_health):
        """Test successful bulk health check."""
        mock_bulk_health.return_value = {
            "organization_id": "test-org-123",
            "total_systems": 3,
            "checked_systems": 3,
            "healthy_systems": 2,
            "unhealthy_systems": 1,
            "results": [
                {"system_id": "sys-1", "status": "healthy", "response_time_ms": 150},
                {"system_id": "sys-2", "status": "healthy", "response_time_ms": 200},
                {
                    "system_id": "sys-3",
                    "status": "unhealthy",
                    "error": "Connection refused",
                },
            ],
            "checked_at": datetime.now().isoformat(),
        }

        response = client.post(
            "/api/v1/integration_v31/external-systems/bulk-health-check?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_systems"] == 3
        assert response.json()["healthy_systems"] == 2
        assert response.json()["unhealthy_systems"] == 1
        assert len(response.json()["results"]) == 3
        mock_bulk_health.assert_called_once()


# =============================================================================
# Configuration & Utilities API Tests
# =============================================================================


class TestConfigurationUtilitiesAPI:
    """Test cases for configuration and utilities API endpoints."""

    def test_get_integration_types_success(self):
        """Test successful integration types retrieval."""
        response = client.get("/api/v1/integration_v31/integration-types")

        assert response.status_code == 200
        types_data = response.json()
        assert len(types_data) == 12
        assert any(t["value"] == "api" for t in types_data)
        assert any(t["value"] == "database" for t in types_data)
        assert any(t["value"] == "webhook" for t in types_data)

    def test_get_data_formats_success(self):
        """Test successful data formats retrieval."""
        response = client.get("/api/v1/integration_v31/data-formats")

        assert response.status_code == 200
        formats_data = response.json()
        assert len(formats_data) == 7
        assert any(f["value"] == "json" for f in formats_data)
        assert any(f["value"] == "xml" for f in formats_data)
        assert any(f["value"] == "csv" for f in formats_data)

    @patch("app.crud.integration_v31.integration_service.validate_data_mapping")
    def test_validate_mapping_success(self, mock_validate):
        """Test successful data mapping validation."""
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "field_coverage": 100.0,
            "validation_details": {
                "required_fields_mapped": True,
                "data_types_compatible": True,
                "transformation_rules_valid": True,
            },
        }

        mapping_config = {
            "field_mappings": {"source_id": "target_id", "source_name": "target_name"},
            "validation_rules": {"required_fields": ["target_id"]},
            "transformation_rules": [],
        }
        sample_data = {"source_id": "123", "source_name": "Test"}

        response = client.post(
            "/api/v1/integration_v31/validate-mapping",
            json={"mapping_config": mapping_config, "sample_data": sample_data},
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True
        assert response.json()["field_coverage"] == 100.0
        mock_validate.assert_called_once()

    @patch("app.crud.integration_v31.integration_service.test_transformation_script")
    def test_test_transformation_script_success(self, mock_test):
        """Test successful transformation script testing."""
        mock_test.return_value = {
            "success": True,
            "output_data": [
                {"name": "John Doe", "formatted_name": "DOE, JOHN"},
                {"name": "Jane Smith", "formatted_name": "SMITH, JANE"},
            ],
            "execution_time_ms": 25,
            "errors": [],
            "warnings": [],
        }

        script = """
def transform(data):
    parts = data['name'].split(' ')
    data['formatted_name'] = f"{parts[-1].upper()}, {parts[0].upper()}"
    return data
        """
        sample_input = [{"name": "John Doe"}, {"name": "Jane Smith"}]

        response = client.post(
            "/api/v1/integration_v31/test-transformation",
            json={
                "transformation_script": script,
                "sample_input": sample_input,
                "language": "python",
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["output_data"]) == 2
        mock_test.assert_called_once()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @patch("app.crud.integration_v31.integration_service.create_external_system")
    def test_internal_server_error(self, mock_create, sample_external_system_data):
        """Test handling of internal server errors."""
        mock_create.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/v1/integration_v31/external-systems", json=sample_external_system_data
        )

        assert response.status_code == 500
        assert "Failed to create external system" in response.json()["detail"]

    def test_invalid_request_data(self):
        """Test handling of invalid request data."""
        invalid_data = {
            "organization_id": "",  # Empty organization_id
            "name": "",  # Empty name
            "integration_type": "invalid_type",  # Invalid enum value
        }

        response = client.post(
            "/api/v1/integration_v31/external-systems", json=invalid_data
        )

        assert response.status_code == 422  # Validation error

    @patch("app.crud.integration_v31.integration_service.delete_external_system")
    def test_delete_nonexistent_resource(self, mock_delete):
        """Test deletion of non-existent resource."""
        mock_delete.return_value = False

        response = client.delete("/api/v1/integration_v31/external-systems/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "External system not found"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration test cases for integration API workflows."""

    @patch("app.crud.integration_v31.integration_service")
    def test_complete_integration_workflow(
        self, mock_service, sample_external_system_data, sample_connector_data
    ):
        """Test complete integration workflow from system to execution."""
        # Mock external system creation
        mock_system = ExternalSystem(**sample_external_system_data)
        mock_system.id = "system-123"
        mock_service.create_external_system.return_value = mock_system

        # Mock connector creation
        sample_connector_data["external_system_id"] = "system-123"
        mock_connector = IntegrationConnector(**sample_connector_data)
        mock_connector.id = "connector-123"
        mock_service.create_connector.return_value = mock_connector

        # Mock execution
        mock_execution = IntegrationExecution(
            id="exec-123",
            organization_id="test-org-123",
            connector_id="connector-123",
            execution_type="manual",
            status=SyncStatus.COMPLETED,
            records_processed=100,
        )
        mock_service.execute_connector.return_value = mock_execution

        # Step 1: Create external system
        sys_response = client.post(
            "/api/v1/integration_v31/external-systems", json=sample_external_system_data
        )
        assert sys_response.status_code == 201

        # Step 2: Create connector
        conn_response = client.post(
            "/api/v1/integration_v31/connectors", json=sample_connector_data
        )
        assert conn_response.status_code == 201

        # Step 3: Execute connector
        exec_request = {"execution_type": "manual", "triggered_by": "user-123"}
        exec_response = client.post(
            "/api/v1/integration_v31/connectors/connector-123/execute",
            json=exec_request,
        )
        assert exec_response.status_code == 200
        assert exec_response.json()["records_processed"] == 100


if __name__ == "__main__":
    pytest.main([__file__])
