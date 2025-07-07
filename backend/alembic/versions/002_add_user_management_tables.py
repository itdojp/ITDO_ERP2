"""Add user management tables.

Revision ID: 002
Revises: 001
Create Date: 2024-01-06 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user management tables."""

    # Add columns to users table
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('profile_image_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True),
                                    server_default=sa.func.now()))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(),
                                    server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_must_change', sa.Boolean(),
                                    server_default='false'))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('created_by', sa.Integer(), nullable=True))

    # Add foreign keys
    op.create_foreign_key('fk_users_deleted_by', 'users', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_users_created_by', 'users', 'users', ['created_by'], ['id'])

    # Create password_history table
    op.create_table('password_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_password_history_user_id', 'password_history', ['user_id'])

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('refresh_token', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('requires_verification', sa.Boolean(), server_default='false'),
        sa.Column('security_alert', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_sessions_session_token', 'user_sessions', ['session_token'], unique=True)
    op.create_index('ix_user_sessions_refresh_token', 'user_sessions', ['refresh_token'], unique=True)
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])

    # Create user_activity_logs table
    op.create_table('user_activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', sa.JSON(), server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_activity_logs_user_id', 'user_activity_logs', ['user_id'])
    op.create_index('ix_user_activity_logs_action', 'user_activity_logs', ['action'])
    op.create_index('ix_user_activity_logs_created_at', 'user_activity_logs', ['created_at'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('changes', sa.JSON(), server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_organization_id', 'audit_logs', ['organization_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop user management tables."""

    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('user_activity_logs')
    op.drop_table('user_sessions')
    op.drop_table('password_history')

    # Drop foreign keys
    op.drop_constraint('fk_users_created_by', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')

    # Drop columns from users table
    op.drop_column('users', 'created_by')
    op.drop_column('users', 'deleted_by')
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'password_must_change')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'profile_image_url')
    op.drop_column('users', 'phone')
