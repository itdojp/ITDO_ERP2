"""
Expense API endpoints for Phase 4 Financial Management - Expense Settlement Workflow.
経費精算ワークフローAPIエンドポイント（財務管理機能Phase 4）
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
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
from app.services.expense_service import ExpenseService

router = APIRouter()


@router.get("/", response_model=ExpenseListResponse)
async def get_expenses(
    employee_id: Optional[int] = Query(None, description="Filter by employee"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    expense_category_id: Optional[int] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[str] = Query(None, description="Date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date to (YYYY-MM-DD)"),
    search_text: Optional[str] = Query(None, description="Search in title/description"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseListResponse:
    """Get expenses with filtering and pagination."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    # Create search filters
    filters = ExpenseSearch(
        employee_id=employee_id,
        project_id=project_id,
        expense_category_id=expense_category_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        search_text=search_text,
    )

    return await service.get_expenses(
        organization_id=current_user.organization_id,
        filters=filters,
        skip=skip,
        limit=limit,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Get expense by ID."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)
    expense = await service.get_expense_by_id(expense_id, current_user.organization_id)

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )

    return expense


@router.post("/", response_model=ExpenseResponse)
async def create_expense(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Create new expense entry."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        return await service.create_expense(
            expense_data=expense_data,
            organization_id=current_user.organization_id,
            employee_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Update expense (only if draft status)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        expense = await service.update_expense(
            expense_id=expense_id,
            expense_data=expense_data,
            organization_id=current_user.organization_id,
        )

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
            )

        return expense

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete expense (only if draft status)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        success = await service.delete_expense(
            expense_id=expense_id,
            organization_id=current_user.organization_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
            )

        return {"message": "Expense deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{expense_id}/submit", response_model=ExpenseResponse)
async def submit_expense(
    expense_id: int,
    submission_data: ExpenseSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Submit expense for approval workflow."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        return await service.submit_expense(
            expense_id=expense_id,
            submission_data=submission_data,
            organization_id=current_user.organization_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: int,
    approval_data: ExpenseApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Approve or reject expense in workflow."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        return await service.approve_expense(
            expense_id=expense_id,
            approval_data=approval_data,
            organization_id=current_user.organization_id,
            approver_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{expense_id}/payment", response_model=ExpenseResponse)
async def process_payment(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Process payment for approved expense."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    try:
        return await service.process_payment(
            expense_id=expense_id,
            organization_id=current_user.organization_id,
            processor_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{expense_id}/approvals", response_model=List[ExpenseApprovalFlowResponse])
async def get_approval_flows(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ExpenseApprovalFlowResponse]:
    """Get approval flows for expense."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)
    return await service.get_approval_flows(
        expense_id=expense_id,
        organization_id=current_user.organization_id,
    )


@router.get("/analytics/summary", response_model=ExpenseSummary)
async def get_expense_summary(
    employee_id: Optional[int] = Query(None, description="Filter by employee"),
    date_from: Optional[str] = Query(None, description="Date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date to (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseSummary:
    """Get expense summary analytics."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)
    return await service.get_expense_summary(
        organization_id=current_user.organization_id,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/my/pending-approvals", response_model=ExpenseListResponse)
async def get_my_pending_approvals(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseListResponse:
    """Get expenses pending approval by current user."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    # Get expenses where current user is an approver
    filters = ExpenseSearch(status="submitted")

    return await service.get_expenses(
        organization_id=current_user.organization_id,
        filters=filters,
        skip=skip,
        limit=limit,
    )


@router.get("/my/expenses", response_model=ExpenseListResponse)
async def get_my_expenses(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseListResponse:
    """Get current user's expenses."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = ExpenseService(db)

    filters = ExpenseSearch(
        employee_id=current_user.id,
        status=status,
    )

    return await service.get_expenses(
        organization_id=current_user.organization_id,
        filters=filters,
        skip=skip,
        limit=limit,
    )
