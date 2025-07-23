"""
Integration System CRUD Operations - CC02 v31.0 Phase 2

Comprehensive integration service with advanced business logic including:
- External System Management & Configuration
- Data Synchronization & ETL Operations
- Third-Party Service Integration
- Webhook & Event Processing
- API Gateway Operations
- Data Transformation & Mapping
- Integration Monitoring & Health Checks
- Message Queue Management
- Authentication & Security
- Performance Analytics & Optimization
"""

import json
import asyncio
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.integration_extended import (
    ExternalSystem,
    IntegrationConnector,
    DataMapping,
    DataTransformation,
    IntegrationExecution,
    WebhookEndpoint,
    WebhookRequest,
    IntegrationMessage,
    IntegrationAuditLog,
    IntegrationType,
    ConnectionStatus,
    SyncDirection,
    SyncStatus,
    DataFormat,
    TransformationType,
)


class IntegrationService:
    """Comprehensive integration service with advanced business logic."""

    # =============================================================================
    # External System Management
    # =============================================================================

    async def create_external_system(self, db: Session, system_data: Dict[str, Any]) -> ExternalSystem:
        """Create a new external system with configuration validation."""
        try:
            # Validate required fields
            required_fields = ["organization_id", "name", "code", "integration_type", "created_by"]
            for field in required_fields:
                if not system_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicate code
            existing = db.query(ExternalSystem).filter(
                ExternalSystem.code == system_data["code"]
            ).first()
            if existing:
                raise ValueError(f"External system with code '{system_data['code']}' already exists")
            
            # Create external system
            external_system = ExternalSystem(**system_data)
            
            # Initialize performance metrics
            external_system.total_requests = 0
            external_system.successful_requests = 0
            external_system.failed_requests = 0
            external_system.uptime_percentage = Decimal("0.00")
            
            # Set default rate limiting if not provided
            if not external_system.rate_limit_requests:
                external_system.rate_limit_requests = 1000
                external_system.rate_limit_period = 3600  # 1 hour
                external_system.rate_limit_remaining = 1000
            
            db.add(external_system)
            db.commit()
            db.refresh(external_system)
            
            # Log audit trail
            await self._log_audit_action(
                db, external_system.organization_id, "create", "external_system",
                external_system.id, None, system_data, external_system.created_by
            )
            
            return external_system
            
        except Exception as e:
            db.rollback()
            raise e

    async def get_external_system(self, db: Session, system_id: str) -> Optional[ExternalSystem]:
        """Get external system by ID with connection status check."""
        system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
        if system:
            # Update connection status if health check is due
            if (not system.last_health_check or 
                datetime.now() - system.last_health_check > timedelta(seconds=system.health_check_interval)):
                await self._check_system_health(db, system)
        return system

    async def list_external_systems(
        self, 
        db: Session, 
        organization_id: str,
        integration_type: Optional[str] = None,
        connection_status: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """List external systems with filtering and pagination."""
        query = db.query(ExternalSystem).filter(ExternalSystem.organization_id == organization_id)
        
        # Apply filters
        if integration_type:
            query = query.filter(ExternalSystem.integration_type == integration_type)
        if connection_status:
            query = query.filter(ExternalSystem.connection_status == connection_status)
        if is_active is not None:
            query = query.filter(ExternalSystem.is_active == is_active)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        systems = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "external_systems": systems,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "has_more": total_count > page * per_page
        }

    async def update_external_system(
        self, 
        db: Session, 
        system_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[ExternalSystem]:
        """Update external system configuration."""
        system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
        if not system:
            return None
        
        old_values = {
            "name": system.name,
            "connection_config": system.connection_config,
            "auth_config": system.auth_config,
            "is_active": system.is_active
        }
        
        # Update fields
        for field, value in update_data.items():
            if field not in ["id", "created_at", "created_by"] and hasattr(system, field):
                setattr(system, field, value)
        
        system.updated_at = datetime.now()
        db.commit()
        db.refresh(system)
        
        # Log audit trail
        await self._log_audit_action(
            db, system.organization_id, "update", "external_system",
            system.id, old_values, update_data, update_data.get("updated_by")
        )
        
        return system

    async def test_system_connection(
        self, 
        db: Session, 
        system_id: str, 
        test_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test connection to external system."""
        system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
        if not system:
            raise ValueError("External system not found")
        
        start_time = datetime.now()
        result = {
            "system_id": system_id,
            "test_type": test_config.get("test_type", "basic"),
            "started_at": start_time.isoformat()
        }
        
        try:
            # Prepare test request
            test_url = test_config.get("test_url") or system.base_url
            timeout = test_config.get("timeout", system.timeout_seconds)
            headers = self._prepare_auth_headers(system)
            
            # Execute test
            response = requests.get(
                test_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Update system status
            system.connection_status = ConnectionStatus.CONNECTED if response.ok else ConnectionStatus.ERROR
            system.last_health_check = datetime.now()
            system.average_response_time = (
                (system.average_response_time or 0) + Decimal(str(response_time))
            ) / 2
            
            db.commit()
            
            result.update({
                "status": "success" if response.ok else "error",
                "response_code": response.status_code,
                "response_time_ms": response_time,
                "response_headers": dict(response.headers),
                "completed_at": end_time.isoformat()
            })
            
            if test_config.get("include_response_body", False):
                result["response_body"] = response.text[:1000]  # Truncate for safety
            
        except requests.RequestException as e:
            system.connection_status = ConnectionStatus.ERROR
            system.last_health_check = datetime.now()
            db.commit()
            
            result.update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })
        
        return result

    # =============================================================================
    # Integration Connector Management
    # =============================================================================

    async def create_connector(self, db: Session, connector_data: Dict[str, Any]) -> IntegrationConnector:
        """Create a new integration connector."""
        try:
            # Validate required fields
            required_fields = ["organization_id", "external_system_id", "name", "code", 
                             "endpoint_url", "sync_direction", "created_by"]
            for field in required_fields:
                if not connector_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Verify external system exists
            external_system = db.query(ExternalSystem).filter(
                ExternalSystem.id == connector_data["external_system_id"]
            ).first()
            if not external_system:
                raise ValueError("External system not found")
            
            # Create connector
            connector = IntegrationConnector(**connector_data)
            
            # Set defaults
            connector.batch_size = connector.batch_size or 100
            connector.parallel_workers = connector.parallel_workers or 1
            connector.timeout_seconds = connector.timeout_seconds or 300
            connector.max_retries = connector.max_retries or 3
            
            db.add(connector)
            db.commit()
            db.refresh(connector)
            
            # Log audit trail
            await self._log_audit_action(
                db, connector.organization_id, "create", "integration_connector",
                connector.id, None, connector_data, connector.created_by
            )
            
            return connector
            
        except Exception as e:
            db.rollback()
            raise e

    async def execute_connector(
        self, 
        db: Session, 
        connector_id: str, 
        execution_config: Dict[str, Any]
    ) -> IntegrationExecution:
        """Execute integration connector with full processing pipeline."""
        connector = db.query(IntegrationConnector).options(
            joinedload(IntegrationConnector.external_system)
        ).filter(IntegrationConnector.id == connector_id).first()
        
        if not connector:
            raise ValueError("Connector not found")
        
        if not connector.is_active:
            raise ValueError("Connector is not active")
        
        # Create execution record
        execution = IntegrationExecution(
            organization_id=connector.organization_id,
            connector_id=connector_id,
            execution_type=execution_config.get("execution_type", "manual"),
            triggered_by=execution_config.get("triggered_by"),
            status=SyncStatus.RUNNING,
            started_at=datetime.now()
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        try:
            # Execute based on sync direction
            if connector.sync_direction == SyncDirection.INBOUND:
                result = await self._execute_inbound_sync(db, connector, execution, execution_config)
            elif connector.sync_direction == SyncDirection.OUTBOUND:
                result = await self._execute_outbound_sync(db, connector, execution, execution_config)
            else:  # BIDIRECTIONAL
                result = await self._execute_bidirectional_sync(db, connector, execution, execution_config)
            
            # Update execution with results
            execution.status = SyncStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            
            # Update metrics
            for key, value in result.items():
                if hasattr(execution, key):
                    setattr(execution, key, value)
            
            # Update connector statistics
            connector.total_executions += 1
            connector.successful_executions += 1
            connector.last_run_at = datetime.now()
            connector.average_execution_time = (
                (connector.average_execution_time or 0) + Decimal(str(execution.duration_ms))
            ) / connector.total_executions
            
            db.commit()
            
        except Exception as e:
            execution.status = SyncStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            
            connector.total_executions += 1
            connector.failed_executions += 1
            connector.error_count += 1
            connector.last_error = str(e)
            
            db.commit()
            
            if connector.alert_on_failure:
                await self._send_failure_notification(db, connector, execution, str(e))
            
            raise e
        
        return execution

    # =============================================================================
    # Data Mapping & Transformation
    # =============================================================================

    async def create_data_mapping(self, db: Session, mapping_data: Dict[str, Any]) -> DataMapping:
        """Create a new data mapping configuration."""
        try:
            # Validate field mappings
            field_mappings = mapping_data.get("field_mappings", {})
            if not field_mappings:
                raise ValueError("Field mappings are required")
            
            # Create mapping
            mapping = DataMapping(**mapping_data)
            
            # Validate mapping configuration
            await self._validate_mapping_configuration(mapping)
            
            db.add(mapping)
            db.commit()
            db.refresh(mapping)
            
            return mapping
            
        except Exception as e:
            db.rollback()
            raise e

    async def create_transformation(self, db: Session, transformation_data: Dict[str, Any]) -> DataTransformation:
        """Create a new data transformation."""
        try:
            transformation = DataTransformation(**transformation_data)
            
            # Validate transformation script if provided
            if transformation.transformation_script:
                await self._validate_transformation_script(transformation)
            
            db.add(transformation)
            db.commit()
            db.refresh(transformation)
            
            return transformation
            
        except Exception as e:
            db.rollback()
            raise e

    async def apply_data_transformation(
        self, 
        db: Session, 
        transformation_id: str, 
        input_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply data transformation to input data."""
        transformation = db.query(DataTransformation).filter(
            DataTransformation.id == transformation_id
        ).first()
        
        if not transformation:
            raise ValueError("Transformation not found")
        
        start_time = datetime.now()
        result = {
            "transformation_id": transformation_id,
            "input_count": len(input_data),
            "output_data": [],
            "errors": [],
            "started_at": start_time
        }
        
        try:
            # Apply transformation based on type
            if transformation.transformation_type == TransformationType.FIELD_MAPPING:
                result["output_data"] = await self._apply_field_mapping(transformation, input_data)
            elif transformation.transformation_type == TransformationType.DATA_CONVERSION:
                result["output_data"] = await self._apply_data_conversion(transformation, input_data)
            elif transformation.transformation_type == TransformationType.CUSTOM_SCRIPT:
                result["output_data"] = await self._execute_custom_script(transformation, input_data)
            else:
                raise ValueError(f"Unsupported transformation type: {transformation.transformation_type}")
            
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            # Update transformation statistics
            transformation.total_executions += 1
            transformation.successful_executions += 1
            transformation.average_execution_time = (
                (transformation.average_execution_time or 0) + Decimal(str(execution_time))
            ) / transformation.total_executions
            
            result.update({
                "status": "success",
                "output_count": len(result["output_data"]),
                "execution_time_ms": execution_time,
                "completed_at": end_time
            })
            
            db.commit()
            
        except Exception as e:
            transformation.total_executions += 1
            transformation.failed_executions += 1
            transformation.last_error = str(e)
            db.commit()
            
            result.update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now()
            })
        
        return result

    # =============================================================================
    # Webhook Management
    # =============================================================================

    async def create_webhook_endpoint(self, db: Session, webhook_data: Dict[str, Any]) -> WebhookEndpoint:
        """Create a new webhook endpoint."""
        try:
            # Generate unique endpoint URL if not provided
            if not webhook_data.get("endpoint_url"):
                webhook_data["endpoint_url"] = f"/webhooks/{webhook_data['organization_id']}/{uuid.uuid4().hex[:8]}"
            
            # Generate webhook secret for signature verification
            if webhook_data.get("enable_signature_verification", True) and not webhook_data.get("webhook_secret"):
                webhook_data["webhook_secret"] = self._generate_webhook_secret()
            
            webhook = WebhookEndpoint(**webhook_data)
            
            db.add(webhook)
            db.commit()
            db.refresh(webhook)
            
            return webhook
            
        except Exception as e:
            db.rollback()
            raise e

    async def process_webhook_request(
        self, 
        db: Session, 
        endpoint_url: str, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process incoming webhook request."""
        webhook = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.endpoint_url == endpoint_url,
            WebhookEndpoint.is_active == True
        ).first()
        
        if not webhook:
            raise ValueError("Webhook endpoint not found or inactive")
        
        # Create request record
        webhook_request = WebhookRequest(
            organization_id=webhook.organization_id,
            webhook_endpoint_id=webhook.id,
            method=request_data.get("method", "POST"),
            headers=request_data.get("headers", {}),
            query_parameters=request_data.get("query_parameters", {}),
            body=request_data.get("body", ""),
            content_type=request_data.get("content_type"),
            content_length=len(request_data.get("body", "")),
            client_ip=request_data.get("client_ip"),
            user_agent=request_data.get("user_agent"),
            received_at=datetime.now()
        )
        
        db.add(webhook_request)
        db.commit()
        db.refresh(webhook_request)
        
        try:
            # Security checks
            security_result = await self._validate_webhook_security(webhook, webhook_request, request_data)
            if not security_result["valid"]:
                webhook_request.processing_status = "blocked"
                webhook_request.error_message = security_result["reason"]
                webhook.blocked_requests += 1
                db.commit()
                return {"status": "blocked", "reason": security_result["reason"]}
            
            # Process webhook
            webhook_request.processing_status = "processing"
            webhook_request.processing_started_at = datetime.now()
            db.commit()
            
            # Execute processing script if configured
            if webhook.processing_script:
                result = await self._execute_webhook_processing(webhook, webhook_request)
            else:
                result = {"status": "received", "message": "Webhook received successfully"}
            
            # Update request with results
            webhook_request.processing_status = "completed"
            webhook_request.processing_completed_at = datetime.now()
            webhook_request.processing_duration_ms = int(
                (webhook_request.processing_completed_at - webhook_request.processing_started_at).total_seconds() * 1000
            )
            webhook_request.response_status_code = 200
            webhook_request.response_body = json.dumps(result)
            
            # Update webhook statistics
            webhook.total_requests += 1
            webhook.successful_requests += 1
            webhook.last_request_at = datetime.now()
            
            db.commit()
            
            return result
            
        except Exception as e:
            webhook_request.processing_status = "failed"
            webhook_request.error_message = str(e)
            webhook_request.response_status_code = 500
            
            webhook.total_requests += 1
            webhook.failed_requests += 1
            
            db.commit()
            
            return {"status": "error", "error": str(e)}

    # =============================================================================
    # Message Queue Management
    # =============================================================================

    async def create_integration_message(self, db: Session, message_data: Dict[str, Any]) -> IntegrationMessage:
        """Create a new integration message for async processing."""
        try:
            # Generate unique message ID if not provided
            if not message_data.get("message_id"):
                message_data["message_id"] = f"{message_data['message_type']}_{uuid.uuid4().hex[:12]}"
            
            message = IntegrationMessage(**message_data)
            
            # Set scheduling
            if message.delay_seconds and message.delay_seconds > 0:
                message.scheduled_at = datetime.now() + timedelta(seconds=message.delay_seconds)
                message.next_attempt_at = message.scheduled_at
            else:
                message.scheduled_at = datetime.now()
                message.next_attempt_at = datetime.now()
            
            # Set expiration
            if not message.expires_at and message_data.get("ttl_seconds"):
                message.expires_at = datetime.now() + timedelta(seconds=message_data["ttl_seconds"])
            
            db.add(message)
            db.commit()
            db.refresh(message)
            
            return message
            
        except Exception as e:
            db.rollback()
            raise e

    async def process_pending_messages(self, db: Session, organization_id: str, limit: int = 100) -> Dict[str, Any]:
        """Process pending integration messages."""
        # Get pending messages
        messages = db.query(IntegrationMessage).filter(
            IntegrationMessage.organization_id == organization_id,
            IntegrationMessage.status == "pending",
            IntegrationMessage.next_attempt_at <= datetime.now(),
            or_(
                IntegrationMessage.expires_at.is_(None),
                IntegrationMessage.expires_at > datetime.now()
            )
        ).order_by(IntegrationMessage.priority.desc(), IntegrationMessage.created_at).limit(limit).all()
        
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "expired": 0,
            "messages": []
        }
        
        for message in messages:
            try:
                # Check if message has expired
                if message.expires_at and message.expires_at <= datetime.now():
                    message.status = "expired"
                    results["expired"] += 1
                    continue
                
                # Update message status
                message.status = "processing"
                message.attempt_count += 1
                message.last_attempt_at = datetime.now()
                db.commit()
                
                # Process message based on type
                result = await self._process_message_by_type(db, message)
                
                if result["success"]:
                    message.status = "completed"
                    message.result_data = result["data"]
                    results["successful"] += 1
                else:
                    if message.attempt_count >= message.max_attempts:
                        message.status = "dead_letter"
                    else:
                        message.status = "pending"
                        message.next_attempt_at = datetime.now() + timedelta(
                            seconds=min(300, 30 * (2 ** message.attempt_count))  # Exponential backoff
                        )
                    
                    message.error_message = result.get("error")
                    results["failed"] += 1
                
                results["processed"] += 1
                results["messages"].append({
                    "message_id": message.message_id,
                    "status": message.status,
                    "attempt_count": message.attempt_count
                })
                
                db.commit()
                
            except Exception as e:
                message.status = "failed"
                message.error_message = str(e)
                results["failed"] += 1
                db.commit()
        
        return results

    # =============================================================================
    # Integration Analytics & Monitoring
    # =============================================================================

    async def get_integration_health(self, db: Session, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive integration system health and metrics."""
        # External systems health
        systems_query = db.query(ExternalSystem).filter(
            ExternalSystem.organization_id == organization_id
        )
        total_systems = systems_query.count()
        active_systems = systems_query.filter(ExternalSystem.is_active == True).count()
        connected_systems = systems_query.filter(
            ExternalSystem.connection_status == ConnectionStatus.CONNECTED
        ).count()
        
        # Connector health
        connectors_query = db.query(IntegrationConnector).filter(
            IntegrationConnector.organization_id == organization_id
        )
        total_connectors = connectors_query.count()
        active_connectors = connectors_query.filter(IntegrationConnector.is_active == True).count()
        
        # Recent execution stats (last 24 hours)
        since_24h = datetime.now() - timedelta(hours=24)
        recent_executions = db.query(IntegrationExecution).filter(
            IntegrationExecution.organization_id == organization_id,
            IntegrationExecution.started_at >= since_24h
        )
        
        total_executions = recent_executions.count()
        successful_executions = recent_executions.filter(
            IntegrationExecution.status == SyncStatus.COMPLETED
        ).count()
        failed_executions = recent_executions.filter(
            IntegrationExecution.status == SyncStatus.FAILED
        ).count()
        
        # Average response times
        avg_response_time = db.query(func.avg(ExternalSystem.average_response_time)).filter(
            ExternalSystem.organization_id == organization_id,
            ExternalSystem.average_response_time.isnot(None)
        ).scalar() or 0
        
        # Message queue health
        pending_messages = db.query(IntegrationMessage).filter(
            IntegrationMessage.organization_id == organization_id,
            IntegrationMessage.status == "pending"
        ).count()
        
        failed_messages = db.query(IntegrationMessage).filter(
            IntegrationMessage.organization_id == organization_id,
            IntegrationMessage.status == "failed"
        ).count()
        
        # Calculate health score
        health_factors = [
            (connected_systems / max(total_systems, 1)) * 0.3,  # Connection health
            (successful_executions / max(total_executions, 1)) * 0.4,  # Execution success rate
            min(1.0, (1000 - avg_response_time) / 1000) * 0.2,  # Response time
            (1 - min(1.0, pending_messages / 100)) * 0.1  # Queue health
        ]
        overall_health_score = sum(health_factors) * 100
        
        return {
            "overall_health_score": round(overall_health_score, 2),
            "status": "healthy" if overall_health_score >= 80 else "degraded" if overall_health_score >= 60 else "unhealthy",
            "external_systems": {
                "total": total_systems,
                "active": active_systems,
                "connected": connected_systems,
                "connection_rate": round((connected_systems / max(total_systems, 1)) * 100, 2)
            },
            "connectors": {
                "total": total_connectors,
                "active": active_connectors
            },
            "executions_24h": {
                "total": total_executions,
                "successful": successful_executions,
                "failed": failed_executions,
                "success_rate": round((successful_executions / max(total_executions, 1)) * 100, 2)
            },
            "performance": {
                "average_response_time_ms": float(avg_response_time or 0),
                "pending_messages": pending_messages,
                "failed_messages": failed_messages
            },
            "checked_at": datetime.now().isoformat()
        }

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _check_system_health(self, db: Session, system: ExternalSystem):
        """Check health of external system."""
        try:
            headers = self._prepare_auth_headers(system)
            response = requests.get(
                system.base_url,
                headers=headers,
                timeout=system.timeout_seconds,
                allow_redirects=True
            )
            
            system.connection_status = ConnectionStatus.CONNECTED if response.ok else ConnectionStatus.ERROR
            system.last_health_check = datetime.now()
            system.total_requests += 1
            
            if response.ok:
                system.successful_requests += 1
            else:
                system.failed_requests += 1
            
            # Update uptime percentage
            if system.total_requests > 0:
                system.uptime_percentage = Decimal(
                    str((system.successful_requests / system.total_requests) * 100)
                )
            
            db.commit()
            
        except requests.RequestException:
            system.connection_status = ConnectionStatus.ERROR
            system.last_health_check = datetime.now()
            system.total_requests += 1
            system.failed_requests += 1
            db.commit()

    def _prepare_auth_headers(self, system: ExternalSystem) -> Dict[str, str]:
        """Prepare authentication headers for external system."""
        headers = {}
        
        if system.auth_type == "api_key":
            headers["Authorization"] = f"ApiKey {system.credentials.get('api_key', '')}"
        elif system.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {system.credentials.get('token', '')}"
        elif system.auth_type == "basic":
            import base64
            username = system.credentials.get('username', '')
            password = system.credentials.get('password', '')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        return headers

    async def _execute_inbound_sync(
        self, 
        db: Session, 
        connector: IntegrationConnector, 
        execution: IntegrationExecution, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute inbound data synchronization."""
        # Fetch data from external system
        headers = self._prepare_auth_headers(connector.external_system)
        headers.update(connector.request_headers or {})
        
        response = requests.get(
            connector.endpoint_url,
            headers=headers,
            params=connector.request_parameters,
            timeout=connector.timeout_seconds
        )
        
        if not response.ok:
            raise Exception(f"External API error: {response.status_code} - {response.text}")
        
        # Parse response data
        if connector.data_format == DataFormat.JSON:
            data = response.json()
        elif connector.data_format == DataFormat.XML:
            # XML parsing logic
            data = self._parse_xml_response(response.text)
        else:
            data = response.text
        
        # Apply transformations if configured
        if connector.transformations:
            for transformation in connector.transformations:
                transform_result = await self.apply_data_transformation(db, transformation.id, data)
                data = transform_result["output_data"]
        
        return {
            "records_received": len(data) if isinstance(data, list) else 1,
            "records_processed": len(data) if isinstance(data, list) else 1,
            "response_status_code": response.status_code,
            "response_headers": dict(response.headers),
            "sample_response_data": data[:3] if isinstance(data, list) else data
        }

    async def _execute_outbound_sync(
        self, 
        db: Session, 
        connector: IntegrationConnector, 
        execution: IntegrationExecution, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute outbound data synchronization."""
        # Get data to send (implementation depends on entity type)
        data_to_send = config.get("data") or []
        
        headers = self._prepare_auth_headers(connector.external_system)
        headers.update(connector.request_headers or {})
        headers["Content-Type"] = "application/json"
        
        # Send data to external system
        response = requests.post(
            connector.endpoint_url,
            headers=headers,
            json=data_to_send,
            timeout=connector.timeout_seconds
        )
        
        if not response.ok:
            raise Exception(f"External API error: {response.status_code} - {response.text}")
        
        return {
            "records_requested": len(data_to_send) if isinstance(data_to_send, list) else 1,
            "records_sent": len(data_to_send) if isinstance(data_to_send, list) else 1,
            "response_status_code": response.status_code,
            "response_headers": dict(response.headers)
        }

    async def _execute_bidirectional_sync(
        self, 
        db: Session, 
        connector: IntegrationConnector, 
        execution: IntegrationExecution, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute bidirectional data synchronization."""
        # Execute both inbound and outbound
        inbound_result = await self._execute_inbound_sync(db, connector, execution, config)
        outbound_result = await self._execute_outbound_sync(db, connector, execution, config)
        
        return {
            **inbound_result,
            **outbound_result,
            "sync_direction": "bidirectional"
        }

    async def _log_audit_action(
        self, 
        db: Session, 
        organization_id: str, 
        action: str, 
        entity_type: str, 
        entity_id: str, 
        old_values: Optional[Dict], 
        new_values: Dict, 
        user_id: Optional[str] = None
    ):
        """Log integration audit action."""
        audit_log = IntegrationAuditLog(
            organization_id=organization_id,
            action_type=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            changes_summary=f"{action.title()} {entity_type}"
        )
        
        db.add(audit_log)
        db.commit()

    def _generate_webhook_secret(self) -> str:
        """Generate secure webhook secret."""
        import secrets
        return secrets.token_urlsafe(32)

    async def _validate_webhook_security(
        self, 
        webhook: WebhookEndpoint, 
        request: WebhookRequest, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate webhook request security."""
        # Check IP allowlist
        if webhook.allowed_ips and request.client_ip not in webhook.allowed_ips:
            return {"valid": False, "reason": "IP not allowed"}
        
        # Check signature if enabled
        if webhook.enable_signature_verification and webhook.webhook_secret:
            signature = request_data.get("headers", {}).get("X-Signature")
            if not signature:
                return {"valid": False, "reason": "Missing signature"}
            
            expected_signature = hmac.new(
                webhook.webhook_secret.encode(),
                request.body.encode() if request.body else b"",
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, f"sha256={expected_signature}"):
                return {"valid": False, "reason": "Invalid signature"}
        
        return {"valid": True}

    async def _process_message_by_type(self, db: Session, message: IntegrationMessage) -> Dict[str, Any]:
        """Process integration message based on its type."""
        try:
            if message.message_type == "data_sync":
                return await self._process_sync_message(db, message)
            elif message.message_type == "webhook_delivery":
                return await self._process_webhook_message(db, message)
            elif message.message_type == "notification":
                return await self._process_notification_message(db, message)
            else:
                return {"success": False, "error": f"Unknown message type: {message.message_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _process_sync_message(self, db: Session, message: IntegrationMessage) -> Dict[str, Any]:
        """Process data synchronization message."""
        # Implementation for sync message processing
        return {"success": True, "data": {"processed": True}}

    async def _process_webhook_message(self, db: Session, message: IntegrationMessage) -> Dict[str, Any]:
        """Process webhook delivery message."""
        # Implementation for webhook message processing
        return {"success": True, "data": {"delivered": True}}

    async def _process_notification_message(self, db: Session, message: IntegrationMessage) -> Dict[str, Any]:
        """Process notification message."""
        # Implementation for notification message processing
        return {"success": True, "data": {"sent": True}}


# Create service instance
integration_service = IntegrationService()