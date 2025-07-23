"""
Integration System API Endpoints - CC02 v31.0 Phase 2

Comprehensive integration API with:
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

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.integration_v31 import integration_service
from app.schemas.integration_v31 import (
    # Bulk operations
    BulkConnectorExecutionRequest,
    BulkExecutionResponse,
    ConnectorExecutionRequest,
    ConnectorListResponse,
    # Data Mapping schemas
    DataMappingCreateRequest,
    DataMappingResponse,
    # Transformation schemas
    DataTransformationCreateRequest,
    DataTransformationResponse,
    ExecutionListResponse,
    # External System schemas
    ExternalSystemCreateRequest,
    ExternalSystemListResponse,
    ExternalSystemResponse,
    ExternalSystemUpdateRequest,
    IntegrationAnalyticsRequest,
    IntegrationAnalyticsResponse,
    # Connector schemas
    IntegrationConnectorCreateRequest,
    IntegrationConnectorResponse,
    # Execution schemas
    IntegrationExecutionResponse,
    # Analytics schemas
    IntegrationHealthResponse,
    # Message Queue schemas
    IntegrationMessageCreateRequest,
    IntegrationMessageResponse,
    MappingListResponse,
    MessageListResponse,
    SystemConnectionTestRequest,
    TransformationExecutionRequest,
    TransformationListResponse,
    # Webhook schemas
    WebhookEndpointCreateRequest,
    WebhookEndpointResponse,
    WebhookListResponse,
    WebhookRequestProcessing,
)

router = APIRouter()


# =============================================================================
# External System Management
# =============================================================================


@router.post(
    "/external-systems",
    response_model=ExternalSystemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_external_system(
    request: ExternalSystemCreateRequest, db: Session = Depends(get_db)
):
    """Create a new external system configuration."""
    try:
        system = await integration_service.create_external_system(db, request.dict())
        return system
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create external system: {str(e)}",
        )


@router.get("/external-systems", response_model=ExternalSystemListResponse)
async def list_external_systems(
    organization_id: str = Query(..., description="Organization ID"),
    integration_type: Optional[str] = Query(
        None, description="Filter by integration type"
    ),
    connection_status: Optional[str] = Query(
        None, description="Filter by connection status"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List external systems with filtering and pagination."""
    try:
        systems = await integration_service.list_external_systems(
            db,
            organization_id,
            integration_type,
            connection_status,
            is_active,
            page,
            per_page,
        )
        return systems
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list external systems: {str(e)}",
        )


@router.get("/external-systems/{system_id}", response_model=ExternalSystemResponse)
async def get_external_system(system_id: str, db: Session = Depends(get_db)):
    """Get a specific external system."""
    try:
        system = await integration_service.get_external_system(db, system_id)
        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="External system not found",
            )
        return system
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get external system: {str(e)}",
        )


@router.put("/external-systems/{system_id}", response_model=ExternalSystemResponse)
async def update_external_system(
    system_id: str, request: ExternalSystemUpdateRequest, db: Session = Depends(get_db)
):
    """Update an external system configuration."""
    try:
        system = await integration_service.update_external_system(
            db, system_id, request.dict(exclude_unset=True)
        )
        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="External system not found",
            )
        return system
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update external system: {str(e)}",
        )


@router.post(
    "/external-systems/{system_id}/test-connection", response_model=Dict[str, Any]
)
async def test_system_connection(
    system_id: str, request: SystemConnectionTestRequest, db: Session = Depends(get_db)
):
    """Test connection to an external system."""
    try:
        result = await integration_service.test_system_connection(
            db, system_id, request.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}",
        )


@router.delete("/external-systems/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_external_system(system_id: str, db: Session = Depends(get_db)):
    """Delete an external system."""
    try:
        success = await integration_service.delete_external_system(db, system_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="External system not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete external system: {str(e)}",
        )


# =============================================================================
# Integration Connector Management
# =============================================================================


@router.post(
    "/connectors",
    response_model=IntegrationConnectorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_connector(
    request: IntegrationConnectorCreateRequest, db: Session = Depends(get_db)
):
    """Create a new integration connector."""
    try:
        connector = await integration_service.create_connector(db, request.dict())
        return connector
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connector: {str(e)}",
        )


@router.get("/connectors", response_model=ConnectorListResponse)
async def list_connectors(
    organization_id: str = Query(..., description="Organization ID"),
    external_system_id: Optional[str] = Query(
        None, description="Filter by external system ID"
    ),
    sync_direction: Optional[str] = Query(None, description="Filter by sync direction"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List integration connectors with filtering and pagination."""
    try:
        connectors = await integration_service.list_connectors(
            db,
            organization_id,
            external_system_id,
            sync_direction,
            entity_type,
            is_active,
            page,
            per_page,
        )
        return connectors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list connectors: {str(e)}",
        )


@router.get("/connectors/{connector_id}", response_model=IntegrationConnectorResponse)
async def get_connector(connector_id: str, db: Session = Depends(get_db)):
    """Get a specific integration connector."""
    try:
        connector = await integration_service.get_connector(db, connector_id)
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
            )
        return connector
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connector: {str(e)}",
        )


@router.put("/connectors/{connector_id}", response_model=IntegrationConnectorResponse)
async def update_connector(
    connector_id: str, request: dict, db: Session = Depends(get_db)
):
    """Update an integration connector."""
    try:
        connector = await integration_service.update_connector(
            db, connector_id, request
        )
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
            )
        return connector
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update connector: {str(e)}",
        )


@router.post(
    "/connectors/{connector_id}/execute", response_model=IntegrationExecutionResponse
)
async def execute_connector(
    connector_id: str, request: ConnectorExecutionRequest, db: Session = Depends(get_db)
):
    """Execute an integration connector."""
    try:
        execution = await integration_service.execute_connector(
            db, connector_id, request.dict()
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute connector: {str(e)}",
        )


@router.get(
    "/connectors/{connector_id}/executions", response_model=ExecutionListResponse
)
async def list_connector_executions(
    connector_id: str,
    status: Optional[str] = Query(None, description="Filter by execution status"),
    execution_type: Optional[str] = Query(None, description="Filter by execution type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List executions for a specific connector."""
    try:
        executions = await integration_service.list_connector_executions(
            db, connector_id, status, execution_type, page, per_page
        )
        return executions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}",
        )


@router.delete("/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(connector_id: str, db: Session = Depends(get_db)):
    """Delete an integration connector."""
    try:
        success = await integration_service.delete_connector(db, connector_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connector: {str(e)}",
        )


# =============================================================================
# Data Mapping Management
# =============================================================================


@router.post(
    "/data-mappings",
    response_model=DataMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_data_mapping(
    request: DataMappingCreateRequest, db: Session = Depends(get_db)
):
    """Create a new data mapping configuration."""
    try:
        mapping = await integration_service.create_data_mapping(db, request.dict())
        return mapping
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data mapping: {str(e)}",
        )


@router.get("/data-mappings", response_model=MappingListResponse)
async def list_data_mappings(
    organization_id: str = Query(..., description="Organization ID"),
    connector_id: Optional[str] = Query(None, description="Filter by connector ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    sync_direction: Optional[str] = Query(None, description="Filter by sync direction"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List data mappings with filtering and pagination."""
    try:
        mappings = await integration_service.list_data_mappings(
            db,
            organization_id,
            connector_id,
            entity_type,
            sync_direction,
            is_active,
            page,
            per_page,
        )
        return mappings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list data mappings: {str(e)}",
        )


@router.get("/data-mappings/{mapping_id}", response_model=DataMappingResponse)
async def get_data_mapping(mapping_id: str, db: Session = Depends(get_db)):
    """Get a specific data mapping."""
    try:
        mapping = await integration_service.get_data_mapping(db, mapping_id)
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data mapping not found"
            )
        return mapping
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data mapping: {str(e)}",
        )


@router.put("/data-mappings/{mapping_id}", response_model=DataMappingResponse)
async def update_data_mapping(
    mapping_id: str, request: dict, db: Session = Depends(get_db)
):
    """Update a data mapping configuration."""
    try:
        mapping = await integration_service.update_data_mapping(db, mapping_id, request)
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data mapping not found"
            )
        return mapping
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data mapping: {str(e)}",
        )


@router.delete("/data-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_mapping(mapping_id: str, db: Session = Depends(get_db)):
    """Delete a data mapping."""
    try:
        success = await integration_service.delete_data_mapping(db, mapping_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data mapping not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data mapping: {str(e)}",
        )


# =============================================================================
# Data Transformation Management
# =============================================================================


@router.post(
    "/transformations",
    response_model=DataTransformationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transformation(
    request: DataTransformationCreateRequest, db: Session = Depends(get_db)
):
    """Create a new data transformation."""
    try:
        transformation = await integration_service.create_transformation(
            db, request.dict()
        )
        return transformation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transformation: {str(e)}",
        )


@router.get("/transformations", response_model=TransformationListResponse)
async def list_transformations(
    organization_id: str = Query(..., description="Organization ID"),
    connector_id: Optional[str] = Query(None, description="Filter by connector ID"),
    transformation_type: Optional[str] = Query(
        None, description="Filter by transformation type"
    ),
    language: Optional[str] = Query(None, description="Filter by script language"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List data transformations with filtering and pagination."""
    try:
        transformations = await integration_service.list_transformations(
            db,
            organization_id,
            connector_id,
            transformation_type,
            language,
            is_active,
            page,
            per_page,
        )
        return transformations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list transformations: {str(e)}",
        )


@router.get(
    "/transformations/{transformation_id}", response_model=DataTransformationResponse
)
async def get_transformation(transformation_id: str, db: Session = Depends(get_db)):
    """Get a specific data transformation."""
    try:
        transformation = await integration_service.get_transformation(
            db, transformation_id
        )
        if not transformation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )
        return transformation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transformation: {str(e)}",
        )


@router.put(
    "/transformations/{transformation_id}", response_model=DataTransformationResponse
)
async def update_transformation(
    transformation_id: str, request: dict, db: Session = Depends(get_db)
):
    """Update a data transformation."""
    try:
        transformation = await integration_service.update_transformation(
            db, transformation_id, request
        )
        if not transformation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )
        return transformation
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transformation: {str(e)}",
        )


@router.post(
    "/transformations/{transformation_id}/execute", response_model=Dict[str, Any]
)
async def execute_transformation(
    transformation_id: str,
    request: TransformationExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute a data transformation on provided input data."""
    try:
        result = await integration_service.apply_data_transformation(
            db, transformation_id, request.input_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute transformation: {str(e)}",
        )


@router.delete(
    "/transformations/{transformation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_transformation(transformation_id: str, db: Session = Depends(get_db)):
    """Delete a data transformation."""
    try:
        success = await integration_service.delete_transformation(db, transformation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transformation: {str(e)}",
        )


# =============================================================================
# Webhook Management
# =============================================================================


@router.post(
    "/webhooks",
    response_model=WebhookEndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_endpoint(
    request: WebhookEndpointCreateRequest, db: Session = Depends(get_db)
):
    """Create a new webhook endpoint."""
    try:
        webhook = await integration_service.create_webhook_endpoint(db, request.dict())
        return webhook
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}",
        )


@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhook_endpoints(
    organization_id: str = Query(..., description="Organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List webhook endpoints with filtering and pagination."""
    try:
        webhooks = await integration_service.list_webhook_endpoints(
            db, organization_id, is_active, page, per_page
        )
        return webhooks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhooks: {str(e)}",
        )


@router.get("/webhooks/{webhook_id}", response_model=WebhookEndpointResponse)
async def get_webhook_endpoint(webhook_id: str, db: Session = Depends(get_db)):
    """Get a specific webhook endpoint."""
    try:
        webhook = await integration_service.get_webhook_endpoint(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found",
            )
        return webhook
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook: {str(e)}",
        )


@router.put("/webhooks/{webhook_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    webhook_id: str, request: dict, db: Session = Depends(get_db)
):
    """Update a webhook endpoint."""
    try:
        webhook = await integration_service.update_webhook_endpoint(
            db, webhook_id, request
        )
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found",
            )
        return webhook
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook: {str(e)}",
        )


@router.post("/webhooks/process/{endpoint_path:path}", response_model=Dict[str, Any])
async def process_webhook_request(
    endpoint_path: str, request: WebhookRequestProcessing, db: Session = Depends(get_db)
):
    """Process incoming webhook request."""
    try:
        full_endpoint = f"/webhooks/{endpoint_path}"
        result = await integration_service.process_webhook_request(
            db, full_endpoint, request.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_endpoint(webhook_id: str, db: Session = Depends(get_db)):
    """Delete a webhook endpoint."""
    try:
        success = await integration_service.delete_webhook_endpoint(db, webhook_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {str(e)}",
        )


# =============================================================================
# Message Queue Management
# =============================================================================


@router.post(
    "/messages",
    response_model=IntegrationMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_integration_message(
    request: IntegrationMessageCreateRequest, db: Session = Depends(get_db)
):
    """Create a new integration message for async processing."""
    try:
        message = await integration_service.create_integration_message(
            db, request.dict()
        )
        return message
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}",
        )


@router.get("/messages", response_model=MessageListResponse)
async def list_integration_messages(
    organization_id: str = Query(..., description="Organization ID"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    queue_name: Optional[str] = Query(None, description="Filter by queue name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List integration messages with filtering and pagination."""
    try:
        messages = await integration_service.list_integration_messages(
            db, organization_id, message_type, status, queue_name, page, per_page
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list messages: {str(e)}",
        )


@router.get("/messages/{message_id}", response_model=IntegrationMessageResponse)
async def get_integration_message(message_id: str, db: Session = Depends(get_db)):
    """Get a specific integration message."""
    try:
        message = await integration_service.get_integration_message(db, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message: {str(e)}",
        )


@router.post("/messages/process", response_model=Dict[str, Any])
async def process_pending_messages(
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum messages to process"),
    db: Session = Depends(get_db),
):
    """Process pending integration messages."""
    try:
        result = await integration_service.process_pending_messages(
            db, organization_id, limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process messages: {str(e)}",
        )


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration_message(message_id: str, db: Session = Depends(get_db)):
    """Delete an integration message."""
    try:
        success = await integration_service.delete_integration_message(db, message_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}",
        )


# =============================================================================
# Analytics & Health Monitoring
# =============================================================================


@router.get("/health", response_model=IntegrationHealthResponse)
async def get_integration_health(
    organization_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
):
    """Get comprehensive integration system health and metrics."""
    try:
        health = await integration_service.get_integration_health(db, organization_id)
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration health: {str(e)}",
        )


@router.post("/analytics", response_model=IntegrationAnalyticsResponse)
async def get_integration_analytics(
    request: IntegrationAnalyticsRequest, db: Session = Depends(get_db)
):
    """Get comprehensive integration analytics and performance metrics."""
    try:
        analytics = await integration_service.get_integration_analytics(
            db, request.dict()
        )
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}",
        )


# =============================================================================
# Bulk Operations
# =============================================================================


@router.post("/connectors/bulk-execute", response_model=BulkExecutionResponse)
async def bulk_execute_connectors(
    request: BulkConnectorExecutionRequest, db: Session = Depends(get_db)
):
    """Execute multiple connectors in bulk."""
    try:
        result = await integration_service.bulk_execute_connectors(db, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute bulk operations: {str(e)}",
        )


@router.post("/external-systems/bulk-health-check", response_model=Dict[str, Any])
async def bulk_health_check_systems(
    organization_id: str = Query(..., description="Organization ID"),
    system_ids: Optional[List[str]] = Query(None, description="System IDs to check"),
    db: Session = Depends(get_db),
):
    """Perform bulk health check on external systems."""
    try:
        result = await integration_service.bulk_health_check_systems(
            db, organization_id, system_ids
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk health check: {str(e)}",
        )


# =============================================================================
# Execution Management
# =============================================================================


@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    organization_id: str = Query(..., description="Organization ID"),
    connector_id: Optional[str] = Query(None, description="Filter by connector ID"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    execution_type: Optional[str] = Query(None, description="Filter by execution type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List integration executions with advanced filtering."""
    try:
        executions = await integration_service.list_executions(
            db,
            organization_id,
            connector_id,
            status,
            execution_type,
            start_date,
            end_date,
            page,
            per_page,
        )
        return executions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}",
        )


@router.get("/executions/{execution_id}", response_model=IntegrationExecutionResponse)
async def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get a specific integration execution."""
    try:
        execution = await integration_service.get_execution(db, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found"
            )
        return execution
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution: {str(e)}",
        )


@router.post(
    "/executions/{execution_id}/retry", response_model=IntegrationExecutionResponse
)
async def retry_execution(execution_id: str, db: Session = Depends(get_db)):
    """Retry a failed integration execution."""
    try:
        execution = await integration_service.retry_execution(db, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found"
            )
        return execution
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry execution: {str(e)}",
        )


# =============================================================================
# Configuration & Utilities
# =============================================================================


@router.get("/integration-types", response_model=List[Dict[str, Any]])
async def get_integration_types():
    """Get available integration types and their descriptions."""
    integration_types = [
        {
            "value": "api",
            "label": "REST API",
            "description": "RESTful web service integration",
        },
        {
            "value": "database",
            "label": "Database",
            "description": "Direct database connection",
        },
        {"value": "file", "label": "File", "description": "File-based data exchange"},
        {
            "value": "message_queue",
            "label": "Message Queue",
            "description": "Message queue integration",
        },
        {
            "value": "webhook",
            "label": "Webhook",
            "description": "HTTP webhook integration",
        },
        {"value": "ftp", "label": "FTP/SFTP", "description": "File transfer protocol"},
        {"value": "email", "label": "Email", "description": "Email-based integration"},
        {
            "value": "cloud_storage",
            "label": "Cloud Storage",
            "description": "Cloud storage integration",
        },
        {
            "value": "erp",
            "label": "ERP System",
            "description": "Enterprise resource planning",
        },
        {
            "value": "crm",
            "label": "CRM System",
            "description": "Customer relationship management",
        },
        {
            "value": "accounting",
            "label": "Accounting",
            "description": "Accounting system integration",
        },
        {
            "value": "ecommerce",
            "label": "E-commerce",
            "description": "E-commerce platform integration",
        },
    ]
    return integration_types


@router.get("/data-formats", response_model=List[Dict[str, Any]])
async def get_data_formats():
    """Get available data formats for integration."""
    data_formats = [
        {"value": "json", "label": "JSON", "description": "JavaScript Object Notation"},
        {"value": "xml", "label": "XML", "description": "Extensible Markup Language"},
        {"value": "csv", "label": "CSV", "description": "Comma-separated values"},
        {"value": "excel", "label": "Excel", "description": "Microsoft Excel format"},
        {
            "value": "fixed_width",
            "label": "Fixed Width",
            "description": "Fixed-width text format",
        },
        {"value": "edi", "label": "EDI", "description": "Electronic Data Interchange"},
        {"value": "custom", "label": "Custom", "description": "Custom data format"},
    ]
    return data_formats


@router.post("/validate-mapping", response_model=Dict[str, Any])
async def validate_data_mapping(
    mapping_config: Dict[str, Any],
    sample_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
):
    """Validate data mapping configuration against sample data."""
    try:
        result = await integration_service.validate_data_mapping(
            mapping_config, sample_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate mapping: {str(e)}",
        )


@router.post("/test-transformation", response_model=Dict[str, Any])
async def test_transformation_script(
    transformation_script: str,
    sample_input: List[Dict[str, Any]],
    language: str = "python",
    db: Session = Depends(get_db),
):
    """Test a transformation script against sample input data."""
    try:
        result = await integration_service.test_transformation_script(
            transformation_script, sample_input, language
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test transformation: {str(e)}",
        )


@router.get("/system-templates", response_model=List[Dict[str, Any]])
async def get_system_templates():
    """Get predefined templates for common external systems."""
    try:
        templates = await integration_service.get_system_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system templates: {str(e)}",
        )


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_integration_logs(
    organization_id: str = Query(..., description="Organization ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Get integration audit logs with filtering."""
    try:
        logs = await integration_service.get_integration_logs(
            db,
            organization_id,
            entity_type,
            entity_id,
            action_type,
            start_date,
            end_date,
            page,
            per_page,
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration logs: {str(e)}",
        )
