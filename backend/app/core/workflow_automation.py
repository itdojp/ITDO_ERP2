"""Workflow Automation & Integration Engine."""

import asyncio
import json
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from app.core.monitoring import monitor_performance


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Workflow step types."""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    DELAY = "delay"
    WEBHOOK = "webhook"
    EMAIL = "email"
    API_CALL = "api_call"
    CUSTOM = "custom"


class TriggerType(str, Enum):
    """Workflow trigger types."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    API_TRIGGERED = "api_triggered"
    FILE_UPLOAD = "file_upload"
    EMAIL_RECEIVED = "email_received"
    WEBHOOK = "webhook"


class IntegrationType(str, Enum):
    """Integration types."""
    REST_API = "rest_api"
    SOAP = "soap"
    GRAPHQL = "graphql"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    MESSAGE_QUEUE = "message_queue"
    EMAIL_SMTP = "email_smtp"
    FTP = "ftp"
    CLOUD_STORAGE = "cloud_storage"


class ExecutionStatus(str, Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


@dataclass
class WorkflowVariable:
    """Workflow variable definition."""
    name: str
    value: Any
    data_type: str
    description: str = ""
    scope: str = "workflow"  # workflow, step, global


@dataclass
class WorkflowStep:
    """Workflow step definition."""
    id: str
    name: str
    step_type: StepType
    configuration: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)
    position: Dict[str, int] = field(default_factory=dict)  # x, y coordinates
    timeout_seconds: int = 300
    retry_count: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class WorkflowTrigger:
    """Workflow trigger definition."""
    id: str
    trigger_type: TriggerType
    configuration: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression for scheduled triggers
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class Integration:
    """External system integration."""
    id: str
    name: str
    integration_type: IntegrationType
    endpoint_url: str
    authentication: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class Workflow:
    """Workflow definition."""
    id: str
    name: str
    description: str
    version: str = "1.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: List[WorkflowVariable] = field(default_factory=list)
    integrations: List[Integration] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class StepExecution:
    """Workflow step execution record."""
    id: str
    workflow_execution_id: str
    step_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_attempt: int = 0
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class WorkflowExecution:
    """Workflow execution instance."""
    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    triggered_by: str = ""
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    step_executions: List[StepExecution] = field(default_factory=list)
    current_step: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


class StepExecutor:
    """Workflow step execution engine."""
    
    def __init__(self):
        """Initialize step executor."""
        self.custom_handlers: Dict[str, Callable] = {}
        self.integration_clients: Dict[str, Any] = {}
    
    def register_custom_handler(self, step_type: str, handler: Callable) -> None:
        """Register custom step handler."""
        self.custom_handlers[step_type] = handler
    
    @monitor_performance("workflow.step.execute")
    async def execute_step(
        self,
        step: WorkflowStep,
        execution_context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute a workflow step."""
        try:
            if step.step_type == StepType.START:
                return await self._execute_start_step(step, execution_context)
            elif step.step_type == StepType.END:
                return await self._execute_end_step(step, execution_context)
            elif step.step_type == StepType.TASK:
                return await self._execute_task_step(step, execution_context)
            elif step.step_type == StepType.DECISION:
                return await self._execute_decision_step(step, execution_context)
            elif step.step_type == StepType.DELAY:
                return await self._execute_delay_step(step, execution_context)
            elif step.step_type == StepType.WEBHOOK:
                return await self._execute_webhook_step(step, execution_context)
            elif step.step_type == StepType.EMAIL:
                return await self._execute_email_step(step, execution_context)
            elif step.step_type == StepType.API_CALL:
                return await self._execute_api_call_step(step, execution_context)
            elif step.step_type == StepType.CUSTOM:
                return await self._execute_custom_step(step, execution_context)
            else:
                return ExecutionStatus.FAILED, {}, f"Unknown step type: {step.step_type}"
        
        except Exception as e:
            return ExecutionStatus.FAILED, {}, str(e)
    
    async def _execute_start_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute start step."""
        # Initialize workflow variables from context
        output = {"initialized_at": datetime.utcnow().isoformat()}
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_end_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute end step."""
        output = {
            "completed_at": datetime.utcnow().isoformat(),
            "final_status": "success"
        }
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_task_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute task step."""
        config = step.configuration
        task_type = config.get("task_type", "generic")
        
        # Simulate task execution
        await asyncio.sleep(0.1)
        
        output = {
            "task_type": task_type,
            "executed_at": datetime.utcnow().isoformat(),
            "result": "task_completed"
        }
        
        # Add task-specific logic
        if task_type == "data_processing":
            output["processed_records"] = config.get("record_count", 100)
        elif task_type == "validation":
            output["validation_result"] = "passed"
        elif task_type == "notification":
            output["notification_sent"] = True
        
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_decision_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute decision step."""
        config = step.configuration
        condition = config.get("condition", "true")
        
        # Evaluate condition (simplified)
        try:
            # In production, use a safe expression evaluator
            result = eval(condition, {}, context.get("variables", {}))
            
            output = {
                "condition": condition,
                "result": result,
                "evaluated_at": datetime.utcnow().isoformat()
            }
            
            return ExecutionStatus.COMPLETED, output, None
        
        except Exception as e:
            return ExecutionStatus.FAILED, {}, f"Condition evaluation failed: {str(e)}"
    
    async def _execute_delay_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute delay step."""
        config = step.configuration
        delay_seconds = config.get("delay_seconds", 1)
        
        await asyncio.sleep(delay_seconds)
        
        output = {
            "delay_seconds": delay_seconds,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_webhook_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute webhook step."""
        config = step.configuration
        url = config.get("url", "")
        method = config.get("method", "POST")
        payload = config.get("payload", {})
        
        # Simulate webhook call
        await asyncio.sleep(0.2)
        
        output = {
            "url": url,
            "method": method,
            "status_code": 200,
            "response": {"success": True},
            "called_at": datetime.utcnow().isoformat()
        }
        
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_email_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute email step."""
        config = step.configuration
        recipients = config.get("recipients", [])
        subject = config.get("subject", "")
        body = config.get("body", "")
        
        # Simulate email sending
        await asyncio.sleep(0.1)
        
        output = {
            "recipients": recipients,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": str(uuid4())
        }
        
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_api_call_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute API call step."""
        config = step.configuration
        url = config.get("url", "")
        method = config.get("method", "GET")
        headers = config.get("headers", {})
        data = config.get("data", {})
        
        # Simulate API call
        await asyncio.sleep(0.3)
        
        output = {
            "url": url,
            "method": method,
            "status_code": 200,
            "response_data": {"api_result": "success"},
            "called_at": datetime.utcnow().isoformat()
        }
        
        return ExecutionStatus.COMPLETED, output, None
    
    async def _execute_custom_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Tuple[ExecutionStatus, Dict[str, Any], Optional[str]]:
        """Execute custom step."""
        config = step.configuration
        handler_name = config.get("handler", "")
        
        if handler_name in self.custom_handlers:
            try:
                handler = self.custom_handlers[handler_name]
                result = await handler(step, context)
                return ExecutionStatus.COMPLETED, result, None
            except Exception as e:
                return ExecutionStatus.FAILED, {}, str(e)
        else:
            return ExecutionStatus.FAILED, {}, f"Custom handler '{handler_name}' not found"


class WorkflowEngine:
    """Main workflow execution engine."""
    
    def __init__(self):
        """Initialize workflow engine."""
        self.step_executor = StepExecutor()
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_queue: deque = deque()
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register event handler."""
        self.event_handlers[event_type].append(handler)
    
    @monitor_performance("workflow.execute")
    async def execute_workflow(
        self,
        workflow: Workflow,
        trigger_data: Dict[str, Any] = None,
        triggered_by: str = ""
    ) -> WorkflowExecution:
        """Execute a workflow."""
        execution = WorkflowExecution(
            id=str(uuid4()),
            workflow_id=workflow.id,
            status=WorkflowStatus.ACTIVE,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by,
            trigger_data=trigger_data or {},
            variables={var.name: var.value for var in workflow.variables}
        )
        
        self.active_executions[execution.id] = execution
        
        try:
            # Find start step
            start_steps = [step for step in workflow.steps if step.step_type == StepType.START]
            if not start_steps:
                raise ValueError("Workflow has no start step")
            
            # Execute workflow steps
            current_step = start_steps[0]
            execution.current_step = current_step.id
            
            while current_step and execution.status == WorkflowStatus.ACTIVE:
                step_execution = await self._execute_workflow_step(
                    workflow, current_step, execution
                )
                execution.step_executions.append(step_execution)
                
                if step_execution.status == ExecutionStatus.FAILED:
                    execution.status = WorkflowStatus.FAILED
                    break
                
                # Determine next step
                next_step = await self._determine_next_step(
                    workflow, current_step, step_execution, execution
                )
                
                if next_step:
                    execution.current_step = next_step.id
                    current_step = next_step
                else:
                    # No next step, workflow completed
                    execution.status = WorkflowStatus.COMPLETED
                    execution.current_step = None
                    break
            
            execution.completed_at = datetime.utcnow()
            
            # Trigger completion events
            await self._trigger_events("workflow_completed", {
                "execution_id": execution.id,
                "workflow_id": workflow.id,
                "status": execution.status.value
            })
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            
            # Add error step execution
            error_execution = StepExecution(
                id=str(uuid4()),
                workflow_execution_id=execution.id,
                step_id="error",
                status=ExecutionStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
            execution.step_executions.append(error_execution)
        
        finally:
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
        
        return execution
    
    async def _execute_workflow_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> StepExecution:
        """Execute a single workflow step."""
        step_execution = StepExecution(
            id=str(uuid4()),
            workflow_execution_id=execution.id,
            step_id=step.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_data=execution.variables.copy()
        )
        
        try:
            # Execute step with timeout
            execution_context = {
                "variables": execution.variables,
                "execution_id": execution.id,
                "workflow_id": workflow.id,
                "trigger_data": execution.trigger_data
            }
            
            start_time = datetime.utcnow()
            
            status, output_data, error_message = await asyncio.wait_for(
                self.step_executor.execute_step(step, execution_context),
                timeout=step.timeout_seconds
            )
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            step_execution.status = status
            step_execution.output_data = output_data
            step_execution.error_message = error_message
            step_execution.completed_at = end_time
            step_execution.execution_time_ms = execution_time
            
            # Update workflow variables with step output
            if status == ExecutionStatus.COMPLETED and output_data:
                execution.variables.update(output_data)
        
        except asyncio.TimeoutError:
            step_execution.status = ExecutionStatus.FAILED
            step_execution.error_message = f"Step timed out after {step.timeout_seconds} seconds"
            step_execution.completed_at = datetime.utcnow()
        
        except Exception as e:
            step_execution.status = ExecutionStatus.FAILED
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.utcnow()
        
        return step_execution
    
    async def _determine_next_step(
        self,
        workflow: Workflow,
        current_step: WorkflowStep,
        step_execution: StepExecution,
        execution: WorkflowExecution
    ) -> Optional[WorkflowStep]:
        """Determine the next step to execute."""
        if current_step.step_type == StepType.END:
            return None
        
        if not current_step.next_steps:
            # No explicit next steps, find end step
            end_steps = [step for step in workflow.steps if step.step_type == StepType.END]
            return end_steps[0] if end_steps else None
        
        # For decision steps, evaluate conditions
        if current_step.step_type == StepType.DECISION:
            output_data = step_execution.output_data
            if output_data and output_data.get("result"):
                # Take first path (true condition)
                next_step_id = current_step.next_steps[0] if current_step.next_steps else None
            else:
                # Take second path (false condition)
                next_step_id = current_step.next_steps[1] if len(current_step.next_steps) > 1 else None
        else:
            # For other steps, take first next step
            next_step_id = current_step.next_steps[0] if current_step.next_steps else None
        
        if next_step_id:
            return next((step for step in workflow.steps if step.id == next_step_id), None)
        
        return None
    
    async def _trigger_events(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Trigger event handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event_data)
                except Exception as e:
                    print(f"Event handler error: {e}")


class IntegrationManager:
    """External integration management."""
    
    def __init__(self):
        """Initialize integration manager."""
        self.integrations: Dict[str, Integration] = {}
        self.connection_pool: Dict[str, Any] = {}
    
    async def register_integration(self, integration: Integration) -> str:
        """Register external integration."""
        self.integrations[integration.id] = integration
        return integration.id
    
    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """Test integration connectivity."""
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}
        
        try:
            # Simulate connection test
            await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "integration_id": integration_id,
                "integration_type": integration.integration_type.value,
                "response_time_ms": 100,
                "tested_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "integration_id": integration_id,
                "error": str(e),
                "tested_at": datetime.utcnow().isoformat()
            }
    
    async def execute_integration_call(
        self,
        integration_id: str,
        operation: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute integration call."""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")
        
        # Simulate integration call
        await asyncio.sleep(0.2)
        
        return {
            "integration_id": integration_id,
            "operation": operation,
            "status": "success",
            "response_data": {"result": "integration_success"},
            "executed_at": datetime.utcnow().isoformat()
        }


class WorkflowAutomationManager:
    """Main workflow automation management system."""
    
    def __init__(self):
        """Initialize workflow automation manager."""
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.workflow_engine = WorkflowEngine()
        self.integration_manager = IntegrationManager()
        self.scheduler_running = False
    
    # Workflow Management
    async def create_workflow(self, workflow: Workflow) -> str:
        """Create a new workflow."""
        self.workflows[workflow.id] = workflow
        return workflow.id
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)
    
    async def list_workflows(self, status: Optional[WorkflowStatus] = None) -> List[Workflow]:
        """List workflows."""
        workflows = list(self.workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows
    
    async def update_workflow(self, workflow: Workflow) -> bool:
        """Update existing workflow."""
        if workflow.id in self.workflows:
            workflow.updated_at = datetime.utcnow()
            self.workflows[workflow.id] = workflow
            return True
        return False
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False
    
    # Workflow Execution
    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_data: Dict[str, Any] = None,
        triggered_by: str = ""
    ) -> Optional[WorkflowExecution]:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            return None
        
        execution = await self.workflow_engine.execute_workflow(
            workflow, trigger_data, triggered_by
        )
        
        self.executions[execution.id] = execution
        return execution
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        return self.executions.get(execution_id)
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        executions = list(self.executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        # Sort by start time, newest first
        executions.sort(key=lambda x: x.started_at, reverse=True)
        
        return executions[:limit]
    
    # Integration Management
    async def register_integration(self, integration: Integration) -> str:
        """Register external integration."""
        return await self.integration_manager.register_integration(integration)
    
    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """Test integration connectivity."""
        return await self.integration_manager.test_integration(integration_id)
    
    # System Management
    async def get_system_status(self) -> Dict[str, Any]:
        """Get automation system status."""
        total_workflows = len(self.workflows)
        active_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE])
        
        # Execution statistics
        total_executions = len(self.executions)
        recent_executions = [
            e for e in self.executions.values()
            if e.started_at > datetime.utcnow() - timedelta(hours=24)
        ]
        
        successful_executions = len([e for e in recent_executions if e.status == WorkflowStatus.COMPLETED])
        failed_executions = len([e for e in recent_executions if e.status == WorkflowStatus.FAILED])
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": active_workflows,
            "total_executions": total_executions,
            "recent_executions_24h": len(recent_executions),
            "successful_executions_24h": successful_executions,
            "failed_executions_24h": failed_executions,
            "active_executions": len(self.workflow_engine.active_executions),
            "integrations": len(self.integration_manager.integrations),
            "scheduler_running": self.scheduler_running,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global workflow automation manager instance
workflow_manager = WorkflowAutomationManager()


# Health check for workflow automation system
async def check_workflow_automation_health() -> Dict[str, Any]:
    """Check workflow automation system health."""
    status = await workflow_manager.get_system_status()
    
    # Determine health status
    health_status = "healthy"
    
    if status["failed_executions_24h"] > status["successful_executions_24h"]:
        health_status = "degraded"
    
    if status["active_workflows"] == 0:
        health_status = "warning"
    
    return {
        "status": health_status,
        "system_status": status,
        "custom_handlers": len(workflow_manager.workflow_engine.step_executor.custom_handlers),
        "event_handlers": len(workflow_manager.workflow_engine.event_handlers)
    }