"""Add task management v2 tables

Revision ID: 004_add_task_management_v2
Revises: 003_complete_type_safe_schema
Create Date: 2024-07-07 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_task_management_v2'
down_revision: Union[str, None] = '003_complete_type_safe_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task status enum
    task_status_enum = postgresql.ENUM(
        'NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'ON_HOLD', 'COMPLETED',
        name='task_status',
        create_type=False
    )
    task_status_enum.create(op.get_bind(), checkfirst=True)

    # Create task priority enum
    task_priority_enum = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'URGENT',
        name='task_priority',
        create_type=False
    )
    task_priority_enum.create(op.get_bind(), checkfirst=True)

    # Create dependency type enum
    dependency_type_enum = postgresql.ENUM(
        'FS', 'SS', 'FF', 'SF',
        name='dependency_type',
        create_type=False
    )
    dependency_type_enum.create(op.get_bind(), checkfirst=True)

    # Create assignment role enum
    assignment_role_enum = postgresql.ENUM(
        'ASSIGNEE', 'REVIEWER', 'OBSERVER',
        name='assignment_role',
        create_type=False
    )
    assignment_role_enum.create(op.get_bind(), checkfirst=True)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Project code'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Project name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Project description'),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.String(length=10), nullable=True, comment='Project start date'),
        sa.Column('end_date', sa.String(length=10), nullable=True, comment='Project end date'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether project is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_deleted_at'), 'projects', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_projects_is_deleted'), 'projects', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_projects_code'), 'projects', ['code'], unique=False)
    op.create_index(op.f('ix_projects_organization_id'), 'projects', ['organization_id'], unique=False)

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('priority', task_priority_enum, nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_deleted_at'), 'tasks', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_tasks_is_deleted'), 'tasks', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_tasks_parent_task_id'), 'tasks', ['parent_task_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_tasks_organization_id'), 'tasks', ['organization_id'], unique=False)

    # Create task_assignments table
    op.create_table('task_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', assignment_role_enum, nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_assignments_task_id'), 'task_assignments', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_assignments_user_id'), 'task_assignments', ['user_id'], unique=False)

    # Create task_dependencies table
    op.create_table('task_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('predecessor_id', sa.Integer(), nullable=False),
        sa.Column('successor_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', dependency_type_enum, nullable=False),
        sa.Column('lag_time', sa.Integer(), nullable=False, comment='Lag time in days'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['predecessor_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_dependencies_predecessor_id'), 'task_dependencies', ['predecessor_id'], unique=False)
    op.create_index(op.f('ix_task_dependencies_successor_id'), 'task_dependencies', ['successor_id'], unique=False)

    # Create task_comments table
    op.create_table('task_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('mentioned_users', sa.JSON(), nullable=True, comment='List of mentioned user IDs'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['task_comments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_comments_deleted_at'), 'task_comments', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_task_comments_is_deleted'), 'task_comments', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_task_comments_task_id'), 'task_comments', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_comments_user_id'), 'task_comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_task_comments_parent_comment_id'), 'task_comments', ['parent_comment_id'], unique=False)

    # Create task_attachments table
    op.create_table('task_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['task_comments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_attachments_deleted_at'), 'task_attachments', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_task_attachments_is_deleted'), 'task_attachments', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_task_attachments_task_id'), 'task_attachments', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_attachments_comment_id'), 'task_attachments', ['comment_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('task_attachments')
    op.drop_table('task_comments')
    op.drop_table('task_dependencies')
    op.drop_table('task_assignments')
    op.drop_table('tasks')
    op.drop_table('projects')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS assignment_role CASCADE')
    op.execute('DROP TYPE IF EXISTS dependency_type CASCADE')
    op.execute('DROP TYPE IF EXISTS task_priority CASCADE')
    op.execute('DROP TYPE IF EXISTS task_status CASCADE')