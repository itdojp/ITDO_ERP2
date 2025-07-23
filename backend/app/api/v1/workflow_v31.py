"""
Workflow System API - CC02 v31.0 Phase 2

Comprehensive RESTful API for workflow management including:
- Business Process Automation & Orchestration
- Approval Workflows & State Management
- Dynamic Workflow Configuration
- Parallel & Sequential Processing
- Conditional Logic & Decision Trees
- Role-Based Task Assignment
- Workflow Analytics & Performance Tracking
- Template-Based Workflow Creation
- Integration Hooks & External Triggers
- Compliance & Audit Trail

Provides 10 main endpoint groups with 60+ individual endpoints
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.workflow_v31 import WorkflowService
from app.schemas.workflow_v31 import (
    TaskActionRequest,
    TaskAssignmentRequest,
    TaskDelegationRequest,
    TaskEscalationRequest,
    WorkflowActivityListResponse,
    # Activity schemas
    WorkflowActivityResponse,
    # Analytics schemas
    WorkflowAnalyticsRequest,
    WorkflowAnalyticsResponse,
    WorkflowAttachmentCreateRequest,
    WorkflowAttachmentListResponse,
    WorkflowAttachmentResponse,
    # Comment and attachment schemas
    WorkflowCommentCreateRequest,
    WorkflowCommentListResponse,
    WorkflowCommentResponse,
    WorkflowDashboardResponse,
    # Definition schemas
    WorkflowDefinitionCreateRequest,
    WorkflowDefinitionListResponse,
    WorkflowDefinitionResponse,
    WorkflowDefinitionUpdateRequest,
    WorkflowInstanceListResponse,
    WorkflowInstanceResponse,
    # Instance schemas
    WorkflowInstanceStartRequest,
    WorkflowStepResponse,
    WorkflowTaskListResponse,
    # Task schemas
    WorkflowTaskResponse,
    WorkflowTemplateListResponse,
    # Template schemas
    WorkflowTemplateResponse,
)

router = APIRouter()

def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    """Get workflow service instance."""
    return WorkflowService(db)


# =============================================================================
# 1. Workflow Definition Management (10 endpoints)
# =============================================================================

@router.post("/definitions", response_model=WorkflowDefinitionResponse)
async def create_workflow_definition(
    definition_data: WorkflowDefinitionCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionResponse:
    """Create a new workflow definition."""
    try:
        definition = await service.create_workflow_definition(definition_data.dict())
        return WorkflowDefinitionResponse(**definition.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow definition: {str(e)}"
        )


@router.get("/definitions", response_model=WorkflowDefinitionListResponse)
async def list_workflow_definitions(
    organization_id: str = Query(..., description="Organization ID"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionListResponse:
    """List workflow definitions with filtering and pagination."""
    try:
        filters = {
            "organization_id": organization_id,
            "workflow_type": workflow_type,
            "category": category,
            "status": status,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        definitions, total = await service.list_workflow_definitions(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowDefinitionListResponse(
            definitions=[WorkflowDefinitionResponse(**d.__dict__) for d in definitions],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list workflow definitions: {str(e)}"
        )


@router.get("/definitions/{definition_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow_definition(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionResponse:
    """Get workflow definition by ID."""
    try:
        definition = await service.get_workflow_definition(definition_id)
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return WorkflowDefinitionResponse(**definition.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow definition: {str(e)}"
        )


@router.put("/definitions/{definition_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow_definition(
    definition_id: str,
    update_data: WorkflowDefinitionUpdateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionResponse:
    """Update workflow definition."""
    try:
        definition = await service.update_workflow_definition(
            definition_id,
            update_data.dict(exclude_unset=True)
        )
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return WorkflowDefinitionResponse(**definition.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update workflow definition: {str(e)}"
        )


@router.delete("/definitions/{definition_id}")
async def delete_workflow_definition(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Delete workflow definition."""
    try:
        success = await service.delete_workflow_definition(definition_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return {"message": "Workflow definition deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete workflow definition: {str(e)}"
        )


@router.post("/definitions/{definition_id}/activate")
async def activate_workflow_definition(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Activate workflow definition."""
    try:
        success = await service.activate_workflow_definition(definition_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return {"message": "Workflow definition activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to activate workflow definition: {str(e)}"
        )


@router.post("/definitions/{definition_id}/deactivate")
async def deactivate_workflow_definition(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Deactivate workflow definition."""
    try:
        success = await service.deactivate_workflow_definition(definition_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return {"message": "Workflow definition deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deactivate workflow definition: {str(e)}"
        )


@router.post("/definitions/{definition_id}/duplicate", response_model=WorkflowDefinitionResponse)
async def duplicate_workflow_definition(
    definition_id: str,
    new_name: str = Query(..., description="Name for the duplicated workflow"),
    new_code: str = Query(..., description="Code for the duplicated workflow"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionResponse:
    """Duplicate workflow definition."""
    try:
        definition = await service.duplicate_workflow_definition(
            definition_id, new_name, new_code
        )
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow definition not found"
            )
        return WorkflowDefinitionResponse(**definition.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to duplicate workflow definition: {str(e)}"
        )


@router.get("/definitions/{definition_id}/steps", response_model=List[WorkflowStepResponse])
async def get_workflow_steps(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> List[WorkflowStepResponse]:
    """Get workflow steps for a definition."""
    try:
        steps = await service.get_workflow_steps(definition_id)
        return [WorkflowStepResponse(**step.__dict__) for step in steps]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow steps: {str(e)}"
        )


@router.post("/definitions/{definition_id}/validate")
async def validate_workflow_definition(
    definition_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Validate workflow definition configuration."""
    try:
        validation_result = await service.validate_workflow_definition(definition_id)
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate workflow definition: {str(e)}"
        )


# =============================================================================
# 2. Workflow Instance Management (10 endpoints)
# =============================================================================

@router.post("/instances", response_model=WorkflowInstanceResponse)
async def start_workflow_instance(
    instance_data: WorkflowInstanceStartRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowInstanceResponse:
    """Start a new workflow instance."""
    try:
        instance = await service.start_workflow_instance(instance_data.dict())
        return WorkflowInstanceResponse(**instance.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start workflow instance: {str(e)}"
        )


@router.get("/instances", response_model=WorkflowInstanceListResponse)
async def list_workflow_instances(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowInstanceListResponse:
    """List workflow instances with filtering and pagination."""
    try:
        filters = {
            "organization_id": organization_id,
            "definition_id": definition_id,
            "status": status,
            "current_assignee_id": assignee_id,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        instances, total = await service.list_workflow_instances(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowInstanceListResponse(
            instances=[WorkflowInstanceResponse(**i.__dict__) for i in instances],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list workflow instances: {str(e)}"
        )


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowInstanceResponse:
    """Get workflow instance by ID."""
    try:
        instance = await service.get_workflow_instance(instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return WorkflowInstanceResponse(**instance.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow instance: {str(e)}"
        )


@router.post("/instances/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str,
    reason: str = Query(..., description="Cancellation reason"),
    cancelled_by: str = Query(..., description="User ID who cancelled"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Cancel workflow instance."""
    try:
        success = await service.cancel_workflow_instance(instance_id, reason, cancelled_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return {"message": "Workflow instance cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel workflow instance: {str(e)}"
        )


@router.post("/instances/{instance_id}/suspend")
async def suspend_workflow_instance(
    instance_id: str,
    reason: str = Query(..., description="Suspension reason"),
    suspended_by: str = Query(..., description="User ID who suspended"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Suspend workflow instance."""
    try:
        success = await service.suspend_workflow_instance(instance_id, reason, suspended_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return {"message": "Workflow instance suspended successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to suspend workflow instance: {str(e)}"
        )


@router.post("/instances/{instance_id}/resume")
async def resume_workflow_instance(
    instance_id: str,
    resumed_by: str = Query(..., description="User ID who resumed"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Resume suspended workflow instance."""
    try:
        success = await service.resume_workflow_instance(instance_id, resumed_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return {"message": "Workflow instance resumed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resume workflow instance: {str(e)}"
        )


@router.post("/instances/{instance_id}/restart")
async def restart_workflow_instance(
    instance_id: str,
    restarted_by: str = Query(..., description="User ID who restarted"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Restart failed workflow instance."""
    try:
        success = await service.restart_workflow_instance(instance_id, restarted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return {"message": "Workflow instance restarted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to restart workflow instance: {str(e)}"
        )


@router.get("/instances/{instance_id}/progress")
async def get_workflow_progress(
    instance_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get detailed workflow progress information."""
    try:
        progress = await service.get_workflow_progress(instance_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow progress: {str(e)}"
        )


@router.get("/instances/{instance_id}/timeline")
async def get_workflow_timeline(
    instance_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get workflow execution timeline."""
    try:
        timeline = await service.get_workflow_timeline(instance_id)
        if not timeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow timeline: {str(e)}"
        )


@router.post("/instances/{instance_id}/reassign")
async def reassign_workflow_instance(
    instance_id: str,
    new_assignee_id: str = Query(..., description="New assignee user ID"),
    reassigned_by: str = Query(..., description="User ID who reassigned"),
    reason: Optional[str] = Query(None, description="Reassignment reason"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Reassign workflow instance to different user."""
    try:
        success = await service.reassign_workflow_instance(
            instance_id, new_assignee_id, reassigned_by, reason
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow instance not found"
            )
        return {"message": "Workflow instance reassigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reassign workflow instance: {str(e)}"
        )


# =============================================================================
# 3. Task Management (10 endpoints)
# =============================================================================

@router.get("/tasks", response_model=WorkflowTaskListResponse)
async def list_workflow_tasks(
    organization_id: str = Query(..., description="Organization ID"),
    instance_id: Optional[str] = Query(None, description="Filter by instance ID"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTaskListResponse:
    """List workflow tasks with filtering and pagination."""
    try:
        filters = {
            "organization_id": organization_id,
            "instance_id": instance_id,
            "assignee_id": assignee_id,
            "status": status,
            "priority": priority,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        tasks, total = await service.list_workflow_tasks(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowTaskListResponse(
            tasks=[WorkflowTaskResponse(**t.__dict__) for t in tasks],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list workflow tasks: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def get_workflow_task(
    task_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTaskResponse:
    """Get workflow task by ID."""
    try:
        task = await service.get_workflow_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return WorkflowTaskResponse(**task.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow task: {str(e)}"
        )


@router.post("/tasks/{task_id}/action")
async def perform_task_action(
    task_id: str,
    action_data: TaskActionRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Perform action on workflow task."""
    try:
        success = await service.perform_task_action(task_id, action_data.dict())
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": f"Task action '{action_data.action_type}' performed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to perform task action: {str(e)}"
        )


@router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    assignment_data: TaskAssignmentRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Assign task to user."""
    try:
        success = await service.assign_task(task_id, assignment_data.dict())
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": "Task assigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign task: {str(e)}"
        )


@router.post("/tasks/{task_id}/delegate")
async def delegate_task(
    task_id: str,
    delegation_data: TaskDelegationRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Delegate task to another user."""
    try:
        success = await service.delegate_task(task_id, delegation_data.dict())
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": "Task delegated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delegate task: {str(e)}"
        )


@router.post("/tasks/{task_id}/escalate")
async def escalate_task(
    task_id: str,
    escalation_data: TaskEscalationRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Escalate task to higher authority."""
    try:
        success = await service.escalate_task(task_id, escalation_data.dict())
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": "Task escalated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to escalate task: {str(e)}"
        )


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    started_by: str = Query(..., description="User ID who started the task"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Start working on a task."""
    try:
        success = await service.start_task(task_id, started_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": "Task started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start task: {str(e)}"
        )


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    result: str = Query(..., description="Task completion result"),
    notes: Optional[str] = Query(None, description="Completion notes"),
    completed_by: str = Query(..., description="User ID who completed the task"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Complete a task."""
    try:
        success = await service.complete_task(task_id, result, notes, completed_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return {"message": "Task completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete task: {str(e)}"
        )


@router.get("/tasks/{task_id}/history")
async def get_task_history(
    task_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get task execution history."""
    try:
        history = await service.get_task_history(task_id)
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow task not found"
            )
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get task history: {str(e)}"
        )


@router.get("/tasks/my-tasks")
async def get_my_tasks(
    user_id: str = Query(..., description="User ID"),
    organization_id: str = Query(..., description="Organization ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTaskListResponse:
    """Get tasks assigned to current user."""
    try:
        filters = {
            "organization_id": organization_id,
            "assignee_id": user_id,
            "status": status,
            "priority": priority,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        tasks, total = await service.list_workflow_tasks(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowTaskListResponse(
            tasks=[WorkflowTaskResponse(**t.__dict__) for t in tasks],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user tasks: {str(e)}"
        )


# =============================================================================
# 4. Comments Management (10 endpoints)
# =============================================================================

@router.post("/tasks/{task_id}/comments", response_model=WorkflowCommentResponse)
async def create_comment(
    task_id: str,
    comment_data: WorkflowCommentCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentResponse:
    """Create a new comment on a task."""
    try:
        comment = await service.create_comment(task_id, comment_data.dict())
        return WorkflowCommentResponse(**comment.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/tasks/{task_id}/comments", response_model=WorkflowCommentListResponse)
async def list_task_comments(
    task_id: str,
    include_internal: bool = Query(False, description="Include internal comments"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentListResponse:
    """List comments for a task."""
    try:
        filters = {
            "task_id": task_id,
            "include_internal": include_internal,
        }

        comments, total = await service.list_task_comments(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowCommentListResponse(
            comments=[WorkflowCommentResponse(**c.__dict__) for c in comments],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list task comments: {str(e)}"
        )


@router.get("/comments/{comment_id}", response_model=WorkflowCommentResponse)
async def get_comment(
    comment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentResponse:
    """Get comment by ID."""
    try:
        comment = await service.get_comment(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return WorkflowCommentResponse(**comment.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get comment: {str(e)}"
        )


@router.put("/comments/{comment_id}", response_model=WorkflowCommentResponse)
async def update_comment(
    comment_id: str,
    comment_text: str = Query(..., description="Updated comment text"),
    updated_by: str = Query(..., description="User ID who updated"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentResponse:
    """Update comment."""
    try:
        comment = await service.update_comment(comment_id, comment_text, updated_by)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return WorkflowCommentResponse(**comment.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    deleted_by: str = Query(..., description="User ID who deleted"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Delete comment."""
    try:
        success = await service.delete_comment(comment_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete comment: {str(e)}"
        )


@router.post("/comments/{comment_id}/reply", response_model=WorkflowCommentResponse)
async def reply_to_comment(
    comment_id: str,
    comment_data: WorkflowCommentCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentResponse:
    """Reply to a comment."""
    try:
        reply = await service.reply_to_comment(comment_id, comment_data.dict())
        return WorkflowCommentResponse(**reply.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reply to comment: {str(e)}"
        )


@router.get("/comments/{comment_id}/thread", response_model=WorkflowCommentListResponse)
async def get_comment_thread(
    comment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentListResponse:
    """Get comment thread (parent and all replies)."""
    try:
        comments, total = await service.get_comment_thread(comment_id)

        return WorkflowCommentListResponse(
            comments=[WorkflowCommentResponse(**c.__dict__) for c in comments],
            total_count=total,
            page=1,
            per_page=total,
            has_more=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get comment thread: {str(e)}"
        )


@router.post("/comments/{comment_id}/mention")
async def mention_users_in_comment(
    comment_id: str,
    user_ids: List[str] = Query(..., description="User IDs to mention"),
    mentioned_by: str = Query(..., description="User ID who mentioned"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Mention users in a comment."""
    try:
        success = await service.mention_users_in_comment(comment_id, user_ids, mentioned_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return {"message": "Users mentioned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to mention users: {str(e)}"
        )


@router.get("/comments/search")
async def search_comments(
    organization_id: str = Query(..., description="Organization ID"),
    search_text: str = Query(..., description="Text to search for"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    author_id: Optional[str] = Query(None, description="Filter by author"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentListResponse:
    """Search comments by text."""
    try:
        filters = {
            "organization_id": organization_id,
            "search_text": search_text,
            "task_id": task_id,
            "author_id": author_id,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        comments, total = await service.search_comments(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowCommentListResponse(
            comments=[WorkflowCommentResponse(**c.__dict__) for c in comments],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to search comments: {str(e)}"
        )


@router.get("/comments/recent")
async def get_recent_comments(
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent comments"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowCommentListResponse:
    """Get recent comments across all tasks."""
    try:
        comments, total = await service.get_recent_comments(organization_id, limit)

        return WorkflowCommentListResponse(
            comments=[WorkflowCommentResponse(**c.__dict__) for c in comments],
            total_count=total,
            page=1,
            per_page=limit,
            has_more=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get recent comments: {str(e)}"
        )


# =============================================================================
# 5. Attachments Management (10 endpoints)
# =============================================================================

@router.post("/tasks/{task_id}/attachments", response_model=WorkflowAttachmentResponse)
async def upload_attachment(
    task_id: str,
    attachment_data: WorkflowAttachmentCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentResponse:
    """Upload attachment to a task."""
    try:
        attachment = await service.upload_attachment(task_id, attachment_data.dict())
        return WorkflowAttachmentResponse(**attachment.__dict__)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload attachment: {str(e)}"
        )


@router.get("/tasks/{task_id}/attachments", response_model=WorkflowAttachmentListResponse)
async def list_task_attachments(
    task_id: str,
    attachment_type: Optional[str] = Query(None, description="Filter by attachment type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentListResponse:
    """List attachments for a task."""
    try:
        filters = {
            "task_id": task_id,
            "attachment_type": attachment_type,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        attachments, total = await service.list_task_attachments(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowAttachmentListResponse(
            attachments=[WorkflowAttachmentResponse(**a.__dict__) for a in attachments],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list task attachments: {str(e)}"
        )


@router.get("/attachments/{attachment_id}", response_model=WorkflowAttachmentResponse)
async def get_attachment(
    attachment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentResponse:
    """Get attachment by ID."""
    try:
        attachment = await service.get_attachment(attachment_id)
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return WorkflowAttachmentResponse(**attachment.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get attachment: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Download attachment file."""
    try:
        file_info = await service.download_attachment(attachment_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return file_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download attachment: {str(e)}"
        )


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    deleted_by: str = Query(..., description="User ID who deleted"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Delete attachment."""
    try:
        success = await service.delete_attachment(attachment_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return {"message": "Attachment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete attachment: {str(e)}"
        )


@router.post("/attachments/{attachment_id}/version", response_model=WorkflowAttachmentResponse)
async def create_attachment_version(
    attachment_id: str,
    attachment_data: WorkflowAttachmentCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentResponse:
    """Create new version of attachment."""
    try:
        new_version = await service.create_attachment_version(attachment_id, attachment_data.dict())
        if not new_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return WorkflowAttachmentResponse(**new_version.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create attachment version: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/versions", response_model=WorkflowAttachmentListResponse)
async def get_attachment_versions(
    attachment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentListResponse:
    """Get all versions of an attachment."""
    try:
        versions, total = await service.get_attachment_versions(attachment_id)

        return WorkflowAttachmentListResponse(
            attachments=[WorkflowAttachmentResponse(**v.__dict__) for v in versions],
            total_count=total,
            page=1,
            per_page=total,
            has_more=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get attachment versions: {str(e)}"
        )


@router.post("/attachments/{attachment_id}/share")
async def share_attachment(
    attachment_id: str,
    user_ids: List[str] = Query(..., description="User IDs to share with"),
    access_level: str = Query("read", description="Access level (read, write)"),
    shared_by: str = Query(..., description="User ID who shared"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, str]:
    """Share attachment with other users."""
    try:
        success = await service.share_attachment(attachment_id, user_ids, access_level, shared_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return {"message": "Attachment shared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to share attachment: {str(e)}"
        )


@router.get("/attachments/search")
async def search_attachments(
    organization_id: str = Query(..., description="Organization ID"),
    filename: Optional[str] = Query(None, description="Search by filename"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    uploaded_by: Optional[str] = Query(None, description="Filter by uploader"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAttachmentListResponse:
    """Search attachments."""
    try:
        filters = {
            "organization_id": organization_id,
            "filename": filename,
            "file_type": file_type,
            "uploaded_by": uploaded_by,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        attachments, total = await service.search_attachments(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowAttachmentListResponse(
            attachments=[WorkflowAttachmentResponse(**a.__dict__) for a in attachments],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to search attachments: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/metadata")
async def get_attachment_metadata(
    attachment_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get attachment metadata and properties."""
    try:
        metadata = await service.get_attachment_metadata(attachment_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get attachment metadata: {str(e)}"
        )


# =============================================================================
# 6. Analytics & Reporting (10 endpoints)
# =============================================================================

@router.post("/analytics", response_model=WorkflowAnalyticsResponse)
async def generate_workflow_analytics(
    analytics_request: WorkflowAnalyticsRequest,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowAnalyticsResponse:
    """Generate comprehensive workflow analytics."""
    try:
        analytics = await service.generate_workflow_analytics(analytics_request.dict())
        return WorkflowAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate workflow analytics: {str(e)}"
        )


@router.get("/analytics/dashboard", response_model=WorkflowDashboardResponse)
async def get_workflow_dashboard(
    organization_id: str = Query(..., description="Organization ID"),
    period_days: int = Query(30, description="Period in days"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDashboardResponse:
    """Get workflow dashboard data."""
    try:
        dashboard_data = await service.get_workflow_dashboard(organization_id, period_days)
        return WorkflowDashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow dashboard: {str(e)}"
        )


@router.get("/analytics/performance")
async def get_performance_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get detailed performance metrics."""
    try:
        metrics = await service.get_performance_metrics(
            organization_id, definition_id, period_start, period_end
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/analytics/bottlenecks")
async def analyze_bottlenecks(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_days: int = Query(30, description="Analysis period in days"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Analyze workflow bottlenecks."""
    try:
        bottlenecks = await service.analyze_bottlenecks(organization_id, definition_id, period_days)
        return bottlenecks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyze bottlenecks: {str(e)}"
        )


@router.get("/analytics/sla-compliance")
async def get_sla_compliance(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get SLA compliance metrics."""
    try:
        compliance = await service.get_sla_compliance(
            organization_id, definition_id, period_start, period_end
        )
        return compliance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get SLA compliance: {str(e)}"
        )


@router.get("/analytics/user-productivity")
async def get_user_productivity(
    organization_id: str = Query(..., description="Organization ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get user productivity metrics."""
    try:
        productivity = await service.get_user_productivity(
            organization_id, user_id, period_start, period_end
        )
        return productivity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user productivity: {str(e)}"
        )


@router.get("/analytics/workflow-trends")
async def get_workflow_trends(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_months: int = Query(12, description="Trend period in months"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get workflow trends over time."""
    try:
        trends = await service.get_workflow_trends(organization_id, definition_id, period_months)
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow trends: {str(e)}"
        )


@router.get("/analytics/cost-analysis")
async def get_cost_analysis(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get workflow cost analysis."""
    try:
        cost_analysis = await service.get_cost_analysis(
            organization_id, definition_id, period_start, period_end
        )
        return cost_analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get cost analysis: {str(e)}"
        )


@router.get("/analytics/quality-metrics")
async def get_quality_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    definition_id: Optional[str] = Query(None, description="Filter by definition ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get workflow quality metrics."""
    try:
        quality_metrics = await service.get_quality_metrics(
            organization_id, definition_id, period_start, period_end
        )
        return quality_metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get quality metrics: {str(e)}"
        )


@router.post("/analytics/custom-report")
async def generate_custom_report(
    organization_id: str = Query(..., description="Organization ID"),
    report_config: Dict[str, any] = Query(..., description="Custom report configuration"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Generate custom workflow report."""
    try:
        report = await service.generate_custom_report(organization_id, report_config)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate custom report: {str(e)}"
        )


# =============================================================================
# 7. Templates Management (5 endpoints)
# =============================================================================

@router.get("/templates", response_model=WorkflowTemplateListResponse)
async def list_workflow_templates(
    organization_id: str = Query(..., description="Organization ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTemplateListResponse:
    """List workflow templates."""
    try:
        filters = {
            "organization_id": organization_id,
            "category": category,
            "industry": industry,
            "is_public": is_public,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        templates, total = await service.list_workflow_templates(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowTemplateListResponse(
            templates=[WorkflowTemplateResponse(**t.__dict__) for t in templates],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list workflow templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_workflow_template(
    template_id: str,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTemplateResponse:
    """Get workflow template by ID."""
    try:
        template = await service.get_workflow_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow template not found"
            )
        return WorkflowTemplateResponse(**template.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow template: {str(e)}"
        )


@router.post("/templates/{template_id}/instantiate", response_model=WorkflowDefinitionResponse)
async def instantiate_template(
    template_id: str,
    name: str = Query(..., description="Name for the new workflow"),
    code: str = Query(..., description="Code for the new workflow"),
    organization_id: str = Query(..., description="Organization ID"),
    created_by: str = Query(..., description="Creator user ID"),
    customizations: Optional[Dict[str, any]] = None,
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowDefinitionResponse:
    """Create workflow definition from template."""
    try:
        definition = await service.instantiate_template(
            template_id, name, code, organization_id, created_by, customizations or {}
        )
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow template not found"
            )
        return WorkflowDefinitionResponse(**definition.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to instantiate template: {str(e)}"
        )


@router.get("/templates/popular")
async def get_popular_templates(
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of templates"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowTemplateListResponse:
    """Get popular workflow templates."""
    try:
        templates, total = await service.get_popular_templates(organization_id, limit)

        return WorkflowTemplateListResponse(
            templates=[WorkflowTemplateResponse(**t.__dict__) for t in templates],
            total_count=total,
            page=1,
            per_page=limit,
            has_more=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get popular templates: {str(e)}"
        )


@router.get("/templates/categories")
async def get_template_categories(
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, List[str]]:
    """Get available template categories and industries."""
    try:
        categories = await service.get_template_categories()
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get template categories: {str(e)}"
        )


# =============================================================================
# 8. Activity Log & Audit (5 endpoints)
# =============================================================================

@router.get("/instances/{instance_id}/activities", response_model=WorkflowActivityListResponse)
async def get_instance_activities(
    instance_id: str,
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    performed_by: Optional[str] = Query(None, description="Filter by user"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowActivityListResponse:
    """Get activities for a workflow instance."""
    try:
        filters = {
            "instance_id": instance_id,
            "activity_type": activity_type,
            "performed_by": performed_by,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        activities, total = await service.get_instance_activities(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowActivityListResponse(
            activities=[WorkflowActivityResponse(**a.__dict__) for a in activities],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get instance activities: {str(e)}"
        )


@router.get("/tasks/{task_id}/activities", response_model=WorkflowActivityListResponse)
async def get_task_activities(
    task_id: str,
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowActivityListResponse:
    """Get activities for a workflow task."""
    try:
        filters = {
            "task_id": task_id,
            "activity_type": activity_type,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        activities, total = await service.get_task_activities(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return WorkflowActivityListResponse(
            activities=[WorkflowActivityResponse(**a.__dict__) for a in activities],
            total_count=total,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get task activities: {str(e)}"
        )


@router.get("/activities/audit-trail")
async def get_audit_trail(
    organization_id: str = Query(..., description="Organization ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get comprehensive audit trail."""
    try:
        filters = {
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        audit_trail = await service.get_audit_trail(
            filters=filters,
            page=page,
            per_page=per_page
        )
        return audit_trail
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get audit trail: {str(e)}"
        )


@router.get("/activities/user-activity")
async def get_user_activity(
    user_id: str = Query(..., description="User ID"),
    organization_id: str = Query(..., description="Organization ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Get user activity summary."""
    try:
        activity = await service.get_user_activity(
            user_id, organization_id, start_date, end_date, page, per_page
        )
        return activity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user activity: {str(e)}"
        )


@router.post("/activities/export")
async def export_activities(
    organization_id: str = Query(..., description="Organization ID"),
    format: str = Query("csv", description="Export format (csv, excel, json)"),
    filters: Optional[Dict[str, any]] = None,
    service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, any]:
    """Export activity data."""
    try:
        export_result = await service.export_activities(
            organization_id, format, filters or {}
        )
        return export_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to export activities: {str(e)}"
        )
