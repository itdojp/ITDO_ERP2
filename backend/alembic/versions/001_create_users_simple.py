"""create users simple table

Revision ID: 001_simple
Create Date: 2025-01-22
"""
<<<<<<< HEAD

=======
>>>>>>> main
import sqlalchemy as sa

from alembic import op

<<<<<<< HEAD
revision = "001_simple"
=======
revision = '001_simple'
>>>>>>> main
down_revision = None


def upgrade():  # type: ignore[no-untyped-def]
<<<<<<< HEAD
    op.create_table(
        "users_simple",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
=======
    op.create_table('users_simple',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
>>>>>>> main
    )


def downgrade():  # type: ignore[no-untyped-def]
<<<<<<< HEAD
    op.drop_table("users_simple")
=======
    op.drop_table('users_simple')
>>>>>>> main
