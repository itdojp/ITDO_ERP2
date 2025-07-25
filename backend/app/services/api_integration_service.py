"""API Integration Platform service for CC02 v64.0 - Day 9: API Integration Platform."""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    APIGatewayUpdate,
    ExternalIntegrationCreate,
    ExternalIntegrationUpdate,
    DataSyncJobCreate,
    WebhookEndpointCreate,
    WebhookEndpointUpdate,
    APIKeyCreate,
    DataMappingCreate,
    IntegrationHealthCheck,
)


class APIGatewayService:
    """Service for managing API gateway operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_gateway(
        self, 
        gateway_data: APIGatewayCreate,
        organization_id: str,
        created_by: str
    ) -> APIGateway:
        """Create a new API gateway."""
        gateway_id = f"gw_{uuid.uuid4().hex[:12]}"
        
        gateway = APIGateway(
            gateway_id=gateway_id,
            organization_id=organization_id,
            created_by=created_by,
            **gateway_data.model_dump()
        )
        
        self.db.add(gateway)
        await self.db.commit()
        await self.db.refresh(gateway)
        return gateway

    async def get_gateway(
        self, 
        gateway_id: str,
        organization_id: str
    ) -> Optional[APIGateway]:
        """Get API gateway by ID."""
        query = select(APIGateway).where(
            and_(
                APIGateway.gateway_id == gateway_id,
                APIGateway.organization_id == organization_id
            )
        ).options(
            selectinload(APIGateway.integrations),
            selectinload(APIGateway.api_keys)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_gateways(
        self,
        organization_id: str,
        status: Optional[ConnectionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[APIGateway]:
        """List API gateways for organization."""
        query = select(APIGateway).where(
            APIGateway.organization_id == organization_id
        )
        
        if status:
            query = query.where(APIGateway.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_gateway(
        self,
        gateway_id: str,
        organization_id: str,
        gateway_data: APIGatewayUpdate
    ) -> Optional[APIGateway]:
        """Update API gateway."""
        query = update(APIGateway).where(
            and_(
                APIGateway.gateway_id == gateway_id,
                APIGateway.organization_id == organization_id
            )
        ).values(**gateway_data.model_dump(exclude_unset=True))
        
        await self.db.execute(query)
        await self.db.commit()
        
        return await self.get_gateway(gateway_id, organization_id)

    async def delete_gateway(
        self,
        gateway_id: str,
        organization_id: str
    ) -> bool:
        """Delete API gateway."""
        query = select(APIGateway).where(
            and_(
                APIGateway.gateway_id == gateway_id,
                APIGateway.organization_id == organization_id
            )
        )
        
        result = await self.db.execute(query)
        gateway = result.scalar_one_or_none()
        
        if gateway:
            await self.db.delete(gateway)
            await self.db.commit()
            return True
        
        return False

    async def health_check_gateway(
        self,
        gateway_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """Perform health check on API gateway."""
        gateway = await self.get_gateway(gateway_id, organization_id)
        if not gateway:
            return {"status": "not_found", "message": "Gateway not found"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                health_url = f"{gateway.base_url}/health"
                response = await client.get(health_url)
                
                health_data = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "status_code": response.status_code,
                    "last_checked": datetime.now(),
                }
                
                # Update gateway health metrics
                await self.db.execute(
                    update(APIGateway)
                    .where(APIGateway.id == gateway.id)
                    .values(
                        last_health_check=datetime.now(),
                        avg_response_time_ms=health_data["response_time_ms"]
                    )
                )
                await self.db.commit()
                
                return health_data
                
        except Exception as e:
            health_data = {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now(),
            }
            
            # Update gateway status to error
            await self.db.execute(
                update(APIGateway)
                .where(APIGateway.id == gateway.id)
                .values(
                    status=ConnectionStatus.ERROR,
                    last_health_check=datetime.now()
                )
            )
            await self.db.commit()
            
            return health_data

    async def update_gateway_statistics(
        self,
        gateway_id: str,
        organization_id: str,
        requests_count: int,
        successful_requests: int,
        failed_requests: int,
        avg_response_time: float
    ) -> None:
        """Update gateway usage statistics."""
        await self.db.execute(
            update(APIGateway)
            .where(
                and_(
                    APIGateway.gateway_id == gateway_id,
                    APIGateway.organization_id == organization_id
                )
            )
            .values(
                total_requests=APIGateway.total_requests + requests_count,
                successful_requests=APIGateway.successful_requests + successful_requests,
                failed_requests=APIGateway.failed_requests + failed_requests,
                avg_response_time_ms=avg_response_time
            )
        )
        await self.db.commit()


class ExternalIntegrationService:
    """Service for managing external system integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_integration(
        self,
        integration_data: ExternalIntegrationCreate,
        organization_id: str,
        created_by: str
    ) -> ExternalIntegration:
        """Create a new external integration."""
        integration_id = f"int_{uuid.uuid4().hex[:12]}"
        
        integration = ExternalIntegration(
            integration_id=integration_id,
            organization_id=organization_id,
            created_by=created_by,
            **integration_data.model_dump()
        )
        
        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def get_integration(
        self,
        integration_id: str,
        organization_id: str
    ) -> Optional[ExternalIntegration]:
        """Get external integration by ID."""
        query = select(ExternalIntegration).where(
            and_(
                ExternalIntegration.integration_id == integration_id,
                ExternalIntegration.organization_id == organization_id
            )
        ).options(
            selectinload(ExternalIntegration.sync_jobs),
            selectinload(ExternalIntegration.webhooks)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_integrations(
        self,
        organization_id: str,
        integration_type: Optional[IntegrationType] = None,
        status: Optional[ConnectionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ExternalIntegration]:
        """List external integrations for organization."""
        query = select(ExternalIntegration).where(
            ExternalIntegration.organization_id == organization_id
        )
        
        if integration_type:
            query = query.where(ExternalIntegration.integration_type == integration_type)
        
        if status:
            query = query.where(ExternalIntegration.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_integration(
        self,
        integration_id: str,
        organization_id: str,
        integration_data: ExternalIntegrationUpdate
    ) -> Optional[ExternalIntegration]:
        """Update external integration."""
        query = update(ExternalIntegration).where(
            and_(
                ExternalIntegration.integration_id == integration_id,
                ExternalIntegration.organization_id == organization_id
            )
        ).values(**integration_data.model_dump(exclude_unset=True))
        
        await self.db.execute(query)
        await self.db.commit()
        
        return await self.get_integration(integration_id, organization_id)

    async def test_integration_connection(
        self,
        integration_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """Test connection to external integration."""
        integration = await self.get_integration(integration_id, organization_id)
        if not integration:
            return {"status": "not_found", "message": "Integration not found"}

        try:
            # Prepare authentication headers
            auth_headers = await self._prepare_auth_headers(integration)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if integration.integration_type == IntegrationType.REST_API:
                    response = await client.get(
                        integration.endpoint_url,
                        headers=auth_headers
                    )
                else:
                    # For other integration types, just check connectivity
                    response = await client.head(
                        integration.endpoint_url,
                        headers=auth_headers
                    )
                
                connection_data = {
                    "status": "connected" if response.status_code < 400 else "failed",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "status_code": response.status_code,
                    "last_tested": datetime.now(),
                }
                
                # Update integration metrics
                await self.db.execute(
                    update(ExternalIntegration)
                    .where(ExternalIntegration.id == integration.id)
                    .values(
                        status=ConnectionStatus.ACTIVE if response.status_code < 400 else ConnectionStatus.ERROR,
                        avg_response_time_ms=connection_data["response_time_ms"],
                        total_requests=ExternalIntegration.total_requests + 1,
                        failed_requests=ExternalIntegration.failed_requests + (1 if response.status_code >= 400 else 0)
                    )
                )
                await self.db.commit()
                
                return connection_data
                
        except Exception as e:
            connection_data = {
                "status": "error",
                "error": str(e),
                "last_tested": datetime.now(),
            }
            
            # Update integration status to error
            await self.db.execute(
                update(ExternalIntegration)
                .where(ExternalIntegration.id == integration.id)
                .values(
                    status=ConnectionStatus.ERROR,
                    failed_requests=ExternalIntegration.failed_requests + 1
                )
            )
            await self.db.commit()
            
            return connection_data

    async def _prepare_auth_headers(
        self, 
        integration: ExternalIntegration
    ) -> Dict[str, str]:
        """Prepare authentication headers for integration."""
        headers = integration.default_headers or {}
        
        if integration.auth_type == AuthenticationType.API_KEY:
            api_key = integration.auth_config.get("api_key")
            header_name = integration.auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key
        
        elif integration.auth_type == AuthenticationType.BEARER_TOKEN:
            token = integration.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif integration.auth_type == AuthenticationType.BASIC_AUTH:
            username = integration.auth_config.get("username")
            password = integration.auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        return headers

    async def trigger_sync_job(
        self,
        integration_id: str,
        organization_id: str,
        job_name: str,
        sync_direction: SyncDirection,
        sync_config: Dict[str, Any]
    ) -> DataSyncJob:
        """Trigger a data synchronization job."""
        integration = await self.get_integration(integration_id, organization_id)
        if not integration:
            raise ValueError("Integration not found")

        job_id = f"sync_{uuid.uuid4().hex[:12]}"
        
        sync_job = DataSyncJob(
            job_id=job_id,
            integration_id=integration.id,
            organization_id=organization_id,
            job_name=job_name,
            sync_direction=sync_direction,
            sync_type="manual",  # Can be full, incremental, delta
            source_system=integration.provider,
            target_system="erp_system",
            entity_type="general",
            sync_config=sync_config,
            triggered_by="api"
        )
        
        self.db.add(sync_job)
        await self.db.commit()
        await self.db.refresh(sync_job)
        
        # Start sync job asynchronously
        asyncio.create_task(self._execute_sync_job(sync_job))
        
        return sync_job

    async def _execute_sync_job(self, sync_job: DataSyncJob) -> None:
        """Execute data synchronization job."""
        try:
            # Update job status to running
            await self.db.execute(
                update(DataSyncJob)
                .where(DataSyncJob.id == sync_job.id)
                .values(
                    status=SyncStatus.RUNNING,
                    started_at=datetime.now()
                )
            )
            await self.db.commit()
            
            # Simulate sync processing (replace with actual integration logic)
            await asyncio.sleep(5)
            
            # Update job status to completed
            await self.db.execute(
                update(DataSyncJob)
                .where(DataSyncJob.id == sync_job.id)
                .values(
                    status=SyncStatus.COMPLETED,
                    completed_at=datetime.now(),
                    duration_seconds=5,
                    records_processed=100,
                    records_created=25,
                    records_updated=50,
                    records_deleted=0,
                    records_failed=0
                )
            )
            await self.db.commit()
            
        except Exception as e:
            # Update job status to failed
            await self.db.execute(
                update(DataSyncJob)
                .where(DataSyncJob.id == sync_job.id)
                .values(
                    status=SyncStatus.FAILED,
                    completed_at=datetime.now(),
                    error_message=str(e)
                )
            )
            await self.db.commit()


class WebhookService:
    """Service for managing webhook endpoints and deliveries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(
        self,
        webhook_data: WebhookEndpointCreate,
        organization_id: str,
        created_by: str
    ) -> WebhookEndpoint:
        """Create a new webhook endpoint."""
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        
        webhook = WebhookEndpoint(
            webhook_id=webhook_id,
            organization_id=organization_id,
            created_by=created_by,
            **webhook_data.model_dump()
        )
        
        # Generate secret key if not provided
        if not webhook.secret_key:
            webhook.secret_key = secrets.token_urlsafe(32)
        
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def get_webhook(
        self,
        webhook_id: str,
        organization_id: str
    ) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID."""
        query = select(WebhookEndpoint).where(
            and_(
                WebhookEndpoint.webhook_id == webhook_id,
                WebhookEndpoint.organization_id == organization_id
            )
        ).options(selectinload(WebhookEndpoint.deliveries))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_webhooks(
        self,
        organization_id: str,
        integration_id: Optional[int] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookEndpoint]:
        """List webhook endpoints for organization."""
        query = select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == organization_id
        )
        
        if integration_id:
            query = query.where(WebhookEndpoint.integration_id == integration_id)
        
        if status:
            query = query.where(WebhookEndpoint.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_webhook(
        self,
        webhook_id: str,
        organization_id: str,
        webhook_data: WebhookEndpointUpdate
    ) -> Optional[WebhookEndpoint]:
        """Update webhook endpoint."""
        query = update(WebhookEndpoint).where(
            and_(
                WebhookEndpoint.webhook_id == webhook_id,
                WebhookEndpoint.organization_id == organization_id
            )
        ).values(**webhook_data.model_dump(exclude_unset=True))
        
        await self.db.execute(query)
        await self.db.commit()
        
        return await self.get_webhook(webhook_id, organization_id)

    async def deliver_webhook(
        self,
        webhook_id: str,
        organization_id: str,
        event_type: str,
        event_id: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Deliver webhook payload to endpoint."""
        webhook = await self.get_webhook(webhook_id, organization_id)
        if not webhook or not webhook.is_enabled:
            raise ValueError("Webhook not found or disabled")

        delivery_id = f"del_{uuid.uuid4().hex[:12]}"
        
        # Create delivery record
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            webhook_id=webhook.id,
            organization_id=organization_id,
            event_type=event_type,
            event_id=event_id,
            request_url=webhook.endpoint_url,
            request_method=webhook.http_method,
            request_payload=payload,
            scheduled_at=datetime.now()
        )
        
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        
        # Perform actual delivery
        await self._perform_webhook_delivery(delivery, webhook)
        
        return delivery

    async def _perform_webhook_delivery(
        self,
        delivery: WebhookDelivery,
        webhook: WebhookEndpoint
    ) -> None:
        """Perform actual webhook delivery."""
        try:
            headers = webhook.custom_headers or {}
            headers["Content-Type"] = webhook.content_type
            
            # Add signature if secret key is configured
            if webhook.secret_key:
                payload_str = json.dumps(delivery.request_payload)
                signature = hashlib.sha256(
                    f"{webhook.secret_key}{payload_str}".encode()
                ).hexdigest()
                headers[webhook.signature_header or "X-Webhook-Signature"] = f"sha256={signature}"
            
            async with httpx.AsyncClient(
                timeout=webhook.timeout_seconds,
                verify=webhook.verify_ssl
            ) as client:
                start_time = datetime.now()
                
                response = await client.request(
                    method=webhook.http_method,
                    url=webhook.endpoint_url,
                    json=delivery.request_payload,
                    headers=headers
                )
                
                end_time = datetime.now()
                response_time = int((end_time - start_time).total_seconds() * 1000)
                
                # Update delivery record
                await self.db.execute(
                    update(WebhookDelivery)
                    .where(WebhookDelivery.id == delivery.id)
                    .values(
                        attempted_at=start_time,
                        completed_at=end_time,
                        response_status_code=response.status_code,
                        response_headers=dict(response.headers),
                        response_body=response.text[:5000],  # Limit response body size
                        response_time_ms=response_time,
                        is_successful=200 <= response.status_code < 300
                    )
                )
                
                # Update webhook statistics
                await self.db.execute(
                    update(WebhookEndpoint)
                    .where(WebhookEndpoint.id == webhook.id)
                    .values(
                        total_deliveries=WebhookEndpoint.total_deliveries + 1,
                        successful_deliveries=WebhookEndpoint.successful_deliveries + (
                            1 if 200 <= response.status_code < 300 else 0
                        ),
                        failed_deliveries=WebhookEndpoint.failed_deliveries + (
                            1 if response.status_code >= 300 else 0
                        ),
                        last_triggered_at=start_time,
                        last_successful_delivery=start_time if 200 <= response.status_code < 300 else webhook.last_successful_delivery
                    )
                )
                
                await self.db.commit()
                
        except Exception as e:
            # Update delivery with error
            await self.db.execute(
                update(WebhookDelivery)
                .where(WebhookDelivery.id == delivery.id)
                .values(
                    attempted_at=datetime.now(),
                    completed_at=datetime.now(),
                    is_successful=False,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
            )
            
            # Update webhook error statistics
            await self.db.execute(
                update(WebhookEndpoint)
                .where(WebhookEndpoint.id == webhook.id)
                .values(
                    total_deliveries=WebhookEndpoint.total_deliveries + 1,
                    failed_deliveries=WebhookEndpoint.failed_deliveries + 1,
                    last_failure_at=datetime.now(),
                    last_error_message=str(e)
                )
            )
            
            await self.db.commit()


class APIKeyService:
    """Service for managing API keys and authentication."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_api_key(
        self,
        key_data: APIKeyCreate,
        organization_id: str,
        created_by: str
    ) -> APIKey:
        """Create a new API key."""
        key_id = f"ak_{uuid.uuid4().hex[:12]}"
        key_value = f"{key_data.key_prefix or 'sk'}_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"
        
        api_key = APIKey(
            key_id=key_id,
            organization_id=organization_id,
            key_value=key_value,
            created_by=created_by,
            **key_data.model_dump()
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def get_api_key(
        self,
        key_value: str
    ) -> Optional[APIKey]:
        """Get API key by value."""
        query = select(APIKey).where(
            and_(
                APIKey.key_value == key_value,
                APIKey.is_active == True,
                or_(
                    APIKey.expires_at.is_(None),
                    APIKey.expires_at > datetime.now()
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def validate_api_key(
        self,
        key_value: str,
        required_scopes: List[str] = None
    ) -> Optional[APIKey]:
        """Validate API key and check permissions."""
        api_key = await self.get_api_key(key_value)
        if not api_key:
            return None
        
        # Check scopes if required
        if required_scopes:
            key_scopes = set(api_key.scopes)
            required_scopes_set = set(required_scopes)
            if not required_scopes_set.issubset(key_scopes):
                return None
        
        # Update last used timestamp
        await self.db.execute(
            update(APIKey)
            .where(APIKey.id == api_key.id)
            .values(last_used_at=datetime.now())
        )
        await self.db.commit()
        
        return api_key

    async def log_api_usage(
        self,
        api_key: Optional[APIKey],
        request_id: str,
        method: str,
        endpoint: str,
        path: str,
        client_ip: str,
        status_code: int,
        response_time_ms: int,
        organization_id: str,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> APIUsageLog:
        """Log API usage for monitoring and analytics."""
        log_id = f"log_{uuid.uuid4().hex[:12]}"
        
        usage_log = APIUsageLog(
            log_id=log_id,
            api_key_id=api_key.id if api_key else None,
            organization_id=organization_id,
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            path=path,
            client_ip=client_ip,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            error_message=error_message,
            auth_method="api_key" if api_key else "none"
        )
        
        self.db.add(usage_log)
        
        # Update API key usage statistics if applicable
        if api_key:
            await self.db.execute(
                update(APIKey)
                .where(APIKey.id == api_key.id)
                .values(
                    total_requests=APIKey.total_requests + 1,
                    successful_requests=APIKey.successful_requests + (1 if status_code < 400 else 0),
                    failed_requests=APIKey.failed_requests + (1 if status_code >= 400 else 0)
                )
            )
        
        await self.db.commit()
        await self.db.refresh(usage_log)
        return usage_log

    async def rotate_api_key(
        self,
        key_id: str,
        organization_id: str
    ) -> APIKey:
        """Rotate API key by generating new key value."""
        query = select(APIKey).where(
            and_(
                APIKey.key_id == key_id,
                APIKey.organization_id == organization_id
            )
        )
        
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise ValueError("API key not found")
        
        # Generate new key value
        new_key_value = f"{api_key.key_prefix or 'sk'}_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"
        
        await self.db.execute(
            update(APIKey)
            .where(APIKey.id == api_key.id)
            .values(
                key_value=new_key_value,
                last_rotation_at=datetime.now()
            )
        )
        await self.db.commit()
        
        # Refresh and return updated key
        await self.db.refresh(api_key)
        return api_key


class IntegrationHealthService:
    """Service for monitoring integration health and performance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def perform_health_check(
        self,
        integration_id: str,
        organization_id: str,
        check_type: str = "connectivity"
    ) -> IntegrationHealth:
        """Perform comprehensive health check on integration."""
        health_id = f"health_{uuid.uuid4().hex[:12]}"
        
        # Get integration details
        integration_query = select(ExternalIntegration).where(
            and_(
                ExternalIntegration.integration_id == integration_id,
                ExternalIntegration.organization_id == organization_id
            )
        )
        result = await self.db.execute(integration_query)
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise ValueError("Integration not found")
        
        health_check = IntegrationHealth(
            health_id=health_id,
            integration_id=integration_id,
            organization_id=organization_id,
            check_timestamp=datetime.now(),
            check_type=check_type
        )
        
        try:
            # Perform connectivity check
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = datetime.now()
                response = await client.get(integration.endpoint_url)
                end_time = datetime.now()
                
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                health_check.connection_successful = response.status_code < 400
                health_check.response_time_ms = response_time_ms
                health_check.is_healthy = response.status_code < 400
                health_check.health_score = self._calculate_health_score(
                    response.status_code, response_time_ms
                )
                
                if response.status_code >= 400:
                    health_check.issues_detected = [f"HTTP {response.status_code} error"]
                    health_check.severity_level = "error"
                elif response_time_ms > 5000:
                    health_check.issues_detected = ["High response time"]
                    health_check.severity_level = "warning"
                else:
                    health_check.severity_level = "info"
        
        except Exception as e:
            health_check.connection_successful = False
            health_check.is_healthy = False
            health_check.health_score = 0.0
            health_check.issues_detected = [str(e)]
            health_check.severity_level = "critical"
        
        self.db.add(health_check)
        await self.db.commit()
        await self.db.refresh(health_check)
        
        return health_check

    def _calculate_health_score(
        self, 
        status_code: int, 
        response_time_ms: int
    ) -> float:
        """Calculate health score based on various metrics."""
        score = 100.0
        
        # Deduct points for error status codes
        if status_code >= 500:
            score -= 50
        elif status_code >= 400:
            score -= 30
        
        # Deduct points for slow response times
        if response_time_ms > 10000:  # >10 seconds
            score -= 40
        elif response_time_ms > 5000:  # >5 seconds
            score -= 20
        elif response_time_ms > 2000:  # >2 seconds
            score -= 10
        
        return max(0.0, score)

    async def get_integration_health_summary(
        self,
        organization_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get health summary for all integrations in organization."""
        since_date = datetime.now() - timedelta(days=days)
        
        # Get latest health checks for each integration
        health_query = select(IntegrationHealth).where(
            and_(
                IntegrationHealth.organization_id == organization_id,
                IntegrationHealth.check_timestamp >= since_date
            )
        ).order_by(IntegrationHealth.check_timestamp.desc())
        
        result = await self.db.execute(health_query)
        health_checks = result.scalars().all()
        
        # Aggregate health data
        integration_health = {}
        for check in health_checks:
            if check.integration_id not in integration_health:
                integration_health[check.integration_id] = {
                    "latest_check": check,
                    "checks": []
                }
            integration_health[check.integration_id]["checks"].append(check)
        
        # Calculate summary statistics
        summary = {
            "total_integrations": len(integration_health),
            "healthy_integrations": 0,
            "unhealthy_integrations": 0,
            "average_health_score": 0.0,
            "critical_issues": [],
            "warning_issues": [],
        }
        
        total_score = 0.0
        for integration_id, data in integration_health.items():
            latest_check = data["latest_check"]
            if latest_check.is_healthy:
                summary["healthy_integrations"] += 1
            else:
                summary["unhealthy_integrations"] += 1
            
            total_score += latest_check.health_score
            
            if latest_check.severity_level == "critical":
                summary["critical_issues"].extend(latest_check.issues_detected)
            elif latest_check.severity_level == "warning":
                summary["warning_issues"].extend(latest_check.issues_detected)
        
        if len(integration_health) > 0:
            summary["average_health_score"] = total_score / len(integration_health)
        
        return summary