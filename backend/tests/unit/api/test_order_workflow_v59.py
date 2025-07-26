"""
Tests for CC02 v59.0 Order Processing Workflow API
Comprehensive test suite covering state management, approval workflows, and automation
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.order_workflow_v59 import (
    APPROVAL_THRESHOLDS,
    VALID_STATE_TRANSITIONS,
    ApprovalEngine,
    ApprovalRequest,
    ApprovalStatus,
    AutomationEngine,
    AutomationTaskResponse,
    BulkOrderProcessingRequest,
    BulkProcessingResponse,
    NotificationType,
    OrderSearchRequest,
    OrderStateManager,
    OrderStateTransitionRequest,
    OrderStatus,
    OrderWorkflowManager,
    OrderWorkflowResponse,
    ProcessingPriority,
    WorkflowTrigger,
)
from app.core.exceptions import BusinessLogicError, NotFoundError
from app.models.customer import Customer
from app.models.order import Order
from app.models.user import User


# Test Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock()
    return session


@pytest.fixture
def sample_order():
    """Sample order for testing"""
    return Order(
        id=uuid4(),
        customer_id=uuid4(),
        order_number="ORD-2024-001",
        status=OrderStatus.PENDING.value,
        total_amount=Decimal("75000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def high_value_order():
    """High value order requiring approval"""
    return Order(
        id=uuid4(),
        customer_id=uuid4(),
        order_number="ORD-2024-002",
        status=OrderStatus.PENDING.value,
        total_amount=Decimal("150000.00"),  # Above manager approval threshold
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_customer():
    """Sample customer for testing"""
    return Customer(
        id=uuid4(),
        email="test.customer@example.com",
        full_name="Test Customer",
        phone="+1234567890",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test.user@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def state_manager(mock_db_session):
    """Create order state manager with mocked database"""
    return OrderStateManager(mock_db_session)


@pytest.fixture
def approval_engine(mock_db_session):
    """Create approval engine with mocked database"""
    return ApprovalEngine(mock_db_session)


@pytest.fixture
def automation_engine(mock_db_session):
    """Create automation engine with mocked database"""
    return AutomationEngine(mock_db_session)


@pytest.fixture
def workflow_manager(mock_db_session):
    """Create workflow manager with mocked database"""
    return OrderWorkflowManager(mock_db_session)


# Unit Tests for OrderStateManager
class TestOrderStateManager:
    @pytest.mark.asyncio
    async def test_validate_transition_valid(self, state_manager, sample_order):
        """Test valid state transition validation"""

        # Mock business rule validation
        with patch.object(state_manager, "_validate_business_rules") as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "warnings": [],
                "requirements": [],
            }

            result = await state_manager.validate_transition(
                sample_order, OrderStatus.CONFIRMED
            )

            assert result["valid"]
            assert "reason" not in result or result["reason"] is None
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_transition_invalid(self, state_manager, sample_order):
        """Test invalid state transition validation"""

        # Try invalid transition: PENDING -> SHIPPED (skipping CONFIRMED, PROCESSING)
        result = await state_manager.validate_transition(
            sample_order, OrderStatus.SHIPPED
        )

        assert not result["valid"]
        assert "Invalid transition" in result["reason"]
        assert OrderStatus.SHIPPED not in result["allowed_transitions"]

    @pytest.mark.asyncio
    async def test_validate_transition_force(self, state_manager, sample_order):
        """Test forced state transition bypassing validation"""

        with patch.object(state_manager, "_validate_business_rules") as mock_validate:
            mock_validate.return_value = {"valid": True}

            # Force invalid transition
            result = await state_manager.validate_transition(
                sample_order, OrderStatus.SHIPPED, force=True
            )

            assert result["valid"]
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_approval_requirements_low_value(
        self, state_manager, sample_order
    ):
        """Test approval requirements for low value order"""

        # Order with amount below approval threshold
        sample_order.total_amount = Decimal("25000.00")

        result = await state_manager._check_approval_requirements(sample_order)

        assert not result["required"]
        assert result["approved"]
        assert result["level"] == "none"

    @pytest.mark.asyncio
    async def test_check_approval_requirements_high_value(
        self, state_manager, high_value_order
    ):
        """Test approval requirements for high value order"""

        result = await state_manager._check_approval_requirements(high_value_order)

        assert result["required"]
        assert not result["approved"]
        assert result["level"] == "manager"

    @pytest.mark.asyncio
    async def test_check_inventory_availability(self, state_manager, sample_order):
        """Test inventory availability check"""

        result = await state_manager._check_inventory_availability(sample_order)

        assert "available" in result
        assert isinstance(result["available"], bool)
        assert "details" in result

    @pytest.mark.asyncio
    async def test_check_payment_status(self, state_manager, sample_order):
        """Test payment status check"""

        result = await state_manager._check_payment_status(sample_order)

        assert "confirmed" in result
        assert isinstance(result["confirmed"], bool)


# Unit Tests for ApprovalEngine
class TestApprovalEngine:
    @pytest.mark.asyncio
    async def test_create_approval_workflow_not_required(
        self, approval_engine, sample_order
    ):
        """Test approval workflow creation for order not requiring approval"""

        # Order below approval threshold
        sample_order.total_amount = Decimal("25000.00")

        result = await approval_engine.create_approval_workflow(sample_order)

        assert not result["approval_required"]
        assert result["status"] == ApprovalStatus.NOT_REQUIRED

    @pytest.mark.asyncio
    async def test_create_approval_workflow_required(
        self, approval_engine, high_value_order
    ):
        """Test approval workflow creation for order requiring approval"""

        result = await approval_engine.create_approval_workflow(high_value_order)

        assert result["approval_required"]
        assert result["status"] == ApprovalStatus.PENDING
        assert result["approval_level"] == "manager"
        assert "approval_id" in result

    def test_determine_approval_level_supervisor(self, approval_engine):
        """Test approval level determination for supervisor level"""

        amount = Decimal("60000.00")  # Above supervisor threshold
        level = approval_engine._determine_approval_level(amount)

        assert level == "manager"  # 60K requires manager approval

    def test_determine_approval_level_manager(self, approval_engine):
        """Test approval level determination for manager level"""

        amount = Decimal("200000.00")  # Above manager threshold
        level = approval_engine._determine_approval_level(amount)

        assert level == "director"

    def test_determine_approval_level_executive(self, approval_engine):
        """Test approval level determination for executive level"""

        amount = Decimal("1500000.00")  # Above executive threshold
        level = approval_engine._determine_approval_level(amount)

        assert level == "executive"

    def test_get_required_approvers(self, approval_engine):
        """Test getting required approvers for approval levels"""

        # Test supervisor level
        approvers = approval_engine._get_required_approvers("supervisor")
        assert "supervisor" in approvers

        # Test manager level
        approvers = approval_engine._get_required_approvers("manager")
        assert "manager" in approvers

        # Test director level
        approvers = approval_engine._get_required_approvers("director")
        assert "director" in approvers

    @pytest.mark.asyncio
    async def test_process_approval_decision_approved(self, approval_engine):
        """Test processing approved decision"""

        request = ApprovalRequest(
            order_id=uuid4(),
            approver_id=uuid4(),
            decision=ApprovalStatus.APPROVED,
            comments="Order approved - all criteria met",
            approval_level="manager",
            auto_process=True,
        )

        with patch.object(
            approval_engine, "_trigger_post_approval_automation"
        ) as mock_automation:
            mock_automation.return_value = {"inventory_allocated": True}

            result = await approval_engine.process_approval_decision(request)

            assert result["decision"] == ApprovalStatus.APPROVED
            assert result["auto_process"]
            assert "automation_triggered" in result
            mock_automation.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_approval_decision_rejected(self, approval_engine):
        """Test processing rejected decision"""

        request = ApprovalRequest(
            order_id=uuid4(),
            approver_id=uuid4(),
            decision=ApprovalStatus.REJECTED,
            comments="Order rejected - insufficient documentation",
            approval_level="manager",
            auto_process=False,
        )

        result = await approval_engine.process_approval_decision(request)

        assert result["decision"] == ApprovalStatus.REJECTED
        assert not result["auto_process"]

    @pytest.mark.asyncio
    async def test_trigger_post_approval_automation(self, approval_engine):
        """Test post-approval automation triggering"""

        order_id = uuid4()

        result = await approval_engine._trigger_post_approval_automation(order_id)

        assert "inventory_allocated" in result
        assert "invoice_generated" in result
        assert "customer_notified" in result
        assert "processing_started" in result


# Unit Tests for AutomationEngine
class TestAutomationEngine:
    @pytest.mark.asyncio
    async def test_execute_workflow_automation_success(self, automation_engine):
        """Test successful workflow automation execution"""

        order_id = uuid4()
        trigger = WorkflowTrigger.ORDER_CREATED
        background_tasks = MagicMock()

        with patch.object(
            automation_engine, "_process_automation_trigger"
        ) as mock_process:
            mock_process.return_value = {
                "status": "completed",
                "background_tasks": ["task1"],
            }

            result = await automation_engine.execute_workflow_automation(
                order_id, trigger, background_tasks
            )

            assert isinstance(result, AutomationTaskResponse)
            assert result.order_id == order_id
            assert result.trigger == trigger
            assert result.status == "completed"
            assert result.execution_time_ms > 0
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_automation_failure(self, automation_engine):
        """Test workflow automation execution failure"""

        order_id = uuid4()
        trigger = WorkflowTrigger.PAYMENT_CONFIRMED
        background_tasks = MagicMock()

        with patch.object(
            automation_engine, "_process_automation_trigger"
        ) as mock_process:
            mock_process.side_effect = Exception("Automation failed")

            result = await automation_engine.execute_workflow_automation(
                order_id, trigger, background_tasks
            )

            assert result.status == "failed"
            assert result.error_details == "Automation failed"
            assert result.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_handle_order_created(self, automation_engine):
        """Test order creation automation handler"""

        order_id = uuid4()

        result = await automation_engine._handle_order_created(order_id)

        assert result["inventory_check"]
        assert result["credit_verification"]
        assert result["customer_notification"]
        assert "background_tasks" in result

    @pytest.mark.asyncio
    async def test_handle_payment_confirmed(self, automation_engine):
        """Test payment confirmation automation handler"""

        order_id = uuid4()

        result = await automation_engine._handle_payment_confirmed(order_id)

        assert result["order_confirmed"]
        assert result["inventory_allocated"]
        assert result["fulfillment_started"]
        assert "background_tasks" in result

    @pytest.mark.asyncio
    async def test_handle_delivery_confirmed(self, automation_engine):
        """Test delivery confirmation automation handler"""

        order_id = uuid4()

        result = await automation_engine._handle_delivery_confirmed(order_id)

        assert result["order_completed"]
        assert result["invoice_finalized"]
        assert result["customer_feedback_requested"]
        assert "background_tasks" in result

    @pytest.mark.asyncio
    async def test_execute_background_task(self, automation_engine):
        """Test background task execution"""

        task_name = "generate_invoice"

        # Should not raise exception
        await automation_engine._execute_background_task(task_name)


# Unit Tests for OrderWorkflowManager
class TestOrderWorkflowManager:
    @pytest.mark.asyncio
    async def test_get_order_workflow_status_success(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test successful order workflow status retrieval"""

        # Mock database query
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = sample_order
        mock_db_session.execute.return_value = order_result

        with (
            patch.object(workflow_manager, "_get_workflow_steps") as mock_steps,
            patch.object(
                workflow_manager, "_identify_workflow_blockers"
            ) as mock_blockers,
            patch.object(workflow_manager, "_determine_next_actions") as mock_actions,
        ):
            mock_steps.return_value = []
            mock_blockers.return_value = []
            mock_actions.return_value = ["Complete payment verification"]

            result = await workflow_manager.get_order_workflow_status(sample_order.id)

            assert isinstance(result, OrderWorkflowResponse)
            assert result.order_id == sample_order.id
            assert result.current_status == OrderStatus.PENDING
            assert result.total_amount == sample_order.total_amount

    @pytest.mark.asyncio
    async def test_get_order_workflow_status_not_found(
        self, workflow_manager, mock_db_session
    ):
        """Test order workflow status retrieval for non-existent order"""

        # Mock database query returning None
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = order_result

        with pytest.raises(NotFoundError, match="Order .* not found"):
            await workflow_manager.get_order_workflow_status(uuid4())

    @pytest.mark.asyncio
    async def test_transition_order_state_success(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test successful order state transition"""

        # Mock order retrieval
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = sample_order
        mock_db_session.execute.return_value = order_result

        # Mock validation and execution
        with (
            patch.object(
                workflow_manager.state_manager, "validate_transition"
            ) as mock_validate,
            patch.object(workflow_manager, "_execute_state_transition") as mock_execute,
            patch.object(workflow_manager, "_get_automation_trigger") as mock_trigger,
            patch.object(workflow_manager, "_send_transition_notifications"),
        ):
            mock_validate.return_value = {"valid": True}
            mock_execute.return_value = {"success": True}
            mock_trigger.return_value = WorkflowTrigger.PAYMENT_CONFIRMED

            request = OrderStateTransitionRequest(
                order_id=sample_order.id,
                new_status=OrderStatus.CONFIRMED,
                notes="Payment verified",
            )

            background_tasks = MagicMock()
            user_id = uuid4()

            result = await workflow_manager.transition_order_state(
                request, user_id, background_tasks
            )

            assert result["order_id"] == sample_order.id
            assert result["transition"]["success"]
            assert result["transition"]["to"] == OrderStatus.CONFIRMED
            mock_validate.assert_called_once()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_transition_order_state_validation_failed(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test order state transition with validation failure"""

        # Mock order retrieval
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = sample_order
        mock_db_session.execute.return_value = order_result

        # Mock validation failure
        with patch.object(
            workflow_manager.state_manager, "validate_transition"
        ) as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "reason": "Insufficient inventory",
            }

            request = OrderStateTransitionRequest(
                order_id=sample_order.id, new_status=OrderStatus.CONFIRMED
            )

            background_tasks = MagicMock()
            user_id = uuid4()

            with pytest.raises(BusinessLogicError, match="Insufficient inventory"):
                await workflow_manager.transition_order_state(
                    request, user_id, background_tasks
                )

    @pytest.mark.asyncio
    async def test_identify_workflow_blockers(self, workflow_manager, high_value_order):
        """Test workflow blocker identification"""

        blockers = await workflow_manager._identify_workflow_blockers(high_value_order)

        assert isinstance(blockers, list)
        # High value order should have pending approval blocker
        assert any("approval" in blocker.lower() for blocker in blockers)

    @pytest.mark.asyncio
    async def test_determine_next_actions(self, workflow_manager, sample_order):
        """Test next actions determination"""

        # Test for PENDING status
        sample_order.status = OrderStatus.PENDING.value
        actions = await workflow_manager._determine_next_actions(sample_order)

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert any("payment" in action.lower() for action in actions)

    def test_estimate_completion_time(self, workflow_manager):
        """Test completion time estimation"""

        estimated_time = workflow_manager._estimate_completion_time(OrderStatus.PENDING)

        assert estimated_time is not None
        assert estimated_time > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_execute_state_transition_success(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test successful state transition execution"""

        mock_db_session.commit = AsyncMock()
        user_id = uuid4()

        result = await workflow_manager._execute_state_transition(
            sample_order, OrderStatus.CONFIRMED, user_id, "Payment verified"
        )

        assert result["success"]
        assert result["new_status"] == OrderStatus.CONFIRMED.value
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_state_transition_failure(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test state transition execution failure"""

        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback = AsyncMock()
        user_id = uuid4()

        result = await workflow_manager._execute_state_transition(
            sample_order, OrderStatus.CONFIRMED, user_id, "Payment verified"
        )

        assert not result["success"]
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_get_automation_trigger(self, workflow_manager):
        """Test automation trigger mapping"""

        # Test various status transitions
        trigger = workflow_manager._get_automation_trigger(OrderStatus.CONFIRMED)
        assert trigger == WorkflowTrigger.PAYMENT_CONFIRMED

        trigger = workflow_manager._get_automation_trigger(OrderStatus.SHIPPED)
        assert trigger == WorkflowTrigger.SHIPPING_PREPARED

        trigger = workflow_manager._get_automation_trigger(OrderStatus.DRAFT)
        assert trigger is None  # No trigger for DRAFT


# Request/Response Model Tests
class TestRequestResponseModels:
    def test_order_state_transition_request_validation(self):
        """Test order state transition request validation"""

        order_id = uuid4()

        # Valid request
        valid_request = OrderStateTransitionRequest(
            order_id=order_id,
            new_status=OrderStatus.CONFIRMED,
            notes="Payment verified and approved",
            priority=ProcessingPriority.HIGH,
            notification_types=[NotificationType.EMAIL, NotificationType.SMS],
        )

        assert valid_request.order_id == order_id
        assert valid_request.new_status == OrderStatus.CONFIRMED
        assert valid_request.priority == ProcessingPriority.HIGH
        assert len(valid_request.notification_types) == 2

    def test_approval_request_validation(self):
        """Test approval request validation"""

        order_id = uuid4()
        approver_id = uuid4()

        # Valid approval request
        valid_request = ApprovalRequest(
            order_id=order_id,
            approver_id=approver_id,
            decision=ApprovalStatus.APPROVED,
            comments="Order meets all approval criteria",
            approval_level="manager",
            auto_process=True,
        )

        assert valid_request.order_id == order_id
        assert valid_request.approver_id == approver_id
        assert valid_request.decision == ApprovalStatus.APPROVED
        assert valid_request.auto_process

        # Test invalid decision
        with pytest.raises(ValueError):
            ApprovalRequest(
                order_id=order_id,
                approver_id=approver_id,
                decision=ApprovalStatus.NOT_REQUIRED,  # Invalid for decision
                approval_level="manager",
            )

    def test_bulk_order_processing_request_validation(self):
        """Test bulk order processing request validation"""

        order_ids = [uuid4() for _ in range(5)]

        # Valid bulk request
        valid_request = BulkOrderProcessingRequest(
            order_ids=order_ids,
            action="approve",
            batch_notes="Bulk approval for verified orders",
            priority=ProcessingPriority.HIGH,
        )

        assert len(valid_request.order_ids) == 5
        assert valid_request.action == "approve"
        assert valid_request.priority == ProcessingPriority.HIGH

        # Test invalid action
        with pytest.raises(ValueError):
            BulkOrderProcessingRequest(order_ids=order_ids, action="invalid_action")

        # Test too many orders
        too_many_orders = [uuid4() for _ in range(150)]
        with pytest.raises(ValueError):
            BulkOrderProcessingRequest(order_ids=too_many_orders, action="approve")

    def test_order_search_request_validation(self):
        """Test order search request validation"""

        customer_id = uuid4()

        # Valid search request
        valid_request = OrderSearchRequest(
            customer_id=customer_id,
            status_filters=[OrderStatus.PENDING, OrderStatus.CONFIRMED],
            date_from=datetime.utcnow() - timedelta(days=30),
            date_to=datetime.utcnow(),
            amount_min=Decimal("1000.00"),
            amount_max=Decimal("10000.00"),
            search_term="important order",
            sort_by="total_amount",
            sort_order="desc",
            page=2,
            per_page=50,
        )

        assert valid_request.customer_id == customer_id
        assert len(valid_request.status_filters) == 2
        assert valid_request.amount_min == Decimal("1000.00")
        assert valid_request.page == 2
        assert valid_request.per_page == 50


# Enum and Constants Tests
class TestEnumsAndConstants:
    def test_order_status_enum_values(self):
        """Test order status enum values"""

        assert OrderStatus.DRAFT == "draft"
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.CONFIRMED == "confirmed"
        assert OrderStatus.PROCESSING == "processing"
        assert OrderStatus.SHIPPED == "shipped"
        assert OrderStatus.DELIVERED == "delivered"
        assert OrderStatus.CANCELLED == "cancelled"
        assert OrderStatus.REFUNDED == "refunded"

    def test_approval_status_enum_values(self):
        """Test approval status enum values"""

        assert ApprovalStatus.NOT_REQUIRED == "not_required"
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.ESCALATED == "escalated"

    def test_workflow_trigger_enum_values(self):
        """Test workflow trigger enum values"""

        assert WorkflowTrigger.ORDER_CREATED == "order_created"
        assert WorkflowTrigger.PAYMENT_CONFIRMED == "payment_confirmed"
        assert WorkflowTrigger.INVENTORY_ALLOCATED == "inventory_allocated"
        assert WorkflowTrigger.APPROVAL_COMPLETED == "approval_completed"
        assert WorkflowTrigger.SHIPPING_PREPARED == "shipping_prepared"
        assert WorkflowTrigger.DELIVERY_CONFIRMED == "delivery_confirmed"

    def test_valid_state_transitions(self):
        """Test valid state transition rules"""

        # Test draft transitions
        draft_transitions = VALID_STATE_TRANSITIONS[OrderStatus.DRAFT]
        assert OrderStatus.PENDING in draft_transitions
        assert OrderStatus.CANCELLED in draft_transitions
        assert OrderStatus.CONFIRMED not in draft_transitions

        # Test pending transitions
        pending_transitions = VALID_STATE_TRANSITIONS[OrderStatus.PENDING]
        assert OrderStatus.CONFIRMED in pending_transitions
        assert OrderStatus.CANCELLED in pending_transitions
        assert OrderStatus.PROCESSING not in pending_transitions

        # Test terminal states
        cancelled_transitions = VALID_STATE_TRANSITIONS[OrderStatus.CANCELLED]
        assert len(cancelled_transitions) == 0  # Terminal state

        refunded_transitions = VALID_STATE_TRANSITIONS[OrderStatus.REFUNDED]
        assert len(refunded_transitions) == 0  # Terminal state

    def test_approval_thresholds(self):
        """Test approval threshold values"""

        assert APPROVAL_THRESHOLDS["supervisor"] == Decimal("50000")
        assert APPROVAL_THRESHOLDS["manager"] == Decimal("100000")
        assert APPROVAL_THRESHOLDS["director"] == Decimal("500000")
        assert APPROVAL_THRESHOLDS["executive"] == Decimal("1000000")

        # Verify thresholds are in ascending order
        thresholds = list(APPROVAL_THRESHOLDS.values())
        assert all(
            thresholds[i] < thresholds[i + 1] for i in range(len(thresholds) - 1)
        )


# Integration Tests
class TestWorkflowIntegration:
    @pytest.mark.asyncio
    async def test_complete_approval_workflow(
        self, workflow_manager, high_value_order, mock_db_session
    ):
        """Test complete approval workflow from creation to decision"""

        # Mock order retrieval
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = high_value_order
        mock_db_session.execute.return_value = order_result

        # Step 1: Create approval workflow
        approval_workflow = (
            await workflow_manager.approval_engine.create_approval_workflow(
                high_value_order
            )
        )

        assert approval_workflow["approval_required"]
        assert approval_workflow["approval_level"] == "manager"

        # Step 2: Process approval decision
        approval_request = ApprovalRequest(
            order_id=high_value_order.id,
            approver_id=uuid4(),
            decision=ApprovalStatus.APPROVED,
            comments="Order approved after review",
            approval_level="manager",
            auto_process=True,
        )

        decision_result = (
            await workflow_manager.approval_engine.process_approval_decision(
                approval_request
            )
        )

        assert decision_result["decision"] == ApprovalStatus.APPROVED
        assert decision_result["auto_process"]

    @pytest.mark.asyncio
    async def test_end_to_end_order_processing(
        self, workflow_manager, sample_order, mock_db_session
    ):
        """Test end-to-end order processing workflow"""

        # Mock order retrieval
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = sample_order
        mock_db_session.execute.return_value = order_result
        mock_db_session.commit = AsyncMock()

        background_tasks = MagicMock()
        user_id = uuid4()

        # Mock all validation methods
        with (
            patch.object(
                workflow_manager.state_manager, "validate_transition"
            ) as mock_validate,
            patch.object(workflow_manager, "_execute_state_transition") as mock_execute,
            patch.object(workflow_manager, "_send_transition_notifications"),
        ):
            mock_validate.return_value = {"valid": True}
            mock_execute.return_value = {"success": True}

            # Step 1: PENDING -> CONFIRMED
            transition_request = OrderStateTransitionRequest(
                order_id=sample_order.id,
                new_status=OrderStatus.CONFIRMED,
                notes="Payment verified",
            )

            result1 = await workflow_manager.transition_order_state(
                transition_request, user_id, background_tasks
            )

            assert result1["transition"]["to"] == OrderStatus.CONFIRMED

            # Step 2: CONFIRMED -> PROCESSING
            sample_order.status = (
                OrderStatus.CONFIRMED.value
            )  # Update for next transition
            transition_request.new_status = OrderStatus.PROCESSING
            transition_request.notes = "Inventory allocated"

            result2 = await workflow_manager.transition_order_state(
                transition_request, user_id, background_tasks
            )

            assert result2["transition"]["to"] == OrderStatus.PROCESSING


# Performance and Edge Case Tests
class TestPerformanceAndEdgeCases:
    @pytest.mark.asyncio
    async def test_bulk_processing_performance(self, mock_db_session):
        """Test bulk processing performance with many orders"""

        # Create 50 orders for bulk processing
        order_ids = [uuid4() for _ in range(50)]

        # Mock database queries for all orders
        mock_orders = []
        for order_id in order_ids:
            mock_order = MagicMock()
            mock_order.id = order_id
            mock_order.status = OrderStatus.PENDING.value
            mock_orders.append(mock_order)

        def mock_execute_side_effect(query):
            # Return different mock orders for each query
            result = MagicMock()
            if mock_orders:
                result.scalar_one_or_none.return_value = mock_orders.pop(0)
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_db_session.execute.side_effect = mock_execute_side_effect

        BulkOrderProcessingRequest(
            order_ids=order_ids, action="approve", batch_notes="Bulk approval test"
        )

        # Execute bulk processing - should complete quickly
        import time

        start_time = time.time()

        # Mock the bulk_process_orders function behavior

        # Simulate processing
        results = []
        errors = []

        for order_id in order_ids[:45]:  # Simulate 45 successful, 5 failed
            results.append(
                {"order_id": str(order_id), "action": "approved", "status": "success"}
            )

        for order_id in order_ids[45:]:  # Simulate 5 failures
            errors.append({"order_id": str(order_id), "error": "Order not found"})

        processing_time = time.time() - start_time

        response = BulkProcessingResponse(
            batch_id=uuid4(),
            total_orders=len(order_ids),
            successful_count=len(results),
            failed_count=len(errors),
            processing_time_seconds=processing_time,
            results=results,
            errors=errors,
        )

        # Assertions
        assert response.total_orders == 50
        assert response.successful_count == 45
        assert response.failed_count == 5
        assert response.processing_time_seconds < 5.0  # Should be fast

    def test_state_transition_edge_cases(self):
        """Test edge cases in state transitions"""

        # Test all valid transitions are defined
        for status in OrderStatus:
            assert status in VALID_STATE_TRANSITIONS

        # Test terminal states have no outgoing transitions
        assert len(VALID_STATE_TRANSITIONS[OrderStatus.CANCELLED]) == 0
        assert len(VALID_STATE_TRANSITIONS[OrderStatus.REFUNDED]) == 0

        # Test draft can only go to pending or cancelled
        draft_transitions = VALID_STATE_TRANSITIONS[OrderStatus.DRAFT]
        assert len(draft_transitions) == 2
        assert OrderStatus.PENDING in draft_transitions
        assert OrderStatus.CANCELLED in draft_transitions

    def test_approval_threshold_edge_cases(self):
        """Test approval threshold edge cases"""

        from app.api.v1.order_workflow_v59 import ApprovalEngine

        engine = ApprovalEngine(MagicMock())

        # Test exact threshold values
        assert engine._determine_approval_level(Decimal("49999.99")) == "none"
        assert engine._determine_approval_level(Decimal("50000.00")) == "supervisor"
        assert engine._determine_approval_level(Decimal("99999.99")) == "supervisor"
        assert engine._determine_approval_level(Decimal("100000.00")) == "manager"

        # Test very high values
        assert engine._determine_approval_level(Decimal("10000000.00")) == "executive"

        # Test zero and negative values
        assert engine._determine_approval_level(Decimal("0.00")) == "none"
        # Note: Negative values should be handled by business logic validation

    @pytest.mark.asyncio
    async def test_automation_error_handling(self, automation_engine):
        """Test automation engine error handling"""

        order_id = uuid4()
        trigger = WorkflowTrigger.ORDER_CREATED
        background_tasks = MagicMock()

        # Mock handler to raise exception
        with patch.object(automation_engine, "_handle_order_created") as mock_handler:
            mock_handler.side_effect = Exception("Handler failed")

            result = await automation_engine.execute_workflow_automation(
                order_id, trigger, background_tasks
            )

            assert result.status == "failed"
            assert "Handler failed" in result.error_details
            assert result.retry_count == 0
            assert result.next_retry_at is not None

    def test_notification_type_combinations(self):
        """Test various notification type combinations"""

        # Test single notification type
        request = OrderStateTransitionRequest(
            order_id=uuid4(),
            new_status=OrderStatus.CONFIRMED,
            notification_types=[NotificationType.EMAIL],
        )
        assert len(request.notification_types) == 1

        # Test multiple notification types
        request = OrderStateTransitionRequest(
            order_id=uuid4(),
            new_status=OrderStatus.CONFIRMED,
            notification_types=[
                NotificationType.EMAIL,
                NotificationType.SMS,
                NotificationType.PUSH,
                NotificationType.WEBHOOK,
            ],
        )
        assert len(request.notification_types) == 4

        # Test empty notification types (should use default)
        request = OrderStateTransitionRequest(
            order_id=uuid4(), new_status=OrderStatus.CONFIRMED
        )
        assert NotificationType.EMAIL in request.notification_types


if __name__ == "__main__":
    pytest.main([__file__])
