"""create products v20 table

Revision ID: 004_v20
Revises: 003_simple
Create Date: 2025-01-22
"""

import sqlalchemy as sa

from alembic import op

revision = "004_v20"
down_revision = "003_simple"


def upgrade():
    op.create_table(
        "products_v20",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=True),
        sa.Column("reorder_level", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_products_v20_code", "products_v20", ["code"])


def downgrade():
    op.drop_index("ix_products_v20_code", "products_v20")
    op.drop_table("products_v20")
