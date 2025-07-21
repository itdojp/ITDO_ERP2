"""Add performance optimization indexes

Revision ID: 001_performance_indexes
Revises: 
Create Date: 2025-01-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for critical queries."""
    
    # Users table indexes
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_org_active', 'users', ['organization_id', 'is_active'])
    op.create_index('idx_users_created_date', 'users', ['created_at'])
    
    # Organizations table indexes
    op.create_index('idx_organizations_code', 'organizations', ['code'])
    op.create_index('idx_organizations_active', 'organizations', ['is_active'])
    
    # Tasks table indexes
    op.create_index('idx_tasks_assignee_status', 'tasks', ['assignee_id', 'status'])
    op.create_index('idx_tasks_project_status', 'tasks', ['project_id', 'status'])
    op.create_index('idx_tasks_priority_due', 'tasks', ['priority', 'due_date'])
    op.create_index('idx_tasks_org_status', 'tasks', ['organization_id', 'status'])
    
    # Customers table indexes (if exists)
    try:
        op.create_index('idx_customers_code_active', 'customers', ['customer_code', 'is_active'])
        op.create_index('idx_customers_org_active', 'customers', ['organization_id', 'is_active'])
        op.create_index('idx_customers_email', 'customers', ['email'])
    except:
        pass  # Table might not exist yet
    
    # Products table indexes (for inventory)
    try:
        op.create_index('idx_products_sku_active', 'products', ['sku', 'is_active'])
        op.create_index('idx_products_category_active', 'products', ['category_id', 'is_active'])
        op.create_index('idx_products_stock_level', 'products', ['current_stock', 'minimum_stock'])
        op.create_index('idx_products_barcode', 'products', ['barcode'])
    except:
        pass  # Table might not exist yet
    
    # Orders table indexes (for order processing)
    try:
        op.create_index('idx_orders_customer_date', 'orders', ['customer_id', 'order_date'])
        op.create_index('idx_orders_status_date', 'orders', ['status', 'order_date'])
        op.create_index('idx_orders_number', 'orders', ['order_number'])
    except:
        pass  # Table might not exist yet
    
    # Audit logs indexes
    try:
        op.create_index('idx_audit_logs_user_date', 'audit_logs', ['user_id', 'created_at'])
        op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
        op.create_index('idx_audit_logs_org_date', 'audit_logs', ['organization_id', 'created_at'])
    except:
        pass  # Table might not exist yet


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop indexes in reverse order
    try:
        op.drop_index('idx_audit_logs_org_date', 'audit_logs')
        op.drop_index('idx_audit_logs_resource', 'audit_logs')
        op.drop_index('idx_audit_logs_user_date', 'audit_logs')
    except:
        pass
    
    try:
        op.drop_index('idx_orders_number', 'orders')
        op.drop_index('idx_orders_status_date', 'orders')
        op.drop_index('idx_orders_customer_date', 'orders')
    except:
        pass
    
    try:
        op.drop_index('idx_products_barcode', 'products')
        op.drop_index('idx_products_stock_level', 'products')
        op.drop_index('idx_products_category_active', 'products')
        op.drop_index('idx_products_sku_active', 'products')
    except:
        pass
    
    try:
        op.drop_index('idx_customers_email', 'customers')
        op.drop_index('idx_customers_org_active', 'customers')
        op.drop_index('idx_customers_code_active', 'customers')
    except:
        pass
    
    op.drop_index('idx_tasks_org_status', 'tasks')
    op.drop_index('idx_tasks_priority_due', 'tasks')
    op.drop_index('idx_tasks_project_status', 'tasks')
    op.drop_index('idx_tasks_assignee_status', 'tasks')
    
    op.drop_index('idx_organizations_active', 'organizations')
    op.drop_index('idx_organizations_code', 'organizations')
    
    op.drop_index('idx_users_created_date', 'users')
    op.drop_index('idx_users_org_active', 'users')
    op.drop_index('idx_users_email_active', 'users')