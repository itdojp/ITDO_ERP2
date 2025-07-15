"""Task repository for database operations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, joinedload

from app.models.task import Task, TaskDependency, TaskHistory, TaskStatus
from app.repositories.base import BaseRepository
from app.schemas.task import TaskSearchParams


class TaskRepository(BaseRepository[Task]):
    """Repository for task database operations."""

    def __init__(self, db: Session):
        """Initialize repository."""
        super().__init__(Task, db)

    def get_by_project(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Task], int]:
        """Get tasks by project with pagination."""
        query = (
            self.db.query(Task)
            .filter(Task.project_id == project_id, ~Task.is_deleted)
            .options(
                joinedload(Task.assignee),
                joinedload(Task.creator),
                joinedload(Task.project),
            )
        )

        total = query.count()
        tasks = query.offset(skip).limit(limit).all()

        return tasks, total

    def get_by_assignee(
        self, assignee_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Task], int]:
        """Get tasks assigned to a user."""
        query = (
            self.db.query(Task)
            .filter(Task.assigned_to == assignee_id, ~Task.is_deleted)
            .options(joinedload(Task.project), joinedload(Task.creator))
        )

        total = query.count()
        tasks = query.offset(skip).limit(limit).all()

        return tasks, total

    def search_tasks(
        self,
        params: TaskSearchParams,
        accessible_project_ids: Optional[List[int]] = None,
    ) -> Tuple[List[Task], int]:
        """Search tasks with filters and pagination."""
        query = (
            self.db.query(Task)
            .filter(~Task.is_deleted)
            .options(
                joinedload(Task.assignee),
                joinedload(Task.creator),
                joinedload(Task.project),
            )
        )

        # Apply project access control
        if accessible_project_ids is not None:
            query = query.filter(Task.project_id.in_(accessible_project_ids))

        # Apply filters
        if params.project_id:
            query = query.filter(Task.project_id == params.project_id)

        if params.assigned_to:
            query = query.filter(Task.assigned_to == params.assigned_to)

        if params.created_by:
            query = query.filter(Task.created_by == params.created_by)

        if params.status:
            query = query.filter(Task.status == params.status)

        if params.priority:
            query = query.filter(Task.priority == params.priority)

        if params.is_overdue is not None:
            now = datetime.now(timezone.utc)
            if params.is_overdue:
                query = query.filter(
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date < now,
                        Task.status != TaskStatus.COMPLETED,
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Task.due_date.is_(None),
                        Task.due_date >= now,
                        Task.status == TaskStatus.COMPLETED,
                    )
                )

        if params.tags:
            # Search for tasks containing any of the specified tags
            tag_list = [tag.strip() for tag in params.tags.split(",")]
            tag_conditions = [Task.tags.contains(tag) for tag in tag_list]
            query = query.filter(or_(*tag_conditions))

        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(Task.title.ilike(search_term), Task.description.ilike(search_term))
            )

        # Date range filters
        if params.start_date_from:
            query = query.filter(Task.start_date >= params.start_date_from)

        if params.start_date_to:
            query = query.filter(Task.start_date <= params.start_date_to)

        if params.due_date_from:
            query = query.filter(Task.due_date >= params.due_date_from)

        if params.due_date_to:
            query = query.filter(Task.due_date <= params.due_date_to)

        # Count total before pagination
        total = query.count()

        # Apply sorting
        if params.sort_by == "title":
            order_col = Task.title
        elif params.sort_by == "status":
            order_col = Task.status
        elif params.sort_by == "priority":
            order_col = Task.priority
        elif params.sort_by == "due_date":
            order_col = Task.due_date
        elif params.sort_by == "created_at":
            order_col = Task.created_at
        elif params.sort_by == "updated_at":
            order_col = Task.updated_at
        else:
            order_col = Task.created_at

        if params.sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # Apply pagination
        skip = (params.page - 1) * params.limit
        tasks = query.offset(skip).limit(params.limit).all()

        return tasks, total

    def get_overdue_tasks(self, project_id: Optional[int] = None) -> List[Task]:
        """Get all overdue tasks."""
        now = datetime.now(timezone.utc)
        query = self.db.query(Task).filter(
            Task.due_date < now, Task.status != TaskStatus.COMPLETED, ~Task.is_deleted
        )

        if project_id:
            query = query.filter(Task.project_id == project_id)

        return query.all()

    def get_blocked_tasks(self, project_id: Optional[int] = None) -> List[Task]:
        """Get all blocked tasks."""
        query = self.db.query(Task).filter(
            Task.status == TaskStatus.BLOCKED, ~Task.is_deleted
        )

        if project_id:
            query = query.filter(Task.project_id == project_id)

        return query.all()

    def get_task_statistics(
        self, project_id: Optional[int] = None, assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get task statistics."""
        query = self.db.query(Task).filter(~Task.is_deleted)

        if project_id:
            query = query.filter(Task.project_id == project_id)

        if assignee_id:
            query = query.filter(Task.assigned_to == assignee_id)

        # Get status counts
        status_counts = (
            query.with_entities(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )

        # Get priority counts (for future use)
        # priority_counts = (
        #     query.with_entities(Task.priority, func.count(Task.id))
        #     .group_by(Task.priority)
        #     .all()
        # )

        # Get overdue count
        now = datetime.now(timezone.utc)
        overdue_count = query.filter(
            Task.due_date < now, Task.status != TaskStatus.COMPLETED
        ).count()

        # Get progress statistics
        progress_stats = query.with_entities(
            func.avg(Task.progress_percentage),
            func.avg(Task.estimated_hours),
            func.avg(Task.actual_hours),
            func.sum(Task.estimated_hours),
            func.sum(Task.actual_hours),
        ).first()

        # Compile statistics
        total_tasks = sum(count for _, count in status_counts)
        completed_tasks = sum(
            count for status, count in status_counts if status == TaskStatus.COMPLETED
        )

        return {
            "total_tasks": total_tasks,
            "todo_tasks": sum(
                count for status, count in status_counts if status == TaskStatus.TODO
            ),
            "in_progress_tasks": sum(
                count
                for status, count in status_counts
                if status == TaskStatus.IN_PROGRESS
            ),
            "in_review_tasks": sum(
                count
                for status, count in status_counts
                if status == TaskStatus.IN_REVIEW
            ),
            "completed_tasks": completed_tasks,
            "cancelled_tasks": sum(
                count
                for status, count in status_counts
                if status == TaskStatus.CANCELLED
            ),
            "blocked_tasks": sum(
                count for status, count in status_counts if status == TaskStatus.BLOCKED
            ),
            "overdue_tasks": overdue_count,
            "avg_progress": float(progress_stats[0] or 0),
            "completion_rate": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "avg_estimated_hours": float(progress_stats[1] or 0),
            "avg_actual_hours": float(progress_stats[2] or 0),
            "total_estimated_hours": float(progress_stats[3] or 0),
            "total_actual_hours": float(progress_stats[4] or 0),
        }

    def get_with_dependencies(self, task_id: int) -> Optional[Task]:
        """Get task with all dependencies loaded."""
        return (
            self.db.query(Task)
            .filter(Task.id == task_id, ~Task.is_deleted)
            .options(
                joinedload(Task.dependencies).joinedload(
                    TaskDependency.depends_on_task
                ),
                joinedload(Task.dependent_tasks).joinedload(TaskDependency.task),
                joinedload(Task.assignee),
                joinedload(Task.creator),
                joinedload(Task.project),
            )
            .first()
        )

    def get_with_history(self, task_id: int, limit: int = 50) -> Optional[Task]:
        """Get task with history."""
        task = (
            self.db.query(Task)
            .filter(Task.id == task_id, ~Task.is_deleted)
            .options(
                joinedload(Task.assignee),
                joinedload(Task.creator),
                joinedload(Task.project),
            )
            .first()
        )

        if task:
            # Load recent history separately to avoid N+1 problem
            task.task_history = (
                self.db.query(TaskHistory)
                .filter(TaskHistory.task_id == task_id)
                .options(joinedload(TaskHistory.user))
                .order_by(TaskHistory.changed_at.desc())
                .limit(limit)
                .all()
            )

        return task

    def create_dependency(
        self,
        task_id: int,
        depends_on_task_id: int,
        dependency_type: str,
        created_by: int,
    ) -> TaskDependency:
        """Create a task dependency."""
        dependency = TaskDependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            created_by=created_by,
        )

        self.db.add(dependency)
        self.db.flush()
        return dependency

    def remove_dependency(self, task_id: int, depends_on_task_id: int) -> bool:
        """Remove a task dependency."""
        dependency = (
            self.db.query(TaskDependency)
            .filter(
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_task_id == depends_on_task_id,
            )
            .first()
        )

        if dependency:
            self.db.delete(dependency)
            self.db.flush()
            return True
        return False

    def get_task_dependencies(self, task_id: int) -> List[TaskDependency]:
        """Get all dependencies for a task."""
        return (
            self.db.query(TaskDependency)
            .filter(TaskDependency.task_id == task_id)
            .options(joinedload(TaskDependency.depends_on_task))
            .all()
        )

    def check_circular_dependency(self, task_id: int, depends_on_task_id: int) -> bool:
        """Check if adding dependency would create circular dependency."""
        # Use recursive CTE to check for circular dependencies
        recursive_query = text("""
            WITH RECURSIVE dependency_path AS (
                -- Base case: direct dependencies
                SELECT task_id, depends_on_task_id, 1 as depth
                FROM task_dependencies
                WHERE task_id = :depends_on_task_id
                AND is_deleted = false

                UNION ALL

                -- Recursive case: follow the dependency chain
                SELECT td.task_id, td.depends_on_task_id, dp.depth + 1
                FROM task_dependencies td
                JOIN dependency_path dp ON td.task_id = dp.depends_on_task_id
                WHERE dp.depth < 10  -- Prevent infinite recursion
                AND td.is_deleted = false
            )
            SELECT COUNT(*) as circular_count
            FROM dependency_path
            WHERE depends_on_task_id = :task_id
        """)

        result = self.db.execute(
            recursive_query,
            {"task_id": task_id, "depends_on_task_id": depends_on_task_id},
        ).fetchone()

        return result.circular_count > 0 if result else False

    def get_tasks_by_status(
        self,
        status: TaskStatus,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        """Get tasks by status."""
        query = self.db.query(Task).filter(Task.status == status, ~Task.is_deleted)

        if project_id:
            query = query.filter(Task.project_id == project_id)

        total = query.count()
        tasks = query.offset(skip).limit(limit).all()

        return tasks, total

    def bulk_update_status(
        self, task_ids: List[int], new_status: TaskStatus, updated_by: int
    ) -> int:
        """Bulk update task status."""
        updated_count = (
            self.db.query(Task)
            .filter(Task.id.in_(task_ids), ~Task.is_deleted)
            .update(
                {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": updated_by,
                },
                synchronize_session=False,
            )
        )

        # Add history entries for bulk update
        for task_id in task_ids:
            history = TaskHistory(
                task_id=task_id,
                action="bulk_status_update",
                details=f'{{"new_status": "{new_status.value}"}}',
                changed_by=updated_by,
                changed_at=datetime.now(timezone.utc),
            )
            self.db.add(history)

        self.db.flush()
        return updated_count

    def get_user_task_counts(self, user_id: int) -> Dict[str, int]:
        """Get task counts for a user across all statuses."""
        status_counts = (
            self.db.query(Task.status, func.count(Task.id))
            .filter(Task.assigned_to == user_id, ~Task.is_deleted)
            .group_by(Task.status)
            .all()
        )

        counts = {status.value: 0 for status in TaskStatus}
        for status, count in status_counts:
            counts[status.value] = count

        return counts
