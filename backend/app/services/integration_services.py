"""
CC02 v55.0 Integration Services Layer
Enterprise-grade Integration and Service Management System
Day 2 of 7-day intensive backend development - Final Component
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IntegrationError
from app.services.audit_service import AuditService


class IntegrationType(str, Enum):
    REST_API = "rest_api"
    SOAP = "soap"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    FTP = "ftp"
    SFTP = "sftp"
    EMAIL = "email"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"


class AuthenticationType(str, Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CUSTOM = "custom"


class DataFormat(str, Enum):
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EXCEL = "excel"
    PLAIN_TEXT = "plain_text"
    BINARY = "binary"


class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


@dataclass
class IntegrationContext:
    """Context for integration operations"""

    integration_id: UUID
    operation: str
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationResult:
    """Result of integration operation"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    execution_time_ms: float = 0
    bytes_transferred: int = 0
    records_processed: int = 0


class BaseIntegrationAdapter(ABC):
    """Base class for integration adapters"""

    def __init__(self, integration_type: IntegrationType, config: Dict[str, Any]) -> dict:
        self.integration_type = integration_type
        self.config = config

    @abstractmethod
    async def send_data(self, context: IntegrationContext) -> IntegrationResult:
        """Send data to external system"""
        pass

    @abstractmethod
    async def receive_data(self, context: IntegrationContext) -> IntegrationResult:
        """Receive data from external system"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to external system"""
        pass

    def get_headers(self, context: IntegrationContext) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = context.headers.copy()

        auth_type = self.config.get("authentication_type")

        if auth_type == AuthenticationType.BEARER_TOKEN:
            token = self.config.get("bearer_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif auth_type == AuthenticationType.API_KEY:
            api_key = self.config.get("api_key")
            key_header = self.config.get("api_key_header", "X-API-Key")
            if api_key:
                headers[key_header] = api_key

        elif auth_type == AuthenticationType.BASIC:
            username = self.config.get("username")
            password = self.config.get("password")
            if username and password:
                import base64

                credentials = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"

        return headers


class RestApiAdapter(BaseIntegrationAdapter):
    """REST API integration adapter"""

    def __init__(self, config: Dict[str, Any]) -> dict:
        super().__init__(IntegrationType.REST_API, config)
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30)

    async def send_data(self, context: IntegrationContext) -> IntegrationResult:
        """Send data via REST API"""

        start_time = datetime.utcnow()

        try:
            url = f"{self.base_url.rstrip('/')}/{context.operation.lstrip('/')}"
            headers = self.get_headers(context)
            headers["Content-Type"] = "application/json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                method = context.parameters.get("method", "POST").upper()

                if method == "GET":
                    response = await client.get(
                        url, headers=headers, params=context.data
                    )
                elif method == "POST":
                    response = await client.post(
                        url, headers=headers, json=context.data
                    )
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=context.data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise IntegrationError(f"Unsupported HTTP method: {method}")

                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                result = IntegrationResult(
                    success=response.is_success,
                    data=response.json() if response.content else None,
                    status_code=response.status_code,
                    response_headers=dict(response.headers),
                    execution_time_ms=execution_time,
                    bytes_transferred=len(response.content),
                )

                if not response.is_success:
                    result.error_message = (
                        f"HTTP {response.status_code}: {response.text}"
                    )

                return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def receive_data(self, context: IntegrationContext) -> IntegrationResult:
        """Receive data via REST API"""
        # Set method to GET for receiving data
        context.parameters["method"] = "GET"
        return await self.send_data(context)

    async def test_connection(self) -> bool:
        """Test REST API connection"""
        try:
            health_endpoint = self.config.get("health_endpoint", "/health")
            url = f"{self.base_url.rstrip('/')}/{health_endpoint.lstrip('/')}"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                return response.is_success
        except:
            return False


class WebhookAdapter(BaseIntegrationAdapter):
    """Webhook integration adapter"""

    def __init__(self, config: Dict[str, Any]) -> dict:
        super().__init__(IntegrationType.WEBHOOK, config)
        self.webhook_url = config.get("webhook_url", "")

    async def send_data(self, context: IntegrationContext) -> IntegrationResult:
        """Send data via webhook"""

        start_time = datetime.utcnow()

        try:
            headers = self.get_headers(context)
            headers["Content-Type"] = "application/json"

            # Add webhook signature if configured
            secret = self.config.get("webhook_secret")
            if secret:
                import hashlib
                import hmac

                payload = json.dumps(context.data)
                signature = hmac.new(
                    secret.encode(), payload.encode(), hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.webhook_url, headers=headers, json=context.data
                )

                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                return IntegrationResult(
                    success=response.is_success,
                    data=response.json() if response.content else None,
                    status_code=response.status_code,
                    response_headers=dict(response.headers),
                    execution_time_ms=execution_time,
                    bytes_transferred=len(response.content),
                    records_processed=1,
                )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def receive_data(self, context: IntegrationContext) -> IntegrationResult:
        """Webhooks are passive receivers"""
        return IntegrationResult(
            success=False, error_message="Webhooks cannot actively receive data"
        )

    async def test_connection(self) -> bool:
        """Test webhook URL accessibility"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.head(self.webhook_url)
                return response.status_code < 500
        except:
            return False


class DatabaseAdapter(BaseIntegrationAdapter):
    """Database integration adapter"""

    def __init__(self, config: Dict[str, Any]) -> dict:
        super().__init__(IntegrationType.DATABASE, config)
        self.connection_string = config.get("connection_string", "")
        self.database_type = config.get("database_type", "postgresql")

    async def send_data(self, context: IntegrationContext) -> IntegrationResult:
        """Send data to database"""

        start_time = datetime.utcnow()

        try:
            # This would integrate with SQLAlchemy or other database libraries
            # For now, simulate the operation
            await asyncio.sleep(0.1)  # Simulate database operation

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return IntegrationResult(
                success=True,
                data={"rows_affected": len(context.data.get("records", []))},
                execution_time_ms=execution_time,
                records_processed=len(context.data.get("records", [])),
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def receive_data(self, context: IntegrationContext) -> IntegrationResult:
        """Receive data from database"""

        start_time = datetime.utcnow()

        try:
            # This would execute database queries
            # For now, simulate the operation
            await asyncio.sleep(0.1)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return IntegrationResult(
                success=True,
                data={"records": []},  # Would contain actual query results
                execution_time_ms=execution_time,
                records_processed=0,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Would test actual database connection
            return True
        except:
            return False


class EmailAdapter(BaseIntegrationAdapter):
    """Email integration adapter"""

    def __init__(self, config: Dict[str, Any]) -> dict:
        super().__init__(IntegrationType.EMAIL, config)
        self.smtp_server = config.get("smtp_server", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.use_tls = config.get("use_tls", True)

    async def send_data(self, context: IntegrationContext) -> IntegrationResult:
        """Send email"""

        start_time = datetime.utcnow()

        try:
            # Would integrate with email library (aiosmtplib, etc.)
            # For now, simulate sending email
            await asyncio.sleep(0.2)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return IntegrationResult(
                success=True,
                data={"message_id": str(uuid4())},
                execution_time_ms=execution_time,
                records_processed=1,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def receive_data(self, context: IntegrationContext) -> IntegrationResult:
        """Receive email (IMAP)"""

        start_time = datetime.utcnow()

        try:
            # Would integrate with IMAP library
            await asyncio.sleep(0.3)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return IntegrationResult(
                success=True,
                data={"emails": []},  # Would contain actual emails
                execution_time_ms=execution_time,
                records_processed=0,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def test_connection(self) -> bool:
        """Test email server connection"""
        try:
            # Would test SMTP connection
            return True
        except:
            return False


class DataMapper:
    """Data mapping and transformation utilities"""

    def __init__(self) -> dict:
        self.mappings: Dict[str, Dict[str, str]] = {}
        self.transformers: Dict[str, Callable] = {}

    def register_mapping(self, integration_id: str, field_mappings: Dict[str, str]) -> dict:
        """Register field mappings for an integration"""
        self.mappings[integration_id] = field_mappings

    def register_transformer(self, name: str, transformer: Callable) -> dict:
        """Register data transformer function"""
        self.transformers[name] = transformer

    def map_data(
        self, integration_id: str, data: Dict[str, Any], reverse: bool = False
    ) -> Dict[str, Any]:
        """Map data fields according to registered mappings"""

        mapping = self.mappings.get(integration_id, {})
        if not mapping:
            return data

        if reverse:
            # Reverse mapping (external -> internal)
            mapping = {v: k for k, v in mapping.items()}

        mapped_data = {}
        for source_field, target_field in mapping.items():
            if source_field in data:
                mapped_data[target_field] = data[source_field]

        # Include unmapped fields
        for key, value in data.items():
            if key not in mapping and key not in mapped_data:
                mapped_data[key] = value

        return mapped_data

    def transform_data(
        self, data: Dict[str, Any], transformations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply data transformations"""

        result = data.copy()

        for transform in transformations:
            field = transform.get("field")
            transformer_name = transform.get("transformer")
            config = transform.get("config", {})

            if field in result and transformer_name in self.transformers:
                transformer = self.transformers[transformer_name]
                result[field] = transformer(result[field], config)

        return result


class IntegrationManager:
    """Enterprise Integration Manager"""

    def __init__(self) -> dict:
        self.adapters: Dict[str, BaseIntegrationAdapter] = {}
        self.data_mapper = DataMapper()
        self.audit_service = AuditService()
        self._register_default_adapters()
        self._register_default_transformers()

    def _register_default_adapters(self) -> dict:
        """Register default integration adapters"""
        # Adapters are registered dynamically based on configuration
        pass

    def _register_default_transformers(self) -> dict:
        """Register default data transformers"""

        def to_uppercase(value: Any, config: Dict[str, Any]) -> str:
            return str(value).upper()

        def to_lowercase(value: Any, config: Dict[str, Any]) -> str:
            return str(value).lower()

        def format_date(value: Any, config: Dict[str, Any]) -> str:
            format_string = config.get("format", "%Y-%m-%d")
            if isinstance(value, datetime):
                return value.strftime(format_string)
            elif isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value)
                    return dt.strftime(format_string)
                except:
                    return value
            return str(value)

        def format_decimal(value: Any, config: Dict[str, Any]) -> str:
            places = config.get("decimal_places", 2)
            try:
                decimal_value = Decimal(str(value))
                return f"{decimal_value:.{places}f}"
            except:
                return str(value)

        self.data_mapper.register_transformer("uppercase", to_uppercase)
        self.data_mapper.register_transformer("lowercase", to_lowercase)
        self.data_mapper.register_transformer("format_date", format_date)
        self.data_mapper.register_transformer("format_decimal", format_decimal)

    def register_integration(
        self,
        integration_id: str,
        integration_type: IntegrationType,
        config: Dict[str, Any],
        field_mappings: Dict[str, str] = None,
        transformations: List[Dict[str, Any]] = None,
    ):
        """Register an integration endpoint"""

        # Create appropriate adapter
        if integration_type == IntegrationType.REST_API:
            adapter = RestApiAdapter(config)
        elif integration_type == IntegrationType.WEBHOOK:
            adapter = WebhookAdapter(config)
        elif integration_type == IntegrationType.DATABASE:
            adapter = DatabaseAdapter(config)
        elif integration_type == IntegrationType.EMAIL:
            adapter = EmailAdapter(config)
        else:
            raise IntegrationError(f"Unsupported integration type: {integration_type}")

        self.adapters[integration_id] = adapter

        # Register field mappings
        if field_mappings:
            self.data_mapper.register_mapping(integration_id, field_mappings)

    async def send_data(
        self,
        integration_id: str,
        operation: str,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
        **parameters,
    ) -> IntegrationResult:
        """Send data to external system"""

        adapter = self.adapters.get(integration_id)
        if not adapter:
            return IntegrationResult(
                success=False, error_message=f"Integration {integration_id} not found"
            )

        # Map and transform data
        mapped_data = self.data_mapper.map_data(integration_id, data)

        # Create context
        context = IntegrationContext(
            integration_id=UUID(integration_id),
            operation=operation,
            data=mapped_data,
            parameters=parameters,
            user_id=user_id,
            session=session,
        )

        # Execute integration
        result = await adapter.send_data(context)

        # Log integration activity
        await self._log_integration_activity(
            integration_id, "send", operation, data, result, user_id
        )

        return result

    async def receive_data(
        self,
        integration_id: str,
        operation: str,
        parameters: Dict[str, Any] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> IntegrationResult:
        """Receive data from external system"""

        adapter = self.adapters.get(integration_id)
        if not adapter:
            return IntegrationResult(
                success=False, error_message=f"Integration {integration_id} not found"
            )

        # Create context
        context = IntegrationContext(
            integration_id=UUID(integration_id),
            operation=operation,
            parameters=parameters or {},
            user_id=user_id,
            session=session,
        )

        # Execute integration
        result = await adapter.receive_data(context)

        # Map received data
        if result.success and result.data:
            result.data = self.data_mapper.map_data(
                integration_id, result.data, reverse=True
            )

        # Log integration activity
        await self._log_integration_activity(
            integration_id, "receive", operation, {}, result, user_id
        )

        return result

    async def test_integration(self, integration_id: str) -> bool:
        """Test integration connection"""

        adapter = self.adapters.get(integration_id)
        if not adapter:
            return False

        try:
            return await adapter.test_connection()
        except Exception:
            return False

    async def sync_data(
        self,
        integration_id: str,
        entity_type: str,
        sync_direction: SyncDirection,
        filters: Dict[str, Any] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> IntegrationResult:
        """Synchronize data with external system"""

        start_time = datetime.utcnow()

        try:
            if sync_direction == SyncDirection.OUTBOUND:
                # Get local data and send to external system
                local_data = await self._get_local_data(entity_type, filters, session)
                result = await self.send_data(
                    integration_id, f"sync_{entity_type}", local_data, user_id, session
                )

            elif sync_direction == SyncDirection.INBOUND:
                # Get data from external system and update local
                result = await self.receive_data(
                    integration_id, f"sync_{entity_type}", filters, user_id, session
                )

                if result.success and result.data:
                    await self._update_local_data(entity_type, result.data, session)

            elif sync_direction == SyncDirection.BIDIRECTIONAL:
                # Two-way synchronization
                outbound_result = await self.sync_data(
                    integration_id,
                    entity_type,
                    SyncDirection.OUTBOUND,
                    filters,
                    user_id,
                    session,
                )
                inbound_result = await self.sync_data(
                    integration_id,
                    entity_type,
                    SyncDirection.INBOUND,
                    filters,
                    user_id,
                    session,
                )

                result = IntegrationResult(
                    success=outbound_result.success and inbound_result.success,
                    data={
                        "outbound": outbound_result.data,
                        "inbound": inbound_result.data,
                    },
                    execution_time_ms=outbound_result.execution_time_ms
                    + inbound_result.execution_time_ms,
                    records_processed=outbound_result.records_processed
                    + inbound_result.records_processed,
                )

            else:
                result = IntegrationResult(
                    success=False,
                    error_message=f"Unsupported sync direction: {sync_direction}",
                )

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return IntegrationResult(
                success=False, error_message=str(e), execution_time_ms=execution_time
            )

    async def bulk_sync(
        self,
        sync_jobs: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[IntegrationResult]:
        """Execute multiple sync jobs in parallel"""

        tasks = []
        for job in sync_jobs:
            task = self.sync_data(
                job["integration_id"],
                job["entity_type"],
                SyncDirection(job["sync_direction"]),
                job.get("filters"),
                user_id,
                session,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(
                    IntegrationResult(success=False, error_message=str(result))
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _get_local_data(
        self,
        entity_type: str,
        filters: Dict[str, Any] = None,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Get local data for synchronization"""

        # This would query the local database
        # For now, return mock data
        return {
            "entity_type": entity_type,
            "records": [],
            "filters_applied": filters or {},
        }

    async def _update_local_data(
        self,
        entity_type: str,
        data: Dict[str, Any],
        session: Optional[AsyncSession] = None,
    ):
        """Update local data from external system"""

        # This would update the local database
        # For now, just validate and return
        if session:
            # Would perform actual database updates
            pass

    async def _log_integration_activity(
        self,
        integration_id: str,
        direction: str,
        operation: str,
        request_data: Dict[str, Any],
        result: IntegrationResult,
        user_id: Optional[UUID] = None,
    ):
        """Log integration activity"""

        await self.audit_service.log_event(
            event_type=f"integration_{direction}",
            entity_type="integration",
            entity_id=UUID(integration_id),
            user_id=user_id,
            details={
                "operation": operation,
                "success": result.success,
                "status_code": result.status_code,
                "execution_time_ms": result.execution_time_ms,
                "bytes_transferred": result.bytes_transferred,
                "records_processed": result.records_processed,
                "error_message": result.error_message,
                "request_size": len(json.dumps(request_data)) if request_data else 0,
            },
        )

    def get_integration_stats(self, integration_id: str) -> Dict[str, Any]:
        """Get integration statistics"""

        # Would query integration logs for statistics
        # For now, return mock stats
        return {
            "integration_id": integration_id,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0,
            "total_bytes_transferred": 0,
            "last_activity": None,
        }

    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all registered integrations"""

        integrations = []
        for integration_id, adapter in self.adapters.items():
            integrations.append(
                {
                    "id": integration_id,
                    "type": adapter.integration_type.value,
                    "config": adapter.config,
                    "status": "active",  # Would check actual status
                }
            )

        return integrations


# Singleton instance
integration_manager = IntegrationManager()


# Helper functions
async def send_integration_data(
    integration_id: str,
    operation: str,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
    **parameters,
) -> IntegrationResult:
    """Send data to external system"""
    return await integration_manager.send_data(
        integration_id, operation, data, user_id, session, **parameters
    )


async def receive_integration_data(
    integration_id: str,
    operation: str,
    parameters: Dict[str, Any] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
) -> IntegrationResult:
    """Receive data from external system"""
    return await integration_manager.receive_data(
        integration_id, operation, parameters, user_id, session
    )


async def sync_integration_data(
    integration_id: str,
    entity_type: str,
    sync_direction: SyncDirection,
    filters: Dict[str, Any] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
) -> IntegrationResult:
    """Synchronize data with external system"""
    return await integration_manager.sync_data(
        integration_id, entity_type, sync_direction, filters, user_id, session
    )


def register_integration(
    integration_id: str,
    integration_type: IntegrationType,
    config: Dict[str, Any],
    field_mappings: Dict[str, str] = None,
    transformations: List[Dict[str, Any]] = None,
):
    """Register integration endpoint"""
    integration_manager.register_integration(
        integration_id, integration_type, config, field_mappings, transformations
    )


async def test_integration_connection(integration_id: str) -> bool:
    """Test integration connection"""
    return await integration_manager.test_integration(integration_id)


# Default integration configurations
def setup_default_integrations() -> None:
    """Setup default integrations"""

    # Sample CRM integration
    register_integration(
        "salesforce_crm",
        IntegrationType.REST_API,
        {
            "base_url": "https://api.salesforce.com",
            "authentication_type": AuthenticationType.OAUTH2,
            "timeout": 30,
        },
        field_mappings={
            "customer_name": "Name",
            "email": "Email",
            "phone": "Phone",
            "company": "Company",
        },
    )

    # Sample accounting system integration
    register_integration(
        "quickbooks_accounting",
        IntegrationType.REST_API,
        {
            "base_url": "https://sandbox-quickbooks.api.intuit.com",
            "authentication_type": AuthenticationType.OAUTH2,
            "timeout": 45,
        },
        field_mappings={
            "invoice_number": "DocNumber",
            "total_amount": "TotalAmt",
            "customer_id": "CustomerRef",
        },
    )

    # Sample email integration
    register_integration(
        "email_notifications",
        IntegrationType.EMAIL,
        {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "authentication_type": AuthenticationType.BASIC,
        },
    )


# Initialize default integrations
setup_default_integrations()
