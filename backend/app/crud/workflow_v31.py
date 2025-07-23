"""
Workflow System CRUD Operations - CC02 v31.0 Phase 2

Comprehensive workflow service with advanced business logic including:
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
"""

import json
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.workflow_extended import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowTask,
    WorkflowActivity,
    WorkflowComment,
    WorkflowAttachment,
    WorkflowTemplate,
    WorkflowAnalytics,
    WorkflowAuditLog,
    WorkflowType,
    WorkflowStatus,
    WorkflowInstanceStatus,
    TaskStatus,
    TaskPriority,
    ActionType,
    TriggerType,
)


class WorkflowService:
    """Comprehensive workflow service with advanced business logic."""

    # =============================================================================
    # Workflow Definition Management
    # =============================================================================

    async def create_workflow_definition(self, db: Session, definition_data: Dict[str, Any]) -> WorkflowDefinition:
        """Create a new workflow definition with validation."""
        try:
            # Validate required fields
            required_fields = ["organization_id", "name", "code", "workflow_type", "definition_schema", "created_by"]
            for field in required_fields:
                if not definition_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicate code
            existing = db.query(WorkflowDefinition).filter(
                WorkflowDefinition.code == definition_data["code"]
            ).first()
            if existing:
                raise ValueError(f"Workflow definition with code '{definition_data['code']}' already exists")
            
            # Validate workflow schema
            await self._validate_workflow_schema(definition_data["definition_schema"])
            
            # Create workflow definition
            definition = WorkflowDefinition(**definition_data)
            
            # Set defaults
            if not definition.version:
                definition.version = "1.0"
            if not definition.sla_minutes:
                definition.sla_minutes = 1440  # 24 hours default
            
            db.add(definition)
            db.commit()
            db.refresh(definition)
            
            # Create workflow steps from schema
            await self._create_steps_from_schema(db, definition)
            
            # Log audit trail
            await self._log_audit_action(
                db, definition.organization_id, "create", "workflow_definition",
                definition.id, None, definition_data, definition.created_by
            )
            
            return definition
            
        except Exception as e:
            db.rollback()
            raise e

    async def get_workflow_definition(self, db: Session, definition_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID with steps."""
        return db.query(WorkflowDefinition).options(
            joinedload(WorkflowDefinition.steps)
        ).filter(WorkflowDefinition.id == definition_id).first()

    async def list_workflow_definitions(
        self, 
        db: Session, 
        organization_id: str,
        workflow_type: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        is_template: Optional[bool] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """List workflow definitions with filtering and pagination."""
        query = db.query(WorkflowDefinition).filter(WorkflowDefinition.organization_id == organization_id)
        
        # Apply filters
        if workflow_type:
            query = query.filter(WorkflowDefinition.workflow_type == workflow_type)
        if status:
            query = query.filter(WorkflowDefinition.status == status)
        if category:
            query = query.filter(WorkflowDefinition.category == category)
        if is_template is not None:
            query = query.filter(WorkflowDefinition.is_template == is_template)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        definitions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "definitions": definitions,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "has_more": total_count > page * per_page
        }

    async def update_workflow_definition(
        self, 
        db: Session, 
        definition_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[WorkflowDefinition]:
        """Update workflow definition with versioning."""
        definition = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == definition_id).first()
        if not definition:
            return None
        
        # Create new version if significant changes
        if self._requires_new_version(update_data):
            return await self._create_new_version(db, definition, update_data)
        
        old_values = {
            "name": definition.name,
            "definition_schema": definition.definition_schema,
            "status": definition.status.value
        }
        
        # Update fields
        for field, value in update_data.items():
            if field not in ["id", "created_at", "created_by"] and hasattr(definition, field):
                setattr(definition, field, value)
        
        definition.updated_at = datetime.now()
        db.commit()
        db.refresh(definition)
        
        # Log audit trail
        await self._log_audit_action(
            db, definition.organization_id, "update", "workflow_definition",
            definition.id, old_values, update_data, update_data.get("updated_by")
        )
        
        return definition

    # =============================================================================
    # Workflow Instance Management
    # =============================================================================

    async def start_workflow_instance(
        self, 
        db: Session, 
        definition_id: str, 
        instance_data: Dict[str, Any]
    ) -> WorkflowInstance:
        """Start a new workflow instance."""
        try:
            # Get workflow definition
            definition = await self.get_workflow_definition(db, definition_id)
            if not definition:
                raise ValueError("Workflow definition not found")
            
            if definition.status != WorkflowStatus.ACTIVE:
                raise ValueError("Workflow definition is not active")
            
            # Generate instance number
            instance_number = await self._generate_instance_number(db, definition)
            
            # Create workflow instance
            instance = WorkflowInstance(
                organization_id=definition.organization_id,
                definition_id=definition_id,
                instance_number=instance_number,
                title=instance_data.get("title") or f"{definition.name} - {instance_number}",
                description=instance_data.get("description"),
                entity_type=instance_data.get("entity_type"),
                entity_id=instance_data.get("entity_id"),
                context_data=instance_data.get("context_data", {}),
                form_data=instance_data.get("form_data", {}),
                priority=instance_data.get("priority", TaskPriority.NORMAL),
                initiated_by=instance_data.get("initiated_by"),
                status=WorkflowInstanceStatus.PENDING,
                started_at=datetime.now()
            )
            
            # Set SLA deadline
            if definition.sla_minutes:
                instance.sla_deadline = datetime.now() + timedelta(minutes=definition.sla_minutes)
            
            # Calculate total steps
            instance.total_steps = len(definition.steps)
            
            db.add(instance)
            db.commit()
            db.refresh(instance)
            
            # Start first step
            await self._start_first_step(db, instance, definition)
            
            # Log activity
            await self._log_workflow_activity(
                db, instance.id, None, ActionType.COMPLETE, "start_workflow",
                f"Workflow instance started", instance.initiated_by
            )
            
            return instance
            
        except Exception as e:
            db.rollback()
            raise e

    async def get_workflow_instance(self, db: Session, instance_id: str) -> Optional[WorkflowInstance]:
        """Get workflow instance by ID with related data."""
        return db.query(WorkflowInstance).options(
            joinedload(WorkflowInstance.definition),
            joinedload(WorkflowInstance.tasks),
            joinedload(WorkflowInstance.activities)
        ).filter(WorkflowInstance.id == instance_id).first()

    async def list_workflow_instances(
        self, 
        db: Session, 
        organization_id: str,
        definition_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """List workflow instances with advanced filtering."""
        query = db.query(WorkflowInstance).filter(WorkflowInstance.organization_id == organization_id)
        
        # Apply filters
        if definition_id:
            query = query.filter(WorkflowInstance.definition_id == definition_id)
        if status:
            query = query.filter(WorkflowInstance.status == status)
        if assignee_id:
            query = query.filter(WorkflowInstance.current_assignee_id == assignee_id)
        if entity_type:
            query = query.filter(WorkflowInstance.entity_type == entity_type)
        if start_date:
            query = query.filter(WorkflowInstance.started_at >= start_date)
        if end_date:
            query = query.filter(WorkflowInstance.started_at <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        instances = query.order_by(desc(WorkflowInstance.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "instances": instances,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "has_more": total_count > page * per_page
        }

    async def advance_workflow_instance(
        self, 
        db: Session, 
        instance_id: str, 
        task_id: str, 
        action_data: Dict[str, Any]
    ) -> WorkflowInstance:
        """Advance workflow instance to next step."""
        try:
            instance = await self.get_workflow_instance(db, instance_id)
            if not instance:
                raise ValueError("Workflow instance not found")
            
            task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
            if not task:
                raise ValueError("Task not found")
            
            # Validate task can be completed
            if task.status not in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                raise ValueError(f"Task cannot be completed from status: {task.status}")
            
            # Complete current task
            await self._complete_task(db, task, action_data)
            
            # Check if workflow can advance
            next_step = await self._determine_next_step(db, instance, task.step_id, action_data)
            
            if next_step:
                # Start next step
                await self._start_workflow_step(db, instance, next_step)
            else:
                # Complete workflow
                await self._complete_workflow_instance(db, instance, action_data)
            
            # Update progress
            await self._update_instance_progress(db, instance)
            
            return instance
            
        except Exception as e:
            db.rollback()
            raise e

    # =============================================================================
    # Task Management
    # =============================================================================

    async def create_workflow_task(
        self, 
        db: Session, 
        task_data: Dict[str, Any]
    ) -> WorkflowTask:
        """Create a new workflow task."""
        try:
            # Generate task number
            task_number = await self._generate_task_number(db, task_data["instance_id"])
            
            task = WorkflowTask(
                **task_data,
                task_number=task_number,
                status=TaskStatus.PENDING,
                assigned_at=datetime.now() if task_data.get("assignee_id") else None
            )
            
            # Set due date based on step configuration
            if task_data.get("estimated_duration_minutes"):
                task.due_date = datetime.now() + timedelta(minutes=task_data["estimated_duration_minutes"])
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Send notification to assignee
            if task.assignee_id:
                await self._send_task_notification(db, task, "assigned")
            
            return task
            
        except Exception as e:
            db.rollback()
            raise e

    async def assign_task(
        self, 
        db: Session, 
        task_id: str, 
        assignee_id: str, 
        assigned_by: str
    ) -> WorkflowTask:
        """Assign task to a user."""
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        old_assignee = task.assignee_id
        
        # Update assignment
        task.assignee_id = assignee_id
        task.assigned_by = assigned_by
        task.assigned_at = datetime.now()
        task.status = TaskStatus.ASSIGNED
        
        db.commit()
        db.refresh(task)
        
        # Log activity
        await self._log_workflow_activity(
            db, task.instance_id, task_id, ActionType.COMPLETE, "assign_task",
            f"Task assigned to user {assignee_id}", assigned_by,
            {"from_assignee": old_assignee, "to_assignee": assignee_id}
        )
        
        # Send notification
        await self._send_task_notification(db, task, "assigned")
        
        return task

    async def delegate_task(
        self, 
        db: Session, 
        task_id: str, 
        delegate_to: str, 
        delegated_by: str, 
        reason: str = None
    ) -> WorkflowTask:
        """Delegate task to another user."""
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        if task.assignee_id != delegated_by:
            raise ValueError("Only the assigned user can delegate this task")
        
        # Store original assignee if not already stored
        if not task.original_assignee_id:
            task.original_assignee_id = task.assignee_id
        
        # Update delegation
        task.delegated_from = delegated_by
        task.delegated_to = delegate_to
        task.assignee_id = delegate_to
        task.assigned_at = datetime.now()
        
        db.commit()
        db.refresh(task)
        
        # Log activity
        await self._log_workflow_activity(
            db, task.instance_id, task_id, ActionType.DELEGATE, "delegate_task",
            f"Task delegated to {delegate_to}. Reason: {reason or 'Not specified'}", delegated_by
        )
        
        # Send notification
        await self._send_task_notification(db, task, "delegated")
        
        return task

    async def escalate_task(
        self, 
        db: Session, 
        task_id: str, 
        escalate_to: str, 
        escalation_reason: str
    ) -> WorkflowTask:
        """Escalate overdue or problematic task."""
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        # Update escalation
        task.escalated_from = task.assignee_id
        task.escalated_to = escalate_to
        task.assignee_id = escalate_to
        task.escalation_reason = escalation_reason
        task.status = TaskStatus.ESCALATED
        task.assigned_at = datetime.now()
        
        # Update instance escalation count
        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == task.instance_id).first()
        if instance:
            instance.escalation_count += 1
        
        db.commit()
        db.refresh(task)
        
        # Log activity
        await self._log_workflow_activity(
            db, task.instance_id, task_id, ActionType.ESCALATE, "escalate_task",
            f"Task escalated to {escalate_to}. Reason: {escalation_reason}", None
        )
        
        # Send notification
        await self._send_task_notification(db, task, "escalated")
        
        return task

    # =============================================================================
    # Comments and Attachments
    # =============================================================================

    async def add_task_comment(
        self, 
        db: Session, 
        task_id: str, 
        comment_data: Dict[str, Any]
    ) -> WorkflowComment:
        """Add comment to a workflow task."""
        try:
            comment = WorkflowComment(**comment_data, task_id=task_id)
            
            # Generate thread ID if this is a root comment
            if not comment.parent_comment_id:
                comment.thread_id = f"thread_{comment.id}"
            else:
                # Get parent comment's thread ID
                parent = db.query(WorkflowComment).filter(WorkflowComment.id == comment.parent_comment_id).first()
                if parent:
                    comment.thread_id = parent.thread_id
            
            db.add(comment)
            
            # Update task comment count
            task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
            if task:
                task.comment_count += 1
            
            db.commit()
            db.refresh(comment)
            
            # Send notifications to mentioned users
            if comment.mentioned_users:
                await self._send_mention_notifications(db, comment)
            
            return comment
            
        except Exception as e:
            db.rollback()
            raise e

    async def add_task_attachment(
        self, 
        db: Session, 
        task_id: str, 
        attachment_data: Dict[str, Any]
    ) -> WorkflowAttachment:
        """Add attachment to a workflow task."""
        try:
            attachment = WorkflowAttachment(**attachment_data, task_id=task_id)
            
            db.add(attachment)
            
            # Update task attachment count
            task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
            if task:
                task.attachment_count += 1
            
            db.commit()
            db.refresh(attachment)
            
            return attachment
            
        except Exception as e:
            db.rollback()
            raise e

    # =============================================================================
    # Analytics and Reporting
    # =============================================================================

    async def generate_workflow_analytics(
        self, 
        db: Session, 
        organization_id: str,
        period_start: datetime,
        period_end: datetime,
        definition_id: Optional[str] = None
    ) -> WorkflowAnalytics:
        """Generate comprehensive workflow analytics."""
        try:
            # Base query for instances in period
            instances_query = db.query(WorkflowInstance).filter(
                WorkflowInstance.organization_id == organization_id,
                WorkflowInstance.started_at >= period_start,
                WorkflowInstance.started_at <= period_end
            )
            
            if definition_id:
                instances_query = instances_query.filter(WorkflowInstance.definition_id == definition_id)
            
            instances = instances_query.all()
            
            # Calculate metrics
            analytics = WorkflowAnalytics(
                organization_id=organization_id,
                definition_id=definition_id,
                period_start=period_start.date(),
                period_end=period_end.date(),
                period_type="custom"
            )
            
            # Instance metrics
            analytics.total_instances = len(instances)
            analytics.completed_instances = len([i for i in instances if i.status == WorkflowInstanceStatus.COMPLETED])
            analytics.failed_instances = len([i for i in instances if i.status == WorkflowInstanceStatus.FAILED])
            analytics.cancelled_instances = len([i for i in instances if i.status == WorkflowInstanceStatus.CANCELLED])
            analytics.active_instances = len([i for i in instances if i.status == WorkflowInstanceStatus.RUNNING])
            
            # Performance metrics
            completed_instances = [i for i in instances if i.status == WorkflowInstanceStatus.COMPLETED and i.duration_minutes]
            if completed_instances:
                durations = [i.duration_minutes for i in completed_instances]
                analytics.average_completion_time_hours = Decimal(str(sum(durations) / len(durations) / 60))
                analytics.median_completion_time_hours = Decimal(str(sorted(durations)[len(durations)//2] / 60))
                analytics.min_completion_time_hours = Decimal(str(min(durations) / 60))
                analytics.max_completion_time_hours = Decimal(str(max(durations) / 60))
            
            # SLA metrics
            sla_breaches = len([i for i in instances if i.sla_breach])
            analytics.sla_breaches = sla_breaches
            if analytics.total_instances > 0:
                analytics.sla_compliance_rate = Decimal(str((1 - sla_breaches / analytics.total_instances) * 100))
            
            # Task metrics
            tasks_query = db.query(WorkflowTask).join(WorkflowInstance).filter(
                WorkflowInstance.organization_id == organization_id,
                WorkflowInstance.started_at >= period_start,
                WorkflowInstance.started_at <= period_end
            )
            
            if definition_id:
                tasks_query = tasks_query.filter(WorkflowInstance.definition_id == definition_id)
            
            tasks = tasks_query.all()
            analytics.total_tasks = len(tasks)
            analytics.completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            analytics.overdue_tasks = len([t for t in tasks if t.due_date and t.due_date < datetime.now() and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]])
            analytics.escalated_tasks = len([t for t in tasks if t.escalated_to])
            analytics.reassigned_tasks = len([t for t in tasks if t.delegated_to])
            
            # Quality metrics
            approved_tasks = len([t for t in tasks if t.completion_result == "approved"])
            rejected_tasks = len([t for t in tasks if t.completion_result == "rejected"])
            if analytics.completed_tasks > 0:
                analytics.approval_rate = Decimal(str(approved_tasks / analytics.completed_tasks * 100))
                analytics.rejection_rate = Decimal(str(rejected_tasks / analytics.completed_tasks * 100))
            
            db.add(analytics)
            db.commit()
            db.refresh(analytics)
            
            return analytics
            
        except Exception as e:
            db.rollback()
            raise e

    async def get_workflow_performance_dashboard(
        self, 
        db: Session, 
        organization_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive workflow performance dashboard."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Get active instances
        active_instances = db.query(WorkflowInstance).filter(
            WorkflowInstance.organization_id == organization_id,
            WorkflowInstance.status.in_([WorkflowInstanceStatus.RUNNING, WorkflowInstanceStatus.WAITING])
        ).count()
        
        # Get overdue tasks
        overdue_tasks = db.query(WorkflowTask).join(WorkflowInstance).filter(
            WorkflowInstance.organization_id == organization_id,
            WorkflowTask.due_date < datetime.now(),
            WorkflowTask.status.in_([TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
        ).count()
        
        # Get completion metrics
        completed_instances = db.query(WorkflowInstance).filter(
            WorkflowInstance.organization_id == organization_id,
            WorkflowInstance.completed_at >= start_date,
            WorkflowInstance.status == WorkflowInstanceStatus.COMPLETED
        ).all()
        
        avg_completion_time = 0
        if completed_instances:
            total_time = sum([i.duration_minutes or 0 for i in completed_instances])
            avg_completion_time = total_time / len(completed_instances) / 60  # Convert to hours
        
        # Get top bottlenecks
        bottleneck_query = db.query(
            WorkflowTask.step_id,
            func.avg(WorkflowTask.actual_duration_minutes).label('avg_duration'),
            func.count(WorkflowTask.id).label('task_count')
        ).join(WorkflowInstance).filter(
            WorkflowInstance.organization_id == organization_id,
            WorkflowTask.completed_at >= start_date,
            WorkflowTask.actual_duration_minutes.isnot(None)
        ).group_by(WorkflowTask.step_id).order_by(desc('avg_duration')).limit(5).all()
        
        return {
            "active_instances": active_instances,
            "overdue_tasks": overdue_tasks,
            "completed_instances_period": len(completed_instances),
            "average_completion_time_hours": round(avg_completion_time, 2),
            "top_bottlenecks": [
                {
                    "step_id": b.step_id,
                    "average_duration_minutes": float(b.avg_duration),
                    "task_count": b.task_count
                } for b in bottleneck_query
            ],
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _validate_workflow_schema(self, schema: Dict[str, Any]):
        """Validate workflow definition schema."""
        required_fields = ["steps", "start_step"]
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Missing required schema field: {field}")
        
        if not isinstance(schema["steps"], list) or len(schema["steps"]) == 0:
            raise ValueError("Schema must contain at least one step")

    async def _create_steps_from_schema(self, db: Session, definition: WorkflowDefinition):
        """Create workflow steps from definition schema."""
        steps_config = definition.definition_schema.get("steps", [])
        
        for i, step_config in enumerate(steps_config):
            step = WorkflowStep(
                organization_id=definition.organization_id,
                definition_id=definition.id,
                name=step_config.get("name", f"Step {i+1}"),
                code=step_config.get("code", f"step_{i+1}"),
                description=step_config.get("description"),
                step_type=step_config.get("type", "task"),
                step_order=i + 1,
                step_config=step_config,
                assignee_type=step_config.get("assignee_type", "user"),
                assignee_id=step_config.get("assignee_id"),
                estimated_duration_minutes=step_config.get("estimated_duration_minutes"),
                is_required=step_config.get("is_required", True)
            )
            db.add(step)
        
        db.commit()

    async def _generate_instance_number(self, db: Session, definition: WorkflowDefinition) -> str:
        """Generate unique instance number."""
        count = db.query(WorkflowInstance).filter(
            WorkflowInstance.definition_id == definition.id
        ).count()
        
        return f"{definition.code}-{count + 1:06d}"

    async def _generate_task_number(self, db: Session, instance_id: str) -> str:
        """Generate unique task number."""
        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()
        task_count = db.query(WorkflowTask).filter(WorkflowTask.instance_id == instance_id).count()
        
        return f"{instance.instance_number}-T{task_count + 1:03d}"

    async def _start_first_step(self, db: Session, instance: WorkflowInstance, definition: WorkflowDefinition):
        """Start the first step of workflow instance."""
        # Get first step
        first_step = db.query(WorkflowStep).filter(
            WorkflowStep.definition_id == definition.id,
            WorkflowStep.step_order == 1
        ).first()
        
        if first_step:
            instance.current_step_id = first_step.id
            instance.status = WorkflowInstanceStatus.RUNNING
            
            # Create first task
            await self.create_workflow_task(db, {
                "organization_id": instance.organization_id,
                "instance_id": instance.id,
                "step_id": first_step.id,
                "name": first_step.name,
                "description": first_step.description,
                "assignee_id": first_step.assignee_id,
                "assignee_type": first_step.assignee_type,
                "estimated_duration_minutes": first_step.estimated_duration_minutes,
                "priority": instance.priority
            })
            
            db.commit()

    async def _complete_task(self, db: Session, task: WorkflowTask, action_data: Dict[str, Any]):
        """Complete a workflow task."""
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.completion_result = action_data.get("result", "completed")
        task.result_data = action_data.get("result_data")
        task.completion_notes = action_data.get("notes")
        
        # Calculate actual duration
        if task.started_at:
            duration = datetime.now() - task.started_at
            task.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        db.commit()

    async def _determine_next_step(
        self, 
        db: Session, 
        instance: WorkflowInstance, 
        current_step_id: str, 
        action_data: Dict[str, Any]
    ) -> Optional[WorkflowStep]:
        """Determine the next step in workflow based on current step and action."""
        current_step = db.query(WorkflowStep).filter(WorkflowStep.id == current_step_id).first()
        if not current_step:
            return None
        
        # Get next step IDs from configuration
        next_step_ids = current_step.next_step_ids
        if not next_step_ids:
            # Get next step by order
            next_step = db.query(WorkflowStep).filter(
                WorkflowStep.definition_id == current_step.definition_id,
                WorkflowStep.step_order == current_step.step_order + 1
            ).first()
            return next_step
        
        # If only one next step, return it
        if len(next_step_ids) == 1:
            return db.query(WorkflowStep).filter(WorkflowStep.id == next_step_ids[0]).first()
        
        # Multiple next steps - apply decision logic
        return await self._apply_decision_logic(db, current_step, next_step_ids, action_data)

    async def _apply_decision_logic(
        self, 
        db: Session, 
        current_step: WorkflowStep, 
        next_step_ids: List[str], 
        action_data: Dict[str, Any]
    ) -> Optional[WorkflowStep]:
        """Apply decision logic to determine next step."""
        # Simple decision logic based on completion result
        result = action_data.get("result", "approved")
        
        # Find step based on result
        for step_id in next_step_ids:
            step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
            if step and step.start_conditions:
                conditions = step.start_conditions
                if conditions.get("required_result") == result:
                    return step
        
        # Default to first next step
        return db.query(WorkflowStep).filter(WorkflowStep.id == next_step_ids[0]).first()

    async def _start_workflow_step(self, db: Session, instance: WorkflowInstance, step: WorkflowStep):
        """Start a new workflow step."""
        instance.current_step_id = step.id
        
        # Create task for the step
        await self.create_workflow_task(db, {
            "organization_id": instance.organization_id,
            "instance_id": instance.id,
            "step_id": step.id,
            "name": step.name,
            "description": step.description,
            "assignee_id": step.assignee_id,
            "assignee_type": step.assignee_type,
            "estimated_duration_minutes": step.estimated_duration_minutes,
            "priority": instance.priority
        })
        
        db.commit()

    async def _complete_workflow_instance(self, db: Session, instance: WorkflowInstance, action_data: Dict[str, Any]):
        """Complete a workflow instance."""
        instance.status = WorkflowInstanceStatus.COMPLETED
        instance.completed_at = datetime.now()
        instance.completed_by = action_data.get("completed_by")
        instance.final_status = "completed"
        instance.final_result = action_data.get("final_result")
        instance.completion_notes = action_data.get("completion_notes")
        
        # Calculate duration
        if instance.started_at:
            duration = instance.completed_at - instance.started_at
            instance.duration_minutes = int(duration.total_seconds() / 60)
        
        # Check SLA breach
        if instance.sla_deadline and instance.completed_at > instance.sla_deadline:
            instance.sla_breach = True
        
        instance.progress_percentage = Decimal("100.00")
        
        db.commit()

    async def _update_instance_progress(self, db: Session, instance: WorkflowInstance):
        """Update workflow instance progress percentage."""
        completed_tasks = db.query(WorkflowTask).filter(
            WorkflowTask.instance_id == instance.id,
            WorkflowTask.status == TaskStatus.COMPLETED
        ).count()
        
        if instance.total_steps > 0:
            instance.progress_percentage = Decimal(str((completed_tasks / instance.total_steps) * 100))
            instance.completed_steps = completed_tasks
        
        db.commit()

    async def _log_workflow_activity(
        self, 
        db: Session, 
        instance_id: str, 
        task_id: Optional[str], 
        action_type: ActionType, 
        activity_type: str, 
        description: str, 
        performed_by: Optional[str],
        activity_data: Optional[Dict[str, Any]] = None
    ):
        """Log workflow activity."""
        activity = WorkflowActivity(
            organization_id=db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first().organization_id,
            instance_id=instance_id,
            task_id=task_id,
            activity_type=activity_type,
            action_type=action_type,
            description=description,
            performed_by=performed_by,
            activity_data=activity_data or {},
            performed_at=datetime.now()
        )
        
        db.add(activity)
        db.commit()

    async def _send_task_notification(self, db: Session, task: WorkflowTask, notification_type: str):
        """Send notification for task events - placeholder for integration with notification system."""
        # This would integrate with the notification system
        pass

    async def _send_mention_notifications(self, db: Session, comment: WorkflowComment):
        """Send notifications to mentioned users in comments."""
        # This would integrate with the notification system
        pass

    async def _log_audit_action(
        self, 
        db: Session, 
        organization_id: str, 
        action: str, 
        entity_type: str, 
        entity_id: str, 
        old_values: Optional[Dict], 
        new_values: Dict, 
        user_id: Optional[str] = None
    ):
        """Log workflow audit action."""
        audit_log = WorkflowAuditLog(
            organization_id=organization_id,
            action_type=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            changes_summary=f"{action.title()} {entity_type}"
        )
        
        db.add(audit_log)
        db.commit()

    def _requires_new_version(self, update_data: Dict[str, Any]) -> bool:
        """Check if update requires creating a new version."""
        significant_fields = ["definition_schema", "workflow_type", "steps_config"]
        return any(field in update_data for field in significant_fields)

    async def _create_new_version(
        self, 
        db: Session, 
        current_definition: WorkflowDefinition, 
        update_data: Dict[str, Any]
    ) -> WorkflowDefinition:
        """Create new version of workflow definition."""
        # Create new version
        new_version = WorkflowDefinition(**{
            **{k: v for k, v in current_definition.__dict__.items() 
               if not k.startswith('_') and k not in ['id', 'created_at', 'updated_at']},
            **update_data,
            "version": self._increment_version(current_definition.version),
            "previous_version_id": current_definition.id
        })
        
        db.add(new_version)
        
        # Mark current version as deprecated
        current_definition.status = WorkflowStatus.DEPRECATED
        
        db.commit()
        db.refresh(new_version)
        
        return new_version

    def _increment_version(self, current_version: str) -> str:
        """Increment version number."""
        try:
            major, minor = current_version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "2.0"


# Create service instance
workflow_service = WorkflowService()