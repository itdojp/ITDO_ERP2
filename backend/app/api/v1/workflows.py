"""Workflow management API endpoints for Phase 6 workflow functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.workflow import Workflow, WorkflowInstance, WorkflowTask
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
    WorkflowInstanceCreate,
    WorkflowInstanceResponse,
    WorkflowTaskResponse,
    WorkflowTaskUpdate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new workflow definition."""
    service = WorkflowService(db)
    workflow = await service.create_workflow(workflow_data)
    return workflow


@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(
    organization_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of workflows with optional filtering."""
    service = WorkflowService(db)
    workflows = await service.get_workflows(
        organization_id=organization_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get workflow by ID."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update workflow."""
    service = WorkflowService(db)
    workflow = await service.update_workflow(workflow_id, workflow_data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete workflow (soft delete)."""
    service = WorkflowService(db)
    success = await service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}


# Workflow Instance endpoints
@router.post("/{workflow_id}/instances", response_model=WorkflowInstanceResponse)
async def start_workflow_instance(
    workflow_id: int,
    instance_data: WorkflowInstanceCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start a new workflow instance."""
    service = WorkflowService(db)
    instance = await service.start_workflow_instance(workflow_id, instance_data)
    return instance


@router.get("/{workflow_id}/instances", response_model=List[WorkflowInstanceResponse])
async def get_workflow_instances(
    workflow_id: int,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get workflow instances."""
    service = WorkflowService(db)
    instances = await service.get_workflow_instances(
        workflow_id=workflow_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return instances


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get workflow instance by ID."""
    service = WorkflowService(db)
    instance = await service.get_workflow_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    return instance


# Workflow Task endpoints
@router.get("/instances/{instance_id}/tasks", response_model=List[WorkflowTaskResponse])
async def get_instance_tasks(
    instance_id: int,
    status: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get tasks for a workflow instance."""
    service = WorkflowService(db)
    tasks = await service.get_instance_tasks(
        instance_id=instance_id,
        status=status,
        assigned_to=assigned_to
    )
    return tasks


@router.put("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def update_workflow_task(
    task_id: int,
    task_data: WorkflowTaskUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update workflow task status and data."""
    service = WorkflowService(db)
    task = await service.update_workflow_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    return task


@router.post("/tasks/{task_id}/complete")
async def complete_workflow_task(
    task_id: int,
    completion_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Complete a workflow task."""
    service = WorkflowService(db)
    success = await service.complete_workflow_task(task_id, completion_data)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    return {"message": "Task completed successfully"}


@router.post("/tasks/{task_id}/assign")
async def assign_workflow_task(
    task_id: int,
    assignee_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Assign workflow task to user."""
    service = WorkflowService(db)
    success = await service.assign_workflow_task(task_id, assignee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    return {"message": "Task assigned successfully"}


# Workflow Analytics endpoints
@router.get("/{workflow_id}/analytics")
async def get_workflow_analytics(
    workflow_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get workflow performance analytics."""
    service = WorkflowService(db)
    analytics = await service.get_workflow_analytics(
        workflow_id=workflow_id,
        start_date=start_date,
        end_date=end_date
    )
    return analytics


@router.get("/instances/{instance_id}/progress")
async def get_instance_progress(
    instance_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get workflow instance progress."""
    service = WorkflowService(db)
    progress = await service.get_instance_progress(instance_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    return progress