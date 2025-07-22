"""create products simple table

Revision ID: 003_simple
Revises: 002_simple
Create Date: 2025-01-22
"""
from alembic import op
import sqlalchemy as sa

revision = '003_simple'
down_revision = '002_simple'

def upgrade():  # type: ignore[no-untyped-def]
    op.create_table('products_simple',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('stock_quantity', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations_simple.id'])
    )

def downgrade():  # type: ignore[no-untyped-def]
    op.drop_table('products_simple')