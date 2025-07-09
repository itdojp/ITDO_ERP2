"""Add department collaborations table

Revision ID: 008
Revises: 007
Create Date: 2024-07-09 19:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create department_collaborations table."""
    op.create_table(
        "department_collaborations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_a_id", sa.Integer(), nullable=False),
        sa.Column("department_b_id", sa.Integer(), nullable=False),
        sa.Column("collaboration_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("approval_status", sa.String(length=20), nullable=False, default="pending"),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_until", sa.DateTime(), nullable=True),
        sa.Column("approved_by_a", sa.Integer(), nullable=True),
        sa.Column("approved_by_b", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["department_a_id"], ["departments.id"], name="fk_dept_collab_dept_a"
        ),
        sa.ForeignKeyConstraint(
            ["department_b_id"], ["departments.id"], name="fk_dept_collab_dept_b"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_a"], ["users.id"], name="fk_dept_collab_approved_by_a"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_b"], ["users.id"], name="fk_dept_collab_approved_by_b"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_dept_collab_created_by"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_dept_collab_updated_by"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name="fk_dept_collab_deleted_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Add indexes
    op.create_index(
        "ix_dept_collab_dept_a_id", "department_collaborations", ["department_a_id"]
    )
    op.create_index(
        "ix_dept_collab_dept_b_id", "department_collaborations", ["department_b_id"]
    )
    op.create_index(
        "ix_dept_collab_is_active", "department_collaborations", ["is_active"]
    )
    op.create_index(
        "ix_dept_collab_approval_status", "department_collaborations", ["approval_status"]
    )
    op.create_index(
        "ix_dept_collab_collaboration_type", "department_collaborations", ["collaboration_type"]
    )
    
    # Add unique constraint to prevent duplicate collaborations
    op.create_index(
        "ix_dept_collab_unique_active",
        "department_collaborations",
        ["department_a_id", "department_b_id", "is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = true AND is_deleted = false"),
    )


def downgrade() -> None:
    """Drop department_collaborations table."""
    op.drop_table("department_collaborations")