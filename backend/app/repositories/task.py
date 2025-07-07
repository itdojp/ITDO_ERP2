"""Task repository with advanced query operations."""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.task import Task, TaskAssignment, TaskDependency, TaskStatus, TaskPriority, DependencyType
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate, TaskSearchParams
from app.core.exceptions import CircularDependency, OptimisticLockError


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    """Repository for Task model with specialized queries."""
    
    def __init__(self, db: Session):
        """Initialize repository with Task model."""
        super().__init__(Task, db)
    
    def search_tasks(
        self,
        params: TaskSearchParams,
        organization_id: int,
        user_accessible_projects: Optional[List[int]] = None
    ) -> tuple[List[Task], int]:
        """Search tasks with advanced filtering and multi-tenant isolation."""
        query = select(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignments).joinedload(TaskAssignment.user),
            selectinload(Task.dependencies_as_successor),
            selectinload(Task.dependencies_as_predecessor)
        ).where(
            and_(
                Task.is_deleted == False,
                Task.organization_id == organization_id
            )
        )
        
        # Project access control
        if user_accessible_projects is not None:
            query = query.where(Task.project_id.in_(user_accessible_projects))
        
        # Apply search filters
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )
        
        if params.status:
            query = query.where(Task.status == params.status)
        
        if params.priority:
            query = query.where(Task.priority == params.priority)
        
        if params.project_id:
            query = query.where(Task.project_id == params.project_id)
        
        if params.assignee_id:
            query = query.join(TaskAssignment).where(
                TaskAssignment.user_id == params.assignee_id
            )
        
        if params.due_date_from:
            query = query.where(Task.due_date >= params.due_date_from)
        
        if params.due_date_to:
            query = query.where(Task.due_date <= params.due_date_to)
        
        if params.tags:
            for tag in params.tags:
                query = query.where(Task.tags.contains([tag]))
        
        if params.is_overdue is not None:
            now = datetime.now()
            if params.is_overdue:
                query = query.where(
                    and_(
                        Task.due_date != None,
                        Task.due_date < now,
                        Task.status != TaskStatus.COMPLETED
                    )
                )
            else:
                query = query.where(
                    or_(
                        Task.due_date == None,
                        Task.due_date >= now,
                        Task.status == TaskStatus.COMPLETED
                    )
                )
        
        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0
        
        # Apply sorting
        if params.sort_by:
            sort_column = getattr(Task, params.sort_by, None)
            if sort_column is not None:
                if params.sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(Task.created_at))
        
        # Apply pagination
        offset = (params.page - 1) * params.limit
        query = query.offset(offset).limit(params.limit)
        
        tasks = list(self.db.scalars(query))
        return tasks, total
    
    def get_user_tasks(
        self,
        user_id: int,
        organization_id: int,
        status_filter: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Task]:
        """Get tasks assigned to a specific user."""
        query = select(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignments)
        ).join(TaskAssignment).where(
            and_(
                TaskAssignment.user_id == user_id,
                Task.is_deleted == False,
                Task.organization_id == organization_id
            )
        )
        
        if status_filter:
            query = query.where(Task.status == status_filter)
        
        query = query.order_by(desc(Task.created_at)).limit(limit)
        return list(self.db.scalars(query))
    
    def get_overdue_tasks(self, organization_id: int) -> List[Task]:
        """Get all overdue tasks in organization."""
        now = datetime.now()
        query = select(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignments).joinedload(TaskAssignment.user)
        ).where(
            and_(
                Task.due_date != None,
                Task.due_date < now,
                Task.status != TaskStatus.COMPLETED,
                Task.is_deleted == False,
                Task.organization_id == organization_id
            )
        ).order_by(Task.due_date)
        
        return list(self.db.scalars(query))
    
    def detect_circular_dependency(
        self,
        predecessor_id: int,
        successor_id: int
    ) -> bool:
        """Detect if adding a dependency would create a circular reference."""
        if predecessor_id == successor_id:
            return True
        
        # Use recursive CTE to check for cycles
        visited = set()
        to_visit = [successor_id]
        
        while to_visit:
            current_id = to_visit.pop()
            if current_id in visited:
                continue
            if current_id == predecessor_id:
                return True
            
            visited.add(current_id)
            
            # Get all successors of current task
            successors = self.db.scalars(
                select(TaskDependency.successor_id)
                .where(TaskDependency.predecessor_id == current_id)
            ).all()
            
            to_visit.extend(successors)
        
        return False
    
    def get_dependency_tree(self, task_id: int) -> Dict[str, Any]:
        """Get the complete dependency tree for a task."""
        def get_predecessors(tid: int, visited: Set[int]) -> List[Dict[str, Any]]:
            if tid in visited:
                return []
            visited.add(tid)
            
            deps = self.db.scalars(
                select(TaskDependency)
                .options(joinedload(TaskDependency.predecessor))
                .where(TaskDependency.successor_id == tid)
            ).all()
            
            return [
                {
                    "task": dep.predecessor,
                    "dependency_type": dep.dependency_type,
                    "lag_time": dep.lag_time,
                    "predecessors": get_predecessors(dep.predecessor_id, visited.copy())
                }
                for dep in deps
            ]
        
        def get_successors(tid: int, visited: Set[int]) -> List[Dict[str, Any]]:
            if tid in visited:
                return []
            visited.add(tid)
            
            deps = self.db.scalars(
                select(TaskDependency)
                .options(joinedload(TaskDependency.successor))
                .where(TaskDependency.predecessor_id == tid)
            ).all()
            
            return [
                {
                    "task": dep.successor,
                    "dependency_type": dep.dependency_type,
                    "lag_time": dep.lag_time,
                    "successors": get_successors(dep.successor_id, visited.copy())
                }
                for dep in deps
            ]
        
        task = self.get(task_id)
        if not task:
            return {}
        
        return {
            "task": task,
            "predecessors": get_predecessors(task_id, set()),
            "successors": get_successors(task_id, set())
        }
    
    def update_with_optimistic_lock(
        self,
        task_id: int,
        update_data: Dict[str, Any],
        expected_version: int
    ) -> Optional[Task]:
        """Update task with optimistic locking."""
        # Get current task
        task = self.get(task_id)
        if not task:
            return None
        
        # Check version
        if task.version != expected_version:
            raise OptimisticLockError(
                f"Task version mismatch. Expected {expected_version}, got {task.version}"
            )
        
        # Update with version increment
        update_data["version"] = task.version + 1
        
        try:
            result = self.db.execute(
                text("""
                    UPDATE tasks 
                    SET version = :new_version, updated_at = NOW(),
                        title = COALESCE(:title, title),
                        description = COALESCE(:description, description),
                        status = COALESCE(:status, status),
                        priority = COALESCE(:priority, priority),
                        due_date = COALESCE(:due_date, due_date),
                        progress_percentage = COALESCE(:progress_percentage, progress_percentage),
                        actual_hours = COALESCE(:actual_hours, actual_hours),
                        tags = COALESCE(:tags, tags)
                    WHERE id = :task_id AND version = :expected_version
                """),
                {
                    "task_id": task_id,
                    "expected_version": expected_version,
                    "new_version": expected_version + 1,
                    "title": update_data.get("title"),
                    "description": update_data.get("description"),
                    "status": update_data.get("status"),
                    "priority": update_data.get("priority"),
                    "due_date": update_data.get("due_date"),
                    "progress_percentage": update_data.get("progress_percentage"),
                    "actual_hours": update_data.get("actual_hours"),
                    "tags": update_data.get("tags")
                }
            )
            
            if hasattr(result, 'rowcount') and result.rowcount == 0:
                raise OptimisticLockError("Task was modified by another user")
            
            self.db.commit()
            return self.get(task_id)
            
        except SQLAlchemyError:
            self.db.rollback()
            raise
    
    def get_critical_path(self, project_id: int) -> List[Task]:
        """Calculate and return the critical path for a project."""
        # Get all tasks in project with dependencies
        tasks = self.db.scalars(
            select(Task)
            .options(
                selectinload(Task.dependencies_as_successor),
                selectinload(Task.dependencies_as_predecessor)
            )
            .where(
                and_(
                    Task.project_id == project_id,
                    Task.is_deleted == False
                )
            )
        ).all()
        
        if not tasks:
            return []
        
        # Build task graph
        task_dict = {task.id: task for task in tasks}
        
        # Calculate earliest start times (forward pass)
        earliest_start: Dict[int, float] = {}
        earliest_finish: Dict[int, float] = {}
        
        def calculate_earliest(task_id: int) -> float:
            if task_id in earliest_start:
                return float(earliest_start[task_id])
            
            task = task_dict[task_id]
            max_predecessor_finish = 0.0
            
            # Check all predecessors
            for dep in task.dependencies_as_successor:
                predecessor_finish = calculate_earliest(dep.predecessor_id) + (
                    task_dict[dep.predecessor_id].estimated_hours or 0
                )
                if dep.dependency_type == DependencyType.FINISH_TO_START:
                    predecessor_finish += dep.lag_time * 24  # Convert days to hours
                
                max_predecessor_finish = max(max_predecessor_finish, predecessor_finish)
            
            earliest_start[task_id] = max_predecessor_finish
            earliest_finish[task_id] = max_predecessor_finish + (task.estimated_hours or 0)
            return earliest_start[task_id]
        
        # Calculate for all tasks
        for task in tasks:
            calculate_earliest(task.id)
        
        # Find project duration
        project_duration = max(earliest_finish.values()) if earliest_finish else 0
        
        # Calculate latest start times (backward pass)
        latest_start: Dict[int, float] = {}
        latest_finish: Dict[int, float] = {}
        
        def calculate_latest(task_id: int) -> float:
            if task_id in latest_finish:
                return float(latest_finish[task_id])
            
            task = task_dict[task_id]
            
            # If no successors, use project duration
            if not task.dependencies_as_predecessor:
                latest_finish[task_id] = project_duration
            else:
                min_successor_start = float('inf')
                for dep in task.dependencies_as_predecessor:
                    successor_start = calculate_latest(dep.successor_id) - (
                        task_dict[dep.successor_id].estimated_hours or 0
                    )
                    if dep.dependency_type == DependencyType.FINISH_TO_START:
                        successor_start -= dep.lag_time * 24
                    
                    min_successor_start = min(min_successor_start, successor_start)
                
                latest_finish[task_id] = min_successor_start
            
            latest_start[task_id] = latest_finish[task_id] - (task.estimated_hours or 0)
            return latest_finish[task_id]
        
        # Calculate for all tasks
        for task in tasks:
            calculate_latest(task.id)
        
        # Find critical path (tasks with zero slack)
        critical_tasks = []
        for task in tasks:
            slack = latest_start[task.id] - earliest_start[task.id]
            if abs(slack) < 0.01:  # Floating point tolerance
                critical_tasks.append(task)
        
        # Sort by earliest start time
        critical_tasks.sort(key=lambda t: earliest_start[t.id])
        return critical_tasks
    
    def get_task_statistics(self, organization_id: int) -> Dict[str, Any]:
        """Get comprehensive task statistics for organization."""
        base_query = select(Task).where(
            and_(
                Task.organization_id == organization_id,
                Task.is_deleted == False
            )
        )
        
        total_tasks = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        
        # Status distribution
        status_counts = {}
        for status in TaskStatus:
            count = self.db.scalar(
                select(func.count())
                .select_from(base_query.where(Task.status == status).subquery())
            ) or 0
            status_counts[status] = count
        
        # Priority distribution
        priority_counts = {}
        for priority in TaskPriority:
            count = self.db.scalar(
                select(func.count())
                .select_from(base_query.where(Task.priority == priority).subquery())
            ) or 0
            priority_counts[priority] = count
        
        # Overdue count
        now = datetime.now()
        overdue_count = self.db.scalar(
            select(func.count())
            .select_from(
                base_query.where(
                    and_(
                        Task.due_date != None,
                        Task.due_date < now,
                        Task.status != TaskStatus.COMPLETED
                    )
                ).subquery()
            )
        ) or 0
        
        # Completion rate
        completed_count = status_counts.get(TaskStatus.COMPLETED, 0)
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Average completion time
        avg_completion_time = self.db.scalar(
            select(func.avg(func.extract('epoch', Task.updated_at - Task.created_at) / 86400))
            .where(
                and_(
                    Task.organization_id == organization_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.is_deleted == False
                )
            )
        )
        
        return {
            "total_tasks": total_tasks,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue_count": overdue_count,
            "completion_rate": round(completion_rate, 2),
            "average_completion_time_days": round(avg_completion_time or 0, 2)
        }