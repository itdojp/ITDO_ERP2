"""create organizations simple table

Revision ID: 002_simple
Revises: 001_simple
Create Date: 2025-01-22
"""
from alembic import op
import sqlalchemy as sa

revision = '002_simple'
down_revision = '001_simple'

def upgrade():  # type: ignore[no-untyped-def]
    op.create_table('organizations_simple',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

def downgrade():  # type: ignore[no-untyped-def]
    op.drop_table('organizations_simple')