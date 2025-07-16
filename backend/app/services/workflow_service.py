"""Workflow service for Phase 6 workflow functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.workflow import (
    NodeType,
    TaskStatus,
    Workflow,
    WorkflowConnection,
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowNode,
    WorkflowTask,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowInstanceCreate,
    WorkflowTaskUpdate,
    WorkflowUpdate,
)


class WorkflowService:
    """Service for workflow management operations."""

    def __init__(self, db: Session):
        self.db = db

    async def create_workflow(self, workflow_data: WorkflowCreate) -> Dict[str, Any]:
        """Create a new workflow definition."""
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            organization_id=workflow_data.organization_id,
            definition=workflow_data.definition,
            is_active=workflow_data.is_active,
            created_by=workflow_data.created_by,
        )

        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        # Create workflow nodes if provided
        if workflow_data.nodes:
            for node_data in workflow_data.nodes:
                node = WorkflowNode(
                    workflow_id=workflow.id,
                    node_type=node_data.node_type,
                    name=node_data.name,
                    config=node_data.config,
                    position_x=node_data.position_x,
                    position_y=node_data.position_y,
                )
                self.db.add(node)

        # Create workflow connections if provided
        if workflow_data.connections:
            for conn_data in workflow_data.connections:
                connection = WorkflowConnection(
                    workflow_id=workflow.id,
                    from_node_id=conn_data.from_node_id,
                    to_node_id=conn_data.to_node_id,
                    condition=conn_data.condition,
                    condition_config=conn_data.condition_config,
                )
                self.db.add(connection)

        self.db.commit()
        return self._workflow_to_dict(workflow)

    async def get_workflows(
        self,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get list of workflows with filtering."""
        query = self.db.query(Workflow).filter(Workflow.is_deleted == False)

        if organization_id:
            query = query.filter(Workflow.organization_id == organization_id)

        if status:
            query = query.filter(Workflow.status == status)

        workflows = query.offset(skip).limit(limit).all()
        return [self._workflow_to_dict(w) for w in workflows]

    async def get_workflow(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        workflow = (
            self.db.query(Workflow)
            .filter(and_(Workflow.id == workflow_id, Workflow.is_deleted == False))
            .first()
        )
        return self._workflow_to_dict(workflow) if workflow else None

    async def update_workflow(
        self, workflow_id: int, workflow_data: WorkflowUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update workflow."""
        workflow = (
            self.db.query(Workflow)
            .filter(and_(Workflow.id == workflow_id, Workflow.is_deleted == False))
            .first()
        )

        if not workflow:
            return None

        for field, value in workflow_data.dict(exclude_unset=True).items():
            setattr(workflow, field, value)

        workflow.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(workflow)

        return self._workflow_to_dict(workflow)

    async def delete_workflow(self, workflow_id: int) -> bool:
        """Soft delete workflow."""
        workflow = (
            self.db.query(Workflow)
            .filter(and_(Workflow.id == workflow_id, Workflow.is_deleted == False))
            .first()
        )

        if not workflow:
            return False

        workflow.is_deleted = True
        workflow.deleted_at = datetime.utcnow()
        self.db.commit()

        return True

    async def start_workflow_instance(
        self, workflow_id: int, instance_data: WorkflowInstanceCreate
    ) -> Dict[str, Any]:
        """Start a new workflow instance."""
        workflow = (
            self.db.query(Workflow)
            .filter(and_(Workflow.id == workflow_id, Workflow.is_deleted == False))
            .first()
        )

        if not workflow:
            raise ValueError("Workflow not found")

        if not workflow.is_active:
            raise ValueError("Workflow is not active")

        instance = WorkflowInstance(
            workflow_id=workflow_id,
            title=instance_data.title,
            description=instance_data.description,
            initiated_by=instance_data.initiated_by,
            organization_id=workflow.organization_id,
            entity_type=instance_data.entity_type,
            entity_id=instance_data.entity_id,
            context_data=instance_data.context_data,
            status=WorkflowInstanceStatus.PENDING,
        )

        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)

        # Create initial workflow tasks
        await self._create_initial_tasks(instance)

        return self._instance_to_dict(instance)

    async def get_workflow_instances(
        self,
        workflow_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get workflow instances."""
        query = self.db.query(WorkflowInstance).filter(
            and_(
                WorkflowInstance.workflow_id == workflow_id,
                WorkflowInstance.is_deleted == False,
            )
        )

        if status:
            query = query.filter(WorkflowInstance.status == status)

        instances = query.offset(skip).limit(limit).all()
        return [self._instance_to_dict(i) for i in instances]

    async def get_workflow_instance(self, instance_id: int) -> Optional[Dict[str, Any]]:
        """Get workflow instance by ID."""
        instance = (
            self.db.query(WorkflowInstance)
            .filter(
                and_(
                    WorkflowInstance.id == instance_id,
                    WorkflowInstance.is_deleted == False,
                )
            )
            .first()
        )
        return self._instance_to_dict(instance) if instance else None

    async def get_instance_tasks(
        self,
        instance_id: int,
        status: Optional[str] = None,
        assigned_to: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get tasks for workflow instance."""
        query = self.db.query(WorkflowTask).filter(
            and_(
                WorkflowTask.instance_id == instance_id,
                WorkflowTask.is_deleted == False,
            )
        )

        if status:
            query = query.filter(WorkflowTask.status == status)

        if assigned_to:
            query = query.filter(WorkflowTask.assigned_to == assigned_to)

        tasks = query.all()
        return [self._task_to_dict(t) for t in tasks]

    async def update_workflow_task(
        self, task_id: int, task_data: WorkflowTaskUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update workflow task."""
        task = (
            self.db.query(WorkflowTask)
            .filter(and_(WorkflowTask.id == task_id, WorkflowTask.is_deleted == False))
            .first()
        )

        if not task:
            return None

        for field, value in task_data.dict(exclude_unset=True).items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)

        return self._task_to_dict(task)

    async def complete_workflow_task(
        self, task_id: int, completion_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete a workflow task."""
        task = (
            self.db.query(WorkflowTask)
            .filter(and_(WorkflowTask.id == task_id, WorkflowTask.is_deleted == False))
            .first()
        )

        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()

        if completion_data:
            task.result_data = completion_data

        self.db.commit()

        # Check if workflow instance should progress
        await self._check_instance_progress(task.instance_id)

        return True

    async def assign_workflow_task(self, task_id: int, assignee_id: int) -> bool:
        """Assign workflow task to user."""
        task = (
            self.db.query(WorkflowTask)
            .filter(and_(WorkflowTask.id == task_id, WorkflowTask.is_deleted == False))
            .first()
        )

        if not task:
            return False

        task.assigned_to = assignee_id
        task.assigned_at = datetime.utcnow()
        task.status = TaskStatus.ASSIGNED

        self.db.commit()
        return True

    async def get_workflow_analytics(
        self,
        workflow_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get workflow performance analytics."""
        query = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.workflow_id == workflow_id
        )

        if start_date:
            query = query.filter(WorkflowInstance.created_at >= start_date)

        if end_date:
            query = query.filter(WorkflowInstance.created_at <= end_date)

        instances = query.all()

        total_instances = len(instances)
        completed_instances = len(
            [i for i in instances if i.status == WorkflowInstanceStatus.COMPLETED]
        )
        avg_completion_time = self._calculate_avg_completion_time(instances)

        return {
            "workflow_id": workflow_id,
            "total_instances": total_instances,
            "completed_instances": completed_instances,
            "completion_rate": completed_instances / total_instances
            if total_instances > 0
            else 0,
            "average_completion_time_hours": avg_completion_time,
            "status_breakdown": self._get_status_breakdown(instances),
        }

    async def get_instance_progress(self, instance_id: int) -> Optional[Dict[str, Any]]:
        """Get workflow instance progress."""
        instance = (
            self.db.query(WorkflowInstance)
            .filter(
                and_(
                    WorkflowInstance.id == instance_id,
                    WorkflowInstance.is_deleted == False,
                )
            )
            .first()
        )

        if not instance:
            return None

        tasks = (
            self.db.query(WorkflowTask)
            .filter(WorkflowTask.instance_id == instance_id)
            .all()
        )

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])

        return {
            "instance_id": instance_id,
            "status": instance.status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "current_tasks": [
                self._task_to_dict(t)
                for t in tasks
                if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
            ],
        }

    async def _create_initial_tasks(self, instance: WorkflowInstance) -> None:
        """Create initial tasks for workflow instance."""
        # Get start nodes from workflow definition
        start_nodes = (
            self.db.query(WorkflowNode)
            .filter(
                and_(
                    WorkflowNode.workflow_id == instance.workflow_id,
                    WorkflowNode.node_type == NodeType.START,
                )
            )
            .all()
        )

        for node in start_nodes:
            # Find next nodes from start
            next_nodes = self._get_next_nodes(node.id)

            for next_node in next_nodes:
                if next_node.node_type in [NodeType.TASK, NodeType.APPROVAL]:
                    task = WorkflowTask(
                        instance_id=instance.id,
                        node_id=next_node.id,
                        name=next_node.name,
                        description=next_node.config.get("description", ""),
                        status=TaskStatus.PENDING,
                        task_config=next_node.config,
                    )
                    self.db.add(task)

        self.db.commit()

    async def _check_instance_progress(self, instance_id: int) -> None:
        """Check if instance can progress to next tasks."""
        instance = self.db.query(WorkflowInstance).get(instance_id)
        if not instance:
            return

        # Get all pending tasks
        pending_tasks = (
            self.db.query(WorkflowTask)
            .filter(
                and_(
                    WorkflowTask.instance_id == instance_id,
                    WorkflowTask.status == TaskStatus.PENDING,
                )
            )
            .all()
        )

        # Check if all required tasks are completed to activate pending tasks
        for task in pending_tasks:
            if self._can_activate_task(task):
                task.status = TaskStatus.ASSIGNED

        # Check if instance is complete
        all_tasks = (
            self.db.query(WorkflowTask)
            .filter(WorkflowTask.instance_id == instance_id)
            .all()
        )

        if all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED] for t in all_tasks
        ):
            instance.status = WorkflowInstanceStatus.COMPLETED
            instance.completed_at = datetime.utcnow()

        self.db.commit()

    def _get_next_nodes(self, node_id: int) -> List[Any]:
        """Get next nodes in workflow."""
        connections = (
            self.db.query(WorkflowConnection)
            .filter(WorkflowConnection.from_node_id == node_id)
            .all()
        )

        next_nodes = []
        for conn in connections:
            node = self.db.query(WorkflowNode).get(conn.to_node_id)
            if node:
                next_nodes.append(node)

        return next_nodes

    def _can_activate_task(self, task: WorkflowTask) -> bool:
        """Check if task can be activated."""
        # Get prerequisite tasks
        node = self.db.query(WorkflowNode).get(task.node_id)
        if not node:
            return False

        prerequisite_connections = (
            self.db.query(WorkflowConnection)
            .filter(WorkflowConnection.to_node_id == node.id)
            .all()
        )

        for conn in prerequisite_connections:
            # Check if prerequisite task is completed
            prerequisite_tasks = (
                self.db.query(WorkflowTask)
                .filter(
                    and_(
                        WorkflowTask.instance_id == task.instance_id,
                        WorkflowTask.node_id == conn.from_node_id,
                    )
                )
                .all()
            )

            if not all(t.status == TaskStatus.COMPLETED for t in prerequisite_tasks):
                return False

        return True

    def _calculate_avg_completion_time(
        self, instances: List[WorkflowInstance]
    ) -> float:
        """Calculate average completion time in hours."""
        completed = [i for i in instances if i.completed_at and i.created_at]

        if not completed:
            return 0.0

        total_hours = sum(
            (i.completed_at - i.created_at).total_seconds() / 3600 for i in completed
        )

        return total_hours / len(completed)

    def _get_status_breakdown(
        self, instances: List[WorkflowInstance]
    ) -> Dict[str, int]:
        """Get status breakdown for instances."""
        breakdown = {}
        for instance in instances:
            status = instance.status
            breakdown[status] = breakdown.get(status, 0) + 1

        return breakdown

    def _workflow_to_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "organization_id": workflow.organization_id,
            "status": workflow.status,
            "is_active": workflow.is_active,
            "definition": workflow.definition,
            "created_by": workflow.created_by,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }

    def _instance_to_dict(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Convert workflow instance to dictionary."""
        return {
            "id": instance.id,
            "workflow_id": instance.workflow_id,
            "title": instance.title,
            "description": instance.description,
            "status": instance.status,
            "initiated_by": instance.initiated_by,
            "organization_id": instance.organization_id,
            "entity_type": instance.entity_type,
            "entity_id": instance.entity_id,
            "context_data": instance.context_data,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
            "completed_at": instance.completed_at,
        }

    def _task_to_dict(self, task: WorkflowTask) -> Dict[str, Any]:
        """Convert workflow task to dictionary."""
        return {
            "id": task.id,
            "instance_id": task.instance_id,
            "node_id": task.node_id,
            "name": task.name,
            "description": task.description,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "assigned_at": task.assigned_at,
            "due_date": task.due_date,
            "completed_at": task.completed_at,
            "task_config": task.task_config,
            "result_data": task.result_data,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
