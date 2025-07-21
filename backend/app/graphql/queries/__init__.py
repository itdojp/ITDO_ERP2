"""GraphQL query resolvers."""

from app.graphql.queries.user_queries import UserQueries
from app.graphql.queries.organization_queries import OrganizationQueries
from app.graphql.queries.task_queries import TaskQueries

__all__ = ["UserQueries", "OrganizationQueries", "TaskQueries"]