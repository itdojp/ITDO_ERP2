"""
CC02 v55.0 External Integration Hub
Enterprise-grade External System Integration and API Management
Day 5 of 7-day intensive backend development
"""

import hashlib
import hmac
import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import aiohttp
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IntegrationError
from app.models.integration import DataMapping, ExternalSystem, SyncJob
from app.services.audit_service import AuditService


class IntegrationType(str, Enum):
    REST_API = "rest_api"
    SOAP = "soap"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    FILE_TRANSFER = "file_transfer"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    EMAIL = "email"
    FTP_SFTP = "ftp_sftp"


class AuthenticationType(str, Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    BASIC_AUTH = "basic_auth"
    CERTIFICATE = "certificate"
    HMAC = "hmac"
    NONE = "none"


class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class DataFormat(str, Enum):
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EDI = "edi"
    FIXED_WIDTH = "fixed_width"
    CUSTOM = "custom"


@dataclass
class IntegrationConfig:
    """Configuration for external integration"""

    system_id: UUID
    base_url: str
    authentication: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit: Optional[Dict[str, Any]] = None
    ssl_verify: bool = True


@dataclass
class SyncResult:
    """Result of synchronization operation"""

    job_id: UUID
    status: SyncStatus
    records_processed: int
    records_success: int
    records_failed: int
    execution_time: float
    error_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookPayload:
    """Webhook payload structure"""

    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


class BaseIntegrationAdapter(ABC):
    """Base class for integration adapters"""

    def __init__(self, config: IntegrationConfig) -> dict:
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> dict:
        connector = aiohttp.TCPConnector(ssl=self.config.ssl_verify)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=self.config.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> dict:
        if self.session:
            await self.session.close()

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """Test connection to external system"""
        pass

    @abstractmethod
    async def fetch_data(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Fetch data from external system"""
        pass

    @abstractmethod
    async def send_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to external system"""
        pass

    def _prepare_authentication(self) -> Dict[str, Any]:
        """Prepare authentication headers/params"""
        auth_config = self.config.authentication
        auth_type = auth_config.get("type", AuthenticationType.NONE)

        if auth_type == AuthenticationType.API_KEY:
            return {
                "headers": {
                    auth_config.get("header_name", "X-API-Key"): auth_config["api_key"]
                }
            }
        elif auth_type == AuthenticationType.BASIC_AUTH:
            import base64

            credentials = f"{auth_config['username']}:{auth_config['password']}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"headers": {"Authorization": f"Basic {encoded}"}}
        elif auth_type == AuthenticationType.JWT:
            return {"headers": {"Authorization": f"Bearer {auth_config['token']}"}}
        elif auth_type == AuthenticationType.OAUTH2:
            return {
                "headers": {"Authorization": f"Bearer {auth_config['access_token']}"}
            }

        return {}


class RestApiAdapter(BaseIntegrationAdapter):
    """REST API integration adapter"""

    async def test_connection(self) -> Tuple[bool, str]:
        """Test REST API connection"""
        try:
            auth_config = self._prepare_authentication()
            headers = auth_config.get("headers", {})

            async with self.session.get(
                f"{self.config.base_url}/health", headers=headers
            ) as response:
                if response.status == 200:
                    return True, "Connection successful"
                else:
                    return False, f"HTTP {response.status}: {await response.text()}"

        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def fetch_data(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Fetch data from REST API"""
        auth_config = self._prepare_authentication()
        headers = auth_config.get("headers", {})

        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                return await response.json()
            elif "application/xml" in content_type or "text/xml" in content_type:
                text = await response.text()
                return self._parse_xml(text)
            else:
                return {"data": await response.text()}

    async def send_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to REST API"""
        auth_config = self._prepare_authentication()
        headers = auth_config.get("headers", {})
        headers["Content-Type"] = "application/json"

        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        async with self.session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            return await response.json()

    def _parse_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML to dictionary"""

        def xml_to_dict(element) -> dict:
            result = {}

            # Add attributes
            if element.attrib:
                result["@attributes"] = element.attrib

            # Add children
            children = list(element)
            if children:
                children_dict = {}
                for child in children:
                    child_data = xml_to_dict(child)
                    if child.tag in children_dict:
                        if not isinstance(children_dict[child.tag], list):
                            children_dict[child.tag] = [children_dict[child.tag]]
                        children_dict[child.tag].append(child_data)
                    else:
                        children_dict[child.tag] = child_data
                result.update(children_dict)

            # Add text content
            if element.text and element.text.strip():
                if result:
                    result["#text"] = element.text.strip()
                else:
                    result = element.text.strip()

            return result

        root = ET.fromstring(xml_text)
        return {root.tag: xml_to_dict(root)}


class SoapAdapter(BaseIntegrationAdapter):
    """SOAP web service integration adapter"""

    async def test_connection(self) -> Tuple[bool, str]:
        """Test SOAP service connection"""
        try:
            wsdl_url = f"{self.config.base_url}?wsdl"
            async with self.session.get(wsdl_url) as response:
                if response.status == 200:
                    return True, "WSDL accessible"
                else:
                    return False, f"WSDL not accessible: HTTP {response.status}"
        except Exception as e:
            return False, f"SOAP connection failed: {str(e)}"

    async def fetch_data(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Fetch data via SOAP"""
        soap_envelope = self._build_soap_envelope(endpoint, params or {})

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{endpoint}"',
        }

        async with self.session.post(
            self.config.base_url, data=soap_envelope, headers=headers
        ) as response:
            response.raise_for_status()
            xml_response = await response.text()
            return self._parse_soap_response(xml_response)

    async def send_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via SOAP"""
        return await self.fetch_data(endpoint, data)

    def _build_soap_envelope(self, action: str, data: Dict[str, Any]) -> str:
        """Build SOAP envelope"""
        params_xml = self._dict_to_xml(data)

        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header/>
            <soap:Body>
                <{action}>
                    {params_xml}
                </{action}>
            </soap:Body>
        </soap:Envelope>"""

        return envelope.strip()

    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = None) -> str:
        """Convert dictionary to XML"""
        xml_parts = []

        for key, value in data.items():
            if isinstance(value, dict):
                xml_parts.append(f"<{key}>{self._dict_to_xml(value)}</{key}>")
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        xml_parts.append(f"<{key}>{self._dict_to_xml(item)}</{key}>")
                    else:
                        xml_parts.append(f"<{key}>{item}</{key}>")
            else:
                xml_parts.append(f"<{key}>{value}</{key}>")

        return "".join(xml_parts)

    def _parse_soap_response(self, xml_response: str) -> Dict[str, Any]:
        """Parse SOAP response"""
        root = ET.fromstring(xml_response)

        # Find the Body element
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        if body is not None and len(body) > 0:
            # Get the first child of Body (the actual response)
            response_element = body[0]
            return self._xml_element_to_dict(response_element)

        return {}

    def _xml_element_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        if element.attrib:
            for key, value in element.attrib.items():
                result[f"@{key}"] = value

        # Add children
        children = list(element)
        if children:
            for child in children:
                child_data = self._xml_element_to_dict(child)
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                if tag in result:
                    if not isinstance(result[tag], list):
                        result[tag] = [result[tag]]
                    result[tag].append(child_data)
                else:
                    result[tag] = child_data

        # Add text content
        if element.text and element.text.strip():
            if result:
                result["#text"] = element.text.strip()
            else:
                return element.text.strip()

        return result


class GraphQLAdapter(BaseIntegrationAdapter):
    """GraphQL integration adapter"""

    async def test_connection(self) -> Tuple[bool, str]:
        """Test GraphQL endpoint"""
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                }
            }
        }
        """

        try:
            result = await self._execute_query(introspection_query)
            if "data" in result:
                return True, "GraphQL endpoint accessible"
            else:
                return False, f"GraphQL error: {result.get('errors', 'Unknown error')}"
        except Exception as e:
            return False, f"GraphQL connection failed: {str(e)}"

    async def fetch_data(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query"""
        query = params.get("query") if params else endpoint
        variables = params.get("variables", {}) if params else {}

        return await self._execute_query(query, variables)

    async def send_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL mutation"""
        mutation = data.get("mutation", endpoint)
        variables = data.get("variables", {})

        return await self._execute_query(mutation, variables)

    async def _execute_query(
        self, query: str, variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query/mutation"""
        auth_config = self._prepare_authentication()
        headers = auth_config.get("headers", {})
        headers["Content-Type"] = "application/json"

        payload = {"query": query, "variables": variables or {}}

        async with self.session.post(
            self.config.base_url, headers=headers, json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()


class WebhookManager:
    """Webhook subscription and processing manager"""

    def __init__(self) -> dict:
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.processors: Dict[str, Callable] = {}

    def subscribe(
        self,
        event_type: str,
        callback_url: str,
        secret: Optional[str] = None,
        filters: Dict[str, Any] = None,
    ) -> str:
        """Subscribe to webhook events"""
        subscription_id = str(uuid4())

        self.subscriptions[subscription_id] = {
            "event_type": event_type,
            "callback_url": callback_url,
            "secret": secret,
            "filters": filters or {},
            "created_at": datetime.utcnow(),
            "active": True,
        }

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> dict:
        """Unsubscribe from webhook"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["active"] = False

    def register_processor(self, event_type: str, processor: Callable) -> dict:
        """Register webhook event processor"""
        self.processors[event_type] = processor

    async def process_webhook(
        self, event_type: str, payload: WebhookPayload, subscription_id: str = None
    ) -> Dict[str, Any]:
        """Process incoming webhook"""

        # Validate subscription
        if subscription_id and subscription_id not in self.subscriptions:
            raise IntegrationError(f"Invalid subscription ID: {subscription_id}")

        subscription = self.subscriptions.get(subscription_id, {})

        # Verify signature if secret is provided
        if subscription.get("secret"):
            if not self._verify_signature(payload, subscription["secret"]):
                raise IntegrationError("Invalid webhook signature")

        # Check filters
        if not self._matches_filters(payload.data, subscription.get("filters", {})):
            return {"status": "filtered", "message": "Event does not match filters"}

        # Process event
        processor = self.processors.get(event_type)
        if processor:
            result = await processor(payload)
            return {"status": "processed", "result": result}
        else:
            return {
                "status": "no_processor",
                "message": f"No processor for event type: {event_type}",
            }

    def _verify_signature(self, payload: WebhookPayload, secret: str) -> bool:
        """Verify webhook signature"""
        if not payload.signature:
            return False

        expected_signature = hmac.new(
            secret.encode(),
            json.dumps(payload.data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(payload.signature, expected_signature)

    def _matches_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if data matches filters"""
        for key, expected_value in filters.items():
            if key not in data or data[key] != expected_value:
                return False
        return True


class DataTransformer:
    """Data transformation utilities"""

    @staticmethod
    def transform_data(data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data using field mapping"""
        result = {}

        for target_field, source_config in mapping.items():
            if isinstance(source_config, str):
                # Simple field mapping
                if source_config in data:
                    result[target_field] = data[source_config]
            elif isinstance(source_config, dict):
                # Complex mapping with transformation
                source_field = source_config.get("source")
                transform_type = source_config.get("transform")
                default_value = source_config.get("default")

                if source_field in data:
                    value = data[source_field]

                    if transform_type == "uppercase":
                        value = str(value).upper()
                    elif transform_type == "lowercase":
                        value = str(value).lower()
                    elif transform_type == "date_format":
                        from datetime import datetime

                        if isinstance(value, str):
                            value = datetime.fromisoformat(value).isoformat()
                    elif transform_type == "decimal":
                        value = Decimal(str(value))

                    result[target_field] = value
                elif default_value is not None:
                    result[target_field] = default_value

        return result

    @staticmethod
    def validate_data(
        data: Dict[str, Any], schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate data against schema"""
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field missing: {field}")

        # Check field types
        field_types = schema.get("properties", {})
        for field, type_config in field_types.items():
            if field in data:
                expected_type = type_config.get("type")
                value = data[field]

                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif expected_type == "number" and not isinstance(
                    value, (int, float, Decimal)
                ):
                    errors.append(f"Field {field} must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")

        return len(errors) == 0, errors


class ExternalIntegrationHub:
    """Central hub for external system integrations"""

    def __init__(self) -> dict:
        self.adapters: Dict[IntegrationType, type] = {
            IntegrationType.REST_API: RestApiAdapter,
            IntegrationType.SOAP: SoapAdapter,
            IntegrationType.GRAPHQL: GraphQLAdapter,
        }
        self.webhook_manager = WebhookManager()
        self.transformer = DataTransformer()
        self.audit_service = AuditService()

    async def register_system(
        self,
        name: str,
        integration_type: IntegrationType,
        config: IntegrationConfig,
        session: AsyncSession,
    ) -> UUID:
        """Register external system"""

        system = ExternalSystem(
            id=uuid4(),
            name=name,
            integration_type=integration_type,
            base_url=config.base_url,
            auth_config=config.authentication,
            configuration=config.__dict__,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(system)
        await session.commit()

        return system.id

    async def test_system_connection(
        self, system_id: UUID, session: AsyncSession
    ) -> Tuple[bool, str]:
        """Test connection to external system"""

        # Get system configuration
        system_result = await session.execute(
            select(ExternalSystem).where(ExternalSystem.id == system_id)
        )
        system = system_result.scalar_one_or_none()

        if not system:
            return False, "System not found"

        # Create adapter
        config = IntegrationConfig(
            system_id=system.id,
            base_url=system.base_url,
            authentication=system.auth_config,
        )

        adapter_class = self.adapters.get(IntegrationType(system.integration_type))
        if not adapter_class:
            return False, f"Unsupported integration type: {system.integration_type}"

        async with adapter_class(config) as adapter:
            return await adapter.test_connection()

    async def sync_data(
        self,
        system_id: UUID,
        endpoint: str,
        direction: SyncDirection,
        data: Dict[str, Any] = None,
        mapping_id: Optional[UUID] = None,
        session: AsyncSession = None,
    ) -> SyncResult:
        """Synchronize data with external system"""

        job_id = uuid4()
        start_time = datetime.utcnow()

        try:
            # Get system configuration
            system_result = await session.execute(
                select(ExternalSystem).where(ExternalSystem.id == system_id)
            )
            system = system_result.scalar_one_or_none()

            if not system:
                raise IntegrationError("System not found")

            # Get data mapping if specified
            mapping = None
            if mapping_id:
                mapping_result = await session.execute(
                    select(DataMapping).where(DataMapping.id == mapping_id)
                )
                mapping = mapping_result.scalar_one_or_none()

            # Create adapter
            config = IntegrationConfig(
                system_id=system.id,
                base_url=system.base_url,
                authentication=system.auth_config,
            )

            adapter_class = self.adapters.get(IntegrationType(system.integration_type))
            if not adapter_class:
                raise IntegrationError(
                    f"Unsupported integration type: {system.integration_type}"
                )

            # Execute sync operation
            result_data = None
            records_processed = 0
            records_success = 0
            records_failed = 0

            async with adapter_class(config) as adapter:
                if direction in [SyncDirection.INBOUND, SyncDirection.BIDIRECTIONAL]:
                    # Fetch data from external system
                    result_data = await adapter.fetch_data(endpoint, data)

                    # Transform data if mapping exists
                    if mapping and result_data:
                        if isinstance(result_data, list):
                            transformed_data = []
                            for item in result_data:
                                try:
                                    transformed_item = self.transformer.transform_data(
                                        item, mapping.field_mapping
                                    )
                                    transformed_data.append(transformed_item)
                                    records_success += 1
                                except Exception:
                                    records_failed += 1
                                records_processed += 1
                            result_data = transformed_data
                        else:
                            result_data = self.transformer.transform_data(
                                result_data, mapping.field_mapping
                            )
                            records_processed = 1
                            records_success = 1

                if direction in [SyncDirection.OUTBOUND, SyncDirection.BIDIRECTIONAL]:
                    # Send data to external system
                    if data:
                        # Transform data if mapping exists
                        send_data = data
                        if mapping:
                            send_data = self.transformer.transform_data(
                                data, mapping.field_mapping
                            )

                        result_data = await adapter.send_data(endpoint, send_data)
                        records_processed = 1
                        records_success = 1

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Create sync job record
            sync_job = SyncJob(
                id=job_id,
                system_id=system_id,
                endpoint=endpoint,
                direction=direction,
                status=SyncStatus.SUCCESS,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed,
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.utcnow(),
            )

            session.add(sync_job)
            await session.commit()

            return SyncResult(
                job_id=job_id,
                status=SyncStatus.SUCCESS,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed,
                execution_time=execution_time,
                metadata={"result_data": result_data},
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Create failed sync job record
            sync_job = SyncJob(
                id=job_id,
                system_id=system_id,
                endpoint=endpoint,
                direction=direction,
                status=SyncStatus.FAILED,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed + 1,
                execution_time=execution_time,
                error_message=str(e),
                started_at=start_time,
                completed_at=datetime.utcnow(),
            )

            session.add(sync_job)
            await session.commit()

            return SyncResult(
                job_id=job_id,
                status=SyncStatus.FAILED,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed + 1,
                execution_time=execution_time,
                error_messages=[str(e)],
            )

    async def create_data_mapping(
        self,
        name: str,
        source_system_id: UUID,
        target_system_id: UUID,
        field_mapping: Dict[str, Any],
        validation_schema: Dict[str, Any] = None,
        session: AsyncSession = None,
    ) -> UUID:
        """Create data mapping between systems"""

        mapping = DataMapping(
            id=uuid4(),
            name=name,
            source_system_id=source_system_id,
            target_system_id=target_system_id,
            field_mapping=field_mapping,
            validation_schema=validation_schema or {},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(mapping)
        await session.commit()

        return mapping.id

    async def schedule_sync_job(
        self,
        system_id: UUID,
        endpoint: str,
        direction: SyncDirection,
        cron_expression: str,
        session: AsyncSession,
    ) -> UUID:
        """Schedule recurring sync job"""

        # In production, would integrate with task scheduler like Celery
        job_id = uuid4()

        # Store schedule configuration
        sync_job = SyncJob(
            id=job_id,
            system_id=system_id,
            endpoint=endpoint,
            direction=direction,
            status=SyncStatus.PENDING,
            cron_schedule=cron_expression,
            is_recurring=True,
            created_at=datetime.utcnow(),
        )

        session.add(sync_job)
        await session.commit()

        return job_id

    async def process_webhook(
        self,
        system_id: UUID,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None,
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Process incoming webhook"""

        webhook_payload = WebhookPayload(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=payload,
            headers=headers or {},
        )

        # Log webhook received
        await self.audit_service.log_event(
            event_type="webhook_received",
            entity_type="external_system",
            entity_id=system_id,
            details={
                "event_type": event_type,
                "payload_size": len(json.dumps(payload)),
                "headers": headers,
            },
        )

        return await self.webhook_manager.process_webhook(event_type, webhook_payload)

    async def get_sync_status(
        self, job_id: UUID, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get sync job status"""

        job_result = await session.execute(select(SyncJob).where(SyncJob.id == job_id))
        job = job_result.scalar_one_or_none()

        if not job:
            return None

        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "records_processed": job.records_processed,
            "records_success": job.records_success,
            "records_failed": job.records_failed,
            "execution_time": job.execution_time,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    async def get_system_metrics(
        self, system_id: UUID, start_date: date, end_date: date, session: AsyncSession
    ) -> Dict[str, Any]:
        """Get integration metrics for system"""

        # Get sync job statistics
        jobs_result = await session.execute(
            select(SyncJob).where(
                and_(
                    SyncJob.system_id == system_id,
                    SyncJob.started_at >= start_date,
                    SyncJob.started_at <= end_date,
                )
            )
        )
        jobs = jobs_result.scalars().all()

        total_jobs = len(jobs)
        successful_jobs = len([j for j in jobs if j.status == SyncStatus.SUCCESS])
        failed_jobs = len([j for j in jobs if j.status == SyncStatus.FAILED])
        total_records = sum(j.records_processed or 0 for j in jobs)
        avg_execution_time = (
            sum(j.execution_time or 0 for j in jobs) / total_jobs
            if total_jobs > 0
            else 0
        )

        return {
            "system_id": str(system_id),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "jobs": {
                "total": total_jobs,
                "successful": successful_jobs,
                "failed": failed_jobs,
                "success_rate": (successful_jobs / total_jobs * 100)
                if total_jobs > 0
                else 0,
            },
            "records": {
                "total_processed": total_records,
                "average_per_job": total_records / total_jobs if total_jobs > 0 else 0,
            },
            "performance": {
                "average_execution_time": avg_execution_time,
                "throughput_per_second": total_records
                / sum(j.execution_time or 0 for j in jobs)
                if sum(j.execution_time or 0 for j in jobs) > 0
                else 0,
            },
        }


# Singleton instance
integration_hub = ExternalIntegrationHub()


# Helper functions
async def register_external_system(
    name: str,
    integration_type: IntegrationType,
    base_url: str,
    authentication: Dict[str, Any],
    session: AsyncSession,
) -> UUID:
    """Register external system"""
    config = IntegrationConfig(
        system_id=uuid4(), base_url=base_url, authentication=authentication
    )
    return await integration_hub.register_system(
        name, integration_type, config, session
    )


async def sync_with_external_system(
    system_id: UUID,
    endpoint: str,
    direction: SyncDirection,
    data: Dict[str, Any] = None,
    session: AsyncSession = None,
) -> SyncResult:
    """Sync data with external system"""
    return await integration_hub.sync_data(
        system_id, endpoint, direction, data, session=session
    )


async def create_system_mapping(
    name: str,
    source_system_id: UUID,
    target_system_id: UUID,
    field_mapping: Dict[str, Any],
    session: AsyncSession,
) -> UUID:
    """Create data mapping"""
    return await integration_hub.create_data_mapping(
        name, source_system_id, target_system_id, field_mapping, session=session
    )
