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
    """
    Retrieve expenses with comprehensive filtering and pagination capabilities.

    This endpoint provides advanced expense management functionality including:
    - Multi-criteria filtering (employee, project, category, status, date range)
    - Full-text search across expense titles and descriptions
    - Pagination support for large datasets
    - Workflow status tracking (draft, submitted, approved, rejected, paid)
    - Integration with approval workflows and payment processing

    **Query Parameters:**
    - `employee_id`: Filter by specific employee (useful for managers reviewing team expenses)
    - `project_id`: Filter by project assignment (for project-based expense tracking)
    - `expense_category_id`: Filter by expense category (travel, meals, office supplies, etc.)
    - `status`: Filter by workflow status (draft, submitted, approved, rejected, paid)
    - `date_from`: Start date for expense period (YYYY-MM-DD format)
    - `date_to`: End date for expense period (YYYY-MM-DD format)
    - `search_text`: Full-text search in expense titles, descriptions, and vendor names
    - `skip`: Number of records to skip for pagination
    - `limit`: Maximum records to return (1-1000, default: 100)

    **Example Request:**
    ```
    GET /expenses/?status=submitted&date_from=2024-03-01&date_to=2024-03-31&limit=50
    ```

    **Response Example:**
    ```json
    {
        "expenses": [
            {
                "id": 1234,
                "expense_number": "EXP-2024-001234",
                "title": "Client Meeting - San Francisco",
                "description": "Travel expenses for client presentation",
                "amount": 850.00,
                "currency": "USD",
                "expense_date": "2024-03-15",
                "status": "approved",
                "employee": {
                    "id": 101,
                    "name": "John Smith",
                    "department": "Sales"
                },
                "category": {
                    "id": 5,
                    "name": "Travel",
                    "code": "TRAVEL"
                },
                "project": {
                    "id": 42,
                    "name": "Q1 Sales Initiative",
                    "code": "PROJ-042"
                },
                "receipts": [
                    {
                        "id": 789,
                        "filename": "airline_receipt.pdf",
                        "file_size": 245760,
                        "uploaded_at": "2024-03-15T14:30:00Z"
                    }
                ],
                "approval_status": {
                    "current_step": "approved",
                    "approved_by": "manager-456",
                    "approved_at": "2024-03-16T09:15:00Z",
                    "next_step": "payment_processing"
                },
                "created_at": "2024-03-15T10:00:00Z",
                "updated_at": "2024-03-16T09:15:00Z"
            }
        ],
        "pagination": {
            "total_count": 156,
            "current_page": 1,
            "total_pages": 4,
            "has_next": true,
            "has_previous": false
        },
        "summary": {
            "total_amount": 12750.00,
            "count_by_status": {
                "draft": 5,
                "submitted": 12,
                "approved": 28,
                "rejected": 2,
                "paid": 109
            },
            "average_amount": 81.73
        }
    }
    ```

    **Status Values:**
    - `draft`: Expense created but not submitted for approval
    - `submitted`: Expense submitted and awaiting approval
    - `approved`: Expense approved and ready for payment
    - `rejected`: Expense rejected and returned to employee
    - `paid`: Expense processed and payment completed

    **Error Responses:**
    - `400 Bad Request`: Invalid query parameters or date format
    - `401 Unauthorized`: Authentication required
    - `403 Forbidden`: Access denied to expense data
    - `422 Unprocessable Entity`: Parameter validation errors
    """
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
    """
    Create a new expense entry with comprehensive validation and workflow integration.

    This endpoint creates expense records with:
    - Automatic expense number generation
    - Multi-currency support with exchange rate validation
    - Receipt attachment handling
    - Project and cost center assignment
    - Policy compliance validation
    - Integration with approval workflows

    **Request Body Example:**
    ```json
    {
        "title": "Conference Registration - TechSummit 2024",
        "description": "Annual technology conference registration fee including workshops",
        "amount": 1200.00,
        "currency": "USD",
        "expense_date": "2024-03-20",
        "expense_category_id": 8,
        "project_id": 42,
        "vendor_name": "TechSummit Events LLC",
        "payment_method": "corporate_card",
        "business_purpose": "Professional development and industry networking",
        "attendees": [
            {
                "name": "John Smith",
                "role": "Senior Developer",
                "internal": true
            }
        ],
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "country": "USA"
        },
        "receipt_urls": [
            "https://storage.example.com/receipts/receipt_001.pdf"
        ],
        "custom_fields": {
            "cost_center": "TECH-DEV-001",
            "budget_line": "Training & Development",
            "approval_required": true
        }
    }
    ```

    **Response Example:**
    ```json
    {
        "id": 1357,
        "expense_number": "EXP-2024-001357",
        "title": "Conference Registration - TechSummit 2024",
        "description": "Annual technology conference registration fee including workshops",
        "amount": 1200.00,
        "currency": "USD",
        "expense_date": "2024-03-20",
        "status": "draft",
        "employee": {
            "id": 101,
            "name": "John Smith",
            "email": "john.smith@company.com",
            "department": "Technology"
        },
        "category": {
            "id": 8,
            "name": "Training & Development",
            "code": "TRAINING",
            "requires_receipt": true,
            "daily_limit": null
        },
        "project": {
            "id": 42,
            "name": "Q1 Development Initiative",
            "code": "PROJ-042",
            "budget_remaining": 15750.00
        },
        "vendor_name": "TechSummit Events LLC",
        "payment_method": "corporate_card",
        "business_purpose": "Professional development and industry networking",
        "policy_compliance": {
            "status": "compliant",
            "violations": [],
            "warnings": [
                "Amount exceeds $1000 - manager approval required"
            ]
        },
        "workflow_status": {
            "current_step": "draft",
            "can_edit": true,
            "can_submit": true,
            "required_approvers": [
                {
                    "level": 1,
                    "approver_id": "mgr-456",
                    "approver_name": "Sarah Johnson",
                    "role": "Department Manager"
                }
            ]
        },
        "created_at": "2024-03-20T16:30:00Z",
        "updated_at": "2024-03-20T16:30:00Z"
    }
    ```

    **Validation Rules:**
    - `title`: Required, 1-255 characters
    - `amount`: Required, positive decimal value
    - `expense_date`: Required, cannot be future date beyond policy limits
    - `expense_category_id`: Must exist and be active
    - `currency`: Must be supported currency code (ISO 4217)
    - `receipt_urls`: Required for categories marked as requiring receipts

    **Policy Validations:**
    - Daily spending limits per category
    - Receipt requirements for specific categories
    - Advance approval requirements for high-value expenses
    - Project budget availability checks
    - Geographic spending restrictions

    **Error Responses:**
    - `400 Bad Request`: Invalid expense data or policy violations
    - `401 Unauthorized`: Authentication required
    - `403 Forbidden`: Insufficient permissions to create expenses
    - `422 Unprocessable Entity`: Validation errors or missing required fields
    """
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
    """
    Submit an expense for approval workflow processing.

    This endpoint initiates the expense approval workflow with:
    - Pre-submission validation and policy compliance checks
    - Automatic approver assignment based on amount and category
    - Notification dispatch to relevant approvers
    - Audit trail creation for compliance tracking
    - Integration with organizational approval hierarchies

    **Path Parameters:**
    - `expense_id`: Unique identifier of the expense to submit

    **Request Body Example:**
    ```json
    {
        "submission_notes": "Urgent approval needed for upcoming conference attendance",
        "priority": "high",
        "requested_approval_date": "2024-03-22",
        "additional_documents": [
            {
                "type": "agenda",
                "url": "https://storage.example.com/docs/conference_agenda.pdf",
                "description": "Conference agenda showing relevant sessions"
            }
        ],
        "delegate_to": null,
        "notify_approvers": true
    }
    ```

    **Response Example:**
    ```json
    {
        "id": 1357,
        "expense_number": "EXP-2024-001357",
        "title": "Conference Registration - TechSummit 2024",
        "amount": 1200.00,
        "currency": "USD",
        "status": "submitted",
        "submission_info": {
            "submitted_at": "2024-03-20T17:45:00Z",
            "submitted_by": "John Smith",
            "submission_notes": "Urgent approval needed for upcoming conference attendance",
            "priority": "high",
            "requested_approval_date": "2024-03-22"
        },
        "approval_workflow": {
            "workflow_id": "wf-expense-std-001",
            "current_step": 1,
            "total_steps": 2,
            "current_approver": {
                "id": "mgr-456",
                "name": "Sarah Johnson",
                "role": "Department Manager",
                "email": "sarah.johnson@company.com",
                "notification_sent": true
            },
            "approval_deadline": "2024-03-25T17:00:00Z",
            "escalation_rules": {
                "escalate_after_hours": 48,
                "escalate_to": "vp-finance"
            }
        },
        "policy_compliance": {
            "status": "compliant",
            "pre_approval_required": false,
            "receipt_complete": true,
            "business_justification_adequate": true,
            "within_budget_limits": true
        },
        "next_actions": [
            {
                "action": "await_approval",
                "expected_by": "2024-03-22T17:00:00Z",
                "responsible_party": "Sarah Johnson"
            }
        ],
        "audit_trail": [
            {
                "action": "created",
                "timestamp": "2024-03-20T16:30:00Z",
                "user": "John Smith",
                "details": "Expense created"
            },
            {
                "action": "submitted",
                "timestamp": "2024-03-20T17:45:00Z",
                "user": "John Smith",
                "details": "Submitted for approval with high priority"
            }
        ]
    }
    ```

    **Submission Requirements:**
    - Expense must be in 'draft' status
    - All required fields must be completed
    - Receipt attachments required for applicable categories
    - Policy compliance validation must pass
    - User must have permission to submit expenses

    **Workflow Features:**
    - Automatic approver determination based on amount thresholds
    - Multi-level approval for high-value expenses
    - Parallel approval paths for cross-departmental expenses
    - Automatic escalation for overdue approvals
    - Integration with email and mobile notifications

    **Error Responses:**
    - `400 Bad Request`: Expense cannot be submitted (wrong status, validation failures)
    - `401 Unauthorized`: Authentication required
    - `403 Forbidden`: No permission to submit this expense
    - `404 Not Found`: Expense not found
    - `422 Unprocessable Entity`: Submission data validation errors
    """
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
