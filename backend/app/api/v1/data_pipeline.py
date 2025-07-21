"""Data Pipeline & ETL Processing API endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.data_pipeline import (
    pipeline_manager,
    DataSource,
    DataSourceType,
    DataFormat,
    TransformationStep,
    TransformationType,
    DataTarget,
    Pipeline,
    PipelineStatus,
    check_data_pipeline_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class DataSourceRequest(BaseModel):
    """Data source creation request."""
    name: str = Field(..., max_length=200)
    source_type: DataSourceType
    connection_config: Dict[str, Any]
    data_format: DataFormat
    schema_definition: Optional[Dict[str, Any]] = {}
    refresh_interval: int = Field(3600, ge=60, le=86400)
    enabled: bool = True


class DataSourceResponse(BaseModel):
    """Data source response schema."""
    id: str
    name: str
    source_type: str
    connection_config: Dict[str, Any]
    data_format: str
    schema_definition: Dict[str, Any]
    refresh_interval: int
    enabled: bool
    last_updated: datetime

    class Config:
        from_attributes = True


class TransformationStepRequest(BaseModel):
    """Transformation step request."""
    name: str = Field(..., max_length=200)
    transformation_type: TransformationType
    configuration: Dict[str, Any]
    order: int = Field(0, ge=0)
    enabled: bool = True


class TransformationStepResponse(BaseModel):
    """Transformation step response schema."""
    id: str
    name: str
    transformation_type: str
    configuration: Dict[str, Any]
    order: int
    enabled: bool

    class Config:
        from_attributes = True


class DataTargetRequest(BaseModel):
    """Data target creation request."""
    name: str = Field(..., max_length=200)
    target_type: DataSourceType
    connection_config: Dict[str, Any]
    data_format: DataFormat
    batch_size: int = Field(1000, ge=1, le=10000)
    enabled: bool = True


class DataTargetResponse(BaseModel):
    """Data target response schema."""
    id: str
    name: str
    target_type: str
    connection_config: Dict[str, Any]
    data_format: str
    batch_size: int
    enabled: bool

    class Config:
        from_attributes = True


class PipelineRequest(BaseModel):
    """Pipeline creation request."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    sources: Optional[List[DataSourceRequest]] = []
    transformations: Optional[List[TransformationStepRequest]] = []
    targets: Optional[List[DataTargetRequest]] = []
    schedule: Optional[str] = Field(None, max_length=100)
    enabled: bool = True


class PipelineResponse(BaseModel):
    """Pipeline response schema."""
    id: str
    name: str
    description: str
    sources: List[DataSourceResponse]
    transformations: List[TransformationStepResponse]
    targets: List[DataTargetResponse]
    schedule: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]

    class Config:
        from_attributes = True


class PipelineExecutionResponse(BaseModel):
    """Pipeline execution response schema."""
    id: str
    pipeline_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    records_processed: int
    records_failed: int
    error_message: Optional[str]
    execution_metrics: Dict[str, Any]

    class Config:
        from_attributes = True


class SystemStatusResponse(BaseModel):
    """System status response schema."""
    total_pipelines: int
    enabled_pipelines: int
    total_executions: int
    recent_executions_24h: int
    successful_executions_24h: int
    failed_executions_24h: int
    active_executions: int
    scheduler_running: bool
    timestamp: str


class PipelineHealthResponse(BaseModel):
    """Pipeline health response schema."""
    status: str
    system_status: SystemStatusResponse
    data_connector_connections: int
    transformer_functions: int


# Pipeline Management Endpoints
@router.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    pipeline_request: PipelineRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new data pipeline."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        # Convert source requests to source objects
        sources = []
        for source_req in pipeline_request.sources or []:
            source = DataSource(
                id="",  # Will be auto-generated
                name=source_req.name,
                source_type=source_req.source_type,
                connection_config=source_req.connection_config,
                data_format=source_req.data_format,
                schema_definition=source_req.schema_definition or {},
                refresh_interval=source_req.refresh_interval,
                enabled=source_req.enabled
            )
            sources.append(source)
        
        # Convert transformation requests to transformation objects
        transformations = []
        for transform_req in pipeline_request.transformations or []:
            transformation = TransformationStep(
                id="",  # Will be auto-generated
                name=transform_req.name,
                transformation_type=transform_req.transformation_type,
                configuration=transform_req.configuration,
                order=transform_req.order,
                enabled=transform_req.enabled
            )
            transformations.append(transformation)
        
        # Convert target requests to target objects
        targets = []
        for target_req in pipeline_request.targets or []:
            target = DataTarget(
                id="",  # Will be auto-generated
                name=target_req.name,
                target_type=target_req.target_type,
                connection_config=target_req.connection_config,
                data_format=target_req.data_format,
                batch_size=target_req.batch_size,
                enabled=target_req.enabled
            )
            targets.append(target)
        
        # Create pipeline
        pipeline = Pipeline(
            id="",  # Will be auto-generated
            name=pipeline_request.name,
            description=pipeline_request.description,
            sources=sources,
            transformations=transformations,
            targets=targets,
            schedule=pipeline_request.schedule,
            enabled=pipeline_request.enabled
        )
        
        pipeline_id = await pipeline_manager.create_pipeline(pipeline)
        created_pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        
        return _convert_pipeline_to_response(created_pipeline)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}"
        )


@router.get("/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_user)
):
    """List all data pipelines."""
    try:
        pipelines = await pipeline_manager.list_pipelines()
        
        return [_convert_pipeline_to_response(pipeline) for pipeline in pipelines]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pipelines: {str(e)}"
        )


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific pipeline."""
    try:
        pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        return _convert_pipeline_to_response(pipeline)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pipeline: {str(e)}"
        )


@router.put("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    pipeline_request: PipelineRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing pipeline."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        existing_pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        if not existing_pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Convert requests to objects (similar to create_pipeline)
        sources = []
        for source_req in pipeline_request.sources or []:
            source = DataSource(
                id="",  # Will be auto-generated
                name=source_req.name,
                source_type=source_req.source_type,
                connection_config=source_req.connection_config,
                data_format=source_req.data_format,
                schema_definition=source_req.schema_definition or {},
                refresh_interval=source_req.refresh_interval,
                enabled=source_req.enabled
            )
            sources.append(source)
        
        transformations = []
        for transform_req in pipeline_request.transformations or []:
            transformation = TransformationStep(
                id="",  # Will be auto-generated
                name=transform_req.name,
                transformation_type=transform_req.transformation_type,
                configuration=transform_req.configuration,
                order=transform_req.order,
                enabled=transform_req.enabled
            )
            transformations.append(transformation)
        
        targets = []
        for target_req in pipeline_request.targets or []:
            target = DataTarget(
                id="",  # Will be auto-generated
                name=target_req.name,
                target_type=target_req.target_type,
                connection_config=target_req.connection_config,
                data_format=target_req.data_format,
                batch_size=target_req.batch_size,
                enabled=target_req.enabled
            )
            targets.append(target)
        
        # Update pipeline
        updated_pipeline = Pipeline(
            id=pipeline_id,
            name=pipeline_request.name,
            description=pipeline_request.description,
            sources=sources,
            transformations=transformations,
            targets=targets,
            schedule=pipeline_request.schedule,
            enabled=pipeline_request.enabled,
            created_at=existing_pipeline.created_at,
            updated_at=datetime.utcnow(),
            last_run=existing_pipeline.last_run
        )
        
        success = await pipeline_manager.update_pipeline(updated_pipeline)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update pipeline"
            )
        
        return _convert_pipeline_to_response(updated_pipeline)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pipeline: {str(e)}"
        )


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a pipeline."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await pipeline_manager.delete_pipeline(pipeline_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        return {"message": f"Pipeline {pipeline_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pipeline: {str(e)}"
        )


# Pipeline Execution Endpoints
@router.post("/pipelines/{pipeline_id}/execute", response_model=PipelineExecutionResponse)
async def execute_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """Execute a pipeline."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        execution = await pipeline_manager.execute_pipeline(pipeline_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found or not enabled"
            )
        
        return PipelineExecutionResponse(
            id=execution.id,
            pipeline_id=execution.pipeline_id,
            status=execution.status.value,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            records_processed=execution.records_processed,
            records_failed=execution.records_failed,
            error_message=execution.error_message,
            execution_metrics=execution.execution_metrics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute pipeline: {str(e)}"
        )


@router.get("/executions", response_model=List[PipelineExecutionResponse])
async def list_executions(
    pipeline_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """List pipeline executions."""
    try:
        executions = await pipeline_manager.list_executions(pipeline_id, limit)
        
        return [
            PipelineExecutionResponse(
                id=execution.id,
                pipeline_id=execution.pipeline_id,
                status=execution.status.value,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                records_processed=execution.records_processed,
                records_failed=execution.records_failed,
                error_message=execution.error_message,
                execution_metrics=execution.execution_metrics
            )
            for execution in executions
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve executions: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=PipelineExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific execution."""
    try:
        execution = await pipeline_manager.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return PipelineExecutionResponse(
            id=execution.id,
            pipeline_id=execution.pipeline_id,
            status=execution.status.value,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            records_processed=execution.records_processed,
            records_failed=execution.records_failed,
            error_message=execution.error_message,
            execution_metrics=execution.execution_metrics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve execution: {str(e)}"
        )


# System Information Endpoints
@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """Get pipeline system status."""
    try:
        status_info = await pipeline_manager.get_system_status()
        
        return SystemStatusResponse(
            total_pipelines=status_info["total_pipelines"],
            enabled_pipelines=status_info["enabled_pipelines"],
            total_executions=status_info["total_executions"],
            recent_executions_24h=status_info["recent_executions_24h"],
            successful_executions_24h=status_info["successful_executions_24h"],
            failed_executions_24h=status_info["failed_executions_24h"],
            active_executions=status_info["active_executions"],
            scheduler_running=status_info["scheduler_running"],
            timestamp=status_info["timestamp"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system status: {str(e)}"
        )


@router.get("/system/types")
async def list_system_types():
    """List available data source types, formats, and transformations."""
    return {
        "source_types": [st.value for st in DataSourceType],
        "data_formats": [df.value for df in DataFormat],
        "transformation_types": [tt.value for tt in TransformationType],
        "pipeline_statuses": [ps.value for ps in PipelineStatus]
    }


# Health check endpoint
@router.get("/health", response_model=PipelineHealthResponse)
async def pipeline_health_check():
    """Check data pipeline system health."""
    try:
        health_info = await check_data_pipeline_health()
        
        system_status = SystemStatusResponse(
            total_pipelines=health_info["system_status"]["total_pipelines"],
            enabled_pipelines=health_info["system_status"]["enabled_pipelines"],
            total_executions=health_info["system_status"]["total_executions"],
            recent_executions_24h=health_info["system_status"]["recent_executions_24h"],
            successful_executions_24h=health_info["system_status"]["successful_executions_24h"],
            failed_executions_24h=health_info["system_status"]["failed_executions_24h"],
            active_executions=health_info["system_status"]["active_executions"],
            scheduler_running=health_info["system_status"]["scheduler_running"],
            timestamp=health_info["system_status"]["timestamp"]
        )
        
        return PipelineHealthResponse(
            status=health_info["status"],
            system_status=system_status,
            data_connector_connections=health_info["data_connector_connections"],
            transformer_functions=health_info["transformer_functions"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Pipeline health check failed: {str(e)}"
        )


# Helper functions
def _convert_pipeline_to_response(pipeline: Pipeline) -> PipelineResponse:
    """Convert pipeline object to response format."""
    sources = [
        DataSourceResponse(
            id=source.id,
            name=source.name,
            source_type=source.source_type.value,
            connection_config=source.connection_config,
            data_format=source.data_format.value,
            schema_definition=source.schema_definition,
            refresh_interval=source.refresh_interval,
            enabled=source.enabled,
            last_updated=source.last_updated
        )
        for source in pipeline.sources
    ]
    
    transformations = [
        TransformationStepResponse(
            id=transform.id,
            name=transform.name,
            transformation_type=transform.transformation_type.value,
            configuration=transform.configuration,
            order=transform.order,
            enabled=transform.enabled
        )
        for transform in pipeline.transformations
    ]
    
    targets = [
        DataTargetResponse(
            id=target.id,
            name=target.name,
            target_type=target.target_type.value,
            connection_config=target.connection_config,
            data_format=target.data_format.value,
            batch_size=target.batch_size,
            enabled=target.enabled
        )
        for target in pipeline.targets
    ]
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        sources=sources,
        transformations=transformations,
        targets=targets,
        schedule=pipeline.schedule,
        enabled=pipeline.enabled,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
        last_run=pipeline.last_run
    )