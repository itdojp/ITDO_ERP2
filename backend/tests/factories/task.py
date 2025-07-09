"""Task test factories."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority, TaskType
from app.models.project import Project
from app.models.user import User
from . import BaseFactory


class TaskFactory(BaseFactory):
    """Factory for creating test tasks."""

    @staticmethod
    def create(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create a test task."""
        defaults = {
            "title": f"Task {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "A test task for unit testing",
            "project_id": project.id,
            "reporter_id": creator.id,
            "status": TaskStatus.TODO,
            "priority": TaskPriority.MEDIUM,
            "task_type": TaskType.FEATURE,
            "due_date": date.today() + timedelta(days=7),
            "estimated_hours": 8.0,
            "labels": ["test", "development"],
            "metadata": {"test": True},
            "dependencies": [],
            "is_deleted": False,
        }
        defaults.update(kwargs)

        task = Task(**defaults)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def create_with_assignee(
        db: Session,
        project: Project,
        creator: User,
        assignee: User,
        **kwargs: Any,
    ) -> Task:
        """Create a test task with an assignee."""
        kwargs["assignee_id"] = assignee.id
        return TaskFactory.create(db, project, creator, **kwargs)

    @staticmethod
    def create_epic(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create an epic task."""
        defaults = {
            "title": f"Epic {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "An epic task for organizing multiple features",
            "task_type": TaskType.EPIC,
            "priority": TaskPriority.HIGH,
            "estimated_hours": 80.0,
            "due_date": date.today() + timedelta(days=30),
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_subtask(
        db: Session,
        project: Project,
        creator: User,
        parent_task: Task,
        **kwargs: Any,
    ) -> Task:
        """Create a subtask."""
        defaults = {
            "title": f"Subtask of {parent_task.title}",
            "description": f"A subtask for {parent_task.title}",
            "parent_task_id": parent_task.id,
            "epic_id": parent_task.epic_id,
            "priority": parent_task.priority,
            "estimated_hours": 4.0,
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_bug(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create a bug task."""
        defaults = {
            "title": f"Bug {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "A bug that needs to be fixed",
            "task_type": TaskType.BUG,
            "priority": TaskPriority.HIGH,
            "estimated_hours": 4.0,
            "due_date": date.today() + timedelta(days=3),
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_task_set(
        db: Session,
        project: Project,
        creator: User,
        assignee: Optional[User] = None,
    ) -> Dict[str, Task]:
        """Create a set of tasks in different states."""
        tasks = {}

        # Todo task
        tasks["todo"] = TaskFactory.create(
            db,
            project,
            creator,
            title="Todo Task",
            status=TaskStatus.TODO,
            assignee_id=assignee.id if assignee else None,
        )

        # In progress task
        tasks["in_progress"] = TaskFactory.create(
            db,
            project,
            creator,
            title="In Progress Task",
            status=TaskStatus.IN_PROGRESS,
            start_date=date.today(),
            assignee_id=assignee.id if assignee else None,
        )

        # In review task
        tasks["in_review"] = TaskFactory.create(
            db,
            project,
            creator,
            title="In Review Task",
            status=TaskStatus.IN_REVIEW,
            start_date=date.today() - timedelta(days=2),
            assignee_id=assignee.id if assignee else None,
        )

        # Completed task
        tasks["done"] = TaskFactory.create(
            db,
            project,
            creator,
            title="Completed Task",
            status=TaskStatus.DONE,
            start_date=date.today() - timedelta(days=5),
            completed_date=date.today(),
            actual_hours=6.0,
            assignee_id=assignee.id if assignee else None,
        )

        # Blocked task
        tasks["blocked"] = TaskFactory.create(
            db,
            project,
            creator,
            title="Blocked Task",
            status=TaskStatus.BLOCKED,
            priority=TaskPriority.HIGH,
            assignee_id=assignee.id if assignee else None,
        )

        # Cancelled task
        tasks["cancelled"] = TaskFactory.create(
            db,
            project,
            creator,
            title="Cancelled Task",
            status=TaskStatus.CANCELLED,
            assignee_id=assignee.id if assignee else None,
        )

        return tasks

    @staticmethod
    def create_with_dependencies(
        db: Session,
        project: Project,
        creator: User,
        dependency_tasks: List[Task],
        **kwargs: Any,
    ) -> Task:
        """Create a task with dependencies."""
        kwargs["dependencies"] = [task.id for task in dependency_tasks]
        return TaskFactory.create(db, project, creator, **kwargs)

    @staticmethod
    def create_overdue_task(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create an overdue task."""
        defaults = {
            "title": "Overdue Task",
            "description": "A task that is overdue",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH,
            "due_date": date.today() - timedelta(days=2),
            "start_date": date.today() - timedelta(days=5),
            "estimated_hours": 8.0,
            "actual_hours": 12.0,
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_task_hierarchy(
        db: Session,
        project: Project,
        creator: User,
        assignee: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Create a task hierarchy with epic, stories, and subtasks."""
        # Create epic
        epic = TaskFactory.create_epic(
            db,
            project,
            creator,
            title="Feature Epic",
            description="An epic for a major feature",
        )

        # Create stories under the epic
        stories = []
        for i in range(3):
            story = TaskFactory.create(
                db,
                project,
                creator,
                title=f"Story {i+1}",
                description=f"User story {i+1} for the epic",
                epic_id=epic.id,
                task_type=TaskType.FEATURE,
                priority=TaskPriority.MEDIUM,
                assignee_id=assignee.id if assignee else None,
            )
            stories.append(story)

        # Create subtasks for the first story
        subtasks = []
        for i in range(2):
            subtask = TaskFactory.create_subtask(
                db,
                project,
                creator,
                stories[0],
                title=f"Subtask {i+1}",
                description=f"Subtask {i+1} for story 1",
                assignee_id=assignee.id if assignee else None,
            )
            subtasks.append(subtask)

        return {
            "epic": epic,
            "stories": stories,
            "subtasks": subtasks,
            "total_tasks": 1 + len(stories) + len(subtasks),
        }

    @staticmethod
    def create_with_time_tracking(
        db: Session,
        project: Project,
        creator: User,
        assignee: User,
        **kwargs: Any,
    ) -> Task:
        """Create a task with time tracking data."""
        defaults = {
            "title": "Time Tracked Task",
            "description": "A task with time tracking",
            "status": TaskStatus.IN_PROGRESS,
            "assignee_id": assignee.id,
            "estimated_hours": 10.0,
            "actual_hours": 6.5,
            "start_date": date.today() - timedelta(days=3),
            "due_date": date.today() + timedelta(days=2),
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_with_labels(
        db: Session,
        project: Project,
        creator: User,
        labels: List[str],
        **kwargs: Any,
    ) -> Task:
        """Create a task with specific labels."""
        kwargs["labels"] = labels
        return TaskFactory.create(db, project, creator, **kwargs)

    @staticmethod
    def create_urgent_task(
        db: Session,
        project: Project,
        creator: User,
        assignee: User,
        **kwargs: Any,
    ) -> Task:
        """Create an urgent task."""
        defaults = {
            "title": "Urgent Task",
            "description": "An urgent task that needs immediate attention",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.URGENT,
            "task_type": TaskType.BUG,
            "assignee_id": assignee.id,
            "due_date": date.today() + timedelta(days=1),
            "estimated_hours": 2.0,
            "labels": ["urgent", "critical", "hotfix"],
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_documentation_task(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create a documentation task."""
        defaults = {
            "title": "Documentation Task",
            "description": "Create documentation for the feature",
            "task_type": TaskType.DOCUMENTATION,
            "priority": TaskPriority.LOW,
            "estimated_hours": 4.0,
            "due_date": date.today() + timedelta(days=14),
            "labels": ["documentation", "write"],
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_testing_task(
        db: Session,
        project: Project,
        creator: User,
        feature_task: Task,
        **kwargs: Any,
    ) -> Task:
        """Create a testing task that depends on a feature task."""
        defaults = {
            "title": f"Test {feature_task.title}",
            "description": f"Create tests for {feature_task.title}",
            "task_type": TaskType.TESTING,
            "priority": TaskPriority.MEDIUM,
            "estimated_hours": 6.0,
            "due_date": feature_task.due_date + timedelta(days=3) if feature_task.due_date else None,
            "dependencies": [feature_task.id],
            "epic_id": feature_task.epic_id,
            "labels": ["testing", "qa"],
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)

    @staticmethod
    def create_maintenance_task(
        db: Session,
        project: Project,
        creator: User,
        **kwargs: Any,
    ) -> Task:
        """Create a maintenance task."""
        defaults = {
            "title": "Maintenance Task",
            "description": "Regular maintenance and cleanup",
            "task_type": TaskType.MAINTENANCE,
            "priority": TaskPriority.LOW,
            "estimated_hours": 3.0,
            "due_date": date.today() + timedelta(days=30),
            "labels": ["maintenance", "cleanup"],
        }
        defaults.update(kwargs)
        return TaskFactory.create(db, project, creator, **defaults)