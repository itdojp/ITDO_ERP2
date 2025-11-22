"""Advanced Workflow & Approval System - CC02 v73.0 Day 18."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .enterprise_auth_system import EnterpriseAuthenticationSystem, PermissionLevel
from .erp_app_architecture import (
    ERPEntityType,
    WorkflowStep,
)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ARCHIVED = "archived"


class ApprovalStatus(str, Enum):
    """Approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class EscalationTrigger(str, Enum):
    """Escalation trigger conditions."""

    TIMEOUT = "timeout"
    REJECTION = "rejection"
    MULTIPLE_REJECTIONS = "multiple_rejections"
    MANUAL = "manual"
    RULE_BASED = "rule_based"
    SYSTEM_ERROR = "system_error"


class WorkflowTrigger(str, Enum):
    """Workflow trigger types."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    API = "api"
    FORM_SUBMISSION = "form_submission"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DATABASE_CHANGE = "database_change"


class ApprovalAction(BaseModel):
    """Approval action details."""

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ApprovalStatus
    approver_id: str
    comments: Optional[str] = None

    # Action context
    step_id: str
    workflow_instance_id: str
    entity_data: Dict[str, Any] = Field(default_factory=dict)

    # Delegation
    delegated_to: Optional[str] = None
    delegation_reason: Optional[str] = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    deadline: Optional[datetime] = None

    # Attachments
    attachments: List[str] = Field(default_factory=list)
    supporting_docs: List[Dict[str, Any]] = Field(default_factory=list)


class EscalationRule(BaseModel):
    """Escalation rule definition."""

    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str

    # Trigger conditions
    trigger_type: EscalationTrigger
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)

    # Escalation actions
    escalate_to: List[str] = Field(default_factory=list)  # user IDs or roles
    escalation_message: str = ""
    include_original_data: bool = True

    # Timing
    delay_minutes: int = 0
    max_escalations: int = 3

    # Priority
    priority: int = 1
    enabled: bool = True


class WorkflowTemplate(BaseModel):
    """Workflow template definition."""

    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str = "1.0"

    # Template metadata
    category: str = "general"
    tags: Set[str] = Field(default_factory=set)
    entity_types: Set[ERPEntityType] = Field(default_factory=set)

    # Workflow definition
    steps: List[WorkflowStep] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    escalation_rules: List[EscalationRule] = Field(default_factory=list)

    # Configuration
    allow_parallel_execution: bool = False
    auto_assign_based_on_data: bool = True
    require_all_approvals: bool = True

    # Access control
    created_by: str
    allowed_initiators: Set[str] = Field(default_factory=set)  # roles or user IDs

    # Status
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class WorkflowInstance(BaseModel):
    """Running workflow instance."""

    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    template_version: str

    # Instance metadata
    title: str
    description: Optional[str] = None
    priority: int = 1  # 1-5, higher = more urgent

    # Data context
    entity_type: ERPEntityType
    entity_id: str
    entity_data: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)

    # Execution state
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_step_index: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    active_approvals: Dict[str, ApprovalAction] = Field(default_factory=dict)

    # Participants
    initiator_id: str
    current_approvers: Set[str] = Field(default_factory=set)
    all_participants: Set[str] = Field(default_factory=set)

    # Timeline
    started_at: datetime = Field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # History
    action_history: List[ApprovalAction] = Field(default_factory=list)
    escalation_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class DynamicApprovalRouter:
    """Dynamic approval routing based on business rules."""

    def __init__(self) -> dict:
        self.routing_rules: Dict[str, Dict[str, Any]] = {}
        self.approval_matrices: Dict[str, Dict[str, Any]] = {}

    def add_routing_rule(
        self,
        rule_name: str,
        conditions: Dict[str, Any],
        approvers: List[str],
        priority: int = 1,
    ) -> None:
        """Add approval routing rule."""
        self.routing_rules[rule_name] = {
            "conditions": conditions,
            "approvers": approvers,
            "priority": priority,
            "enabled": True,
        }

    def add_approval_matrix(
        self,
        matrix_name: str,
        entity_type: ERPEntityType,
        amount_thresholds: Dict[str, List[str]],  # amount_range -> approvers
    ) -> None:
        """Add approval matrix for amount-based routing."""
        self.approval_matrices[matrix_name] = {
            "entity_type": entity_type,
            "thresholds": amount_thresholds,
            "enabled": True,
        }

    async def get_approvers(
        self,
        entity_type: ERPEntityType,
        entity_data: Dict[str, Any],
        step_config: Dict[str, Any],
    ) -> List[str]:
        """Get dynamic list of approvers for entity."""
        approvers = []

        # Check routing rules
        for rule_name, rule in self.routing_rules.items():
            if not rule["enabled"]:
                continue

            if self._evaluate_conditions(rule["conditions"], entity_data):
                approvers.extend(rule["approvers"])

        # Check approval matrices
        for matrix_name, matrix in self.approval_matrices.items():
            if not matrix["enabled"] or matrix["entity_type"] != entity_type:
                continue

            amount = entity_data.get("amount", 0)
            matrix_approvers = self._get_matrix_approvers(matrix["thresholds"], amount)
            approvers.extend(matrix_approvers)

        # Remove duplicates and return
        return list(set(approvers))

    def _evaluate_conditions(
        self, conditions: Dict[str, Any], data: Dict[str, Any]
    ) -> bool:
        """Evaluate routing conditions."""
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition.get("operator", "eq")
                value = condition.get("value")

                field_value = data.get(field)

                if operator == "eq" and field_value != value:
                    return False
                elif operator == "gt" and float(field_value or 0) <= float(value):
                    return False
                elif operator == "gte" and float(field_value or 0) < float(value):
                    return False
                elif operator == "lt" and float(field_value or 0) >= float(value):
                    return False
                elif operator == "lte" and float(field_value or 0) > float(value):
                    return False
                elif operator == "in" and field_value not in value:
                    return False
                elif operator == "contains" and value not in str(field_value or ""):
                    return False
            else:
                # Simple equality check
                if data.get(field) != condition:
                    return False

        return True

    def _get_matrix_approvers(
        self, thresholds: Dict[str, List[str]], amount: float
    ) -> List[str]:
        """Get approvers from approval matrix based on amount."""
        for threshold_range, approvers in thresholds.items():
            if self._amount_in_range(amount, threshold_range):
                return approvers

        return []

    def _amount_in_range(self, amount: float, range_str: str) -> bool:
        """Check if amount is in specified range."""
        try:
            if "-" in range_str:
                min_val, max_val = range_str.split("-")
                return float(min_val) <= amount <= float(max_val)
            elif ">" in range_str:
                min_val = range_str.replace(">", "").strip()
                return amount > float(min_val)
            elif "<" in range_str:
                max_val = range_str.replace("<", "").strip()
                return amount < float(max_val)
            else:
                return amount == float(range_str)
        except ValueError:
            return False


class WorkflowEngine:
    """Advanced workflow execution engine."""

    def __init__(self, auth_system: EnterpriseAuthenticationSystem) -> dict:
        self.auth_system = auth_system
        self.approval_router = DynamicApprovalRouter()

        # Storage
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.escalation_rules: Dict[str, EscalationRule] = {}

        # Execution state
        self.running_instances: Set[str] = set()
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}

        # Initialize default templates and rules
        self._initialize_default_configurations()

    def _initialize_default_configurations(self) -> None:
        """Initialize default workflow configurations."""
        # Purchase Order Approval Template
        po_template = WorkflowTemplate(
            name="Purchase Order Approval",
            description="Standard purchase order approval workflow",
            category="procurement",
            entity_types={ERPEntityType.ORDER},
            steps=[
                WorkflowStep(
                    step_id="manager_review",
                    name="Manager Review",
                    description="Department manager reviews purchase order",
                    step_type="approval",
                    assignee_role="department_manager",
                    timeout_hours=24,
                    required_permissions=[PermissionLevel.APPROVE],
                ),
                WorkflowStep(
                    step_id="finance_approval",
                    name="Finance Approval",
                    description="Finance team approves purchase order",
                    step_type="approval",
                    assignee_role="finance_manager",
                    timeout_hours=48,
                    required_permissions=[PermissionLevel.APPROVE],
                    conditions={
                        "amount_threshold": {"field": "total_amount", "value": 10000}
                    },
                ),
                WorkflowStep(
                    step_id="procurement_processing",
                    name="Procurement Processing",
                    description="Process approved purchase order",
                    step_type="action",
                ),
            ],
            created_by="system",
            allowed_initiators={"procurement_user", "department_manager"},
        )
        self.register_template(po_template)

        # Employee Onboarding Template
        onboarding_template = WorkflowTemplate(
            name="Employee Onboarding",
            description="New employee onboarding process",
            category="hr",
            entity_types={ERPEntityType.EMPLOYEE},
            steps=[
                WorkflowStep(
                    step_id="hr_verification",
                    name="HR Verification",
                    description="HR verifies employee documentation",
                    step_type="approval",
                    assignee_role="hr_manager",
                    timeout_hours=48,
                ),
                WorkflowStep(
                    step_id="it_setup",
                    name="IT Setup",
                    description="Setup employee IT accounts and equipment",
                    step_type="action",
                    assignee_role="it_admin",
                ),
                WorkflowStep(
                    step_id="manager_introduction",
                    name="Manager Introduction",
                    description="Direct manager introduces new employee",
                    step_type="approval",
                    assignee_user="manager_id",
                    timeout_hours=72,
                ),
            ],
            created_by="system",
            allowed_initiators={"hr_manager", "hr_user"},
        )
        self.register_template(onboarding_template)

        # Setup approval routing
        self._setup_approval_routing()

        # Setup escalation rules
        self._setup_escalation_rules()

    def _setup_approval_routing(self) -> None:
        """Setup dynamic approval routing rules."""
        # High-value purchase orders require additional approval
        self.approval_router.add_routing_rule(
            "high_value_po",
            conditions={
                "total_amount": {"operator": "gt", "value": 50000},
                "entity_type": "order",
            },
            approvers=["cfo", "ceo"],
            priority=1,
        )

        # IT purchases need IT manager approval
        self.approval_router.add_routing_rule(
            "it_purchases",
            conditions={"category": "IT", "entity_type": "order"},
            approvers=["it_manager"],
            priority=2,
        )

        # Purchase order approval matrix
        self.approval_router.add_approval_matrix(
            "po_amount_matrix",
            ERPEntityType.ORDER,
            {
                "0-1000": ["department_manager"],
                "1000-10000": ["department_manager", "finance_manager"],
                "10000-50000": ["department_manager", "finance_manager", "director"],
                ">50000": ["department_manager", "finance_manager", "director", "cfo"],
            },
        )

    def _setup_escalation_rules(self) -> None:
        """Setup escalation rules."""
        # Timeout escalation
        timeout_escalation = EscalationRule(
            name="Approval Timeout Escalation",
            description="Escalate when approval times out",
            trigger_type=EscalationTrigger.TIMEOUT,
            trigger_conditions={"timeout_hours": 24},
            escalate_to=["manager", "director"],
            escalation_message="Approval request has timed out and requires immediate attention.",
            delay_minutes=0,
        )
        self.escalation_rules[timeout_escalation.rule_id] = timeout_escalation

        # Multiple rejection escalation
        rejection_escalation = EscalationRule(
            name="Multiple Rejection Escalation",
            description="Escalate after multiple rejections",
            trigger_type=EscalationTrigger.MULTIPLE_REJECTIONS,
            trigger_conditions={"rejection_count": 2},
            escalate_to=["director", "vp"],
            escalation_message="Request has been rejected multiple times and may need review.",
            delay_minutes=30,
        )
        self.escalation_rules[rejection_escalation.rule_id] = rejection_escalation

    def register_template(self, template: WorkflowTemplate) -> None:
        """Register a workflow template."""
        self.templates[template.template_id] = template

    async def start_workflow(
        self,
        template_id: str,
        entity_type: ERPEntityType,
        entity_id: str,
        entity_data: Dict[str, Any],
        initiator_id: str,
        title: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> WorkflowInstance:
        """Start a new workflow instance."""
        template = self.templates.get(template_id)
        if not template or not template.active:
            raise ValueError(f"Template {template_id} not found or inactive")

        # Check if initiator is allowed
        if (
            template.allowed_initiators
            and initiator_id not in template.allowed_initiators
            and not self._user_has_allowed_role(
                initiator_id, template.allowed_initiators
            )
        ):
            raise PermissionError(
                f"User {initiator_id} not allowed to initiate this workflow"
            )

        # Create workflow instance
        instance = WorkflowInstance(
            template_id=template_id,
            template_version=template.version,
            title=title or f"{template.name} - {entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            variables=variables or {},
            initiator_id=initiator_id,
        )

        # Store instance
        self.instances[instance.instance_id] = instance
        self.running_instances.add(instance.instance_id)

        # Start execution
        await self._execute_next_step(instance.instance_id)

        # Emit workflow started event
        await self._emit_event(
            "workflow_started",
            {
                "instance_id": instance.instance_id,
                "template_id": template_id,
                "initiator_id": initiator_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
            },
        )

        return instance

    async def _execute_next_step(self, instance_id: str) -> None:
        """Execute the next step in workflow."""
        instance = self.instances.get(instance_id)
        if not instance or instance.status != WorkflowStatus.RUNNING:
            return

        template = self.templates.get(instance.template_id)
        if not template:
            await self._fail_workflow(instance_id, "Template not found")
            return

        # Check if workflow is complete
        if instance.current_step_index >= len(template.steps):
            await self._complete_workflow(instance_id)
            return

        current_step = template.steps[instance.current_step_index]

        try:
            step_result = await self._execute_step(instance, current_step)

            if step_result.get("completed", False):
                # Step completed, move to next
                instance.completed_steps.append(current_step.step_id)
                instance.current_step_index += 1

                # Schedule next step execution
                asyncio.create_task(self._execute_next_step(instance_id))

            elif step_result.get("waiting", False):
                # Step is waiting for approval
                instance.status = WorkflowStatus.RUNNING

                # Setup timeout handling
                timeout_hours = current_step.timeout_hours
                if timeout_hours:
                    timeout_task = asyncio.create_task(
                        self._handle_step_timeout(
                            instance_id, current_step.step_id, timeout_hours
                        )
                    )
                    self.scheduled_tasks[
                        f"{instance_id}_{current_step.step_id}_timeout"
                    ] = timeout_task

        except Exception as e:
            await self._fail_workflow(instance_id, f"Step execution failed: {str(e)}")

    async def _execute_step(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_result = {"completed": False, "waiting": False}

        if step.step_type == "approval":
            # Create approval request
            approvers = await self._get_step_approvers(instance, step)

            if not approvers:
                # No approvers found, skip step
                step_result["completed"] = True
                return step_result

            # Create approval action for each approver
            for approver_id in approvers:
                approval = ApprovalAction(
                    action_type=ApprovalStatus.PENDING,
                    approver_id=approver_id,
                    step_id=step.step_id,
                    workflow_instance_id=instance.instance_id,
                    entity_data=instance.entity_data,
                    deadline=datetime.now() + timedelta(hours=step.timeout_hours or 24),
                )

                instance.active_approvals[approval.action_id] = approval
                instance.current_approvers.add(approver_id)
                instance.all_participants.add(approver_id)

            step_result["waiting"] = True

            # Send approval notifications
            await self._notify_approvers(instance, step, approvers)

        elif step.step_type == "action":
            # Execute automated action
            action_result = await self._execute_action(instance, step)
            step_result["completed"] = True
            step_result["action_result"] = action_result

        elif step.step_type == "condition":
            # Evaluate condition
            condition_result = self._evaluate_step_condition(instance, step)
            step_result["completed"] = True

            if not condition_result:
                # Condition failed, skip remaining steps or follow alternative path
                instance.status = WorkflowStatus.COMPLETED

        elif step.step_type == "notification":
            # Send notification
            await self._send_notification(instance, step)
            step_result["completed"] = True

        return step_result

    async def _get_step_approvers(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> List[str]:
        """Get approvers for workflow step."""
        approvers = []

        # Static assignment
        if step.assignee_user:
            approvers.append(step.assignee_user)

        if step.assignee_role:
            # Get users with specified role
            role_users = self._get_users_with_role(step.assignee_role)
            approvers.extend(role_users)

        # Dynamic assignment
        dynamic_approvers = await self.approval_router.get_approvers(
            instance.entity_type, instance.entity_data, step.dict()
        )
        approvers.extend(dynamic_approvers)

        # Remove duplicates
        return list(set(approvers))

    async def approve_step(
        self,
        instance_id: str,
        approval_id: str,
        approver_id: str,
        action: ApprovalStatus,
        comments: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Process approval action."""
        instance = self.instances.get(instance_id)
        if not instance:
            return False

        approval = instance.active_approvals.get(approval_id)
        if not approval or approval.approver_id != approver_id:
            return False

        # Update approval
        approval.action_type = action
        approval.comments = comments
        approval.attachments = attachments or []

        # Add to history
        instance.action_history.append(approval)

        # Remove from active approvals
        del instance.active_approvals[approval_id]
        instance.current_approvers.discard(approver_id)

        # Check if step can proceed
        template = self.templates.get(instance.template_id)
        current_step = template.steps[instance.current_step_index]

        if action == ApprovalStatus.APPROVED:
            # Check if all required approvals are complete
            if self._are_step_approvals_complete(instance, current_step):
                # Continue workflow
                instance.completed_steps.append(current_step.step_id)
                instance.current_step_index += 1

                # Cancel timeout tasks
                self._cancel_step_timeout(instance_id, current_step.step_id)

                # Execute next step
                await self._execute_next_step(instance_id)

        elif action == ApprovalStatus.REJECTED:
            # Handle rejection
            rejection_count = sum(
                1
                for action in instance.action_history
                if action.step_id == current_step.step_id
                and action.action_type == ApprovalStatus.REJECTED
            )

            # Check escalation rules
            await self._check_escalation(
                instance,
                EscalationTrigger.REJECTION,
                {"rejection_count": rejection_count, "step_id": current_step.step_id},
            )

            # Cancel other pending approvals for this step
            await self._cancel_step_approvals(instance, current_step.step_id)

            # Fail workflow or handle rejection logic
            if rejection_count >= 2:  # Multiple rejections
                await self._check_escalation(
                    instance,
                    EscalationTrigger.MULTIPLE_REJECTIONS,
                    {"rejection_count": rejection_count},
                )
            else:
                # Workflow can continue with rejection handling
                pass

        elif action == ApprovalStatus.DELEGATED:
            # Handle delegation
            delegated_to = approval.delegated_to
            if delegated_to:
                # Create new approval for delegate
                new_approval = ApprovalAction(
                    action_type=ApprovalStatus.PENDING,
                    approver_id=delegated_to,
                    step_id=current_step.step_id,
                    workflow_instance_id=instance_id,
                    entity_data=instance.entity_data,
                    deadline=approval.deadline,
                )

                instance.active_approvals[new_approval.action_id] = new_approval
                instance.current_approvers.add(delegated_to)
                instance.all_participants.add(delegated_to)

                # Notify delegate
                await self._notify_approvers(instance, current_step, [delegated_to])

        # Emit approval event
        await self._emit_event(
            "approval_action",
            {
                "instance_id": instance_id,
                "approval_id": approval_id,
                "approver_id": approver_id,
                "action": action,
                "step_id": current_step.step_id,
            },
        )

        return True

    def _are_step_approvals_complete(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> bool:
        """Check if step approvals are complete."""
        template = self.templates.get(instance.template_id)

        # Get pending approvals for this step
        pending_approvals = [
            approval
            for approval in instance.active_approvals.values()
            if approval.step_id == step.step_id
            and approval.action_type == ApprovalStatus.PENDING
        ]

        if template.require_all_approvals:
            # All approvals must be completed
            return len(pending_approvals) == 0
        else:
            # At least one approval is sufficient
            approved_count = sum(
                1
                for action in instance.action_history
                if action.step_id == step.step_id
                and action.action_type == ApprovalStatus.APPROVED
            )
            return approved_count > 0

    async def _handle_step_timeout(
        self, instance_id: str, step_id: str, timeout_hours: int
    ) -> None:
        """Handle step timeout."""
        await asyncio.sleep(timeout_hours * 3600)  # Convert to seconds

        instance = self.instances.get(instance_id)
        if not instance or step_id not in [
            step.step_id for step in self.templates[instance.template_id].steps
        ]:
            return

        # Check if step is still active
        active_approvals = [
            approval
            for approval in instance.active_approvals.values()
            if approval.step_id == step_id
        ]

        if active_approvals:
            # Step has timed out
            await self._check_escalation(
                instance,
                EscalationTrigger.TIMEOUT,
                {"step_id": step_id, "timeout_hours": timeout_hours},
            )

            # Mark approvals as expired
            for approval in active_approvals:
                approval.action_type = ApprovalStatus.EXPIRED
                instance.action_history.append(approval)

            # Clear active approvals
            instance.active_approvals = {
                k: v
                for k, v in instance.active_approvals.items()
                if v.step_id != step_id
            }

            # Emit timeout event
            await self._emit_event(
                "step_timeout",
                {
                    "instance_id": instance_id,
                    "step_id": step_id,
                    "timeout_hours": timeout_hours,
                },
            )

    async def _check_escalation(
        self,
        instance: WorkflowInstance,
        trigger: EscalationTrigger,
        context: Dict[str, Any],
    ) -> None:
        """Check and execute escalation rules."""
        for rule in self.escalation_rules.values():
            if not rule.enabled or rule.trigger_type != trigger:
                continue

            if self._evaluate_escalation_conditions(rule.trigger_conditions, context):
                await self._execute_escalation(instance, rule, context)

    def _evaluate_escalation_conditions(
        self, conditions: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Evaluate escalation rule conditions."""
        for condition_key, condition_value in conditions.items():
            context_value = context.get(condition_key)

            if isinstance(condition_value, dict):
                operator = condition_value.get("operator", "eq")
                value = condition_value.get("value")

                if operator == "eq" and context_value != value:
                    return False
                elif operator == "gt" and (context_value or 0) <= value:
                    return False
                elif operator == "gte" and (context_value or 0) < value:
                    return False
            else:
                if context_value != condition_value:
                    return False

        return True

    async def _execute_escalation(
        self, instance: WorkflowInstance, rule: EscalationRule, context: Dict[str, Any]
    ) -> None:
        """Execute escalation rule."""
        # Wait for delay if specified
        if rule.delay_minutes > 0:
            await asyncio.sleep(rule.delay_minutes * 60)

        # Create escalation record
        escalation_record = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "trigger": rule.trigger_type,
            "escalated_to": rule.escalate_to,
            "escalated_at": datetime.now(),
            "context": context,
            "original_data": instance.entity_data if rule.include_original_data else {},
        }

        instance.escalation_history.append(escalation_record)

        # Send escalation notifications
        for escalation_target in rule.escalate_to:
            await self._send_escalation_notification(
                instance, rule, escalation_target, context
            )

        # Emit escalation event
        await self._emit_event(
            "workflow_escalated",
            {
                "instance_id": instance.instance_id,
                "rule_id": rule.rule_id,
                "escalated_to": rule.escalate_to,
                "context": context,
            },
        )

    async def _send_escalation_notification(
        self,
        instance: WorkflowInstance,
        rule: EscalationRule,
        target: str,
        context: Dict[str, Any],
    ) -> None:
        """Send escalation notification."""
        # Implementation would send actual notification
        print(
            f"[Workflow] Escalation notification sent to {target} for rule {rule.name}"
        )

    async def _notify_approvers(
        self, instance: WorkflowInstance, step: WorkflowStep, approvers: List[str]
    ) -> None:
        """Send approval notifications to approvers."""
        for approver_id in approvers:
            # Implementation would send actual notification
            print(
                f"[Workflow] Approval notification sent to {approver_id} for step {step.name}"
            )

    async def _execute_action(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute automated workflow action."""
        # Implementation would execute actual business action
        print(f"[Workflow] Executing action step: {step.name}")
        return {"status": "completed", "executed_at": datetime.now()}

    def _evaluate_step_condition(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> bool:
        """Evaluate step condition."""
        conditions = step.conditions
        if not conditions:
            return True

        # Evaluate conditions against instance data
        for condition_key, condition_value in conditions.items():
            if isinstance(condition_value, dict):
                field = condition_value.get("field")
                operator = condition_value.get("operator", "eq")
                value = condition_value.get("value")

                field_value = instance.entity_data.get(field)

                if operator == "eq" and field_value != value:
                    return False
                elif operator == "gt" and (field_value or 0) <= value:
                    return False
                elif operator == "gte" and (field_value or 0) < value:
                    return False
                elif operator == "lt" and (field_value or 0) >= value:
                    return False
                elif operator == "lte" and (field_value or 0) > value:
                    return False

        return True

    async def _send_notification(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> None:
        """Send workflow notification."""
        # Implementation would send actual notification
        print(f"[Workflow] Notification sent for step: {step.name}")

    async def _complete_workflow(self, instance_id: str) -> None:
        """Complete workflow instance."""
        instance = self.instances.get(instance_id)
        if not instance:
            return

        instance.status = WorkflowStatus.COMPLETED
        instance.completed_at = datetime.now()

        # Remove from running instances
        self.running_instances.discard(instance_id)

        # Cancel any pending tasks
        self._cancel_instance_tasks(instance_id)

        # Emit completion event
        await self._emit_event(
            "workflow_completed",
            {
                "instance_id": instance_id,
                "template_id": instance.template_id,
                "completed_at": instance.completed_at,
                "duration_minutes": (
                    instance.completed_at - instance.started_at
                ).total_seconds()
                / 60,
            },
        )

    async def _fail_workflow(self, instance_id: str, error_message: str) -> None:
        """Fail workflow instance."""
        instance = self.instances.get(instance_id)
        if not instance:
            return

        instance.status = WorkflowStatus.FAILED
        instance.error_message = error_message
        instance.completed_at = datetime.now()

        # Remove from running instances
        self.running_instances.discard(instance_id)

        # Cancel any pending tasks
        self._cancel_instance_tasks(instance_id)

        # Emit failure event
        await self._emit_event(
            "workflow_failed",
            {
                "instance_id": instance_id,
                "template_id": instance.template_id,
                "error_message": error_message,
                "failed_at": instance.completed_at,
            },
        )

    def _cancel_step_timeout(self, instance_id: str, step_id: str) -> None:
        """Cancel step timeout task."""
        task_key = f"{instance_id}_{step_id}_timeout"
        task = self.scheduled_tasks.get(task_key)
        if task and not task.done():
            task.cancel()
            del self.scheduled_tasks[task_key]

    async def _cancel_step_approvals(
        self, instance: WorkflowInstance, step_id: str
    ) -> None:
        """Cancel pending approvals for step."""
        approvals_to_cancel = [
            approval_id
            for approval_id, approval in instance.active_approvals.items()
            if approval.step_id == step_id
        ]

        for approval_id in approvals_to_cancel:
            approval = instance.active_approvals[approval_id]
            approval.action_type = ApprovalStatus.CANCELLED
            instance.action_history.append(approval)
            del instance.active_approvals[approval_id]

    def _cancel_instance_tasks(self, instance_id: str) -> None:
        """Cancel all tasks for workflow instance."""
        tasks_to_cancel = [
            task_key
            for task_key in self.scheduled_tasks.keys()
            if task_key.startswith(instance_id)
        ]

        for task_key in tasks_to_cancel:
            task = self.scheduled_tasks[task_key]
            if not task.done():
                task.cancel()
            del self.scheduled_tasks[task_key]

    def _user_has_allowed_role(self, user_id: str, allowed_roles: Set[str]) -> bool:
        """Check if user has any of the allowed roles."""
        # Implementation would check user roles from auth system
        return True  # Simplified for now

    def _get_users_with_role(self, role: str) -> List[str]:
        """Get users with specified role."""
        # Implementation would query auth system for users with role
        return [f"user_with_{role}"]  # Simplified for now

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit workflow event."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                print(f"[Workflow] Event handler error: {e}")

    def register_event_handler(self, event_type: str, handler: callable) -> None:
        """Register workflow event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow instance status."""
        instance = self.instances.get(instance_id)
        if not instance:
            return None

        template = self.templates.get(instance.template_id)
        current_step = None
        if template and instance.current_step_index < len(template.steps):
            current_step = template.steps[instance.current_step_index]

        return {
            "instance_id": instance_id,
            "template_id": instance.template_id,
            "title": instance.title,
            "status": instance.status,
            "current_step": current_step.name if current_step else "Completed",
            "progress": {
                "completed_steps": len(instance.completed_steps),
                "total_steps": len(template.steps) if template else 0,
                "percentage": (
                    len(instance.completed_steps) / len(template.steps) * 100
                )
                if template and template.steps
                else 100,
            },
            "active_approvals": len(instance.active_approvals),
            "current_approvers": list(instance.current_approvers),
            "started_at": instance.started_at.isoformat(),
            "deadline": instance.deadline.isoformat() if instance.deadline else None,
            "escalation_count": len(instance.escalation_history),
            "last_action": instance.action_history[-1].dict()
            if instance.action_history
            else None,
        }

    def get_user_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending approvals for user."""
        pending_approvals = []

        for instance in self.instances.values():
            if instance.status != WorkflowStatus.RUNNING:
                continue

            for approval in instance.active_approvals.values():
                if (
                    approval.approver_id == user_id
                    and approval.action_type == ApprovalStatus.PENDING
                ):
                    template = self.templates.get(instance.template_id)

                    pending_approvals.append(
                        {
                            "approval_id": approval.action_id,
                            "instance_id": instance.instance_id,
                            "workflow_name": template.name if template else "Unknown",
                            "title": instance.title,
                            "step_name": approval.step_id,
                            "entity_type": instance.entity_type,
                            "entity_id": instance.entity_id,
                            "priority": instance.priority,
                            "created_at": approval.created_at.isoformat(),
                            "deadline": approval.deadline.isoformat()
                            if approval.deadline
                            else None,
                            "entity_data": instance.entity_data,
                        }
                    )

        # Sort by priority and deadline
        pending_approvals.sort(
            key=lambda x: (x["priority"], x["deadline"] or "9999-12-31")
        )
        return pending_approvals
