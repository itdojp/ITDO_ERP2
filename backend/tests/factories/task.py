"""Factory for creating test Task instances."""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, timedelta, timezone

from app.models.task import Task, TaskStatus, TaskPriority, TaskAssignment, TaskDependency, DependencyType, AssignmentRole
from tests.factories.user import UserFactory
from tests.factories.organization import ProjectFactory


class TaskFactory(SQLAlchemyModelFactory):
    """Factory for Task model."""
    
    class Meta:
        model = Task
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("text", max_nb_chars=200)
    project_id = factory.SubFactory(ProjectFactory)
    status = TaskStatus.NOT_STARTED
    priority = TaskPriority.MEDIUM
    due_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=7))
    estimated_hours = factory.Faker("random_int", min=1, max=40)
    progress_percentage = 0
    tags = factory.LazyFunction(lambda: ["test", "sample"])
    created_by = factory.SubFactory(UserFactory)
    organization_id = factory.LazyAttribute(lambda obj: obj.project.organization_id)


class TaskAssignmentFactory(SQLAlchemyModelFactory):
    """Factory for TaskAssignment model."""
    
    class Meta:
        model = TaskAssignment
        sqlalchemy_session_persistence = "commit"
    
    task_id = factory.SubFactory(TaskFactory)
    user_id = factory.SubFactory(UserFactory)
    role = AssignmentRole.ASSIGNEE
    assigned_by = factory.SubFactory(UserFactory)
    assigned_at = factory.LazyFunction(datetime.now)


class TaskDependencyFactory(SQLAlchemyModelFactory):
    """Factory for TaskDependency model."""
    
    class Meta:
        model = TaskDependency
        sqlalchemy_session_persistence = "commit"
    
    predecessor_id = factory.SubFactory(TaskFactory)
    successor_id = factory.SubFactory(TaskFactory)
    dependency_type = DependencyType.FINISH_TO_START
    lag_time = 0