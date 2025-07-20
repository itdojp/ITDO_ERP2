"""
Expense Service for Phase 4 Financial Management - Expense Settlement Workflow.
経費精算ワークフローサービス（財務管理機能Phase 4）
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import Expense, ExpenseApprovalFlow, ExpenseStatus
from app.schemas.expense import (
    ExpenseApprovalAction,
    ExpenseApprovalFlowResponse,
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseSearch,
    ExpenseSubmission,
    ExpenseSummary,
    ExpenseUpdate,
)


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_expense(
        self, expense_data: ExpenseCreate, organization_id: int, employee_id: int
    ) -> ExpenseResponse:
        """Create new expense entry."""
        # Generate unique expense number
        expense_number = await self._generate_expense_number(organization_id)

        expense = Expense(
            organization_id=organization_id,
            employee_id=employee_id,
            expense_number=expense_number,
            **expense_data.model_dump(),
        )

        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)

        return ExpenseResponse.model_validate(expense)

    async def get_expenses(
        self,
        organization_id: int,
        filters: ExpenseSearch,
        skip: int = 0,
        limit: int = 100,
    ) -> ExpenseListResponse:
        """Get expenses with filtering and pagination."""
        query = (
            select(Expense)
            .where(
                and_(
                    Expense.organization_id == organization_id,
                    Expense.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Expense.employee),
                selectinload(Expense.expense_category),
                selectinload(Expense.project),
            )
        )

        # Apply filters
        if filters.employee_id:
            query = query.where(Expense.employee_id == filters.employee_id)

        if filters.project_id:
            query = query.where(Expense.project_id == filters.project_id)

        if filters.expense_category_id:
            query = query.where(
                Expense.expense_category_id == filters.expense_category_id
            )

        if filters.status:
            query = query.where(Expense.status == filters.status)

        if filters.date_from:
            query = query.where(Expense.expense_date >= filters.date_from)

        if filters.date_to:
            query = query.where(Expense.expense_date <= filters.date_to)

        if filters.amount_min:
            query = query.where(Expense.amount >= filters.amount_min)

        if filters.amount_max:
            query = query.where(Expense.amount <= filters.amount_max)

        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.where(
                or_(
                    Expense.title.ilike(search_pattern),
                    Expense.description.ilike(search_pattern),
                    Expense.vendor_name.ilike(search_pattern),
                )
            )

        # Count total
        count_query = select(func.count(Expense.id)).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(desc(Expense.expense_date), desc(Expense.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        expenses = result.scalars().all()

        page = (skip // limit) + 1

        return ExpenseListResponse(
            items=[ExpenseResponse.model_validate(expense) for expense in expenses],
            total=total,
            page=page,
            limit=limit,
            has_next=(skip + limit) < total,
            has_prev=skip > 0,
        )

    async def get_expense_by_id(
        self, expense_id: int, organization_id: int
    ) -> Optional[ExpenseResponse]:
        """Get expense by ID."""
        query = (
            select(Expense)
            .where(
                and_(
                    Expense.id == expense_id,
                    Expense.organization_id == organization_id,
                    Expense.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Expense.employee),
                selectinload(Expense.expense_category),
                selectinload(Expense.project),
                selectinload(Expense.approved_by_user),
                selectinload(Expense.paid_by_user),
            )
        )

        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()

        if expense:
            return ExpenseResponse.model_validate(expense)
        return None

    async def update_expense(
        self, expense_id: int, expense_data: ExpenseUpdate, organization_id: int
    ) -> Optional[ExpenseResponse]:
        """Update expense (only if draft status)."""
        query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()

        if not expense:
            return None

        # Only allow updates for draft expenses
        if expense.status != ExpenseStatus.DRAFT:
            raise ValueError("Can only update draft expenses")

        # Update fields
        for field, value in expense_data.model_dump(exclude_unset=True).items():
            setattr(expense, field, value)

        expense.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(expense)

        return ExpenseResponse.model_validate(expense)

    async def submit_expense(
        self,
        expense_id: int,
        submission_data: ExpenseSubmission,
        organization_id: int,
    ) -> ExpenseResponse:
        """Submit expense for approval workflow."""
        query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()

        if not expense:
            raise ValueError("Expense not found")

        if expense.status != ExpenseStatus.DRAFT:
            raise ValueError("Can only submit draft expenses")

        # Update status to submitted
        expense.status = ExpenseStatus.SUBMITTED
        expense.updated_at = datetime.utcnow()

        # Create approval flow based on expense amount
        await self._create_approval_flow(expense)

        await self.db.commit()
        await self.db.refresh(expense)

        return ExpenseResponse.model_validate(expense)

    async def approve_expense(
        self,
        expense_id: int,
        approval_data: ExpenseApprovalAction,
        organization_id: int,
        approver_id: int,
    ) -> ExpenseResponse:
        """Approve or reject expense in workflow."""
        # Get expense
        expense_query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        expense_result = await self.db.execute(expense_query)
        expense = expense_result.scalar_one_or_none()

        if not expense:
            raise ValueError("Expense not found")

        if expense.status != ExpenseStatus.SUBMITTED:
            raise ValueError("Can only approve submitted expenses")

        # Get pending approval for this approver
        flow_query = select(ExpenseApprovalFlow).where(
            and_(
                ExpenseApprovalFlow.expense_id == expense_id,
                ExpenseApprovalFlow.approver_id == approver_id,
                ExpenseApprovalFlow.approved_at.is_(None),
            )
        )

        flow_result = await self.db.execute(flow_query)
        approval_flow = flow_result.scalar_one_or_none()

        if not approval_flow:
            raise ValueError("No pending approval found for this user")

        if approval_data.action == "approve":
            # Approve this level
            approval_flow.approved_at = datetime.utcnow()
            approval_flow.comments = approval_data.comments

            # Check if all required approvals are complete
            all_flows_query = select(ExpenseApprovalFlow).where(
                and_(
                    ExpenseApprovalFlow.expense_id == expense_id,
                    ExpenseApprovalFlow.is_required,
                )
            )

            all_flows_result = await self.db.execute(all_flows_query)
            all_flows = all_flows_result.scalars().all()

            # Update approval flow first
            await self.db.commit()
            await self.db.refresh(approval_flow)

            # Re-fetch flows to check completion
            all_flows_result = await self.db.execute(all_flows_query)
            all_flows = all_flows_result.scalars().all()

            all_approved = all(flow.approved_at is not None for flow in all_flows)

            if all_approved:
                expense.status = ExpenseStatus.APPROVED
                expense.approved_by = approver_id
                expense.approved_at = datetime.utcnow()

        elif approval_data.action == "reject":
            # Reject expense
            expense.status = ExpenseStatus.REJECTED
            expense.rejected_reason = approval_data.comments
            expense.updated_at = datetime.utcnow()

            # Mark rejection in flow
            approval_flow.comments = approval_data.comments

        await self.db.commit()
        await self.db.refresh(expense)

        return ExpenseResponse.model_validate(expense)

    async def process_payment(
        self, expense_id: int, organization_id: int, processor_id: int
    ) -> ExpenseResponse:
        """Process payment for approved expense."""
        query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()

        if not expense:
            raise ValueError("Expense not found")

        if expense.status != ExpenseStatus.APPROVED:
            raise ValueError("Can only process payment for approved expenses")

        # Update payment status
        expense.status = ExpenseStatus.PAID
        expense.paid_at = datetime.utcnow()
        expense.paid_by = processor_id
        expense.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(expense)

        return ExpenseResponse.model_validate(expense)

    async def get_expense_summary(
        self,
        organization_id: int,
        employee_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> ExpenseSummary:
        """Get expense summary analytics."""
        # Base query
        query = select(Expense).where(
            and_(
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        # Apply filters
        if employee_id:
            query = query.where(Expense.employee_id == employee_id)

        if date_from:
            query = query.where(Expense.expense_date >= date_from)

        if date_to:
            query = query.where(Expense.expense_date <= date_to)

        result = await self.db.execute(query)
        expenses = result.scalars().all()

        # Calculate summary statistics
        total_expenses = len(expenses)
        total_amount = Decimal(str(sum(expense.amount for expense in expenses) or 0))

        pending_expenses = [e for e in expenses if e.status == ExpenseStatus.SUBMITTED]
        approved_expenses = [e for e in expenses if e.status == ExpenseStatus.APPROVED]
        rejected_expenses = [e for e in expenses if e.status == ExpenseStatus.REJECTED]
        paid_expenses = [e for e in expenses if e.status == ExpenseStatus.PAID]

        return ExpenseSummary(
            total_expenses=total_expenses,
            total_amount=total_amount,
            pending_approval_count=len(pending_expenses),
            pending_approval_amount=Decimal(str(sum(e.amount for e in pending_expenses) or 0)),
            approved_count=len(approved_expenses),
            approved_amount=Decimal(str(sum(e.amount for e in approved_expenses) or 0)),
            rejected_count=len(rejected_expenses),
            rejected_amount=Decimal(str(sum(e.amount for e in rejected_expenses) or 0)),
            paid_count=len(paid_expenses),
            paid_amount=Decimal(str(sum(e.amount for e in paid_expenses) or 0)),
        )

    async def _generate_expense_number(self, organization_id: int) -> str:
        """Generate unique expense number."""
        # Get current year and month
        now = datetime.utcnow()
        prefix = f"EXP{now.year:04d}{now.month:02d}"

        # Get latest number for this prefix
        query = select(func.max(Expense.expense_number)).where(
            and_(
                Expense.organization_id == organization_id,
                Expense.expense_number.like(f"{prefix}%"),
            )
        )

        result = await self.db.execute(query)
        latest_number = result.scalar()

        if latest_number:
            # Extract sequence number and increment
            sequence = int(latest_number[-4:]) + 1
        else:
            sequence = 1

        return f"{prefix}{sequence:04d}"

    async def _create_approval_flow(self, expense: Expense) -> None:
        """Create approval flow based on expense amount and organizational rules."""
        flows_to_create = []

        # Simple approval flow based on amount
        if expense.amount <= Decimal("10000"):
            # Under 10,000 JPY: Direct supervisor approval
            flows_to_create.append(
                ExpenseApprovalFlow(
                    expense_id=expense.id,
                    # Simplified: self-approval for demo
                    approver_id=expense.employee_id,
                    approval_level=1,
                    is_required=True,
                )
            )
        elif expense.amount <= Decimal("50000"):
            # 10,001 - 50,000 JPY: Department manager approval
            flows_to_create.extend(
                [
                    ExpenseApprovalFlow(
                        expense_id=expense.id,
                        approver_id=expense.employee_id,  # Simplified: Level 1
                        approval_level=1,
                        is_required=True,
                    ),
                    ExpenseApprovalFlow(
                        expense_id=expense.id,
                        approver_id=expense.employee_id,  # Simplified: Level 2
                        approval_level=2,
                        is_required=True,
                    ),
                ]
            )
        else:
            # Over 50,000 JPY: Executive approval required
            flows_to_create.extend(
                [
                    ExpenseApprovalFlow(
                        expense_id=expense.id,
                        approver_id=expense.employee_id,  # Simplified: Level 1
                        approval_level=1,
                        is_required=True,
                    ),
                    ExpenseApprovalFlow(
                        expense_id=expense.id,
                        approver_id=expense.employee_id,  # Simplified: Level 2
                        approval_level=2,
                        is_required=True,
                    ),
                    ExpenseApprovalFlow(
                        expense_id=expense.id,
                        approver_id=expense.employee_id,  # Simplified: Level 3
                        approval_level=3,
                        is_required=True,
                    ),
                ]
            )

        # Add flows to database
        for flow in flows_to_create:
            self.db.add(flow)

        await self.db.flush()

    async def get_approval_flows(
        self, expense_id: int, organization_id: int
    ) -> List[ExpenseApprovalFlowResponse]:
        """Get approval flows for expense."""
        # Verify expense belongs to organization
        expense_query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        expense_result = await self.db.execute(expense_query)
        expense = expense_result.scalar_one_or_none()

        if not expense:
            return []

        # Get approval flows
        flows_query = (
            select(ExpenseApprovalFlow)
            .where(ExpenseApprovalFlow.expense_id == expense_id)
            .options(selectinload(ExpenseApprovalFlow.approver))
            .order_by(ExpenseApprovalFlow.approval_level)
        )

        flows_result = await self.db.execute(flows_query)
        flows = flows_result.scalars().all()

        return [ExpenseApprovalFlowResponse.model_validate(flow) for flow in flows]

    async def delete_expense(self, expense_id: int, organization_id: int) -> bool:
        """Delete expense (only if draft status)."""
        query = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.organization_id == organization_id,
                Expense.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()

        if not expense:
            return False

        # Only allow deletion of draft expenses
        if expense.status != ExpenseStatus.DRAFT:
            raise ValueError("Can only delete draft expenses")

        # Soft delete
        expense.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True
