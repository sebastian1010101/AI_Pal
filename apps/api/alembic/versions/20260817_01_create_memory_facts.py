"""Create memory facts table.

Revision ID: 20260817_01
Revises:
Create Date: 2026-08-17
"""

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260817_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "memory_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=True),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.CheckConstraint("importance >= 0 AND importance <= 1", name="ck_memory_facts_importance"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_facts_session_id", "memory_facts", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_facts_session_id", table_name="memory_facts")
    op.drop_table("memory_facts")
