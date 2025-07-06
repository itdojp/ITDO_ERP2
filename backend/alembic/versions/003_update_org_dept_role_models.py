"""Update organization, department, and role models

Revision ID: 003
Revises: 002
Create Date: 2025-01-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update organization, department, and role models with new fields."""
    
    # Add new fields to organizations table
    op.add_column('organizations', sa.Column('name_kana', sa.String(200), nullable=True))
    op.add_column('organizations', sa.Column('name_en', sa.String(200), nullable=True))
    op.add_column('organizations', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('organizations', sa.Column('fax', sa.String(20), nullable=True))
    op.add_column('organizations', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('website', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('postal_code', sa.String(10), nullable=True))
    op.add_column('organizations', sa.Column('prefecture', sa.String(50), nullable=True))
    op.add_column('organizations', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('address_line1', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('address_line2', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('business_type', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('industry', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('capital', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('employee_count', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('fiscal_year_end', sa.String(5), nullable=True))
    op.add_column('organizations', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('settings', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('logo_url', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('organizations', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('organizations', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('updated_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for organizations
    op.create_foreign_key('fk_organizations_parent_id', 'organizations', 'organizations', ['parent_id'], ['id'])
    op.create_foreign_key('fk_organizations_created_by', 'organizations', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_organizations_updated_by', 'organizations', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_organizations_deleted_by', 'organizations', 'users', ['deleted_by'], ['id'])
    
    # Add indexes for organizations
    op.create_index('ix_organizations_is_deleted', 'organizations', ['is_deleted'])
    op.create_index('ix_organizations_deleted_at', 'organizations', ['deleted_at'])
    
    # Add new fields to departments table
    op.add_column('departments', sa.Column('name_kana', sa.String(200), nullable=True))
    op.add_column('departments', sa.Column('name_en', sa.String(200), nullable=True))
    op.add_column('departments', sa.Column('short_name', sa.String(50), nullable=True))
    op.add_column('departments', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('manager_id', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('departments', sa.Column('fax', sa.String(20), nullable=True))
    op.add_column('departments', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('departments', sa.Column('location', sa.String(255), nullable=True))
    op.add_column('departments', sa.Column('budget', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('headcount_limit', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('department_type', sa.String(50), nullable=True))
    op.add_column('departments', sa.Column('cost_center_code', sa.String(50), nullable=True))
    op.add_column('departments', sa.Column('display_order', sa.Integer(), server_default='0', nullable=False))
    op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('departments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('departments', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('departments', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('updated_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for departments
    op.create_foreign_key('fk_departments_parent_id', 'departments', 'departments', ['parent_id'], ['id'])
    op.create_foreign_key('fk_departments_manager_id', 'departments', 'users', ['manager_id'], ['id'])
    op.create_foreign_key('fk_departments_created_by', 'departments', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_departments_updated_by', 'departments', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_departments_deleted_by', 'departments', 'users', ['deleted_by'], ['id'])
    
    # Add indexes for departments
    op.create_index('ix_departments_parent_id', 'departments', ['parent_id'])
    op.create_index('ix_departments_is_deleted', 'departments', ['is_deleted'])
    op.create_index('ix_departments_deleted_at', 'departments', ['deleted_at'])
    
    # Add new fields to roles table
    op.add_column('roles', sa.Column('name_en', sa.String(200), nullable=True))
    op.add_column('roles', sa.Column('role_type', sa.String(50), server_default='custom', nullable=False))
    op.add_column('roles', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('roles', sa.Column('permissions', JSON(), server_default='{}', nullable=False))
    op.add_column('roles', sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('roles', sa.Column('display_order', sa.Integer(), server_default='0', nullable=False))
    op.add_column('roles', sa.Column('icon', sa.String(50), nullable=True))
    op.add_column('roles', sa.Column('color', sa.String(7), nullable=True))
    op.add_column('roles', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('roles', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.add_column('roles', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('roles', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('roles', sa.Column('updated_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for roles
    op.create_foreign_key('fk_roles_parent_id', 'roles', 'roles', ['parent_id'], ['id'])
    op.create_foreign_key('fk_roles_created_by', 'roles', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_roles_updated_by', 'roles', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_roles_deleted_by', 'roles', 'users', ['deleted_by'], ['id'])
    
    # Add indexes for roles
    op.create_index('ix_roles_is_deleted', 'roles', ['is_deleted'])
    op.create_index('ix_roles_deleted_at', 'roles', ['deleted_at'])
    
    # Add new fields to user_roles table
    op.add_column('user_roles', sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('user_roles', sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('user_roles', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('user_roles', sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user_roles', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('user_roles', sa.Column('approval_status', sa.String(50), nullable=True))
    op.add_column('user_roles', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('user_roles', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_roles', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('user_roles', sa.Column('updated_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for user_roles
    op.create_foreign_key('fk_user_roles_approved_by', 'user_roles', 'users', ['approved_by'], ['id'])
    op.create_foreign_key('fk_user_roles_created_by', 'user_roles', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_user_roles_updated_by', 'user_roles', 'users', ['updated_by'], ['id'])
    
    # Add unique constraint and indexes for user_roles
    op.create_unique_constraint('uq_user_role_org_dept', 'user_roles', 
                                ['user_id', 'role_id', 'organization_id', 'department_id'])
    op.create_index('ix_user_roles_expires_at', 'user_roles', ['expires_at'])
    op.create_index('ix_user_roles_is_active', 'user_roles', ['is_active'])


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop indexes and constraints for user_roles
    op.drop_index('ix_user_roles_is_active', 'user_roles')
    op.drop_index('ix_user_roles_expires_at', 'user_roles')
    op.drop_constraint('uq_user_role_org_dept', 'user_roles', type_='unique')
    op.drop_constraint('fk_user_roles_updated_by', 'user_roles', type_='foreignkey')
    op.drop_constraint('fk_user_roles_created_by', 'user_roles', type_='foreignkey')
    op.drop_constraint('fk_user_roles_approved_by', 'user_roles', type_='foreignkey')
    
    # Drop columns from user_roles
    op.drop_column('user_roles', 'updated_by')
    op.drop_column('user_roles', 'created_by')
    op.drop_column('user_roles', 'approved_at')
    op.drop_column('user_roles', 'approved_by')
    op.drop_column('user_roles', 'approval_status')
    op.drop_column('user_roles', 'notes')
    op.drop_column('user_roles', 'is_primary')
    op.drop_column('user_roles', 'is_active')
    op.drop_column('user_roles', 'valid_from')
    op.drop_column('user_roles', 'assigned_at')
    
    # Drop indexes and constraints for roles
    op.drop_index('ix_roles_deleted_at', 'roles')
    op.drop_index('ix_roles_is_deleted', 'roles')
    op.drop_constraint('fk_roles_deleted_by', 'roles', type_='foreignkey')
    op.drop_constraint('fk_roles_updated_by', 'roles', type_='foreignkey')
    op.drop_constraint('fk_roles_created_by', 'roles', type_='foreignkey')
    op.drop_constraint('fk_roles_parent_id', 'roles', type_='foreignkey')
    
    # Drop columns from roles
    op.drop_column('roles', 'updated_by')
    op.drop_column('roles', 'created_by')
    op.drop_column('roles', 'is_deleted')
    op.drop_column('roles', 'deleted_by')
    op.drop_column('roles', 'deleted_at')
    op.drop_column('roles', 'color')
    op.drop_column('roles', 'icon')
    op.drop_column('roles', 'display_order')
    op.drop_column('roles', 'is_system')
    op.drop_column('roles', 'permissions')
    op.drop_column('roles', 'parent_id')
    op.drop_column('roles', 'role_type')
    op.drop_column('roles', 'name_en')
    
    # Drop indexes and constraints for departments
    op.drop_index('ix_departments_deleted_at', 'departments')
    op.drop_index('ix_departments_is_deleted', 'departments')
    op.drop_index('ix_departments_parent_id', 'departments')
    op.drop_constraint('fk_departments_deleted_by', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_updated_by', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_created_by', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_manager_id', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_parent_id', 'departments', type_='foreignkey')
    
    # Drop columns from departments
    op.drop_column('departments', 'updated_by')
    op.drop_column('departments', 'created_by')
    op.drop_column('departments', 'is_deleted')
    op.drop_column('departments', 'deleted_by')
    op.drop_column('departments', 'deleted_at')
    op.drop_column('departments', 'description')
    op.drop_column('departments', 'display_order')
    op.drop_column('departments', 'cost_center_code')
    op.drop_column('departments', 'department_type')
    op.drop_column('departments', 'headcount_limit')
    op.drop_column('departments', 'budget')
    op.drop_column('departments', 'location')
    op.drop_column('departments', 'email')
    op.drop_column('departments', 'fax')
    op.drop_column('departments', 'phone')
    op.drop_column('departments', 'manager_id')
    op.drop_column('departments', 'parent_id')
    op.drop_column('departments', 'short_name')
    op.drop_column('departments', 'name_en')
    op.drop_column('departments', 'name_kana')
    
    # Drop indexes and constraints for organizations
    op.drop_index('ix_organizations_deleted_at', 'organizations')
    op.drop_index('ix_organizations_is_deleted', 'organizations')
    op.drop_constraint('fk_organizations_deleted_by', 'organizations', type_='foreignkey')
    op.drop_constraint('fk_organizations_updated_by', 'organizations', type_='foreignkey')
    op.drop_constraint('fk_organizations_created_by', 'organizations', type_='foreignkey')
    op.drop_constraint('fk_organizations_parent_id', 'organizations', type_='foreignkey')
    
    # Drop columns from organizations
    op.drop_column('organizations', 'updated_by')
    op.drop_column('organizations', 'created_by')
    op.drop_column('organizations', 'is_deleted')
    op.drop_column('organizations', 'deleted_by')
    op.drop_column('organizations', 'deleted_at')
    op.drop_column('organizations', 'logo_url')
    op.drop_column('organizations', 'description')
    op.drop_column('organizations', 'settings')
    op.drop_column('organizations', 'parent_id')
    op.drop_column('organizations', 'fiscal_year_end')
    op.drop_column('organizations', 'employee_count')
    op.drop_column('organizations', 'capital')
    op.drop_column('organizations', 'industry')
    op.drop_column('organizations', 'business_type')
    op.drop_column('organizations', 'address_line2')
    op.drop_column('organizations', 'address_line1')
    op.drop_column('organizations', 'city')
    op.drop_column('organizations', 'prefecture')
    op.drop_column('organizations', 'postal_code')
    op.drop_column('organizations', 'website')
    op.drop_column('organizations', 'email')
    op.drop_column('organizations', 'fax')
    op.drop_column('organizations', 'phone')
    op.drop_column('organizations', 'name_en')
    op.drop_column('organizations', 'name_kana')