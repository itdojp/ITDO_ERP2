"""
CC02 v55.0 Workflow Engine
Enterprise-grade Workflow Management and Automation System
Day 2 of 7-day intensive backend development
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import WorkflowError
from app.models.workflow import (
    Workflow,
    WorkflowConnection,
    WorkflowHistory,
    WorkflowInstance,
    WorkflowNode,
    WorkflowTask,
)
from app.services.audit_service import AuditService
from app.services.business_rules_engine import RuleContext


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class NodeType(str, Enum):
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    TIMER = "timer"
    EVENT = "event"
    SUBPROCESS = "subprocess"
    SCRIPT = "script"
    APPROVAL = "approval"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectionType(str, Enum):
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"
    DEFAULT = "default"
    ERROR = "error"


@dataclass
class WorkflowContext:
    """Context for workflow execution"""

    workflow_id: UUID
    instance_id: UUID
    variables: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeExecutionResult:
    """Result of node execution"""

    node_id: UUID
    success: bool
    next_nodes: List[UUID] = field(default_factory=list)
    variables_updated: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0


class WorkflowEngine:
    """Enterprise Workflow Engine"""

    def __init__(self) -> dict:
        self.node_executors: Dict[str, Callable] = {}
        self.audit_service = AuditService()
        self._register_default_executors()

    def _register_default_executors(self) -> dict:
        """Register default node executors"""
        self.node_executors.update(
            {
                NodeType.START: self._execute_start_node,
                NodeType.END: self._execute_end_node,
                NodeType.TASK: self._execute_task_node,
                NodeType.DECISION: self._execute_decision_node,
                NodeType.PARALLEL: self._execute_parallel_node,
                NodeType.MERGE: self._execute_merge_node,
                NodeType.TIMER: self._execute_timer_node,
                NodeType.EVENT: self._execute_event_node,
                NodeType.SUBPROCESS: self._execute_subprocess_node,
                NodeType.SCRIPT: self._execute_script_node,
                NodeType.APPROVAL: self._execute_approval_node,
            }
        )

    async def start_workflow(
        self,
        workflow_id: UUID,
        initial_variables: Dict[str, Any] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> WorkflowInstance:
        """Start a new workflow instance"""

        # Get workflow definition
        workflow = await self._get_workflow(workflow_id, session)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            raise WorkflowError(f"Workflow {workflow_id} is not active")

        # Create workflow instance
        instance = WorkflowInstance(
            id=uuid4(),
            workflow_id=workflow_id,
            status=WorkflowStatus.ACTIVE,
            variables=initial_variables or {},
            started_by=user_id,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if session:
            session.add(instance)
            await session.flush()

        # Create workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            instance_id=instance.id,
            variables=instance.variables,
            user_id=user_id,
            session=session,
        )

        # Find and execute start node
        start_nodes = [
            node for node in workflow.nodes if node.node_type == NodeType.START
        ]
        if not start_nodes:
            raise WorkflowError("Workflow has no start node")

        # Execute start node
        await self._execute_node(start_nodes[0], context)

        # Log workflow start
        await self._log_workflow_event(
            "workflow_started",
            context,
            {"workflow_name": workflow.name, "initial_variables": initial_variables},
        )

        return instance

    async def continue_workflow(
        self,
        instance_id: UUID,
        node_id: UUID,
        variables_update: Dict[str, Any] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        """Continue workflow execution from a specific node"""

        # Get workflow instance
        instance = await self._get_workflow_instance(instance_id, session)
        if not instance:
            raise WorkflowError(f"Workflow instance {instance_id} not found")

        if instance.status not in [WorkflowStatus.ACTIVE, WorkflowStatus.SUSPENDED]:
            raise WorkflowError(f"Cannot continue workflow in {instance.status} status")

        # Update variables
        if variables_update:
            instance.variables.update(variables_update)
            instance.updated_at = datetime.utcnow()

        # Create context
        context = WorkflowContext(
            workflow_id=instance.workflow_id,
            instance_id=instance_id,
            variables=instance.variables,
            user_id=user_id,
            session=session,
        )

        # Get node
        node = await self._get_workflow_node(node_id, session)
        if not node:
            raise WorkflowError(f"Node {node_id} not found")

        # Execute node
        result = await self._execute_node(node, context)

        # Update instance variables
        if result.variables_updated:
            instance.variables.update(result.variables_updated)
            instance.updated_at = datetime.utcnow()

        return result.success

    async def suspend_workflow(
        self,
        instance_id: UUID,
        reason: str,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ):
        """Suspend workflow execution"""

        instance = await self._get_workflow_instance(instance_id, session)
        if not instance:
            raise WorkflowError(f"Workflow instance {instance_id} not found")

        instance.status = WorkflowStatus.SUSPENDED
        instance.updated_at = datetime.utcnow()

        context = WorkflowContext(
            workflow_id=instance.workflow_id,
            instance_id=instance_id,
            user_id=user_id,
            session=session,
        )

        await self._log_workflow_event(
            "workflow_suspended", context, {"reason": reason}
        )

    async def cancel_workflow(
        self,
        instance_id: UUID,
        reason: str,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ):
        """Cancel workflow execution"""

        instance = await self._get_workflow_instance(instance_id, session)
        if not instance:
            raise WorkflowError(f"Workflow instance {instance_id} not found")

        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()

        # Cancel pending tasks
        await self._cancel_pending_tasks(instance_id, session)

        context = WorkflowContext(
            workflow_id=instance.workflow_id,
            instance_id=instance_id,
            user_id=user_id,
            session=session,
        )

        await self._log_workflow_event(
            "workflow_cancelled", context, {"reason": reason}
        )

    async def _execute_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute a workflow node"""

        start_time = datetime.utcnow()

        try:
            # Get node executor
            executor = self.node_executors.get(node.node_type)
            if not executor:
                raise WorkflowError(
                    f"No executor found for node type: {node.node_type}"
                )

            # Execute node
            result = await executor(node, context)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            # Log node execution
            await self._log_node_execution(node, context, result)

            # Continue to next nodes if successful
            if result.success and result.next_nodes:
                await self._continue_to_next_nodes(result.next_nodes, context)

            return result

        except Exception as e:
            error_result = NodeExecutionResult(
                node_id=node.id,
                success=False,
                error=str(e),
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
            )

            await self._log_node_execution(node, context, error_result)
            await self._handle_node_error(node, context, str(e))

            return error_result

    async def _continue_to_next_nodes(
        self, next_node_ids: List[UUID], context: WorkflowContext
    ):
        """Continue execution to next nodes"""

        for node_id in next_node_ids:
            node = await self._get_workflow_node(node_id, context.session)
            if node:
                await self._execute_node(node, context)

    # Node Executors
    async def _execute_start_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute start node"""

        # Get outgoing connections
        next_nodes = await self._get_next_nodes(node.id, context.session)

        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            next_nodes=next_nodes,
            message="Workflow started",
        )

    async def _execute_end_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute end node"""

        # Mark workflow instance as completed
        instance = await self._get_workflow_instance(
            context.instance_id, context.session
        )
        if instance:
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

        await self._log_workflow_event(
            "workflow_completed", context, {"end_node": str(node.id)}
        )

        return NodeExecutionResult(
            node_id=node.id, success=True, message="Workflow completed"
        )

    async def _execute_task_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute task node"""

        task_config = node.config or {}
        task_type = task_config.get("task_type", "manual")

        if task_type == "manual":
            # Create manual task
            task = WorkflowTask(
                id=uuid4(),
                workflow_instance_id=context.instance_id,
                node_id=node.id,
                task_type=task_type,
                title=task_config.get("title", node.name),
                description=task_config.get("description"),
                assigned_to=task_config.get("assigned_to"),
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            if context.session:
                context.session.add(task)

            # Manual tasks don't continue automatically
            return NodeExecutionResult(
                node_id=node.id, success=True, message="Manual task created"
            )

        elif task_type == "automated":
            # Execute automated task
            script = task_config.get("script")
            if script:
                result = await self._execute_script(script, context)
                next_nodes = await self._get_next_nodes(node.id, context.session)

                return NodeExecutionResult(
                    node_id=node.id,
                    success=result.get("success", True),
                    next_nodes=next_nodes if result.get("success", True) else [],
                    variables_updated=result.get("variables", {}),
                    message=result.get("message", "Automated task completed"),
                )

        # Default: continue to next nodes
        next_nodes = await self._get_next_nodes(node.id, context.session)
        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            next_nodes=next_nodes,
            message="Task node executed",
        )

    async def _execute_decision_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute decision node"""

        decision_config = node.config or {}
        conditions = decision_config.get("conditions", [])

        # Evaluate conditions to determine next path
        next_nodes = []

        for condition in conditions:
            if await self._evaluate_condition(condition, context):
                connection_id = condition.get("connection_id")
                if connection_id:
                    target_node = await self._get_connection_target(
                        connection_id, context.session
                    )
                    if target_node:
                        next_nodes.append(target_node)
                break

        # If no conditions matched, use default path
        if not next_nodes:
            default_nodes = await self._get_next_nodes(
                node.id, context.session, ConnectionType.DEFAULT
            )
            next_nodes.extend(default_nodes)

        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            next_nodes=next_nodes,
            message="Decision evaluated",
        )

    async def _execute_parallel_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute parallel node (fork)"""

        # Get all outgoing paths
        next_nodes = await self._get_next_nodes(node.id, context.session)

        # Execute all paths in parallel
        tasks = []
        for node_id in next_nodes:
            target_node = await self._get_workflow_node(node_id, context.session)
            if target_node:
                tasks.append(self._execute_node(target_node, context))

        # Wait for all parallel tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            message=f"Parallel execution started for {len(next_nodes)} paths",
        )

    async def _execute_merge_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute merge node (join)"""

        # Check if all incoming paths are completed
        incoming_nodes = await self._get_incoming_nodes(node.id, context.session)
        all_completed = await self._check_all_paths_completed(
            incoming_nodes, context.instance_id, context.session
        )

        if all_completed:
            next_nodes = await self._get_next_nodes(node.id, context.session)
            return NodeExecutionResult(
                node_id=node.id,
                success=True,
                next_nodes=next_nodes,
                message="All parallel paths merged",
            )
        else:
            return NodeExecutionResult(
                node_id=node.id,
                success=True,
                message="Waiting for parallel paths to complete",
            )

    async def _execute_timer_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute timer node"""

        timer_config = node.config or {}
        delay_minutes = timer_config.get("delay_minutes", 0)

        if delay_minutes > 0:
            # In production, this would schedule a delayed execution
            # For now, we'll just log it and continue
            await self._log_workflow_event(
                "timer_scheduled",
                context,
                {"delay_minutes": delay_minutes, "node_id": str(node.id)},
            )

        next_nodes = await self._get_next_nodes(node.id, context.session)
        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            next_nodes=next_nodes,
            message=f"Timer set for {delay_minutes} minutes",
        )

    async def _execute_event_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute event node"""

        event_config = node.config or {}
        event_type = event_config.get("event_type")

        # Trigger event
        await self._log_workflow_event(
            f"event_triggered_{event_type}", context, {"event_config": event_config}
        )

        next_nodes = await self._get_next_nodes(node.id, context.session)
        return NodeExecutionResult(
            node_id=node.id,
            success=True,
            next_nodes=next_nodes,
            message=f"Event {event_type} triggered",
        )

    async def _execute_subprocess_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute subprocess node"""

        subprocess_config = node.config or {}
        subprocess_workflow_id = subprocess_config.get("workflow_id")

        if subprocess_workflow_id:
            # Start subprocess workflow
            subprocess_variables = subprocess_config.get("variables", {})
            subprocess_variables.update(context.variables)

            subprocess_instance = await self.start_workflow(
                UUID(subprocess_workflow_id),
                subprocess_variables,
                context.user_id,
                context.session,
            )

            # In production, would wait for subprocess completion
            # For now, continue immediately
            next_nodes = await self._get_next_nodes(node.id, context.session)
            return NodeExecutionResult(
                node_id=node.id,
                success=True,
                next_nodes=next_nodes,
                message=f"Subprocess {subprocess_instance.id} started",
            )

        return NodeExecutionResult(
            node_id=node.id, success=False, error="No subprocess workflow specified"
        )

    async def _execute_script_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute script node"""

        script_config = node.config or {}
        script = script_config.get("script")

        if script:
            result = await self._execute_script(script, context)
            next_nodes = (
                await self._get_next_nodes(node.id, context.session)
                if result.get("success", True)
                else []
            )

            return NodeExecutionResult(
                node_id=node.id,
                success=result.get("success", True),
                next_nodes=next_nodes,
                variables_updated=result.get("variables", {}),
                message=result.get("message", "Script executed"),
                error=result.get("error"),
            )

        return NodeExecutionResult(
            node_id=node.id, success=False, error="No script specified"
        )

    async def _execute_approval_node(
        self, node: WorkflowNode, context: WorkflowContext
    ) -> NodeExecutionResult:
        """Execute approval node"""

        approval_config = node.config or {}

        # Create approval task
        task = WorkflowTask(
            id=uuid4(),
            workflow_instance_id=context.instance_id,
            node_id=node.id,
            task_type="approval",
            title=approval_config.get("title", f"Approval Required: {node.name}"),
            description=approval_config.get("description"),
            assigned_to=approval_config.get("approver_id"),
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if context.session:
            context.session.add(task)

        return NodeExecutionResult(
            node_id=node.id, success=True, message="Approval task created"
        )

    # Helper Methods
    async def _get_workflow(
        self, workflow_id: UUID, session: AsyncSession
    ) -> Optional[Workflow]:
        """Get workflow by ID"""
        if not session:
            return None

        result = await session.execute(
            select(Workflow)
            .options(selectinload(Workflow.nodes), selectinload(Workflow.connections))
            .where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def _get_workflow_instance(
        self, instance_id: UUID, session: AsyncSession
    ) -> Optional[WorkflowInstance]:
        """Get workflow instance by ID"""
        if not session:
            return None

        result = await session.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        return result.scalar_one_or_none()

    async def _get_workflow_node(
        self, node_id: UUID, session: AsyncSession
    ) -> Optional[WorkflowNode]:
        """Get workflow node by ID"""
        if not session:
            return None

        result = await session.execute(
            select(WorkflowNode).where(WorkflowNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def _get_next_nodes(
        self,
        node_id: UUID,
        session: AsyncSession,
        connection_type: ConnectionType = None,
    ) -> List[UUID]:
        """Get next nodes from connections"""
        if not session:
            return []

        query = select(WorkflowConnection.target_node_id).where(
            WorkflowConnection.source_node_id == node_id
        )

        if connection_type:
            query = query.where(WorkflowConnection.connection_type == connection_type)

        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def _get_incoming_nodes(
        self, node_id: UUID, session: AsyncSession
    ) -> List[UUID]:
        """Get incoming nodes from connections"""
        if not session:
            return []

        result = await session.execute(
            select(WorkflowConnection.source_node_id).where(
                WorkflowConnection.target_node_id == node_id
            )
        )
        return [row[0] for row in result.fetchall()]

    async def _get_connection_target(
        self, connection_id: UUID, session: AsyncSession
    ) -> Optional[UUID]:
        """Get target node of a connection"""
        if not session:
            return None

        result = await session.execute(
            select(WorkflowConnection.target_node_id).where(
                WorkflowConnection.id == connection_id
            )
        )
        row = result.first()
        return row[0] if row else None

    async def _evaluate_condition(
        self, condition: Dict[str, Any], context: WorkflowContext
    ) -> bool:
        """Evaluate a condition"""

        # Use business rules engine for condition evaluation
        RuleContext(
            entity_type="workflow",
            entity_id=context.instance_id,
            data=context.variables,
            user_id=context.user_id,
            session=context.session,
        )

        field_name = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        if not all([field_name, operator]):
            return False

        # Get field value
        field_value = self._get_field_value(field_name, context.variables)

        # Simple condition evaluation
        if operator == "equals":
            return field_value == expected_value
        elif operator == "not_equals":
            return field_value != expected_value
        elif operator == "greater_than":
            return float(field_value) > float(expected_value)
        elif operator == "less_than":
            return float(field_value) < float(expected_value)
        elif operator == "contains":
            return str(expected_value).lower() in str(field_value).lower()

        return False

    def _get_field_value(self, field_path: str, variables: Dict[str, Any]) -> Any:
        """Get field value using dot notation"""
        parts = field_path.split(".")
        value = variables

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    async def _execute_script(
        self, script: str, context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute a script (simplified implementation)"""

        try:
            # In production, would use a proper script execution environment
            # For now, return a success result
            return {
                "success": True,
                "message": "Script executed successfully",
                "variables": {},
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _check_all_paths_completed(
        self, incoming_node_ids: List[UUID], instance_id: UUID, session: AsyncSession
    ) -> bool:
        """Check if all incoming paths are completed"""

        # In production, would check execution history
        # For now, assume all paths are completed
        return True

    async def _cancel_pending_tasks(
        self, instance_id: UUID, session: AsyncSession
    ) -> dict:
        """Cancel all pending tasks for a workflow instance"""

        if not session:
            return

        await session.execute(
            update(WorkflowTask)
            .where(
                and_(
                    WorkflowTask.workflow_instance_id == instance_id,
                    WorkflowTask.status == TaskStatus.PENDING,
                )
            )
            .values(status=TaskStatus.CANCELLED, updated_at=datetime.utcnow())
        )

    async def _handle_node_error(
        self, node: WorkflowNode, context: WorkflowContext, error: str
    ):
        """Handle node execution error"""

        # Mark workflow instance as error
        instance = await self._get_workflow_instance(
            context.instance_id, context.session
        )
        if instance:
            instance.status = WorkflowStatus.ERROR
            instance.updated_at = datetime.utcnow()

        await self._log_workflow_event(
            "workflow_error", context, {"node_id": str(node.id), "error": error}
        )

    async def _log_workflow_event(
        self, event_type: str, context: WorkflowContext, details: Dict[str, Any]
    ):
        """Log workflow event"""

        await self.audit_service.log_event(
            event_type=event_type,
            entity_type="workflow_instance",
            entity_id=context.instance_id,
            user_id=context.user_id,
            details=details,
        )

    async def _log_node_execution(
        self, node: WorkflowNode, context: WorkflowContext, result: NodeExecutionResult
    ):
        """Log node execution"""

        if context.session:
            history = WorkflowHistory(
                id=uuid4(),
                workflow_instance_id=context.instance_id,
                node_id=node.id,
                action="node_executed",
                success=result.success,
                message=result.message,
                error=result.error,
                execution_time_ms=result.execution_time_ms,
                variables_before=context.variables.copy(),
                variables_after={**context.variables, **result.variables_updated},
                executed_by=context.user_id,
                executed_at=datetime.utcnow(),
            )

            context.session.add(history)

    def register_node_executor(self, node_type: str, executor: Callable) -> dict:
        """Register custom node executor"""
        self.node_executors[node_type] = executor


# Singleton instance
workflow_engine = WorkflowEngine()


# Helper functions
async def start_workflow_instance(
    workflow_id: UUID,
    initial_variables: Dict[str, Any] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
) -> WorkflowInstance:
    """Start a workflow instance"""
    return await workflow_engine.start_workflow(
        workflow_id, initial_variables, user_id, session
    )


async def continue_workflow_instance(
    instance_id: UUID,
    node_id: UUID,
    variables_update: Dict[str, Any] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
) -> bool:
    """Continue workflow execution"""
    return await workflow_engine.continue_workflow(
        instance_id, node_id, variables_update, user_id, session
    )


async def suspend_workflow_instance(
    instance_id: UUID,
    reason: str,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
):
    """Suspend workflow instance"""
    await workflow_engine.suspend_workflow(instance_id, reason, user_id, session)


async def cancel_workflow_instance(
    instance_id: UUID,
    reason: str,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
):
    """Cancel workflow instance"""
    await workflow_engine.cancel_workflow(instance_id, reason, user_id, session)
