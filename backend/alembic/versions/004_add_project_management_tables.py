"""Add project management tables

Revision ID: 004
Revises: 003
Create Date: 2025-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('project_manager_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('name_en', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('budget', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('actual_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['project_manager_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_projects_org_code')
    )
    op.create_index('ix_projects_actual_end_date', 'projects', ['actual_end_date'], unique=False)
    op.create_index('ix_projects_actual_start_date', 'projects', ['actual_start_date'], unique=False)
    op.create_index('ix_projects_budget', 'projects', ['budget'], unique=False)
    op.create_index('ix_projects_planned_end_date', 'projects', ['planned_end_date'], unique=False)
    op.create_index('ix_projects_planned_start_date', 'projects', ['planned_start_date'], unique=False)
    op.create_index('ix_projects_priority', 'projects', ['priority'], unique=False)
    op.create_index('ix_projects_progress', 'projects', ['progress_percentage'], unique=False)
    op.create_index('ix_projects_status', 'projects', ['status'], unique=False)
    op.create_index('ix_projects_type', 'projects', ['project_type'], unique=False)

    # Create project_members table
    op.create_table('project_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('allocation_percentage', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_members_project_user')
    )
    op.create_index('ix_project_members_allocation', 'project_members', ['allocation_percentage'], unique=False)
    op.create_index('ix_project_members_is_active', 'project_members', ['is_active'], unique=False)
    op.create_index('ix_project_members_role', 'project_members', ['role'], unique=False)

    # Create project_phases table
    op.create_table('project_phases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('phase_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('planned_start_date', sa.Date(), nullable=False),
        sa.Column('planned_end_date', sa.Date(), nullable=False),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'phase_number', name='uq_project_phases_project_number')
    )
    op.create_index('ix_project_phases_actual_end_date', 'project_phases', ['actual_end_date'], unique=False)
    op.create_index('ix_project_phases_actual_start_date', 'project_phases', ['actual_start_date'], unique=False)
    op.create_index('ix_project_phases_planned_end_date', 'project_phases', ['planned_end_date'], unique=False)
    op.create_index('ix_project_phases_planned_start_date', 'project_phases', ['planned_start_date'], unique=False)
    op.create_index('ix_project_phases_progress', 'project_phases', ['progress_percentage'], unique=False)
    op.create_index('ix_project_phases_status', 'project_phases', ['status'], unique=False)

    # Create project_milestones table
    op.create_table('project_milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['project_phases.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_milestones_critical', 'project_milestones', ['is_critical'], unique=False)
    op.create_index('ix_project_milestones_due_date', 'project_milestones', ['due_date'], unique=False)
    op.create_index('ix_project_milestones_status', 'project_milestones', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_project_milestones_status', table_name='project_milestones')
    op.drop_index('ix_project_milestones_due_date', table_name='project_milestones')
    op.drop_index('ix_project_milestones_critical', table_name='project_milestones')
    
    op.drop_index('ix_project_phases_status', table_name='project_phases')
    op.drop_index('ix_project_phases_progress', table_name='project_phases')
    op.drop_index('ix_project_phases_planned_start_date', table_name='project_phases')
    op.drop_index('ix_project_phases_planned_end_date', table_name='project_phases')
    op.drop_index('ix_project_phases_actual_start_date', table_name='project_phases')
    op.drop_index('ix_project_phases_actual_end_date', table_name='project_phases')
    
    op.drop_index('ix_project_members_role', table_name='project_members')
    op.drop_index('ix_project_members_is_active', table_name='project_members')
    op.drop_index('ix_project_members_allocation', table_name='project_members')
    
    op.drop_index('ix_projects_type', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_progress', table_name='projects')
    op.drop_index('ix_projects_priority', table_name='projects')
    op.drop_index('ix_projects_planned_start_date', table_name='projects')
    op.drop_index('ix_projects_planned_end_date', table_name='projects')
    op.drop_index('ix_projects_budget', table_name='projects')
    op.drop_index('ix_projects_actual_start_date', table_name='projects')
    op.drop_index('ix_projects_actual_end_date', table_name='projects')
    
    # Drop tables in reverse dependency order
    op.drop_table('project_milestones')
    op.drop_table('project_phases')
    op.drop_table('project_members')
    op.drop_table('projects')