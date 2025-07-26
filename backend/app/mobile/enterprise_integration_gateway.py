"""Enterprise Integration & API Gateway System - CC02 v73.0 Day 18."""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
import jwt
from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from .enterprise_auth_system import EnterpriseAuthenticationSystem


class IntegrationType(str, Enum):
    """Integration types supported by the gateway."""
    REST_API = "rest_api"
    SOAP_WS = "soap_ws"
    GRAPHQL = "graphql"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"
    FTP_SFTP = "ftp_sftp"
    EMAIL = "email"
    WEBHOOK = "webhook"
    EDI = "edi"


class ProtocolType(str, Enum):
    """Communication protocols."""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    MQTT = "mqtt"
    AMQP = "amqp"
    KAFKA = "kafka"
    WEBSOCKET = "websocket"


class AuthenticationType(str, Enum):
    """Authentication methods for integrations."""
    NONE = "none"
    BASIC = "basic"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    OAUTH1 = "oauth1"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    NTLM = "ntlm"
    KERBEROS = "kerberos"


class IntegrationStatus(str, Enum):
    """Integration connection status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    TESTING = "testing"


class MessageFormat(str, Enum):
    """Message formats for data exchange."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EDI_X12 = "edi_x12"
    EDI_EDIFACT = "edi_edifact"
    FIXED_WIDTH = "fixed_width"
    DELIMITED = "delimited"
    BINARY = "binary"


class IntegrationEndpoint(BaseModel):
    """Integration endpoint configuration."""
    endpoint_id: str
    name: str
    description: str
    integration_type: IntegrationType
    
    # Connection details
    protocol: ProtocolType = ProtocolType.HTTPS
    base_url: str
    port: Optional[int] = None
    path: str = "/"
    
    # Authentication
    auth_type: AuthenticationType = AuthenticationType.NONE
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Data format
    request_format: MessageFormat = MessageFormat.JSON
    response_format: MessageFormat = MessageFormat.JSON
    
    # Headers and parameters
    default_headers: Dict[str, str] = Field(default_factory=dict)
    default_params: Dict[str, str] = Field(default_factory=dict)
    
    # Retry and timeout configuration
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1
    
    # Rate limiting
    rate_limit_requests: Optional[int] = None
    rate_limit_window_seconds: Optional[int] = None
    
    # Health monitoring
    health_check_url: Optional[str] = None
    health_check_interval_seconds: int = 300
    
    # Status and metadata
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    last_health_check: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    # Security
    ssl_verify: bool = True
    allowed_origins: Set[str] = Field(default_factory=set)
    
    # Caching
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300


class DataTransformation(BaseModel):
    """Data transformation rule."""
    transformation_id: str
    name: str
    description: str
    
    # Source and target
    source_format: MessageFormat
    target_format: MessageFormat
    
    # Transformation rules
    field_mappings: Dict[str, str] = Field(default_factory=dict)  # source_field -> target_field
    value_transformations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    conditional_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Data validation
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Error handling
    error_handling: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance
    batch_size: int = 1000
    parallel_processing: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class APIRoute(BaseModel):
    """API Gateway route configuration."""
    route_id: str
    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    
    # Target configuration
    target_endpoint_id: str
    target_path: str
    target_method: Optional[str] = None  # If different from source method
    
    # Authentication and authorization
    auth_required: bool = True
    required_roles: Set[str] = Field(default_factory=set)
    required_permissions: Set[str] = Field(default_factory=set)
    
    # Rate limiting
    rate_limit: Optional[Dict[str, Any]] = None
    
    # Request/Response transformation
    request_transformation_id: Optional[str] = None
    response_transformation_id: Optional[str] = None
    
    # Caching
    cache_enabled: bool = False
    cache_key_template: Optional[str] = None
    cache_ttl_seconds: int = 300
    
    # Monitoring and logging
    logging_enabled: bool = True
    metrics_enabled: bool = True
    
    # Request/Response modification
    request_headers_add: Dict[str, str] = Field(default_factory=dict)
    request_headers_remove: Set[str] = Field(default_factory=set)
    response_headers_add: Dict[str, str] = Field(default_factory=dict)
    response_headers_remove: Set[str] = Field(default_factory=set)
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    
    # Status
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class IntegrationMessage(BaseModel):
    """Message for integration communication."""
    message_id: str
    endpoint_id: str
    
    # Message content
    payload: Any
    headers: Dict[str, str] = Field(default_factory=dict)
    
    # Routing information
    source_system: str
    target_system: str
    message_type: str
    
    # Processing information
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # Status and tracking
    status: str = "pending"  # pending, processing, completed, failed, retry
    retry_count: int = 0
    max_retries: int = 3
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Transformation
    original_payload: Optional[Any] = None
    transformation_applied: bool = False
    
    # Correlation
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None


class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self):
        self.buckets: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit."""
        now = time.time()
        
        if key not in self.buckets:
            self.buckets[key] = {
                "requests": [],
                "window_start": now
            }
        
        bucket = self.buckets[key]
        
        # Remove old requests outside the window
        bucket["requests"] = [
            req_time for req_time in bucket["requests"]
            if now - req_time < window_seconds
        ]
        
        # Check if we're within the limit
        if len(bucket["requests"]) >= max_requests:
            return False, {
                "allowed": False,
                "requests_remaining": 0,
                "reset_time": bucket["requests"][0] + window_seconds,
                "retry_after": bucket["requests"][0] + window_seconds - now
            }
        
        # Add current request
        bucket["requests"].append(now)
        
        return True, {
            "allowed": True,
            "requests_remaining": max_requests - len(bucket["requests"]),
            "reset_time": now + window_seconds,
            "retry_after": 0
        }


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, threshold: int = 5, timeout_seconds: int = 60):
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.threshold:
                self.state = "open"
            
            raise e


class DataTransformer:
    """Data transformation engine."""
    
    def __init__(self):
        self.transformations: Dict[str, DataTransformation] = {}
    
    def register_transformation(self, transformation: DataTransformation) -> None:
        """Register a data transformation."""
        self.transformations[transformation.transformation_id] = transformation
    
    async def transform(
        self,
        transformation_id: str,
        data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Transform data using specified transformation."""
        transformation = self.transformations.get(transformation_id)
        if not transformation:
            raise ValueError(f"Transformation {transformation_id} not found")
        
        try:
            # Apply field mappings
            transformed_data = await self._apply_field_mappings(
                data, transformation.field_mappings
            )
            
            # Apply value transformations
            transformed_data = await self._apply_value_transformations(
                transformed_data, transformation.value_transformations
            )
            
            # Apply conditional rules
            transformed_data = await self._apply_conditional_rules(
                transformed_data, transformation.conditional_rules, context or {}
            )
            
            # Validate transformed data
            validation_result = await self._validate_data(
                transformed_data, transformation.validation_rules
            )
            
            if not validation_result["valid"]:
                raise ValueError(f"Validation failed: {validation_result['errors']}")
            
            return transformed_data
            
        except Exception as e:
            # Handle transformation errors
            error_handling = transformation.error_handling
            if error_handling.get("on_error") == "skip":
                return data  # Return original data
            elif error_handling.get("on_error") == "default":
                return error_handling.get("default_value")
            else:
                raise e
    
    async def _apply_field_mappings(
        self,
        data: Any,
        mappings: Dict[str, str]
    ) -> Any:
        """Apply field mappings to data."""
        if not isinstance(data, dict) or not mappings:
            return data
        
        transformed = {}
        
        # Apply mappings
        for source_field, target_field in mappings.items():
            if source_field in data:
                # Support nested field access with dot notation
                if "." in target_field:
                    self._set_nested_field(transformed, target_field, data[source_field])
                else:
                    transformed[target_field] = data[source_field]
        
        # Include unmapped fields
        for field, value in data.items():
            if field not in mappings and field not in transformed:
                transformed[field] = value
        
        return transformed
    
    def _set_nested_field(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set nested field value using dot notation."""
        parts = field_path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    async def _apply_value_transformations(
        self,
        data: Any,
        transformations: Dict[str, Dict[str, Any]]
    ) -> Any:
        """Apply value transformations to data."""
        if not isinstance(data, dict) or not transformations:
            return data
        
        for field, transform_config in transformations.items():
            if field in data:
                data[field] = await self._transform_value(
                    data[field], transform_config
                )
        
        return data
    
    async def _transform_value(self, value: Any, config: Dict[str, Any]) -> Any:
        """Transform individual value."""
        transform_type = config.get("type")
        
        if transform_type == "uppercase":
            return str(value).upper() if value is not None else value
        elif transform_type == "lowercase":
            return str(value).lower() if value is not None else value
        elif transform_type == "date_format":
            from_format = config.get("from_format", "%Y-%m-%d")
            to_format = config.get("to_format", "%m/%d/%Y")
            if isinstance(value, str):
                try:
                    dt = datetime.strptime(value, from_format)
                    return dt.strftime(to_format)
                except ValueError:
                    return value
        elif transform_type == "lookup":
            lookup_table = config.get("lookup_table", {})
            return lookup_table.get(str(value), value)
        elif transform_type == "default":
            default_value = config.get("default_value")
            return value if value is not None else default_value
        elif transform_type == "regex_replace":
            import re
            pattern = config.get("pattern")
            replacement = config.get("replacement", "")
            if pattern and isinstance(value, str):
                return re.sub(pattern, replacement, value)
        
        return value
    
    async def _apply_conditional_rules(
        self,
        data: Any,
        rules: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Any:
        """Apply conditional transformation rules."""
        if not isinstance(data, dict) or not rules:
            return data
        
        for rule in rules:
            condition = rule.get("condition", {})
            action = rule.get("action", {})
            
            if await self._evaluate_condition(condition, data, context):
                data = await self._apply_action(action, data, context)
        
        return data
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate transformation condition."""
        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        if not field or not operator:
            return True
        
        actual_value = data.get(field)
        
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "contains":
            return str(expected_value) in str(actual_value) if actual_value else False
        elif operator == "exists":
            return field in data
        elif operator == "not_exists":
            return field not in data
        
        return False
    
    async def _apply_action(
        self,
        action: Dict[str, Any],
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply transformation action."""
        action_type = action.get("type")
        
        if action_type == "set_field":
            field = action.get("field")
            value = action.get("value")
            if field:
                data[field] = value
        elif action_type == "remove_field":
            field = action.get("field")
            if field and field in data:
                del data[field]
        elif action_type == "copy_field":
            source_field = action.get("source_field")
            target_field = action.get("target_field")
            if source_field and target_field and source_field in data:
                data[target_field] = data[source_field]
        
        return data
    
    async def _validate_data(
        self,
        data: Any,
        validation_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate transformed data."""
        errors = []
        
        for rule in validation_rules:
            rule_type = rule.get("type")
            field = rule.get("field")
            
            if rule_type == "required" and field:
                if field not in data or data[field] is None:
                    errors.append(f"Field '{field}' is required")
            elif rule_type == "type_check" and field:
                expected_type = rule.get("expected_type")
                if field in data and expected_type:
                    if expected_type == "string" and not isinstance(data[field], str):
                        errors.append(f"Field '{field}' must be a string")
                    elif expected_type == "number" and not isinstance(data[field], (int, float)):
                        errors.append(f"Field '{field}' must be a number")
        
        return {"valid": len(errors) == 0, "errors": errors}


class IntegrationConnector(ABC):
    """Abstract base class for integration connectors."""
    
    @abstractmethod
    async def connect(self, endpoint: IntegrationEndpoint) -> bool:
        """Establish connection to the endpoint."""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        endpoint: IntegrationEndpoint,
        message: IntegrationMessage
    ) -> Dict[str, Any]:
        """Send message to the endpoint."""
        pass
    
    @abstractmethod
    async def receive_message(
        self,
        endpoint: IntegrationEndpoint
    ) -> Optional[IntegrationMessage]:
        """Receive message from the endpoint."""
        pass
    
    @abstractmethod
    async def health_check(self, endpoint: IntegrationEndpoint) -> bool:
        """Check endpoint health."""
        pass
    
    @abstractmethod
    async def disconnect(self, endpoint: IntegrationEndpoint) -> None:
        """Close connection to the endpoint."""
        pass


class RESTAPIConnector(IntegrationConnector):
    """REST API connector implementation."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self, endpoint: IntegrationEndpoint) -> bool:
        """Establish connection to REST API."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return True
    
    async def send_message(
        self,
        endpoint: IntegrationEndpoint,
        message: IntegrationMessage
    ) -> Dict[str, Any]:
        """Send message to REST API."""
        if not self.session:
            await self.connect(endpoint)
        
        url = f"{endpoint.base_url}{endpoint.path}"
        headers = {**endpoint.default_headers, **message.headers}
        
        # Apply authentication
        headers = await self._apply_authentication(headers, endpoint.auth_config, endpoint.auth_type)
        
        try:
            method = message.headers.get("method", "POST").upper()
            
            if method == "GET":
                async with self.session.get(url, headers=headers, ssl=endpoint.ssl_verify) as response:
                    result = await self._process_response(response)
            elif method == "POST":
                async with self.session.post(
                    url, 
                    json=message.payload if endpoint.request_format == MessageFormat.JSON else None,
                    data=message.payload if endpoint.request_format != MessageFormat.JSON else None,
                    headers=headers,
                    ssl=endpoint.ssl_verify
                ) as response:
                    result = await self._process_response(response)
            elif method == "PUT":
                async with self.session.put(
                    url,
                    json=message.payload if endpoint.request_format == MessageFormat.JSON else None,
                    data=message.payload if endpoint.request_format != MessageFormat.JSON else None,
                    headers=headers,
                    ssl=endpoint.ssl_verify
                ) as response:
                    result = await self._process_response(response)
            elif method == "DELETE":
                async with self.session.delete(url, headers=headers, ssl=endpoint.ssl_verify) as response:
                    result = await self._process_response(response)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "response_data": None
            }
    
    async def _apply_authentication(
        self,
        headers: Dict[str, str],
        auth_config: Dict[str, Any],
        auth_type: AuthenticationType
    ) -> Dict[str, str]:
        """Apply authentication to headers."""
        if auth_type == AuthenticationType.BEARER_TOKEN:
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == AuthenticationType.API_KEY:
            api_key = auth_config.get("api_key")
            header_name = auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key
        elif auth_type == AuthenticationType.BASIC:
            username = auth_config.get("username")
            password = auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    async def _process_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Process HTTP response."""
        try:
            if response.content_type == "application/json":
                response_data = await response.json()
            else:
                response_data = await response.text()
            
            return {
                "success": 200 <= response.status < 300,
                "status_code": response.status,
                "response_data": response_data,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": response.status,
                "error": str(e),
                "response_data": None
            }
    
    async def receive_message(
        self,
        endpoint: IntegrationEndpoint
    ) -> Optional[IntegrationMessage]:
        """REST APIs typically don't receive messages (pull-based)."""
        return None
    
    async def health_check(self, endpoint: IntegrationEndpoint) -> bool:
        """Check REST API health."""
        if endpoint.health_check_url:
            try:
                if not self.session:
                    await self.connect(endpoint)
                
                async with self.session.get(
                    endpoint.health_check_url,
                    ssl=endpoint.ssl_verify
                ) as response:
                    return 200 <= response.status < 300
            except Exception:
                return False
        
        return True  # Assume healthy if no health check URL
    
    async def disconnect(self, endpoint: IntegrationEndpoint) -> None:
        """Close REST API connection."""
        if self.session:
            await self.session.close()
            self.session = None


class EnterpriseIntegrationGateway:
    """Main enterprise integration and API gateway."""
    
    def __init__(
        self,
        sdk: MobileERPSDK,
        auth_system: EnterpriseAuthenticationSystem
    ):
        self.sdk = sdk
        self.auth_system = auth_system
        
        # Core components
        self.endpoints: Dict[str, IntegrationEndpoint] = {}
        self.routes: Dict[str, APIRoute] = {}
        self.transformations: Dict[str, DataTransformation] = {}
        
        # Engines and utilities
        self.data_transformer = DataTransformer()
        self.rate_limiter = RateLimiter()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Connectors
        self.connectors: Dict[IntegrationType, IntegrationConnector] = {
            IntegrationType.REST_API: RESTAPIConnector()
        }
        
        # Message queue and processing
        self.message_queue: List[IntegrationMessage] = []
        self.processing_messages: Set[str] = set()
        
        # Metrics and monitoring
        self.metrics = {
            "messages_processed": 0,
            "messages_failed": 0,
            "average_response_time": 0.0,
            "endpoints_healthy": 0,
            "endpoints_total": 0
        }
        
        # Setup default configurations
        self._setup_default_endpoints()
        self._setup_default_routes()
        self._setup_default_transformations()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _setup_default_endpoints(self) -> None:
        """Setup default integration endpoints."""
        # SAP Integration Endpoint
        sap_endpoint = IntegrationEndpoint(
            endpoint_id="sap_erp",
            name="SAP ERP Integration",
            description="Integration with SAP ERP system",
            integration_type=IntegrationType.REST_API,
            base_url="https://sap.company.com/api/v1",
            auth_type=AuthenticationType.OAUTH2,
            auth_config={
                "client_id": "erp_mobile_client",
                "client_secret": "secret",
                "token_url": "https://sap.company.com/oauth/token"
            },
            default_headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout_seconds=45,
            max_retries=3
        )
        
        self.endpoints[sap_endpoint.endpoint_id] = sap_endpoint
        
        # Salesforce Integration
        salesforce_endpoint = IntegrationEndpoint(
            endpoint_id="salesforce_crm",
            name="Salesforce CRM Integration",
            description="Integration with Salesforce CRM",
            integration_type=IntegrationType.REST_API,
            base_url="https://company.salesforce.com/services/data/v58.0",
            auth_type=AuthenticationType.OAUTH2,
            auth_config={
                "client_id": "salesforce_client",
                "client_secret": "secret",
                "token_url": "https://login.salesforce.com/services/oauth2/token"
            },
            health_check_url="https://company.salesforce.com/services/data/v58.0/limits",
            rate_limit_requests=100,
            rate_limit_window_seconds=60
        )
        
        self.endpoints[salesforce_endpoint.endpoint_id] = salesforce_endpoint
        
        # Microsoft Dynamics Integration
        dynamics_endpoint = IntegrationEndpoint(
            endpoint_id="dynamics_365",
            name="Microsoft Dynamics 365 Integration",
            description="Integration with Microsoft Dynamics 365",
            integration_type=IntegrationType.REST_API,
            base_url="https://company.api.crm.dynamics.com/api/data/v9.2",
            auth_type=AuthenticationType.OAUTH2,
            auth_config={
                "client_id": "dynamics_client",
                "client_secret": "secret",
                "token_url": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token"
            }
        )
        
        self.endpoints[dynamics_endpoint.endpoint_id] = dynamics_endpoint
    
    def _setup_default_routes(self) -> None:
        """Setup default API gateway routes."""
        # Customer data route
        customer_route = APIRoute(
            route_id="customer_data",
            path="/api/v1/customers/*",
            method="*",  # All methods
            target_endpoint_id="sap_erp",
            target_path="/customers",
            auth_required=True,
            required_roles={"sales_user", "customer_service"},
            rate_limit={
                "requests": 100,
                "window_seconds": 60
            },
            cache_enabled=True,
            cache_ttl_seconds=300
        )
        
        self.routes[customer_route.route_id] = customer_route
        
        # Invoice processing route
        invoice_route = APIRoute(
            route_id="invoice_processing",
            path="/api/v1/invoices",
            method="POST",
            target_endpoint_id="sap_erp",
            target_path="/financial/invoices",
            auth_required=True,
            required_permissions={"finance.write"},
            request_transformation_id="invoice_transform",
            logging_enabled=True,
            metrics_enabled=True
        )
        
        self.routes[invoice_route.route_id] = invoice_route
    
    def _setup_default_transformations(self) -> None:
        """Setup default data transformations."""
        # Invoice transformation
        invoice_transform = DataTransformation(
            transformation_id="invoice_transform",
            name="Invoice Data Transformation",
            description="Transform mobile invoice data to SAP format",
            source_format=MessageFormat.JSON,
            target_format=MessageFormat.JSON,
            field_mappings={
                "customer_id": "CustomerNumber",
                "invoice_date": "DocumentDate",
                "due_date": "DueDate",
                "total_amount": "GrossAmount",
                "line_items": "LineItems"
            },
            value_transformations={
                "DocumentDate": {
                    "type": "date_format",
                    "from_format": "%Y-%m-%d",
                    "to_format": "%d.%m.%Y"
                },
                "CustomerNumber": {
                    "type": "uppercase"
                }
            }
        )
        
        self.transformations[invoice_transform.transformation_id] = invoice_transform
        self.data_transformer.register_transformation(invoice_transform)
        
        # Customer transformation
        customer_transform = DataTransformation(
            transformation_id="customer_transform",
            name="Customer Data Transformation",
            description="Transform customer data between systems",
            source_format=MessageFormat.JSON,
            target_format=MessageFormat.JSON,
            field_mappings={
                "first_name": "FirstName",
                "last_name": "LastName",
                "email": "EmailAddress",
                "phone": "PhoneNumber",
                "address": "Address"
            }
        )
        
        self.transformations[customer_transform.transformation_id] = customer_transform
        self.data_transformer.register_transformation(customer_transform)
    
    def _start_background_tasks(self) -> None:
        """Start background processing tasks."""
        # Message processor
        task = asyncio.create_task(self._message_processor_loop())
        self._background_tasks.append(task)
        
        # Health checker
        task = asyncio.create_task(self._health_checker_loop())
        self._background_tasks.append(task)
        
        # Metrics collector
        task = asyncio.create_task(self._metrics_collector_loop())
        self._background_tasks.append(task)
    
    async def _message_processor_loop(self) -> None:
        """Background loop for processing integration messages."""
        while True:
            try:
                await self._process_message_queue()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in message processor loop: {e}")
                await asyncio.sleep(5)
    
    async def _health_checker_loop(self) -> None:
        """Background loop for endpoint health checking."""
        while True:
            try:
                await self._check_endpoint_health()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error in health checker loop: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_collector_loop(self) -> None:
        """Background loop for metrics collection."""
        while True:
            try:
                await self._update_metrics()
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                print(f"Error in metrics collector loop: {e}")
                await asyncio.sleep(60)
    
    async def register_endpoint(self, endpoint: IntegrationEndpoint) -> None:
        """Register new integration endpoint."""
        self.endpoints[endpoint.endpoint_id] = endpoint
        
        # Initialize circuit breaker
        if endpoint.endpoint_id not in self.circuit_breakers:
            self.circuit_breakers[endpoint.endpoint_id] = CircuitBreaker()
        
        # Test connection
        try:
            connector = self.connectors.get(endpoint.integration_type)
            if connector:
                await connector.connect(endpoint)
                endpoint.status = IntegrationStatus.ACTIVE
            else:
                endpoint.status = IntegrationStatus.ERROR
        except Exception:
            endpoint.status = IntegrationStatus.ERROR
    
    async def send_message(
        self,
        endpoint_id: str,
        payload: Any,
        headers: Dict[str, str] = None,
        transformation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message to integration endpoint."""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        # Create message
        message = IntegrationMessage(
            message_id=f"msg_{int(time.time() * 1000)}_{endpoint_id}",
            endpoint_id=endpoint_id,
            payload=payload,
            headers=headers or {},
            source_system="mobile_erp",
            target_system=endpoint.name,
            message_type="request"
        )
        
        # Apply transformation if specified
        if transformation_id:
            try:
                message.original_payload = message.payload
                message.payload = await self.data_transformer.transform(
                    transformation_id, message.payload
                )
                message.transformation_applied = True
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Transformation failed: {str(e)}",
                    "message_id": message.message_id
                }
        
        # Add to queue for processing
        self.message_queue.append(message)
        
        return {
            "success": True,
            "message_id": message.message_id,
            "status": "queued"
        }
    
    async def _process_message_queue(self) -> None:
        """Process messages in the queue."""
        if not self.message_queue:
            return
        
        # Process up to 10 messages at a time
        messages_to_process = self.message_queue[:10]
        
        for message in messages_to_process:
            if message.message_id not in self.processing_messages:
                await self._process_message(message)
    
    async def _process_message(self, message: IntegrationMessage) -> None:
        """Process individual message."""
        self.processing_messages.add(message.message_id)
        
        try:
            endpoint = self.endpoints.get(message.endpoint_id)
            if not endpoint:
                raise ValueError(f"Endpoint {message.endpoint_id} not found")
            
            # Check rate limiting
            if endpoint.rate_limit_requests:
                allowed, rate_info = await self.rate_limiter.check_rate_limit(
                    f"endpoint_{message.endpoint_id}",
                    endpoint.rate_limit_requests,
                    endpoint.rate_limit_window_seconds or 60
                )
                
                if not allowed:
                    message.status = "rate_limited"
                    message.error_message = f"Rate limit exceeded. Retry after {rate_info['retry_after']} seconds"
                    return
            
            # Get connector
            connector = self.connectors.get(endpoint.integration_type)
            if not connector:
                raise ValueError(f"No connector for integration type: {endpoint.integration_type}")
            
            # Process with circuit breaker
            circuit_breaker = self.circuit_breakers.get(message.endpoint_id)
            if circuit_breaker:
                result = await circuit_breaker.call(
                    connector.send_message, endpoint, message
                )
            else:
                result = await connector.send_message(endpoint, message)
            
            # Update message status
            if result.get("success"):
                message.status = "completed"
                message.processed_at = datetime.now()
                self.metrics["messages_processed"] += 1
            else:
                message.status = "failed"
                message.error_message = result.get("error", "Unknown error")
                message.error_details = result
                self.metrics["messages_failed"] += 1
            
            # Remove from queue
            if message in self.message_queue:
                self.message_queue.remove(message)
                
        except Exception as e:
            message.status = "failed"
            message.error_message = str(e)
            message.retry_count += 1
            
            if message.retry_count >= message.max_retries:
                if message in self.message_queue:
                    self.message_queue.remove(message)
                self.metrics["messages_failed"] += 1
            else:
                # Retry later
                message.status = "retry"
        
        finally:
            self.processing_messages.discard(message.message_id)
    
    async def _check_endpoint_health(self) -> None:
        """Check health of all endpoints."""
        healthy_count = 0
        
        for endpoint in self.endpoints.values():
            try:
                connector = self.connectors.get(endpoint.integration_type)
                if connector:
                    is_healthy = await connector.health_check(endpoint)
                    
                    if is_healthy:
                        endpoint.status = IntegrationStatus.ACTIVE
                        healthy_count += 1
                    else:
                        endpoint.status = IntegrationStatus.ERROR
                    
                    endpoint.last_health_check = datetime.now()
            except Exception:
                endpoint.status = IntegrationStatus.ERROR
        
        self.metrics["endpoints_healthy"] = healthy_count
        self.metrics["endpoints_total"] = len(self.endpoints)
    
    async def _update_metrics(self) -> None:
        """Update system metrics."""
        # Calculate average response time (mock)
        if self.metrics["messages_processed"] > 0:
            self.metrics["average_response_time"] = 250.5  # Mock value
        
        # Update endpoint status
        active_endpoints = len([
            e for e in self.endpoints.values() 
            if e.status == IntegrationStatus.ACTIVE
        ])
        self.metrics["endpoints_healthy"] = active_endpoints
    
    def get_endpoint_status(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific endpoint."""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return None
        
        return {
            "endpoint_id": endpoint.endpoint_id,
            "name": endpoint.name,
            "status": endpoint.status,
            "integration_type": endpoint.integration_type,
            "last_health_check": endpoint.last_health_check.isoformat() if endpoint.last_health_check else None,
            "rate_limit": {
                "requests": endpoint.rate_limit_requests,
                "window_seconds": endpoint.rate_limit_window_seconds
            } if endpoint.rate_limit_requests else None
        }
    
    def list_endpoints(self, integration_type: Optional[IntegrationType] = None) -> List[Dict[str, Any]]:
        """List all integration endpoints."""
        endpoints = []
        
        for endpoint in self.endpoints.values():
            if integration_type and endpoint.integration_type != integration_type:
                continue
            
            endpoints.append({
                "endpoint_id": endpoint.endpoint_id,
                "name": endpoint.name,
                "integration_type": endpoint.integration_type,
                "status": endpoint.status,
                "base_url": endpoint.base_url,
                "auth_type": endpoint.auth_type
            })
        
        return endpoints
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get integration gateway metrics."""
        return {
            **self.metrics,
            "queue_size": len(self.message_queue),
            "processing_count": len(self.processing_messages),
            "total_endpoints": len(self.endpoints),
            "total_routes": len(self.routes),
            "total_transformations": len(self.transformations),
            "uptime_seconds": time.time() - (time.time() - 3600),  # Mock 1 hour uptime
            "circuit_breakers": {
                endpoint_id: {
                    "state": cb.state,
                    "failure_count": cb.failure_count
                }
                for endpoint_id, cb in self.circuit_breakers.items()
            }
        }