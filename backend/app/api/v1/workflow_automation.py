"""Workflow Automation & Integration API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.workflow_automation import (
    workflow_manager,
    Workflow,
    WorkflowStep,
    WorkflowTrigger,
    WorkflowVariable,
    Integration,
    WorkflowStatus,
    StepType,
    TriggerType,
    IntegrationType,
    check_workflow_automation_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class WorkflowVariableRequest(BaseModel):
    """Workflow variable request."""
    name: str = Field(..., max_length=100)
    value: Any
    data_type: str = Field(..., max_length=50)
    description: str = Field("", max_length=500)
    scope: str = Field("workflow", max_length=50)


class WorkflowVariableResponse(BaseModel):
    """Workflow variable response."""
    name: str
    value: Any
    data_type: str
    description: str
    scope: str

    class Config:
        from_attributes = True


class WorkflowStepRequest(BaseModel):
    """Workflow step request."""
    name: str = Field(..., max_length=200)
    step_type: StepType
    configuration: Dict[str, Any] = {}
    conditions: Dict[str, Any] = {}
    next_steps: List[str] = []
    position: Dict[str, int] = {}
    timeout_seconds: int = Field(300, ge=1, le=3600)
    retry_count: int = Field(0, ge=0, le=5)
    enabled: bool = True


class WorkflowStepResponse(BaseModel):
    """Workflow step response."""
    id: str
    name: str
    step_type: str
    configuration: Dict[str, Any]
    conditions: Dict[str, Any]
    next_steps: List[str]
    position: Dict[str, int]
    timeout_seconds: int
    retry_count: int
    enabled: bool

    class Config:
        from_attributes = True


class WorkflowTriggerRequest(BaseModel):
    """Workflow trigger request."""
    trigger_type: TriggerType
    configuration: Dict[str, Any] = {}
    schedule: Optional[str] = Field(None, max_length=100)
    enabled: bool = True


class WorkflowTriggerResponse(BaseModel):
    """Workflow trigger response."""
    id: str
    trigger_type: str
    configuration: Dict[str, Any]
    schedule: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


class IntegrationRequest(BaseModel):
    """Integration request."""
    name: str = Field(..., max_length=200)
    integration_type: IntegrationType
    endpoint_url: str = Field(..., max_length=500)
    authentication: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    timeout: int = Field(30, ge=1, le=300)
    enabled: bool = True


class IntegrationResponse(BaseModel):
    """Integration response."""
    id: str
    name: str
    integration_type: str
    endpoint_url: str
    authentication: Dict[str, Any]
    headers: Dict[str, str]
    timeout: int
    enabled: bool

    class Config:
        from_attributes = True


class WorkflowRequest(BaseModel):
    """Workflow creation request."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    version: str = Field("1.0", max_length=20)
    steps: List[WorkflowStepRequest] = []
    triggers: List[WorkflowTriggerRequest] = []
    variables: List[WorkflowVariableRequest] = []
    integrations: List[IntegrationRequest] = []
    status: WorkflowStatus = WorkflowStatus.DRAFT


class WorkflowResponse(BaseModel):
    """Workflow response."""
    id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStepResponse]
    triggers: List[WorkflowTriggerResponse]
    variables: List[WorkflowVariableResponse]
    integrations: List[IntegrationResponse]
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class WorkflowExecutionRequest(BaseModel):
    """Workflow execution request."""
    trigger_data: Dict[str, Any] = {}


class StepExecutionResponse(BaseModel):
    """Step execution response."""
    id: str
    workflow_execution_id: str
    step_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    retry_attempt: int
    execution_time_ms: Optional[float]

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response."""
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    triggered_by: str
    trigger_data: Dict[str, Any]
    variables: Dict[str, Any]
    step_executions: List[StepExecutionResponse]
    current_step: Optional[str]

    class Config:
        from_attributes = True


class SystemStatusResponse(BaseModel):
    """System status response."""
    total_workflows: int
    active_workflows: int
    total_executions: int
    recent_executions_24h: int
    successful_executions_24h: int
    failed_executions_24h: int
    active_executions: int
    integrations: int
    scheduler_running: bool
    timestamp: str


class WorkflowHealthResponse(BaseModel):
    """Workflow health response."""
    status: str
    system_status: SystemStatusResponse
    custom_handlers: int
    event_handlers: int


# Workflow Management Endpoints
@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow_request: WorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow."""
    try:
        # Convert request objects to domain objects
        steps = []
        for step_req in workflow_request.steps:
            step = WorkflowStep(
                id="",  # Will be auto-generated
                name=step_req.name,
                step_type=step_req.step_type,
                configuration=step_req.configuration,
                conditions=step_req.conditions,
                next_steps=step_req.next_steps,
                position=step_req.position,
                timeout_seconds=step_req.timeout_seconds,
                retry_count=step_req.retry_count,
                enabled=step_req.enabled
            )
            steps.append(step)
        
        triggers = []
        for trigger_req in workflow_request.triggers:
            trigger = WorkflowTrigger(
                id="",  # Will be auto-generated
                trigger_type=trigger_req.trigger_type,
                configuration=trigger_req.configuration,
                schedule=trigger_req.schedule,
                enabled=trigger_req.enabled
            )
            triggers.append(trigger)
        
        variables = []
        for var_req in workflow_request.variables:
            variable = WorkflowVariable(
                name=var_req.name,
                value=var_req.value,
                data_type=var_req.data_type,
                description=var_req.description,
                scope=var_req.scope
            )
            variables.append(variable)
        
        integrations = []
        for int_req in workflow_request.integrations:
            integration = Integration(
                id="",  # Will be auto-generated
                name=int_req.name,
                integration_type=int_req.integration_type,
                endpoint_url=int_req.endpoint_url,
                authentication=int_req.authentication,
                headers=int_req.headers,
                timeout=int_req.timeout,
                enabled=int_req.enabled
            )
            integrations.append(integration)
        
        # Create workflow
        workflow = Workflow(
            id="",  # Will be auto-generated
            name=workflow_request.name,
            description=workflow_request.description,
            version=workflow_request.version,
            steps=steps,
            triggers=triggers,
            variables=variables,
            integrations=integrations,
            status=workflow_request.status,
            created_by=str(current_user.id)
        )
        
        workflow_id = await workflow_manager.create_workflow(workflow)
        created_workflow = await workflow_manager.get_workflow(workflow_id)
        
        return _convert_workflow_to_response(created_workflow)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    status_filter: Optional[WorkflowStatus] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List workflows."""
    try:
        workflows = await workflow_manager.list_workflows(status_filter)
        
        return [_convert_workflow_to_response(workflow) for workflow in workflows]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific workflow."""
    try:
        workflow = await workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return _convert_workflow_to_response(workflow)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_request: WorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing workflow."""
    try:
        existing_workflow = await workflow_manager.get_workflow(workflow_id)
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Convert request to domain objects (similar to create)
        steps = []
        for step_req in workflow_request.steps:
            step = WorkflowStep(
                id="",  # Will be auto-generated
                name=step_req.name,
                step_type=step_req.step_type,
                configuration=step_req.configuration,
                conditions=step_req.conditions,
                next_steps=step_req.next_steps,
                position=step_req.position,
                timeout_seconds=step_req.timeout_seconds,
                retry_count=step_req.retry_count,
                enabled=step_req.enabled
            )
            steps.append(step)
        
        triggers = []
        for trigger_req in workflow_request.triggers:
            trigger = WorkflowTrigger(
                id="",  # Will be auto-generated
                trigger_type=trigger_req.trigger_type,
                configuration=trigger_req.configuration,
                schedule=trigger_req.schedule,
                enabled=trigger_req.enabled
            )
            triggers.append(trigger)
        
        variables = []
        for var_req in workflow_request.variables:
            variable = WorkflowVariable(
                name=var_req.name,
                value=var_req.value,
                data_type=var_req.data_type,
                description=var_req.description,
                scope=var_req.scope
            )
            variables.append(variable)
        
        integrations = []
        for int_req in workflow_request.integrations:
            integration = Integration(
                id="",  # Will be auto-generated
                name=int_req.name,
                integration_type=int_req.integration_type,
                endpoint_url=int_req.endpoint_url,
                authentication=int_req.authentication,
                headers=int_req.headers,
                timeout=int_req.timeout,
                enabled=int_req.enabled
            )
            integrations.append(integration)
        
        # Update workflow
        updated_workflow = Workflow(
            id=workflow_id,
            name=workflow_request.name,
            description=workflow_request.description,
            version=workflow_request.version,
            steps=steps,
            triggers=triggers,
            variables=variables,
            integrations=integrations,
            status=workflow_request.status,
            created_at=existing_workflow.created_at,
            updated_at=datetime.utcnow(),
            created_by=existing_workflow.created_by
        )
        
        success = await workflow_manager.update_workflow(updated_workflow)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update workflow"
            )
        
        return _convert_workflow_to_response(updated_workflow)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a workflow."""
    try:
        success = await workflow_manager.delete_workflow(workflow_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return {"message": f"Workflow {workflow_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {str(e)}"
        )


# Workflow Execution Endpoints
@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    execution_request: WorkflowExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a workflow."""
    try:
        execution = await workflow_manager.execute_workflow(
            workflow_id=workflow_id,
            trigger_data=execution_request.trigger_data,
            triggered_by=str(current_user.id)
        )
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found or not active"
            )
        
        return _convert_execution_to_response(execution)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.get("/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """List workflow executions."""
    try:
        executions = await workflow_manager.list_executions(workflow_id, limit)
        
        return [_convert_execution_to_response(execution) for execution in executions]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve executions: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific execution."""
    try:
        execution = await workflow_manager.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return _convert_execution_to_response(execution)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve execution: {str(e)}"
        )


# Integration Management Endpoints
@router.post("/integrations")
async def register_integration(
    integration_request: IntegrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register an external integration."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        integration = Integration(
            id="",  # Will be auto-generated
            name=integration_request.name,
            integration_type=integration_request.integration_type,
            endpoint_url=integration_request.endpoint_url,
            authentication=integration_request.authentication,
            headers=integration_request.headers,
            timeout=integration_request.timeout,
            enabled=integration_request.enabled
        )
        
        integration_id = await workflow_manager.register_integration(integration)
        
        return {
            "message": "Integration registered successfully",
            "integration_id": integration_id,
            "name": integration_request.name,
            "type": integration_request.integration_type.value,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register integration: {str(e)}"
        )


@router.post("/integrations/{integration_id}/test")
async def test_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user)
):
    """Test integration connectivity."""
    try:
        test_result = await workflow_manager.test_integration(integration_id)
        
        return test_result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test integration: {str(e)}"
        )


@router.get("/integrations")
async def list_integrations(
    current_user: User = Depends(get_current_user)
):
    """List all integrations."""
    try:
        integrations = workflow_manager.integration_manager.integrations
        
        integration_list = []
        for integration_id, integration in integrations.items():
            integration_list.append({
                "id": integration.id,
                "name": integration.name,
                "integration_type": integration.integration_type.value,
                "endpoint_url": integration.endpoint_url,
                "enabled": integration.enabled
            })
        
        return {
            "integrations": integration_list,
            "total_count": len(integration_list),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integrations: {str(e)}"
        )


# System Information Endpoints
@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """Get workflow automation system status."""
    try:
        status_info = await workflow_manager.get_system_status()
        
        return SystemStatusResponse(
            total_workflows=status_info["total_workflows"],
            active_workflows=status_info["active_workflows"],
            total_executions=status_info["total_executions"],
            recent_executions_24h=status_info["recent_executions_24h"],
            successful_executions_24h=status_info["successful_executions_24h"],
            failed_executions_24h=status_info["failed_executions_24h"],
            active_executions=status_info["active_executions"],
            integrations=status_info["integrations"],
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
    """List available workflow types and enums."""
    return {
        "workflow_statuses": [ws.value for ws in WorkflowStatus],
        "step_types": [st.value for st in StepType],
        "trigger_types": [tt.value for tt in TriggerType],
        "integration_types": [it.value for it in IntegrationType]
    }


# Health check endpoint
@router.get("/health", response_model=WorkflowHealthResponse)
async def workflow_health_check():
    """Check workflow automation system health."""
    try:
        health_info = await check_workflow_automation_health()
        
        system_status = SystemStatusResponse(
            total_workflows=health_info["system_status"]["total_workflows"],
            active_workflows=health_info["system_status"]["active_workflows"],
            total_executions=health_info["system_status"]["total_executions"],
            recent_executions_24h=health_info["system_status"]["recent_executions_24h"],
            successful_executions_24h=health_info["system_status"]["successful_executions_24h"],
            failed_executions_24h=health_info["system_status"]["failed_executions_24h"],
            active_executions=health_info["system_status"]["active_executions"],
            integrations=health_info["system_status"]["integrations"],
            scheduler_running=health_info["system_status"]["scheduler_running"],
            timestamp=health_info["system_status"]["timestamp"]
        )
        
        return WorkflowHealthResponse(
            status=health_info["status"],
            system_status=system_status,
            custom_handlers=health_info["custom_handlers"],
            event_handlers=health_info["event_handlers"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Workflow health check failed: {str(e)}"
        )


# Helper functions
def _convert_workflow_to_response(workflow: Workflow) -> WorkflowResponse:
    """Convert workflow object to response format."""
    steps = [
        WorkflowStepResponse(
            id=step.id,
            name=step.name,
            step_type=step.step_type.value,
            configuration=step.configuration,
            conditions=step.conditions,
            next_steps=step.next_steps,
            position=step.position,
            timeout_seconds=step.timeout_seconds,
            retry_count=step.retry_count,
            enabled=step.enabled
        )
        for step in workflow.steps
    ]
    
    triggers = [
        WorkflowTriggerResponse(
            id=trigger.id,
            trigger_type=trigger.trigger_type.value,
            configuration=trigger.configuration,
            schedule=trigger.schedule,
            enabled=trigger.enabled
        )
        for trigger in workflow.triggers
    ]
    
    variables = [
        WorkflowVariableResponse(
            name=var.name,
            value=var.value,
            data_type=var.data_type,
            description=var.description,
            scope=var.scope
        )
        for var in workflow.variables
    ]
    
    integrations = [
        IntegrationResponse(
            id=integration.id,
            name=integration.name,
            integration_type=integration.integration_type.value,
            endpoint_url=integration.endpoint_url,
            authentication=integration.authentication,
            headers=integration.headers,
            timeout=integration.timeout,
            enabled=integration.enabled
        )
        for integration in workflow.integrations
    ]
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        steps=steps,
        triggers=triggers,
        variables=variables,
        integrations=integrations,
        status=workflow.status.value,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        created_by=workflow.created_by
    )


def _convert_execution_to_response(execution) -> WorkflowExecutionResponse:
    """Convert execution object to response format."""
    step_executions = [
        StepExecutionResponse(
            id=step_exec.id,
            workflow_execution_id=step_exec.workflow_execution_id,
            step_id=step_exec.step_id,
            status=step_exec.status.value,
            started_at=step_exec.started_at,
            completed_at=step_exec.completed_at,
            input_data=step_exec.input_data,
            output_data=step_exec.output_data,
            error_message=step_exec.error_message,
            retry_attempt=step_exec.retry_attempt,
            execution_time_ms=step_exec.execution_time_ms
        )
        for step_exec in execution.step_executions
    ]
    
    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        triggered_by=execution.triggered_by,
        trigger_data=execution.trigger_data,
        variables=execution.variables,
        step_executions=step_executions,
        current_step=execution.current_step
    )