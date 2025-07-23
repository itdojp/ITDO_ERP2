"""
Project Management API - CC02 v31.0 Phase 2

Complete project management system with 10 comprehensive endpoints:
1. Project Management
2. Task Management
3. Resource Management
4. Time Tracking
5. Risk Management
6. Milestone Management
7. Issue Management
8. Portfolio Management
9. Template Management
10. Project Analytics
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.project_v31 import (
    approve_time_entry,
    calculate_project_health_score,
    create_portfolio,
    create_project,
    create_project_resource,
    create_project_risk,
    create_task,
    create_task_dependency,
    create_time_entry,
    delete_project,
    get_organization_project_summary,
    get_portfolios,
    get_project,
    get_project_dashboard_metrics,
    get_project_resources,
    get_project_risks,
    get_projects,
    get_task,
    get_tasks,
    get_time_entries,
    update_project,
    update_resource_allocation,
    update_risk_status,
    update_task,
)
from app.schemas.project_v31 import (
    ApproveTimeEntryRequest,
    BulkTaskUpdateRequest,
    CreateProjectFromTemplateRequest,
    OrganizationProjectSummary,
    ProjectCloneRequest,
    ProjectCreate,
    ProjectDashboardMetrics,
    ProjectHealthScore,
    ProjectIssueCreate,
    ProjectIssueResponse,
    ProjectIssueUpdate,
    ProjectMilestoneCreate,
    ProjectMilestoneResponse,
    ProjectMilestoneUpdate,
    ProjectPortfolioCreate,
    ProjectPortfolioResponse,
    ProjectPortfolioUpdate,
    ProjectResourceCreate,
    ProjectResourceResponse,
    ProjectResourceUpdate,
    ProjectResponse,
    ProjectRiskCreate,
    ProjectRiskResponse,
    ProjectRiskUpdate,
    ProjectTemplateCreate,
    ProjectTemplateResponse,
    ProjectUpdate,
    TaskCreate,
    TaskDependencyCreate,
    TaskDependencyResponse,
    TaskResponse,
    TaskUpdate,
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryUpdate,
    UpdateRiskStatusRequest,
)

router = APIRouter()

# =============================================================================
# 1. Project Management Endpoint
# =============================================================================


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    organization_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    project_manager_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    start_date_from: Optional[date] = Query(None),
    end_date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[ProjectResponse]:
    """List projects with comprehensive filtering and pagination."""
    try:
        filters = {}
        if organization_id:
            filters["organization_id"] = organization_id
        if status:
            filters["status"] = status
        if project_manager_id:
            filters["project_manager_id"] = project_manager_id
        if priority:
            filters["priority"] = priority
        if project_type:
            filters["project_type"] = project_type
        if is_active is not None:
            filters["is_active"] = is_active
        if start_date_from:
            filters["start_date_from"] = start_date_from
        if end_date_to:
            filters["end_date_to"] = end_date_to

        projects = get_projects(db, filters=filters, skip=skip, limit=limit)
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving projects: {str(e)}",
        )


@router.post("/projects", response_model=ProjectResponse)
async def create_new_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a new project with validation."""
    try:
        project = create_project(db, project_data)
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}",
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_details(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Get detailed project information."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project_details(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project information."""
    try:
        project = update_project(db, project_id, project_data)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}",
        )


@router.delete("/projects/{project_id}")
async def delete_project_record(
    project_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete (archive) project."""
    try:
        success = delete_project(db, project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return {"message": "Project successfully archived"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}",
        )


# =============================================================================
# 2. Task Management Endpoint
# =============================================================================


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    is_blocked: Optional[bool] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[TaskResponse]:
    """List tasks with comprehensive filtering."""
    try:
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if assigned_to_id:
            filters["assigned_to_id"] = assigned_to_id
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if task_type:
            filters["task_type"] = task_type
        if is_blocked is not None:
            filters["is_blocked"] = is_blocked
        if due_date_from:
            filters["due_date_from"] = due_date_from
        if due_date_to:
            filters["due_date_to"] = due_date_to

        tasks = get_tasks(db, filters=filters, skip=skip, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tasks: {str(e)}",
        )


@router.post("/tasks", response_model=TaskResponse)
async def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Create a new task."""
    try:
        task = create_task(db, task_data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_details(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Get detailed task information."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_details(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Update task information."""
    try:
        task = update_task(db, task_id, task_data)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}",
        )


@router.post("/tasks/{task_id}/dependencies", response_model=TaskDependencyResponse)
async def create_task_dependency_relationship(
    task_id: str,
    dependency_data: TaskDependencyCreate,
    db: Session = Depends(get_db),
) -> TaskDependencyResponse:
    """Create task dependency."""
    try:
        # Ensure task_id matches the path parameter
        if dependency_data.task_id != task_id:
            dependency_data.task_id = task_id

        dependency = create_task_dependency(db, dependency_data)
        return dependency
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task dependency: {str(e)}",
        )


@router.put("/tasks/bulk-update", response_model=Dict[str, Any])
async def bulk_update_tasks(
    bulk_data: BulkTaskUpdateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Bulk update multiple tasks."""
    try:
        updated_count = 0
        errors = []

        for task_id in bulk_data.task_ids:
            try:
                # Create update object from bulk updates
                from app.schemas.project_v31 import TaskUpdate

                task_update = TaskUpdate(**bulk_data.updates)
                task = update_task(db, task_id, task_update)
                if task:
                    updated_count += 1
                else:
                    errors.append(f"Task {task_id} not found")
            except Exception as e:
                errors.append(f"Task {task_id}: {str(e)}")

        return {
            "updated_count": updated_count,
            "total_requested": len(bulk_data.task_ids),
            "errors": errors,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk update: {str(e)}",
        )


# =============================================================================
# 3. Resource Management Endpoint
# =============================================================================


@router.get(
    "/projects/{project_id}/resources", response_model=List[ProjectResourceResponse]
)
async def list_project_resources(
    project_id: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> List[ProjectResourceResponse]:
    """List resources allocated to project."""
    try:
        resources = get_project_resources(db, project_id, active_only)
        return resources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving project resources: {str(e)}",
        )


@router.post("/projects/{project_id}/resources", response_model=ProjectResourceResponse)
async def create_resource_allocation(
    project_id: str,
    resource_data: ProjectResourceCreate,
    db: Session = Depends(get_db),
) -> ProjectResourceResponse:
    """Allocate resource to project."""
    try:
        # Ensure project_id matches
        if resource_data.project_id != project_id:
            resource_data.project_id = project_id

        resource = create_project_resource(db, resource_data)
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating resource allocation: {str(e)}",
        )


@router.put("/resources/{resource_id}", response_model=ProjectResourceResponse)
async def update_resource_allocation_details(
    resource_id: str,
    resource_data: ProjectResourceUpdate,
    db: Session = Depends(get_db),
) -> ProjectResourceResponse:
    """Update resource allocation."""
    try:
        resource = update_resource_allocation(db, resource_id, resource_data)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource allocation not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating resource allocation: {str(e)}",
        )


# =============================================================================
# 4. Time Tracking Endpoint
# =============================================================================


@router.get("/time-entries", response_model=List[TimeEntryResponse])
async def list_time_entries(
    project_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_billable: Optional[bool] = Query(None),
    is_approved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[TimeEntryResponse]:
    """List time entries with filtering."""
    try:
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if user_id:
            filters["user_id"] = user_id
        if task_id:
            filters["task_id"] = task_id
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if is_billable is not None:
            filters["is_billable"] = is_billable
        if is_approved is not None:
            filters["is_approved"] = is_approved

        entries = get_time_entries(db, filters=filters, skip=skip, limit=limit)
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving time entries: {str(e)}",
        )


@router.post("/time-entries", response_model=TimeEntryResponse)
async def create_time_entry(
    time_data: TimeEntryCreate,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Create a new time entry."""
    try:
        entry = create_time_entry(db, time_data)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating time entry: {str(e)}",
        )


@router.put("/time-entries/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry_details(
    entry_id: str,
    time_data: TimeEntryUpdate,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Update time entry."""
    try:
        from app.models.project_extended import TimeEntry

        # Get existing entry
        entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
            )

        # Update fields
        update_data = time_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        # Recalculate billing amount if billable
        if entry.is_billable and entry.billing_rate:
            entry.billing_amount = entry.hours * entry.billing_rate

        entry.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(entry)

        return entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating time entry: {str(e)}",
        )


@router.post("/time-entries/{entry_id}/approve", response_model=TimeEntryResponse)
async def approve_time_entry_request(
    entry_id: str,
    approval_data: ApproveTimeEntryRequest,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Approve time entry."""
    try:
        entry = approve_time_entry(db, entry_id, approval_data.approver_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
            )
        return entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving time entry: {str(e)}",
        )


# =============================================================================
# 5. Risk Management Endpoint
# =============================================================================


@router.get("/projects/{project_id}/risks", response_model=List[ProjectRiskResponse])
async def list_project_risks(
    project_id: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> List[ProjectRiskResponse]:
    """List risks for project."""
    try:
        risks = get_project_risks(db, project_id, active_only)
        return risks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving project risks: {str(e)}",
        )


@router.post("/projects/{project_id}/risks", response_model=ProjectRiskResponse)
async def create_project_risk_assessment(
    project_id: str,
    risk_data: ProjectRiskCreate,
    db: Session = Depends(get_db),
) -> ProjectRiskResponse:
    """Create project risk."""
    try:
        # Ensure project_id matches
        if risk_data.project_id != project_id:
            risk_data.project_id = project_id

        risk = create_project_risk(db, risk_data)
        return risk
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project risk: {str(e)}",
        )


@router.put("/risks/{risk_id}", response_model=ProjectRiskResponse)
async def update_project_risk_details(
    risk_id: str,
    risk_data: ProjectRiskUpdate,
    db: Session = Depends(get_db),
) -> ProjectRiskResponse:
    """Update project risk."""
    try:
        from app.models.project_extended import ProjectRisk

        # Get existing risk
        risk = db.query(ProjectRisk).filter(ProjectRisk.id == risk_id).first()
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
            )

        # Update fields
        update_data = risk_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(risk, field, value)

        # Recalculate risk score if probability or impact changed
        if risk.probability and risk.impact:
            risk.risk_score = risk.probability * risk.impact * 100

        risk.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(risk)

        return risk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating risk: {str(e)}",
        )


@router.post("/risks/{risk_id}/status", response_model=ProjectRiskResponse)
async def update_risk_status_action(
    risk_id: str,
    status_data: UpdateRiskStatusRequest,
    db: Session = Depends(get_db),
) -> ProjectRiskResponse:
    """Update risk status."""
    try:
        risk = update_risk_status(db, risk_id, status_data.status)
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
            )
        return risk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating risk status: {str(e)}",
        )


# =============================================================================
# 6. Milestone Management Endpoint
# =============================================================================


@router.get(
    "/projects/{project_id}/milestones", response_model=List[ProjectMilestoneResponse]
)
async def list_project_milestones(
    project_id: str,
    db: Session = Depends(get_db),
) -> List[ProjectMilestoneResponse]:
    """List milestones for project."""
    try:
        from app.models.project_extended import ProjectMilestoneExtended

        milestones = (
            db.query(ProjectMilestoneExtended)
            .filter(ProjectMilestoneExtended.project_id == project_id)
            .all()
        )

        return milestones
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving milestones: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/milestones", response_model=ProjectMilestoneResponse
)
async def create_project_milestone(
    project_id: str,
    milestone_data: ProjectMilestoneCreate,
    db: Session = Depends(get_db),
) -> ProjectMilestoneResponse:
    """Create project milestone."""
    try:
        from app.models.project_extended import ProjectMilestoneExtended

        # Ensure project_id matches
        if milestone_data.project_id != project_id:
            milestone_data.project_id = project_id

        milestone = ProjectMilestoneExtended(**milestone_data.model_dump())
        milestone.created_by = "system"  # Should come from auth context

        db.add(milestone)
        db.commit()
        db.refresh(milestone)

        return milestone
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating milestone: {str(e)}",
        )


@router.put("/milestones/{milestone_id}", response_model=ProjectMilestoneResponse)
async def update_project_milestone_details(
    milestone_id: str,
    milestone_data: ProjectMilestoneUpdate,
    db: Session = Depends(get_db),
) -> ProjectMilestoneResponse:
    """Update project milestone."""
    try:
        from app.models.project_extended import ProjectMilestoneExtended

        milestone = (
            db.query(ProjectMilestoneExtended)
            .filter(ProjectMilestoneExtended.id == milestone_id)
            .first()
        )

        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found"
            )

        update_data = milestone_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(milestone, field, value)

        milestone.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(milestone)

        return milestone
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating milestone: {str(e)}",
        )


# =============================================================================
# 7. Issue Management Endpoint
# =============================================================================


@router.get("/projects/{project_id}/issues", response_model=List[ProjectIssueResponse])
async def list_project_issues(
    project_id: str,
    status: Optional[str] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[ProjectIssueResponse]:
    """List issues for project."""
    try:
        from app.models.project_extended import ProjectIssue

        query = db.query(ProjectIssue).filter(ProjectIssue.project_id == project_id)

        if status:
            query = query.filter(ProjectIssue.status == status)
        if assigned_to_id:
            query = query.filter(ProjectIssue.assigned_to_id == assigned_to_id)
        if priority:
            query = query.filter(ProjectIssue.priority == priority)
        if issue_type:
            query = query.filter(ProjectIssue.issue_type == issue_type)

        issues = query.offset(skip).limit(limit).all()
        return issues
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving issues: {str(e)}",
        )


@router.post("/projects/{project_id}/issues", response_model=ProjectIssueResponse)
async def create_project_issue(
    project_id: str,
    issue_data: ProjectIssueCreate,
    db: Session = Depends(get_db),
) -> ProjectIssueResponse:
    """Create project issue."""
    try:
        from app.models.project_extended import ProjectExtended, ProjectIssue

        # Validate project exists
        project = (
            db.query(ProjectExtended).filter(ProjectExtended.id == project_id).first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Ensure project_id matches
        if issue_data.project_id != project_id:
            issue_data.project_id = project_id

        # Generate issue number if not provided
        if not issue_data.issue_number:
            count = (
                db.query(ProjectIssue)
                .filter(ProjectIssue.project_id == project_id)
                .count()
            )
            issue_data.issue_number = f"{project.project_code}-I-{count + 1:04d}"

        issue = ProjectIssue(**issue_data.model_dump())

        db.add(issue)
        db.commit()
        db.refresh(issue)

        return issue
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating issue: {str(e)}",
        )


@router.put("/issues/{issue_id}", response_model=ProjectIssueResponse)
async def update_project_issue_details(
    issue_id: str,
    issue_data: ProjectIssueUpdate,
    db: Session = Depends(get_db),
) -> ProjectIssueResponse:
    """Update project issue."""
    try:
        from app.models.project_extended import ProjectIssue

        issue = db.query(ProjectIssue).filter(ProjectIssue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found"
            )

        update_data = issue_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)

        issue.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(issue)

        return issue
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating issue: {str(e)}",
        )


# =============================================================================
# 8. Portfolio Management Endpoint
# =============================================================================


@router.get("/portfolios", response_model=List[ProjectPortfolioResponse])
async def list_portfolios(
    organization_id: str = Query(...),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> List[ProjectPortfolioResponse]:
    """List portfolios for organization."""
    try:
        portfolios = get_portfolios(db, organization_id, active_only)
        return portfolios
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolios: {str(e)}",
        )


@router.post("/portfolios", response_model=ProjectPortfolioResponse)
async def create_project_portfolio(
    portfolio_data: ProjectPortfolioCreate,
    db: Session = Depends(get_db),
) -> ProjectPortfolioResponse:
    """Create project portfolio."""
    try:
        portfolio = create_portfolio(db, portfolio_data)
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating portfolio: {str(e)}",
        )


@router.put("/portfolios/{portfolio_id}", response_model=ProjectPortfolioResponse)
async def update_portfolio_details(
    portfolio_id: str,
    portfolio_data: ProjectPortfolioUpdate,
    db: Session = Depends(get_db),
) -> ProjectPortfolioResponse:
    """Update portfolio."""
    try:
        from app.models.project_extended import ProjectPortfolio

        portfolio = (
            db.query(ProjectPortfolio)
            .filter(ProjectPortfolio.id == portfolio_id)
            .first()
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        update_data = portfolio_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(portfolio, field, value)

        portfolio.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(portfolio)

        return portfolio
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating portfolio: {str(e)}",
        )


# =============================================================================
# 9. Template Management Endpoint
# =============================================================================


@router.get("/templates", response_model=List[ProjectTemplateResponse])
async def list_project_templates(
    organization_id: str = Query(...),
    category: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[ProjectTemplateResponse]:
    """List project templates."""
    try:
        from app.models.project_extended import ProjectTemplate

        query = db.query(ProjectTemplate).filter(
            ProjectTemplate.organization_id == organization_id
        )

        if category:
            query = query.filter(ProjectTemplate.category == category)
        if is_public is not None:
            query = query.filter(ProjectTemplate.is_public == is_public)
        if active_only:
            query = query.filter(ProjectTemplate.is_active)

        templates = query.offset(skip).limit(limit).all()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving templates: {str(e)}",
        )


@router.post("/templates", response_model=ProjectTemplateResponse)
async def create_project_template(
    template_data: ProjectTemplateCreate,
    db: Session = Depends(get_db),
) -> ProjectTemplateResponse:
    """Create project template."""
    try:
        from app.models.project_extended import ProjectTemplate

        template = ProjectTemplate(**template_data.model_dump())
        template.created_by = "system"  # Should come from auth context

        db.add(template)
        db.commit()
        db.refresh(template)

        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}",
        )


@router.post("/templates/{template_id}/create-project", response_model=ProjectResponse)
async def create_project_from_template(
    template_id: str,
    project_request: CreateProjectFromTemplateRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create project from template."""
    try:
        from app.models.project_extended import ProjectTemplate

        # Get template
        template = (
            db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )

        # Create project from template data
        project_create = ProjectCreate(
            organization_id=project_request.organization_id,
            name=project_request.project_name,
            project_manager_id=project_request.project_manager_id,
            planned_start_date=project_request.planned_start_date,
            total_budget=project_request.total_budget,
            **template.template_data,
        )

        project = create_project(db, project_create)

        # Increment template usage count
        template.usage_count += 1
        db.commit()

        return project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project from template: {str(e)}",
        )


# =============================================================================
# 10. Project Analytics Endpoint
# =============================================================================


@router.get("/projects/{project_id}/dashboard", response_model=ProjectDashboardMetrics)
async def get_project_dashboard_data(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectDashboardMetrics:
    """Get project dashboard metrics."""
    try:
        metrics = get_project_dashboard_metrics(db, project_id)
        return ProjectDashboardMetrics(**metrics)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard metrics: {str(e)}",
        )


@router.get("/projects/{project_id}/health", response_model=ProjectHealthScore)
async def get_project_health_analysis(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectHealthScore:
    """Get project health score analysis."""
    try:
        health = calculate_project_health_score(db, project_id)
        return ProjectHealthScore(**health)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating health score: {str(e)}",
        )


@router.get(
    "/organizations/{organization_id}/project-summary",
    response_model=OrganizationProjectSummary,
)
async def get_organization_summary(
    organization_id: str,
    db: Session = Depends(get_db),
) -> OrganizationProjectSummary:
    """Get organization-wide project summary."""
    try:
        summary = get_organization_project_summary(db, organization_id)
        return OrganizationProjectSummary(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving organization summary: {str(e)}",
        )


@router.post("/projects/{project_id}/clone", response_model=ProjectResponse)
async def clone_project(
    project_id: str,
    clone_request: ProjectCloneRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Clone an existing project."""
    try:
        # Get source project
        source_project = get_project(db, project_id)
        if not source_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source project not found"
            )

        # Create new project with cloned data
        project_data = {
            "organization_id": source_project.organization_id,
            "name": clone_request.new_project_name,
            "description": f"Cloned from {source_project.name}",
            "project_type": source_project.project_type,
            "methodology": source_project.methodology,
            "sprint_duration": source_project.sprint_duration,
            "is_billable": source_project.is_billable,
        }

        if clone_request.include_timeline and source_project.planned_start_date:
            from datetime import timedelta

            duration = (
                source_project.planned_end_date - source_project.planned_start_date
            ).days
            project_data["planned_start_date"] = date.today()
            project_data["planned_end_date"] = date.today() + timedelta(days=duration)

        project_create = ProjectCreate(**project_data)
        new_project = create_project(db, project_create)

        # TODO: Clone tasks, resources if requested
        # This would involve creating new task records with updated project_id

        return new_project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cloning project: {str(e)}",
        )
