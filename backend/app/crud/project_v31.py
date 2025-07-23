"""
Project Management CRUD Operations - CC02 v31.0 Phase 2

Comprehensive project management operations with:
- Project Planning & Management
- Task Management & Dependencies
- Resource Management & Allocation
- Time Tracking & Reporting
- Risk Management
- Portfolio Management
- Quality Assurance
- Collaboration Tools
- Project Analytics
- Template Management
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.project_extended import (
    ProjectExtended,
    ProjectPortfolio,
    ProjectResource,
    ProjectRisk,
    ProjectStatus,
    RiskLevel,
    RiskStatus,
    TaskDependencyExtended,
    TaskExtended,
    TaskStatus,
    TimeEntry,
)

# =============================================================================
# Project Management CRUD
# =============================================================================

def create_project(db: Session, project_data: Any) -> ProjectExtended:
    """Create a new project with validation."""
    # Validate project manager exists
    if hasattr(project_data, 'project_manager_id') and project_data.project_manager_id:
        from app.models.user import User
        manager = db.query(User).filter(User.id == project_data.project_manager_id).first()
        if not manager:
            raise ValueError("Project manager not found")

    # Generate unique project code if not provided
    if not hasattr(project_data, 'project_code') or not project_data.project_code:
        # Generate code based on organization and sequence
        org_id = project_data.organization_id
        count = db.query(ProjectExtended).filter(
            ProjectExtended.organization_id == org_id
        ).count()
        project_data.project_code = f"PRJ-{org_id[:3].upper()}-{count + 1:04d}"

    # Validate date logic
    if (hasattr(project_data, 'planned_start_date') and hasattr(project_data, 'planned_end_date')
        and project_data.planned_start_date and project_data.planned_end_date):
        if project_data.planned_start_date >= project_data.planned_end_date:
            raise ValueError("Project start date must be before end date")

    project = ProjectExtended(**project_data.model_dump())
    project.created_by = getattr(project_data, 'created_by', 'system')

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_project(db: Session, project_id: str) -> Optional[ProjectExtended]:
    """Get project by ID with related data."""
    return db.query(ProjectExtended).options(
        joinedload(ProjectExtended.project_manager),
        joinedload(ProjectExtended.sponsor),
        joinedload(ProjectExtended.tasks),
        joinedload(ProjectExtended.resources),
        joinedload(ProjectExtended.milestones),
        joinedload(ProjectExtended.risks)
    ).filter(ProjectExtended.id == project_id).first()


def get_projects(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ProjectExtended]:
    """Get projects with filtering and pagination."""
    query = db.query(ProjectExtended)

    if filters:
        if "organization_id" in filters:
            query = query.filter(ProjectExtended.organization_id == filters["organization_id"])
        if "status" in filters:
            query = query.filter(ProjectExtended.status == filters["status"])
        if "project_manager_id" in filters:
            query = query.filter(ProjectExtended.project_manager_id == filters["project_manager_id"])
        if "priority" in filters:
            query = query.filter(ProjectExtended.priority == filters["priority"])
        if "is_active" in filters:
            query = query.filter(ProjectExtended.is_active == filters["is_active"])
        if "project_type" in filters:
            query = query.filter(ProjectExtended.project_type == filters["project_type"])
        if "start_date_from" in filters:
            query = query.filter(ProjectExtended.planned_start_date >= filters["start_date_from"])
        if "end_date_to" in filters:
            query = query.filter(ProjectExtended.planned_end_date <= filters["end_date_to"])

    return query.options(
        joinedload(ProjectExtended.project_manager),
        joinedload(ProjectExtended.resources)
    ).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: str, project_data: Any) -> Optional[ProjectExtended]:
    """Update project with validation."""
    project = db.query(ProjectExtended).filter(ProjectExtended.id == project_id).first()
    if not project:
        return None

    update_data = project_data.model_dump(exclude_unset=True)

    # Validate date logic if dates are being updated
    if "planned_start_date" in update_data or "planned_end_date" in update_data:
        start_date = update_data.get("planned_start_date", project.planned_start_date)
        end_date = update_data.get("planned_end_date", project.planned_end_date)
        if start_date and end_date and start_date >= end_date:
            raise ValueError("Project start date must be before end date")

    # Calculate progress based on task completion if updating tasks
    if project.tasks:
        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.COMPLETED])
        if total_tasks > 0:
            project.progress_percentage = Decimal((completed_tasks / total_tasks) * 100)

    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow()
    project.updated_by = getattr(project_data, 'updated_by', 'system')

    db.commit()
    db.refresh(project)

    return project


def delete_project(db: Session, project_id: str) -> bool:
    """Soft delete project (mark as inactive)."""
    project = db.query(ProjectExtended).filter(ProjectExtended.id == project_id).first()
    if not project:
        return False

    project.is_active = False
    project.status = ProjectStatus.ARCHIVED
    project.updated_at = datetime.utcnow()

    db.commit()
    return True


# =============================================================================
# Task Management CRUD
# =============================================================================

def create_task(db: Session, task_data: Any) -> TaskExtended:
    """Create a new task with validation."""
    # Validate project exists
    project = db.query(ProjectExtended).filter(
        ProjectExtended.id == task_data.project_id
    ).first()
    if not project:
        raise ValueError("Project not found")

    # Generate task number if not provided
    if not hasattr(task_data, 'task_number') or not task_data.task_number:
        count = db.query(TaskExtended).filter(
            TaskExtended.project_id == task_data.project_id
        ).count()
        task_data.task_number = f"{project.project_code}-T-{count + 1:04d}"

    # Validate parent task if specified
    if hasattr(task_data, 'parent_task_id') and task_data.parent_task_id:
        parent = db.query(TaskExtended).filter(
            TaskExtended.id == task_data.parent_task_id
        ).first()
        if not parent or parent.project_id != task_data.project_id:
            raise ValueError("Invalid parent task")

    task = TaskExtended(**task_data.model_dump())
    task.created_by = getattr(task_data, 'created_by', 'system')

    # Calculate remaining hours
    if task.estimated_hours:
        task.remaining_hours = task.estimated_hours - (task.actual_hours or 0)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def get_task(db: Session, task_id: str) -> Optional[TaskExtended]:
    """Get task by ID with related data."""
    return db.query(TaskExtended).options(
        joinedload(TaskExtended.project),
        joinedload(TaskExtended.assigned_to),
        joinedload(TaskExtended.dependencies),
        joinedload(TaskExtended.time_entries),
        joinedload(TaskExtended.comments)
    ).filter(TaskExtended.id == task_id).first()


def get_tasks(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TaskExtended]:
    """Get tasks with filtering and pagination."""
    query = db.query(TaskExtended)

    if filters:
        if "project_id" in filters:
            query = query.filter(TaskExtended.project_id == filters["project_id"])
        if "assigned_to_id" in filters:
            query = query.filter(TaskExtended.assigned_to_id == filters["assigned_to_id"])
        if "status" in filters:
            query = query.filter(TaskExtended.status == filters["status"])
        if "priority" in filters:
            query = query.filter(TaskExtended.priority == filters["priority"])
        if "task_type" in filters:
            query = query.filter(TaskExtended.task_type == filters["task_type"])
        if "is_blocked" in filters:
            query = query.filter(TaskExtended.is_blocked == filters["is_blocked"])
        if "due_date_from" in filters:
            query = query.filter(TaskExtended.due_date >= filters["due_date_from"])
        if "due_date_to" in filters:
            query = query.filter(TaskExtended.due_date <= filters["due_date_to"])

    return query.options(
        joinedload(TaskExtended.assigned_to),
        joinedload(TaskExtended.project)
    ).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: str, task_data: Any) -> Optional[TaskExtended]:
    """Update task with validation and automatic calculations."""
    task = db.query(TaskExtended).filter(TaskExtended.id == task_id).first()
    if not task:
        return None

    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    # Recalculate remaining hours
    if task.estimated_hours:
        task.remaining_hours = task.estimated_hours - (task.actual_hours or 0)

    # Auto-calculate progress based on time spent
    if task.estimated_hours and task.actual_hours:
        calculated_progress = min((task.actual_hours / task.estimated_hours) * 100, 100)
        if not hasattr(task_data, 'progress_percentage'):
            task.progress_percentage = Decimal(calculated_progress)

    # Set completion date if status changed to completed
    if task.status == TaskStatus.COMPLETED and not task.completion_date:
        task.completion_date = date.today()

    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task


def create_task_dependency(db: Session, dependency_data: Any) -> TaskDependencyExtended:
    """Create task dependency with validation."""
    # Validate tasks exist and are different
    if dependency_data.task_id == dependency_data.dependent_task_id:
        raise ValueError("Task cannot depend on itself")

    task = db.query(TaskExtended).filter(TaskExtended.id == dependency_data.task_id).first()
    dependent_task = db.query(TaskExtended).filter(
        TaskExtended.id == dependency_data.dependent_task_id
    ).first()

    if not task or not dependent_task:
        raise ValueError("One or both tasks not found")

    # Check for circular dependencies
    if would_create_circular_dependency(db, dependency_data.task_id, dependency_data.dependent_task_id):
        raise ValueError("This dependency would create a circular reference")

    dependency = TaskDependencyExtended(**dependency_data.model_dump())
    dependency.created_by = getattr(dependency_data, 'created_by', 'system')

    db.add(dependency)
    db.commit()
    db.refresh(dependency)

    return dependency


def would_create_circular_dependency(db: Session, task_id: str, dependent_task_id: str) -> bool:
    """Check if adding a dependency would create a circular reference."""
    # Simple circular dependency check - can be enhanced with more sophisticated algorithm
    existing_deps = db.query(TaskDependencyExtended).filter(
        TaskDependencyExtended.task_id == dependent_task_id,
        TaskDependencyExtended.dependent_task_id == task_id
    ).first()

    return existing_deps is not None


# =============================================================================
# Resource Management CRUD
# =============================================================================

def create_project_resource(db: Session, resource_data: Any) -> ProjectResource:
    """Create project resource allocation."""
    # Validate project exists
    project = db.query(ProjectExtended).filter(
        ProjectExtended.id == resource_data.project_id
    ).first()
    if not project:
        raise ValueError("Project not found")

    # Validate user exists
    from app.models.user import User
    user = db.query(User).filter(User.id == resource_data.user_id).first()
    if not user:
        raise ValueError("User not found")

    # Check for overlapping assignments with high allocation
    if resource_data.allocation_percentage > 80:
        overlapping = db.query(ProjectResource).filter(
            ProjectResource.user_id == resource_data.user_id,
            ProjectResource.is_active,
            ProjectResource.start_date <= resource_data.end_date if resource_data.end_date else True,
            or_(
                ProjectResource.end_date.is_(None),
                ProjectResource.end_date >= resource_data.start_date
            ),
            ProjectResource.allocation_percentage > 50
        ).first()

        if overlapping:
            raise ValueError("User is already allocated to another project during this period")

    resource = ProjectResource(**resource_data.model_dump())
    resource.created_by = getattr(resource_data, 'created_by', 'system')

    db.add(resource)
    db.commit()
    db.refresh(resource)

    return resource


def get_project_resources(
    db: Session,
    project_id: str,
    active_only: bool = True
) -> List[ProjectResource]:
    """Get all resources allocated to a project."""
    query = db.query(ProjectResource).filter(ProjectResource.project_id == project_id)

    if active_only:
        query = query.filter(ProjectResource.is_active)

    return query.options(joinedload(ProjectResource.user)).all()


def update_resource_allocation(
    db: Session,
    resource_id: str,
    resource_data: Any
) -> Optional[ProjectResource]:
    """Update resource allocation."""
    resource = db.query(ProjectResource).filter(ProjectResource.id == resource_id).first()
    if not resource:
        return None

    update_data = resource_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(resource, field, value)

    resource.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(resource)

    return resource


# =============================================================================
# Time Tracking CRUD
# =============================================================================

def create_time_entry(db: Session, time_data: Any) -> TimeEntry:
    """Create time entry with validation."""
    # Validate project exists
    project = db.query(ProjectExtended).filter(
        ProjectExtended.id == time_data.project_id
    ).first()
    if not project:
        raise ValueError("Project not found")

    # Validate task if specified
    if hasattr(time_data, 'task_id') and time_data.task_id:
        task = db.query(TaskExtended).filter(
            TaskExtended.id == time_data.task_id,
            TaskExtended.project_id == time_data.project_id
        ).first()
        if not task:
            raise ValueError("Task not found or doesn't belong to project")

    # Validate time entry doesn't exceed reasonable limits
    if time_data.hours > 24:
        raise ValueError("Time entry cannot exceed 24 hours per day")

    # Calculate billing amount if billable
    time_entry = TimeEntry(**time_data.model_dump())

    if time_entry.is_billable and time_entry.billing_rate:
        time_entry.billing_amount = time_entry.hours * time_entry.billing_rate

    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)

    # Update task actual hours if task specified
    if time_entry.task_id:
        update_task_actual_hours(db, time_entry.task_id)

    return time_entry


def update_task_actual_hours(db: Session, task_id: str):
    """Update task actual hours based on time entries."""
    total_hours = db.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.task_id == task_id
    ).scalar() or 0

    task = db.query(TaskExtended).filter(TaskExtended.id == task_id).first()
    if task:
        task.actual_hours = Decimal(total_hours)
        if task.estimated_hours:
            task.remaining_hours = task.estimated_hours - task.actual_hours
        db.commit()


def get_time_entries(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TimeEntry]:
    """Get time entries with filtering."""
    query = db.query(TimeEntry)

    if filters:
        if "project_id" in filters:
            query = query.filter(TimeEntry.project_id == filters["project_id"])
        if "user_id" in filters:
            query = query.filter(TimeEntry.user_id == filters["user_id"])
        if "task_id" in filters:
            query = query.filter(TimeEntry.task_id == filters["task_id"])
        if "date_from" in filters:
            query = query.filter(TimeEntry.date >= filters["date_from"])
        if "date_to" in filters:
            query = query.filter(TimeEntry.date <= filters["date_to"])
        if "is_billable" in filters:
            query = query.filter(TimeEntry.is_billable == filters["is_billable"])
        if "is_approved" in filters:
            query = query.filter(TimeEntry.is_approved == filters["is_approved"])

    return query.options(
        joinedload(TimeEntry.project),
        joinedload(TimeEntry.task),
        joinedload(TimeEntry.user)
    ).offset(skip).limit(limit).all()


def approve_time_entry(db: Session, entry_id: str, approver_id: str) -> Optional[TimeEntry]:
    """Approve time entry."""
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        return None

    entry.is_approved = True
    entry.approved_by_id = approver_id
    entry.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(entry)

    return entry


# =============================================================================
# Risk Management CRUD
# =============================================================================

def create_project_risk(db: Session, risk_data: Any) -> ProjectRisk:
    """Create project risk with assessment."""
    risk = ProjectRisk(**risk_data.model_dump())

    # Calculate risk score if probability and impact provided
    if risk.probability and risk.impact:
        risk.risk_score = risk.probability * risk.impact * 100

        # Determine risk level based on score
        if risk.risk_score >= 75:
            risk.risk_level = RiskLevel.CRITICAL
        elif risk.risk_score >= 50:
            risk.risk_level = RiskLevel.HIGH
        elif risk.risk_score >= 25:
            risk.risk_level = RiskLevel.MEDIUM
        else:
            risk.risk_level = RiskLevel.LOW

    risk.created_by = getattr(risk_data, 'created_by', 'system')
    risk.identified_date = risk.identified_date or date.today()

    db.add(risk)
    db.commit()
    db.refresh(risk)

    return risk


def get_project_risks(
    db: Session,
    project_id: str,
    active_only: bool = True
) -> List[ProjectRisk]:
    """Get all risks for a project."""
    query = db.query(ProjectRisk).filter(ProjectRisk.project_id == project_id)

    if active_only:
        query = query.filter(ProjectRisk.status != RiskStatus.CLOSED)

    return query.options(joinedload(ProjectRisk.owner)).all()


def update_risk_status(db: Session, risk_id: str, status: RiskStatus) -> Optional[ProjectRisk]:
    """Update risk status."""
    risk = db.query(ProjectRisk).filter(ProjectRisk.id == risk_id).first()
    if not risk:
        return None

    risk.status = status
    risk.last_reviewed_date = date.today()

    if status == RiskStatus.CLOSED:
        risk.actual_closure_date = date.today()

    risk.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(risk)

    return risk


# =============================================================================
# Portfolio Management CRUD
# =============================================================================

def create_portfolio(db: Session, portfolio_data: Any) -> ProjectPortfolio:
    """Create project portfolio."""
    portfolio = ProjectPortfolio(**portfolio_data.model_dump())
    portfolio.created_by = getattr(portfolio_data, 'created_by', 'system')

    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    return portfolio


def get_portfolios(
    db: Session,
    organization_id: str,
    active_only: bool = True
) -> List[ProjectPortfolio]:
    """Get portfolios for organization."""
    query = db.query(ProjectPortfolio).filter(
        ProjectPortfolio.organization_id == organization_id
    )

    if active_only:
        query = query.filter(ProjectPortfolio.is_active)

    return query.options(joinedload(ProjectPortfolio.portfolio_manager)).all()


# =============================================================================
# Project Analytics and Reporting
# =============================================================================

def get_project_dashboard_metrics(db: Session, project_id: str) -> Dict[str, Any]:
    """Get comprehensive project dashboard metrics."""
    project = db.query(ProjectExtended).filter(ProjectExtended.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # Task metrics
    total_tasks = db.query(TaskExtended).filter(TaskExtended.project_id == project_id).count()
    completed_tasks = db.query(TaskExtended).filter(
        TaskExtended.project_id == project_id,
        TaskExtended.status == TaskStatus.COMPLETED
    ).count()

    # Time metrics
    total_logged_hours = db.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.project_id == project_id
    ).scalar() or 0

    billable_hours = db.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.project_id == project_id,
        TimeEntry.is_billable
    ).scalar() or 0

    # Risk metrics
    high_risks = db.query(ProjectRisk).filter(
        ProjectRisk.project_id == project_id,
        ProjectRisk.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
        ProjectRisk.status != RiskStatus.CLOSED
    ).count()

    # Budget metrics
    total_cost = db.query(func.sum(TimeEntry.billing_amount)).filter(
        TimeEntry.project_id == project_id,
        TimeEntry.is_billable
    ).scalar() or 0

    return {
        "project_id": project_id,
        "project_name": project.name,
        "status": project.status,
        "progress_percentage": float(project.progress_percentage or 0),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "task_completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "total_logged_hours": float(total_logged_hours),
        "billable_hours": float(billable_hours),
        "estimated_hours": float(project.estimated_hours or 0),
        "actual_hours": float(project.actual_hours or 0),
        "budget_utilization": (float(total_cost) / float(project.total_budget) * 100) if project.total_budget else 0,
        "high_priority_risks": high_risks,
        "team_size": project.team_size or 0,
        "days_remaining": (project.planned_end_date - date.today()).days if project.planned_end_date else None,
        "is_on_schedule": project.planned_end_date >= date.today() if project.planned_end_date else True,
        "quality_score": float(project.quality_score or 0)
    }


def get_organization_project_summary(db: Session, organization_id: str) -> Dict[str, Any]:
    """Get organization-wide project summary."""
    # Project status distribution
    status_counts = db.query(
        ProjectExtended.status,
        func.count(ProjectExtended.id)
    ).filter(
        ProjectExtended.organization_id == organization_id,
        ProjectExtended.is_active
    ).group_by(ProjectExtended.status).all()

    # Resource utilization
    active_resources = db.query(ProjectResource).join(ProjectExtended).filter(
        ProjectExtended.organization_id == organization_id,
        ProjectResource.is_active
    ).count()

    # Budget summary
    total_budget = db.query(func.sum(ProjectExtended.total_budget)).filter(
        ProjectExtended.organization_id == organization_id,
        ProjectExtended.is_active
    ).scalar() or 0

    actual_cost = db.query(func.sum(ProjectExtended.actual_cost)).filter(
        ProjectExtended.organization_id == organization_id,
        ProjectExtended.is_active
    ).scalar() or 0

    return {
        "organization_id": organization_id,
        "total_active_projects": sum(count for _, count in status_counts),
        "project_status_distribution": {status: count for status, count in status_counts},
        "total_resources_allocated": active_resources,
        "total_budget": float(total_budget),
        "total_actual_cost": float(actual_cost),
        "budget_utilization": (float(actual_cost) / float(total_budget) * 100) if total_budget > 0 else 0,
        "summary_date": datetime.utcnow()
    }


def calculate_project_health_score(db: Session, project_id: str) -> Dict[str, Any]:
    """Calculate comprehensive project health score."""
    project = db.query(ProjectExtended).filter(ProjectExtended.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    health_factors = {}

    # Schedule health (40% weight)
    if project.planned_end_date:
        days_total = (project.planned_end_date - project.planned_start_date).days if project.planned_start_date else 365
        days_remaining = (project.planned_end_date - date.today()).days
        schedule_health = min(max((days_remaining / days_total) * 100, 0), 100) if days_total > 0 else 50
    else:
        schedule_health = 50

    health_factors["schedule"] = {"score": schedule_health, "weight": 0.4}

    # Budget health (25% weight)
    if project.total_budget and project.total_budget > 0:
        budget_utilization = (project.actual_cost or 0) / project.total_budget
        budget_health = max(100 - (budget_utilization * 100), 0)
    else:
        budget_health = 50

    health_factors["budget"] = {"score": budget_health, "weight": 0.25}

    # Quality health (20% weight)
    quality_health = (project.quality_score or 3) * 20  # Convert 0-5 to 0-100
    health_factors["quality"] = {"score": quality_health, "weight": 0.2}

    # Risk health (15% weight)
    high_risks = db.query(ProjectRisk).filter(
        ProjectRisk.project_id == project_id,
        ProjectRisk.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
        ProjectRisk.status != RiskStatus.CLOSED
    ).count()

    risk_health = max(100 - (high_risks * 25), 0)
    health_factors["risk"] = {"score": risk_health, "weight": 0.15}

    # Calculate overall health score
    overall_score = sum(
        factor["score"] * factor["weight"]
        for factor in health_factors.values()
    )

    # Determine health status
    if overall_score >= 80:
        health_status = "healthy"
    elif overall_score >= 60:
        health_status = "at_risk"
    elif overall_score >= 40:
        health_status = "unhealthy"
    else:
        health_status = "critical"

    return {
        "project_id": project_id,
        "overall_health_score": round(overall_score, 2),
        "health_status": health_status,
        "health_factors": health_factors,
        "recommendations": generate_health_recommendations(health_factors)
    }


def generate_health_recommendations(health_factors: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on health factors."""
    recommendations = []

    for factor_name, factor_data in health_factors.items():
        if factor_data["score"] < 60:
            if factor_name == "schedule":
                recommendations.append("Consider extending timeline or reducing scope")
            elif factor_name == "budget":
                recommendations.append("Review budget allocation and cost control measures")
            elif factor_name == "quality":
                recommendations.append("Implement additional quality assurance measures")
            elif factor_name == "risk":
                recommendations.append("Address high-priority risks immediately")

    if not recommendations:
        recommendations.append("Project appears healthy - maintain current practices")

    return recommendations
