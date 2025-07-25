"""
CC02 v55.0 Data Processing API
Enterprise-grade Data Processing and Analytics Management
Day 4 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, validator
import pandas as pd
import io

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.exceptions import DataProcessingError, ValidationError
from app.models.data_processing import (
    DataPipeline, ProcessingJob, DataTransformation, DataSource,
    ProcessingStep, JobExecution, DataQualityCheck, ProcessingMetrics
)
from app.models.user import User
from app.services.data_processing_engine import (
    data_processing_engine, ProcessingType, DataSourceType, JobStatus,
    QualityCheckType, AggregationType, ProcessingResult
)

router = APIRouter(prefix="/data-processing", tags=["data-processing"])

# Request/Response Models
class ProcessingJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    processing_type: ProcessingType
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)

class ProcessingJobResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    processing_type: ProcessingType
    config: Dict[str, Any]
    schedule: Optional[str]
    status: JobStatus
    is_active: bool
    tags: List[str]
    records_processed: Optional[int]
    execution_time_ms: Optional[float]
    error_message: Optional[str]
    created_by: UUID
    created_by_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_executed: Optional[datetime]

    class Config:
        from_attributes = True

class JobExecutionRequest(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)

class JobExecutionResponse(BaseModel):
    execution_id: UUID
    job_id: UUID
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime]
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    execution_time_ms: float
    memory_used_mb: float
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

    class Config:
        from_attributes = True

class DataPipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: List[Dict[str, Any]] = Field(..., min_items=1)
    schedule: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    retry_config: Dict[str, Any] = Field(default_factory=dict)

class DataPipelineResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    steps: List[Dict[str, Any]]
    schedule: Optional[str]
    status: str
    is_active: bool
    retry_config: Dict[str, Any]
    last_execution: Optional[Dict[str, Any]]
    success_rate: float
    avg_execution_time_ms: float
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: DataSourceType
    connection_config: Dict[str, Any] = Field(default_factory=dict)
    schema_config: Optional[Dict[str, Any]] = Field(None)
    is_active: bool = Field(default=True)

class DataSourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: DataSourceType
    connection_config: Dict[str, Any]
    schema_config: Optional[Dict[str, Any]]
    is_active: bool
    last_tested: Optional[datetime]
    test_result: Optional[bool]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DataQualityCheckCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    check_type: QualityCheckType
    target_table: str = Field(..., min_length=1, max_length=100)
    config: Dict[str, Any] = Field(default_factory=dict)
    threshold: float = Field(default=0.95, ge=0, le=1)
    is_active: bool = Field(default=True)

class DataQualityResult(BaseModel):
    check_id: UUID
    check_name: str
    check_type: QualityCheckType
    passed: bool
    score: float
    threshold: float
    details: Dict[str, Any]
    checked_at: datetime

class ETLJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_config: Dict[str, Any]
    transformation_config: Dict[str, Any] = Field(default_factory=dict)
    target_config: Dict[str, Any]
    schedule: Optional[str] = Field(None)

class AggregationJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_table: str = Field(..., min_length=1, max_length=100)
    groupby_fields: List[str] = Field(default_factory=list)
    aggregations: Dict[str, AggregationType]
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    target_table: Optional[str] = Field(None, max_length=100)

class ValidationJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_table: str = Field(..., min_length=1, max_length=100)
    validation_rules: List[Dict[str, Any]]
    quality_checks: List[Dict[str, Any]] = Field(default_factory=list)
    fail_on_errors: bool = Field(default=False)

class AnalyticsRequest(BaseModel):
    dataset: str = Field(..., min_length=1, max_length=100)
    metrics: List[str] = Field(..., min_items=1)
    dimensions: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    date_range: Optional[Dict[str, str]] = Field(None)
    limit: int = Field(default=1000, ge=1, le=10000)

# Helper Functions
async def get_job_or_404(
    job_id: UUID,
    db: AsyncSession,
    user_id: Optional[UUID] = None
) -> ProcessingJob:
    """Get processing job or raise 404"""
    
    query = select(ProcessingJob).where(ProcessingJob.id == job_id)
    
    if user_id:
        query = query.where(ProcessingJob.created_by == user_id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found"
        )
    
    return job

# Processing Jobs Management
@router.post("/jobs", response_model=ProcessingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_processing_job(
    job: ProcessingJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new processing job"""
    
    # Validate configuration based on processing type
    config_errors = await _validate_job_config(job.processing_type, job.config)
    if config_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": config_errors}
        )
    
    db_job = ProcessingJob(
        id=uuid4(),
        name=job.name,
        description=job.description,
        processing_type=job.processing_type,
        config=job.config,
        schedule=job.schedule,
        status=JobStatus.PENDING,
        is_active=job.is_active,
        tags=job.tags,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    return ProcessingJobResponse(
        id=db_job.id,
        name=db_job.name,
        description=db_job.description,
        processing_type=db_job.processing_type,
        config=db_job.config,
        schedule=db_job.schedule,
        status=db_job.status,
        is_active=db_job.is_active,
        tags=db_job.tags,
        records_processed=db_job.records_processed,
        execution_time_ms=db_job.execution_time_ms,
        error_message=db_job.error_message,
        created_by=db_job.created_by,
        created_by_name=current_user.username,
        created_at=db_job.created_at,
        updated_at=db_job.updated_at,
        last_executed=db_job.completed_at
    )

@router.get("/jobs", response_model=List[ProcessingJobResponse])
async def list_processing_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    processing_type: Optional[ProcessingType] = Query(None),
    status: Optional[JobStatus] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, min_length=1),
    tags: Optional[List[str]] = Query(None),
    created_by: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List processing jobs with filtering"""
    
    query = select(ProcessingJob).options(joinedload(ProcessingJob.created_by_user))
    
    # Apply filters
    if processing_type:
        query = query.where(ProcessingJob.processing_type == processing_type)
    
    if status:
        query = query.where(ProcessingJob.status == status)
    
    if is_active is not None:
        query = query.where(ProcessingJob.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                ProcessingJob.name.ilike(search_term),
                ProcessingJob.description.ilike(search_term)
            )
        )
    
    if tags:
        # PostgreSQL array overlap operator
        query = query.where(ProcessingJob.tags.op('&&')(tags))
    
    if created_by:
        query = query.where(ProcessingJob.created_by == created_by)
    
    # Apply pagination and ordering
    query = query.offset(skip).limit(limit).order_by(ProcessingJob.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        ProcessingJobResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            processing_type=job.processing_type,
            config=job.config,
            schedule=job.schedule,
            status=job.status,
            is_active=job.is_active,
            tags=job.tags,
            records_processed=job.records_processed,
            execution_time_ms=job.execution_time_ms,
            error_message=job.error_message,
            created_by=job.created_by,
            created_by_name=job.created_by_user.username if job.created_by_user else None,
            created_at=job.created_at,
            updated_at=job.updated_at,
            last_executed=job.completed_at
        )
        for job in jobs
    ]

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific processing job"""
    
    job = await get_job_or_404(job_id, db)
    
    # Load creator info
    creator_result = await db.execute(
        select(User).where(User.id == job.created_by)
    )
    creator = creator_result.scalar_one_or_none()
    
    return ProcessingJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        processing_type=job.processing_type,
        config=job.config,
        schedule=job.schedule,
        status=job.status,
        is_active=job.is_active,
        tags=job.tags,
        records_processed=job.records_processed,
        execution_time_ms=job.execution_time_ms,
        error_message=job.error_message,
        created_by=job.created_by,
        created_by_name=creator.username if creator else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        last_executed=job.completed_at
    )

@router.put("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def update_processing_job(
    job_id: UUID = Path(...),
    job_update: ProcessingJobCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a processing job"""
    
    job = await get_job_or_404(job_id, db, current_user.id)
    
    # Validate new configuration
    config_errors = await _validate_job_config(job_update.processing_type, job_update.config)
    if config_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": config_errors}
        )
    
    # Update job fields
    job.name = job_update.name
    job.description = job_update.description
    job.processing_type = job_update.processing_type
    job.config = job_update.config
    job.schedule = job_update.schedule
    job.is_active = job_update.is_active
    job.tags = job_update.tags
    job.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    
    return ProcessingJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        processing_type=job.processing_type,
        config=job.config,
        schedule=job.schedule,
        status=job.status,
        is_active=job.is_active,
        tags=job.tags,
        records_processed=job.records_processed,
        execution_time_ms=job.execution_time_ms,
        error_message=job.error_message,
        created_by=job.created_by,
        created_by_name=current_user.username,
        created_at=job.created_at,
        updated_at=job.updated_at,
        last_executed=job.completed_at
    )

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processing_job(
    job_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a processing job"""
    
    job = await get_job_or_404(job_id, db, current_user.id)
    
    # Check if job is currently running
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running job"
        )
    
    await db.delete(job)
    await db.commit()

# Job Execution
@router.post("/jobs/{job_id}/execute", response_model=JobExecutionResponse)
async def execute_job(
    job_id: UUID = Path(...),
    execution_request: JobExecutionRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Execute a processing job"""
    
    job = await get_job_or_404(job_id, db)
    
    if not job.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not active"
        )
    
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is already running"
        )
    
    execution_id = uuid4()
    
    # Create job execution record
    execution = JobExecution(
        id=execution_id,
        job_id=job_id,
        status=JobStatus.PENDING,
        input_data=execution_request.input_data,
        parameters=execution_request.parameters,
        priority=execution_request.priority,
        started_by=current_user.id,
        started_at=datetime.utcnow()
    )
    
    db.add(execution)
    await db.commit()
    
    # Execute job in background
    if background_tasks:
        background_tasks.add_task(
            _execute_job_background,
            job_id,
            execution_id,
            execution_request.input_data,
            current_user.id
        )
    else:
        # Execute synchronously for testing
        result = await data_processing_engine.execute_job(
            job_id, execution_request.input_data, current_user.id, db
        )
        
        # Update execution record
        execution.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
        execution.completed_at = datetime.utcnow()
        execution.records_processed = result.records_processed
        execution.records_created = result.records_created
        execution.records_updated = result.records_updated
        execution.records_deleted = result.records_deleted
        execution.execution_time_ms = result.execution_time_ms
        execution.memory_used_mb = result.memory_used_mb
        execution.errors = result.errors
        execution.warnings = result.warnings
        execution.metrics = result.metrics
        
        await db.commit()
    
    await db.refresh(execution)
    
    return JobExecutionResponse(
        execution_id=execution.id,
        job_id=execution.job_id,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        records_processed=execution.records_processed or 0,
        records_created=execution.records_created or 0,
        records_updated=execution.records_updated or 0,
        records_deleted=execution.records_deleted or 0,
        execution_time_ms=execution.execution_time_ms or 0,
        memory_used_mb=execution.memory_used_mb or 0,
        errors=execution.errors or [],
        warnings=execution.warnings or [],
        metrics=execution.metrics or {}
    )

@router.get("/jobs/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: UUID = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[JobStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get job execution history"""
    
    await get_job_or_404(job_id, db)
    
    query = select(JobExecution).where(JobExecution.job_id == job_id)
    
    if status:
        query = query.where(JobExecution.status == status)
    
    query = query.offset(skip).limit(limit).order_by(JobExecution.started_at.desc())
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [
        JobExecutionResponse(
            execution_id=execution.id,
            job_id=execution.job_id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            records_processed=execution.records_processed or 0,
            records_created=execution.records_created or 0,
            records_updated=execution.records_updated or 0,
            records_deleted=execution.records_deleted or 0,
            execution_time_ms=execution.execution_time_ms or 0,
            memory_used_mb=execution.memory_used_mb or 0,
            errors=execution.errors or [],
            warnings=execution.warnings or [],
            metrics=execution.metrics or {}
        )
        for execution in executions
    ]

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a running job"""
    
    job = await get_job_or_404(job_id, db)
    
    if job.status != JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not running"
        )
    
    await data_processing_engine.cancel_job(job_id, current_user.id, db)
    
    return {"message": "Job cancellation requested"}

# ETL Jobs
@router.post("/etl", response_model=ProcessingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_etl_job(
    etl_job: ETLJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create an ETL processing job"""
    
    config = {
        "extract": etl_job.source_config,
        "transform": etl_job.transformation_config,
        "load": etl_job.target_config
    }
    
    job_create = ProcessingJobCreate(
        name=etl_job.name,
        processing_type=ProcessingType.ETL,
        config=config,
        schedule=etl_job.schedule
    )
    
    return await create_processing_job(job_create, db, current_user)

# Aggregation Jobs
@router.post("/aggregation", response_model=ProcessingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_aggregation_job(
    agg_job: AggregationJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create an aggregation processing job"""
    
    config = {
        "source_table": agg_job.source_table,
        "groupby": agg_job.groupby_fields,
        "aggregations": {field: agg_type.value for field, agg_type in agg_job.aggregations.items()},
        "filters": agg_job.filters,
        "target_table": agg_job.target_table
    }
    
    job_create = ProcessingJobCreate(
        name=agg_job.name,
        processing_type=ProcessingType.AGGREGATION,
        config=config
    )
    
    return await create_processing_job(job_create, db, current_user)

# Validation Jobs
@router.post("/validation", response_model=ProcessingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_validation_job(
    val_job: ValidationJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a data validation job"""
    
    config = {
        "target_table": val_job.target_table,
        "rules": val_job.validation_rules,
        "quality_checks": val_job.quality_checks,
        "fail_on_errors": val_job.fail_on_errors
    }
    
    job_create = ProcessingJobCreate(
        name=val_job.name,
        processing_type=ProcessingType.VALIDATION,
        config=config
    )
    
    return await create_processing_job(job_create, db, current_user)

# Data Sources
@router.post("/sources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    source: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new data source"""
    
    db_source = DataSource(
        id=uuid4(),
        name=source.name,
        source_type=source.source_type,
        connection_config=source.connection_config,
        schema_config=source.schema_config,
        is_active=source.is_active,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    
    return DataSourceResponse(
        id=db_source.id,
        name=db_source.name,
        source_type=db_source.source_type,
        connection_config=db_source.connection_config,
        schema_config=db_source.schema_config,
        is_active=db_source.is_active,
        last_tested=db_source.last_tested,
        test_result=db_source.test_result,
        created_at=db_source.created_at,
        updated_at=db_source.updated_at
    )

@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    source_type: Optional[DataSourceType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List data sources"""
    
    query = select(DataSource)
    
    if source_type:
        query = query.where(DataSource.source_type == source_type)
    
    if is_active is not None:
        query = query.where(DataSource.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(DataSource.created_at.desc())
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return [
        DataSourceResponse(
            id=source.id,
            name=source.name,
            source_type=source.source_type,
            connection_config=source.connection_config,
            schema_config=source.schema_config,
            is_active=source.is_active,
            last_tested=source.last_tested,
            test_result=source.test_result,
            created_at=source.created_at,
            updated_at=source.updated_at
        )
        for source in sources
    ]

@router.post("/sources/{source_id}/test")
async def test_data_source(
    source_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Test data source connection"""
    
    source_result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = source_result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Test connection based on source type
    try:
        test_result = await _test_source_connection(source)
        
        # Update test results
        source.last_tested = datetime.utcnow()
        source.test_result = test_result
        source.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "source_id": str(source_id),
            "test_result": test_result,
            "tested_at": source.last_tested.isoformat(),
            "message": "Connection successful" if test_result else "Connection failed"
        }
    
    except Exception as e:
        source.last_tested = datetime.utcnow()
        source.test_result = False
        source.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "source_id": str(source_id),
            "test_result": False,
            "tested_at": source.last_tested.isoformat(),
            "message": f"Connection test failed: {str(e)}"
        }

# Data Quality
@router.post("/quality-checks", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_quality_check(
    check: DataQualityCheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a data quality check"""
    
    db_check = DataQualityCheck(
        id=uuid4(),
        name=check.name,
        check_type=check.check_type,
        target_table=check.target_table,
        config=check.config,
        threshold=check.threshold,
        is_active=check.is_active,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_check)
    await db.commit()
    await db.refresh(db_check)
    
    return {
        "id": str(db_check.id),
        "name": db_check.name,
        "check_type": db_check.check_type.value,
        "target_table": db_check.target_table,
        "config": db_check.config,
        "threshold": db_check.threshold,
        "is_active": db_check.is_active,
        "created_at": db_check.created_at.isoformat()
    }

@router.post("/quality-checks/{check_id}/run", response_model=DataQualityResult)
async def run_quality_check(
    check_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run a data quality check"""
    
    check_result = await db.execute(
        select(DataQualityCheck).where(DataQualityCheck.id == check_id)
    )
    check = check_result.scalar_one_or_none()
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality check not found"
        )
    
    # Run quality check
    try:
        score, details = await _run_quality_check(check, db)
        passed = score >= check.threshold
        
        return DataQualityResult(
            check_id=check.id,
            check_name=check.name,
            check_type=check.check_type,
            passed=passed,
            score=score,
            threshold=check.threshold,
            details=details,
            checked_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality check failed: {str(e)}"
        )

# Analytics
@router.post("/analytics/query", response_model=Dict[str, Any])
async def run_analytics_query(
    request: AnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run analytics query"""
    
    try:
        # Build analytics query
        query_parts = []
        select_parts = []
        
        # Add dimensions
        for dimension in request.dimensions:
            select_parts.append(dimension)
        
        # Add metrics
        for metric in request.metrics:
            if metric == 'count':
                select_parts.append('COUNT(*) as count')
            elif metric == 'sum':
                select_parts.append('SUM(amount) as total_amount')
            elif metric == 'avg':
                select_parts.append('AVG(amount) as avg_amount')
            else:
                select_parts.append(f'{metric}')
        
        # Build query
        select_clause = ', '.join(select_parts)
        query = f"SELECT {select_clause} FROM {request.dataset}"
        
        # Add filters
        if request.filters:
            filter_conditions = []
            for filter_item in request.filters:
                field = filter_item.get('field')
                operator = filter_item.get('operator')
                value = filter_item.get('value')
                
                if field and operator and value is not None:
                    if operator == 'equals':
                        filter_conditions.append(f"{field} = '{value}'")
                    elif operator == 'greater_than':
                        filter_conditions.append(f"{field} > {value}")
                    elif operator == 'less_than':
                        filter_conditions.append(f"{field} < {value}")
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        # Add grouping
        if request.dimensions:
            query += f" GROUP BY {', '.join(request.dimensions)}"
        
        # Add ordering and limit
        query += f" ORDER BY {select_parts[0]} LIMIT {request.limit}"
        
        # Execute query
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        # Convert to dictionaries
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        
        return {
            "dataset": request.dataset,
            "query": query,
            "result_count": len(data),
            "data": data,
            "executed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analytics query failed: {str(e)}"
        )

# File Processing
@router.post("/files/upload")
async def upload_file_for_processing(
    file: UploadFile = File(...),
    processing_type: ProcessingType = Query(ProcessingType.ETL),
    target_table: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload file for data processing"""
    
    # Validate file type
    allowed_types = ['text/csv', 'application/json', 'application/vnd.ms-excel', 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not supported"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process based on file type
        if file.content_type == 'text/csv':
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.content_type == 'application/json':
            data = json.loads(content.decode('utf-8'))
            df = pd.DataFrame(data if isinstance(data, list) else [data])
        elif 'excel' in file.content_type:
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format"
            )
        
        # Convert to records
        records = df.to_dict('records')
        
        # Create temporary processing job
        config = {
            "extract": {
                "source_type": "memory",
                "data": records
            },
            "transform": {
                "transformations": []
            },
            "load": {
                "target_type": "database",
                "table": target_table or "temp_upload",
                "mode": "insert"
            }
        }
        
        job = await data_processing_engine.create_job(
            f"File Upload: {file.filename}",
            processing_type,
            config,
            user_id=current_user.id,
            session=db
        )
        
        # Execute immediately
        result = await data_processing_engine.execute_job(
            job.id,
            {"records": records},
            current_user.id,
            db
        )
        
        return {
            "filename": file.filename,
            "file_size": len(content),
            "records_count": len(records),
            "columns": list(df.columns),
            "processing_result": {
                "success": result.success,
                "records_processed": result.records_processed,
                "execution_time_ms": result.execution_time_ms,
                "errors": result.errors
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )

@router.get("/files/export/{table_name}")
async def export_table_data(
    table_name: str = Path(...),
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    limit: int = Query(10000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export table data to file"""
    
    try:
        # Query data
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = await db.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Generate file content
        if format == "csv":
            content = df.to_csv(index=False)
            media_type = "text/csv"
            filename = f"{table_name}.csv"
        elif format == "json":
            content = df.to_json(orient="records", indent=2)
            media_type = "application/json"
            filename = f"{table_name}.json"
        elif format == "excel":
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            content = buffer.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{table_name}.xlsx"
        
        # Return file response
        return StreamingResponse(
            io.BytesIO(content.encode() if isinstance(content, str) else content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

# Metrics and Monitoring
@router.get("/metrics/dashboard")
async def get_processing_metrics(
    period_days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get data processing metrics dashboard"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Job statistics
    jobs_stats = await db.execute(
        select(
            func.count(ProcessingJob.id).label('total_jobs'),
            func.count().filter(ProcessingJob.status == JobStatus.COMPLETED).label('completed_jobs'),
            func.count().filter(ProcessingJob.status == JobStatus.FAILED).label('failed_jobs'),
            func.count().filter(ProcessingJob.status == JobStatus.RUNNING).label('running_jobs')
        )
        .where(ProcessingJob.created_at >= start_date)
    )
    stats = jobs_stats.first()
    
    # Execution statistics
    exec_stats = await db.execute(
        select(
            func.avg(JobExecution.execution_time_ms).label('avg_execution_time'),
            func.sum(JobExecution.records_processed).label('total_records_processed'),
            func.avg(JobExecution.memory_used_mb).label('avg_memory_used')
        )
        .where(JobExecution.started_at >= start_date)
    )
    exec_data = exec_stats.first()
    
    # Jobs by type
    type_stats = await db.execute(
        select(
            ProcessingJob.processing_type,
            func.count(ProcessingJob.id).label('count')
        )
        .where(ProcessingJob.created_at >= start_date)
        .group_by(ProcessingJob.processing_type)
    )
    
    jobs_by_type = {row.processing_type.value: row.count for row in type_stats.fetchall()}
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": period_days
        },
        "jobs": {
            "total": stats.total_jobs or 0,
            "completed": stats.completed_jobs or 0,
            "failed": stats.failed_jobs or 0,
            "running": stats.running_jobs or 0,
            "success_rate": (stats.completed_jobs / stats.total_jobs * 100) if stats.total_jobs > 0 else 0
        },
        "execution": {
            "avg_execution_time_ms": float(exec_data.avg_execution_time or 0),
            "total_records_processed": int(exec_data.total_records_processed or 0),
            "avg_memory_used_mb": float(exec_data.avg_memory_used or 0)
        },
        "jobs_by_type": jobs_by_type,
        "active_jobs": data_processing_engine.get_active_jobs()
    }

# Helper Functions
async def _validate_job_config(processing_type: ProcessingType, config: Dict[str, Any]) -> List[str]:
    """Validate job configuration"""
    
    errors = []
    
    if processing_type == ProcessingType.ETL:
        if 'extract' not in config:
            errors.append("ETL job requires 'extract' configuration")
        if 'load' not in config:
            errors.append("ETL job requires 'load' configuration")
    
    elif processing_type == ProcessingType.AGGREGATION:
        if 'aggregations' not in config:
            errors.append("Aggregation job requires 'aggregations' configuration")
    
    elif processing_type == ProcessingType.VALIDATION:
        if 'rules' not in config:
            errors.append("Validation job requires 'rules' configuration")
    
    return errors

async def _execute_job_background(
    job_id: UUID,
    execution_id: UUID,
    input_data: Dict[str, Any],
    user_id: UUID
):
    """Execute job in background"""
    
    try:
        # This would be implemented with a proper task queue (Celery, etc.)
        # For now, just execute directly
        async with get_db() as db:
            result = await data_processing_engine.execute_job(job_id, input_data, user_id, db)
            
            # Update execution record
            execution_result = await db.execute(
                select(JobExecution).where(JobExecution.id == execution_id)
            )
            execution = execution_result.scalar_one_or_none()
            
            if execution:
                execution.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.records_processed = result.records_processed
                execution.execution_time_ms = result.execution_time_ms
                execution.errors = result.errors
                execution.warnings = result.warnings
                
                await db.commit()
    
    except Exception as e:
        # Log error and update execution record
        async with get_db() as db:
            execution_result = await db.execute(
                select(JobExecution).where(JobExecution.id == execution_id)
            )
            execution = execution_result.scalar_one_or_none()
            
            if execution:
                execution.status = JobStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.errors = [str(e)]
                
                await db.commit()

async def _test_source_connection(source: DataSource) -> bool:
    """Test data source connection"""
    
    try:
        if source.source_type == DataSourceType.DATABASE:
            # Test database connection
            return True
        elif source.source_type == DataSourceType.API:
            # Test API endpoint
            return True
        elif source.source_type == DataSourceType.FILE:
            # Test file access
            return True
        else:
            return False
    except Exception:
        return False

async def _run_quality_check(check: DataQualityCheck, db: AsyncSession) -> Tuple[float, Dict[str, Any]]:
    """Run data quality check"""
    
    if check.check_type == QualityCheckType.COMPLETENESS:
        # Check completeness
        query = f"SELECT COUNT(*) as total, COUNT({check.config.get('field', '*')}) as non_null FROM {check.target_table}"
        result = await db.execute(text(query))
        row = result.first()
        
        score = (row.non_null / row.total) if row.total > 0 else 0
        details = {"total_records": row.total, "non_null_records": row.non_null}
        
        return score, details
    
    elif check.check_type == QualityCheckType.UNIQUENESS:
        # Check uniqueness
        field = check.config.get('field', 'id')
        query = f"SELECT COUNT(*) as total, COUNT(DISTINCT {field}) as unique_count FROM {check.target_table}"
        result = await db.execute(text(query))
        row = result.first()
        
        score = (row.unique_count / row.total) if row.total > 0 else 0
        details = {"total_records": row.total, "unique_records": row.unique_count}
        
        return score, details
    
    else:
        # Default: return perfect score
        return 1.0, {"message": "Check type not implemented"}