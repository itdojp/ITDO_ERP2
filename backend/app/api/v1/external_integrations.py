"""
CC02 v55.0 External Integrations API
Enterprise-grade External System Integration Management
Day 5 of 7-day intensive backend development
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.integration import (
    DataMapping,
    ExternalSystem,
    IntegrationEndpoint,
    SyncJob,
)
from app.models.user import User
from app.services.external_integration_hub import (
    AuthenticationType,
    IntegrationConfig,
    IntegrationType,
    SyncDirection,
    SyncStatus,
    integration_hub,
)

router = APIRouter(prefix="/integrations", tags=["external-integrations"])


# Request/Response Models
class ExternalSystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    integration_type: IntegrationType
    base_url: str = Field(..., regex=r"^https?://")
    authentication: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    rate_limit: Optional[Dict[str, Any]] = None
    ssl_verify: bool = Field(default=True)


class ExternalSystemResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    integration_type: IntegrationType
    base_url: str
    authentication_type: Optional[str]
    headers: Dict[str, str]
    timeout: int
    retry_attempts: int
    rate_limit: Optional[Dict[str, Any]]
    ssl_verify: bool
    is_active: bool
    last_sync: Optional[datetime]
    total_syncs: int
    success_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataMappingCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    source_system_id: UUID
    target_system_id: UUID
    field_mapping: Dict[str, Any] = Field(default_factory=dict)
    validation_schema: Dict[str, Any] = Field(default_factory=dict)
    transformation_rules: Dict[str, Any] = Field(default_factory=dict)


class DataMappingResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    source_system_id: UUID
    source_system_name: str
    target_system_id: UUID
    target_system_name: str
    field_mapping: Dict[str, Any]
    validation_schema: Dict[str, Any]
    transformation_rules: Dict[str, Any]
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncJobCreate(BaseModel):
    system_id: UUID
    endpoint: str = Field(..., min_length=1, max_length=200)
    direction: SyncDirection
    data: Optional[Dict[str, Any]] = None
    mapping_id: Optional[UUID] = None
    schedule_expression: Optional[str] = Field(
        None, description="Cron expression for recurring jobs"
    )
    immediate_execution: bool = Field(default=True)


class SyncJobResponse(BaseModel):
    id: UUID
    system_id: UUID
    system_name: str
    endpoint: str
    direction: SyncDirection
    status: SyncStatus
    records_processed: Optional[int]
    records_success: Optional[int]
    records_failed: Optional[int]
    execution_time: Optional[float]
    error_message: Optional[str]
    is_recurring: bool
    schedule_expression: Optional[str]
    next_run: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class IntegrationEndpointCreate(BaseModel):
    system_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1, max_length=200)
    method: str = Field(..., regex="^(GET|POST|PUT|DELETE|PATCH)$")
    description: Optional[str] = Field(None, max_length=500)
    request_schema: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    rate_limit: Optional[int] = Field(None, ge=1)


class IntegrationEndpointResponse(BaseModel):
    id: UUID
    system_id: UUID
    system_name: str
    name: str
    path: str
    method: str
    description: Optional[str]
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    rate_limit: Optional[int]
    usage_count: int
    last_used: Optional[datetime]
    average_response_time: Optional[float]
    success_rate: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookSubscriptionCreate(BaseModel):
    system_id: UUID
    event_type: str = Field(..., min_length=1, max_length=100)
    callback_url: str = Field(..., regex=r"^https?://")
    secret: Optional[str] = Field(None, min_length=8)
    filters: Dict[str, Any] = Field(default_factory=dict)
    retry_attempts: int = Field(default=3, ge=0, le=10)


class WebhookSubscriptionResponse(BaseModel):
    id: UUID
    system_id: UUID
    system_name: str
    event_type: str
    callback_url: str
    has_secret: bool
    filters: Dict[str, Any]
    retry_attempts: int
    delivery_count: int
    failure_count: int
    success_rate: float
    last_delivery: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None
    mapping_id: Optional[UUID] = None
    dry_run: bool = Field(default=False)


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float]
    details: Dict[str, Any] = Field(default_factory=dict)


# External Systems Management
@router.post(
    "/systems",
    response_model=ExternalSystemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_external_system(
    system: ExternalSystemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new external system integration"""

    # Validate authentication configuration
    auth_type = system.authentication.get("type")
    if auth_type and auth_type not in [e.value for e in AuthenticationType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid authentication type: {auth_type}",
        )

    # Create integration config
    config = IntegrationConfig(
        system_id=uuid4(),
        base_url=system.base_url,
        authentication=system.authentication,
        headers=system.headers,
        timeout=system.timeout,
        retry_attempts=system.retry_attempts,
        rate_limit=system.rate_limit,
        ssl_verify=system.ssl_verify,
    )

    # Register system
    system_id = await integration_hub.register_system(
        system.name, system.integration_type, config, db
    )

    # Get created system
    system_result = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == system_id)
    )
    db_system = system_result.scalar_one()

    return ExternalSystemResponse(
        id=db_system.id,
        name=db_system.name,
        description=system.description,
        integration_type=db_system.integration_type,
        base_url=db_system.base_url,
        authentication_type=system.authentication.get("type"),
        headers=system.headers,
        timeout=system.timeout,
        retry_attempts=system.retry_attempts,
        rate_limit=system.rate_limit,
        ssl_verify=system.ssl_verify,
        is_active=db_system.is_active,
        last_sync=None,
        total_syncs=0,
        success_rate=0.0,
        created_at=db_system.created_at,
        updated_at=db_system.updated_at,
    )


@router.get("/systems", response_model=List[ExternalSystemResponse])
async def list_external_systems(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    integration_type: Optional[IntegrationType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List external systems"""

    query = select(ExternalSystem)

    if integration_type:
        query = query.where(ExternalSystem.integration_type == integration_type)

    if is_active is not None:
        query = query.where(ExternalSystem.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(ExternalSystem.created_at.desc())

    result = await db.execute(query)
    systems = result.scalars().all()

    return [
        ExternalSystemResponse(
            id=system.id,
            name=system.name,
            description=None,
            integration_type=system.integration_type,
            base_url=system.base_url,
            authentication_type=system.auth_config.get("type")
            if system.auth_config
            else None,
            headers={},
            timeout=30,
            retry_attempts=3,
            rate_limit=None,
            ssl_verify=True,
            is_active=system.is_active,
            last_sync=None,  # Would calculate from sync jobs
            total_syncs=0,  # Would calculate from sync jobs
            success_rate=0.0,  # Would calculate from sync jobs
            created_at=system.created_at,
            updated_at=system.updated_at,
        )
        for system in systems
    ]


@router.get("/systems/{system_id}", response_model=ExternalSystemResponse)
async def get_external_system(
    system_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get external system details"""

    system_result = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == system_id)
    )
    system = system_result.scalar_one_or_none()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="External system not found"
        )

    # Get sync statistics
    sync_stats = await db.execute(
        select(
            func.count(SyncJob.id).label("total_syncs"),
            func.count(SyncJob.id)
            .filter(SyncJob.status == SyncStatus.SUCCESS)
            .label("successful_syncs"),
            func.max(SyncJob.completed_at).label("last_sync"),
        ).where(SyncJob.system_id == system_id)
    )
    stats = sync_stats.first()

    total_syncs = stats.total_syncs or 0
    successful_syncs = stats.successful_syncs or 0
    success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0.0

    return ExternalSystemResponse(
        id=system.id,
        name=system.name,
        description=None,
        integration_type=system.integration_type,
        base_url=system.base_url,
        authentication_type=system.auth_config.get("type")
        if system.auth_config
        else None,
        headers={},
        timeout=30,
        retry_attempts=3,
        rate_limit=None,
        ssl_verify=True,
        is_active=system.is_active,
        last_sync=stats.last_sync,
        total_syncs=total_syncs,
        success_rate=success_rate,
        created_at=system.created_at,
        updated_at=system.updated_at,
    )


@router.post("/systems/{system_id}/test", response_model=TestConnectionResponse)
async def test_system_connection(
    system_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Test connection to external system"""

    start_time = datetime.utcnow()
    success, message = await integration_hub.test_system_connection(system_id, db)
    response_time = (datetime.utcnow() - start_time).total_seconds()

    return TestConnectionResponse(
        success=success,
        message=message,
        response_time=response_time,
        details={"tested_at": datetime.utcnow().isoformat()},
    )


# Data Mappings Management
@router.post(
    "/mappings", response_model=DataMappingResponse, status_code=status.HTTP_201_CREATED
)
async def create_data_mapping(
    mapping: DataMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new data mapping"""

    # Validate systems exist
    source_system = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == mapping.source_system_id)
    )
    if not source_system.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Source system not found"
        )

    target_system = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == mapping.target_system_id)
    )
    if not target_system.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Target system not found"
        )

    mapping_id = await integration_hub.create_data_mapping(
        mapping.name,
        mapping.source_system_id,
        mapping.target_system_id,
        mapping.field_mapping,
        mapping.validation_schema,
        db,
    )

    # Get created mapping with system names
    mapping_result = await db.execute(
        select(DataMapping, ExternalSystem.name.label("source_name"))
        .join(ExternalSystem, DataMapping.source_system_id == ExternalSystem.id)
        .where(DataMapping.id == mapping_id)
    )
    db_mapping, source_name = mapping_result.first()

    target_result = await db.execute(
        select(ExternalSystem.name).where(ExternalSystem.id == mapping.target_system_id)
    )
    target_name = target_result.scalar_one()

    return DataMappingResponse(
        id=db_mapping.id,
        name=db_mapping.name,
        description=mapping.description,
        source_system_id=db_mapping.source_system_id,
        source_system_name=source_name,
        target_system_id=db_mapping.target_system_id,
        target_system_name=target_name,
        field_mapping=db_mapping.field_mapping,
        validation_schema=db_mapping.validation_schema,
        transformation_rules=mapping.transformation_rules,
        is_active=db_mapping.is_active,
        usage_count=0,
        created_at=db_mapping.created_at,
        updated_at=db_mapping.updated_at,
    )


@router.get("/mappings", response_model=List[DataMappingResponse])
async def list_data_mappings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    source_system_id: Optional[UUID] = Query(None),
    target_system_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List data mappings"""

    query = select(
        DataMapping,
        ExternalSystem.name.label("source_name"),
        ExternalSystem.name.label("target_name"),
    ).select_from(
        DataMapping.join(
            ExternalSystem, DataMapping.source_system_id == ExternalSystem.id
        )
    )

    if source_system_id:
        query = query.where(DataMapping.source_system_id == source_system_id)

    if target_system_id:
        query = query.where(DataMapping.target_system_id == target_system_id)

    query = query.offset(skip).limit(limit).order_by(DataMapping.created_at.desc())

    result = await db.execute(query)
    mappings = result.fetchall()

    responses = []
    for mapping, source_name, _ in mappings:
        # Get target system name separately
        target_result = await db.execute(
            select(ExternalSystem.name).where(
                ExternalSystem.id == mapping.target_system_id
            )
        )
        target_name = target_result.scalar_one()

        responses.append(
            DataMappingResponse(
                id=mapping.id,
                name=mapping.name,
                description=None,
                source_system_id=mapping.source_system_id,
                source_system_name=source_name,
                target_system_id=mapping.target_system_id,
                target_system_name=target_name,
                field_mapping=mapping.field_mapping,
                validation_schema=mapping.validation_schema,
                transformation_rules={},
                is_active=mapping.is_active,
                usage_count=0,  # Would calculate from sync jobs
                created_at=mapping.created_at,
                updated_at=mapping.updated_at,
            )
        )

    return responses


# Sync Jobs Management
@router.post(
    "/sync", response_model=SyncJobResponse, status_code=status.HTTP_201_CREATED
)
async def create_sync_job(
    job: SyncJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create and optionally execute sync job"""

    # Validate system exists
    system_result = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == job.system_id)
    )
    system = system_result.scalar_one_or_none()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="System not found"
        )

    # Create sync job
    job_id = uuid4()

    if job.schedule_expression:
        # Schedule recurring job
        job_id = await integration_hub.schedule_sync_job(
            job.system_id, job.endpoint, job.direction, job.schedule_expression, db
        )

    if job.immediate_execution:
        # Execute immediately in background
        background_tasks.add_task(
            _execute_sync_job,
            job.system_id,
            job.endpoint,
            job.direction,
            job.data,
            job.mapping_id,
            db,
        )

    # Create job record
    sync_job = SyncJob(
        id=job_id,
        system_id=job.system_id,
        endpoint=job.endpoint,
        direction=job.direction,
        status=SyncStatus.PENDING if job.immediate_execution else SyncStatus.PENDING,
        is_recurring=bool(job.schedule_expression),
        schedule_expression=job.schedule_expression,
        created_at=datetime.utcnow(),
    )

    db.add(sync_job)
    await db.commit()
    await db.refresh(sync_job)

    return SyncJobResponse(
        id=sync_job.id,
        system_id=sync_job.system_id,
        system_name=system.name,
        endpoint=sync_job.endpoint,
        direction=sync_job.direction,
        status=sync_job.status,
        records_processed=sync_job.records_processed,
        records_success=sync_job.records_success,
        records_failed=sync_job.records_failed,
        execution_time=sync_job.execution_time,
        error_message=sync_job.error_message,
        is_recurring=sync_job.is_recurring,
        schedule_expression=sync_job.schedule_expression,
        next_run=None,  # Would calculate based on cron expression
        started_at=sync_job.started_at,
        completed_at=sync_job.completed_at,
        created_at=sync_job.created_at,
    )


async def _execute_sync_job(
    system_id: UUID,
    endpoint: str,
    direction: SyncDirection,
    data: Optional[Dict[str, Any]],
    mapping_id: Optional[UUID],
    db: AsyncSession,
):
    """Execute sync job in background"""
    try:
        await integration_hub.sync_data(
            system_id, endpoint, direction, data, mapping_id, db
        )
        # Job result is automatically stored by integration_hub
    except Exception:
        # Error handling is done in integration_hub
        pass


@router.get("/sync", response_model=List[SyncJobResponse])
async def list_sync_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    system_id: Optional[UUID] = Query(None),
    status: Optional[SyncStatus] = Query(None),
    direction: Optional[SyncDirection] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List sync jobs"""

    query = select(SyncJob, ExternalSystem.name.label("system_name")).join(
        ExternalSystem, SyncJob.system_id == ExternalSystem.id
    )

    if system_id:
        query = query.where(SyncJob.system_id == system_id)

    if status:
        query = query.where(SyncJob.status == status)

    if direction:
        query = query.where(SyncJob.direction == direction)

    if date_from:
        query = query.where(SyncJob.created_at >= date_from)

    if date_to:
        query = query.where(SyncJob.created_at <= date_to)

    query = query.offset(skip).limit(limit).order_by(SyncJob.created_at.desc())

    result = await db.execute(query)
    jobs = result.fetchall()

    return [
        SyncJobResponse(
            id=job.SyncJob.id,
            system_id=job.SyncJob.system_id,
            system_name=job.system_name,
            endpoint=job.SyncJob.endpoint,
            direction=job.SyncJob.direction,
            status=job.SyncJob.status,
            records_processed=job.SyncJob.records_processed,
            records_success=job.SyncJob.records_success,
            records_failed=job.SyncJob.records_failed,
            execution_time=job.SyncJob.execution_time,
            error_message=job.SyncJob.error_message,
            is_recurring=job.SyncJob.is_recurring,
            schedule_expression=job.SyncJob.schedule_expression,
            next_run=None,  # Would calculate
            started_at=job.SyncJob.started_at,
            completed_at=job.SyncJob.completed_at,
            created_at=job.SyncJob.created_at,
        )
        for job in jobs
    ]


@router.get("/sync/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get sync job details"""

    job_status = await integration_hub.get_sync_status(job_id, db)

    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found"
        )

    # Get system name
    job_result = await db.execute(
        select(SyncJob, ExternalSystem.name.label("system_name"))
        .join(ExternalSystem, SyncJob.system_id == ExternalSystem.id)
        .where(SyncJob.id == job_id)
    )
    job, system_name = job_result.first()

    return SyncJobResponse(
        id=job.id,
        system_id=job.system_id,
        system_name=system_name,
        endpoint=job.endpoint,
        direction=job.direction,
        status=SyncStatus(job_status["status"]),
        records_processed=job_status["records_processed"],
        records_success=job_status["records_success"],
        records_failed=job_status["records_failed"],
        execution_time=job_status["execution_time"],
        error_message=job_status["error_message"],
        is_recurring=job.is_recurring,
        schedule_expression=job.schedule_expression,
        next_run=None,
        started_at=datetime.fromisoformat(job_status["started_at"])
        if job_status["started_at"]
        else None,
        completed_at=datetime.fromisoformat(job_status["completed_at"])
        if job_status["completed_at"]
        else None,
        created_at=job.created_at,
    )


# Integration Endpoints Management
@router.post(
    "/endpoints",
    response_model=IntegrationEndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_integration_endpoint(
    endpoint: IntegrationEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create integration endpoint"""

    # Validate system exists
    system_result = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == endpoint.system_id)
    )
    system = system_result.scalar_one_or_none()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="System not found"
        )

    db_endpoint = IntegrationEndpoint(
        id=uuid4(),
        system_id=endpoint.system_id,
        name=endpoint.name,
        path=endpoint.path,
        method=endpoint.method,
        description=endpoint.description,
        request_schema=endpoint.request_schema,
        response_schema=endpoint.response_schema,
        rate_limit=endpoint.rate_limit,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_endpoint)
    await db.commit()
    await db.refresh(db_endpoint)

    return IntegrationEndpointResponse(
        id=db_endpoint.id,
        system_id=db_endpoint.system_id,
        system_name=system.name,
        name=db_endpoint.name,
        path=db_endpoint.path,
        method=db_endpoint.method,
        description=db_endpoint.description,
        request_schema=db_endpoint.request_schema,
        response_schema=db_endpoint.response_schema,
        rate_limit=db_endpoint.rate_limit,
        usage_count=0,
        last_used=None,
        average_response_time=None,
        success_rate=0.0,
        is_active=db_endpoint.is_active,
        created_at=db_endpoint.created_at,
        updated_at=db_endpoint.updated_at,
    )


@router.get("/endpoints", response_model=List[IntegrationEndpointResponse])
async def list_integration_endpoints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    system_id: Optional[UUID] = Query(None),
    method: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List integration endpoints"""

    query = select(IntegrationEndpoint, ExternalSystem.name.label("system_name")).join(
        ExternalSystem, IntegrationEndpoint.system_id == ExternalSystem.id
    )

    if system_id:
        query = query.where(IntegrationEndpoint.system_id == system_id)

    if method:
        query = query.where(IntegrationEndpoint.method == method.upper())

    query = (
        query.offset(skip).limit(limit).order_by(IntegrationEndpoint.created_at.desc())
    )

    result = await db.execute(query)
    endpoints = result.fetchall()

    return [
        IntegrationEndpointResponse(
            id=endpoint.IntegrationEndpoint.id,
            system_id=endpoint.IntegrationEndpoint.system_id,
            system_name=endpoint.system_name,
            name=endpoint.IntegrationEndpoint.name,
            path=endpoint.IntegrationEndpoint.path,
            method=endpoint.IntegrationEndpoint.method,
            description=endpoint.IntegrationEndpoint.description,
            request_schema=endpoint.IntegrationEndpoint.request_schema,
            response_schema=endpoint.IntegrationEndpoint.response_schema,
            rate_limit=endpoint.IntegrationEndpoint.rate_limit,
            usage_count=0,  # Would calculate
            last_used=None,  # Would track
            average_response_time=None,  # Would calculate
            success_rate=0.0,  # Would calculate
            is_active=endpoint.IntegrationEndpoint.is_active,
            created_at=endpoint.IntegrationEndpoint.created_at,
            updated_at=endpoint.IntegrationEndpoint.updated_at,
        )
        for endpoint in endpoints
    ]


# System Metrics and Analytics
@router.get("/systems/{system_id}/metrics")
async def get_system_metrics(
    system_id: UUID = Path(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get integration metrics for system"""

    metrics = await integration_hub.get_system_metrics(
        system_id, start_date, end_date, db
    )

    return metrics


@router.get("/dashboard")
async def get_integration_dashboard(
    period_days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get integration dashboard data"""

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period_days)

    # Get system counts
    systems_result = await db.execute(
        select(
            func.count(ExternalSystem.id).label("total_systems"),
            func.count(ExternalSystem.id)
            .filter(ExternalSystem.is_active)
            .label("active_systems"),
        )
    )
    systems_stats = systems_result.first()

    # Get sync job statistics
    jobs_result = await db.execute(
        select(
            func.count(SyncJob.id).label("total_jobs"),
            func.count(SyncJob.id)
            .filter(SyncJob.status == SyncStatus.SUCCESS)
            .label("successful_jobs"),
            func.count(SyncJob.id)
            .filter(SyncJob.status == SyncStatus.FAILED)
            .label("failed_jobs"),
            func.sum(SyncJob.records_processed).label("total_records"),
            func.avg(SyncJob.execution_time).label("avg_execution_time"),
        ).where(and_(SyncJob.created_at >= start_date, SyncJob.created_at <= end_date))
    )
    jobs_stats = jobs_result.first()

    total_jobs = jobs_stats.total_jobs or 0
    successful_jobs = jobs_stats.successful_jobs or 0

    return {
        "period": {
            "days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "systems": {
            "total": systems_stats.total_systems or 0,
            "active": systems_stats.active_systems or 0,
            "inactive": (systems_stats.total_systems or 0)
            - (systems_stats.active_systems or 0),
        },
        "sync_jobs": {
            "total": total_jobs,
            "successful": successful_jobs,
            "failed": jobs_stats.failed_jobs or 0,
            "success_rate": (successful_jobs / total_jobs * 100)
            if total_jobs > 0
            else 0,
        },
        "data_processing": {
            "total_records": jobs_stats.total_records or 0,
            "average_execution_time": jobs_stats.avg_execution_time or 0,
            "throughput_per_minute": (jobs_stats.total_records or 0)
            / ((jobs_stats.avg_execution_time or 1) / 60)
            if jobs_stats.avg_execution_time
            else 0,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


# Webhook Management
@router.post(
    "/webhooks",
    response_model=WebhookSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_subscription(
    webhook: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create webhook subscription"""

    # Validate system exists
    system_result = await db.execute(
        select(ExternalSystem).where(ExternalSystem.id == webhook.system_id)
    )
    system = system_result.scalar_one_or_none()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="System not found"
        )

    subscription_id = integration_hub.webhook_manager.subscribe(
        webhook.event_type, webhook.callback_url, webhook.secret, webhook.filters
    )

    return WebhookSubscriptionResponse(
        id=UUID(subscription_id),
        system_id=webhook.system_id,
        system_name=system.name,
        event_type=webhook.event_type,
        callback_url=webhook.callback_url,
        has_secret=bool(webhook.secret),
        filters=webhook.filters,
        retry_attempts=webhook.retry_attempts,
        delivery_count=0,
        failure_count=0,
        success_rate=0.0,
        last_delivery=None,
        is_active=True,
        created_at=datetime.utcnow(),
    )


@router.post("/webhooks/{system_id}/process")
async def process_webhook(
    system_id: UUID = Path(...),
    event_type: str = Body(...),
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Process incoming webhook (called by external systems)"""

    result = await integration_hub.process_webhook(
        system_id, event_type, payload, session=db
    )

    return result
