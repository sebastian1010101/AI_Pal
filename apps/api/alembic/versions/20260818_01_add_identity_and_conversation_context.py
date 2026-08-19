"""Add persistent identity and short-term conversation context.

Revision ID: 20260818_01
Revises: 20260817_01
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260818_01"
down_revision = "20260817_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_memory_facts_session_id", table_name="memory_facts")
    op.alter_column("memory_facts", "session_id", new_column_name="identity_id")
    op.create_index("ix_memory_facts_identity_id", "memory_facts", ["identity_id"])
    op.create_table(
        "conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_conversation_messages_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_messages_context",
        "conversation_messages",
        ["identity_id", "conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_context", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_memory_facts_identity_id", table_name="memory_facts")
    op.alter_column("memory_facts", "identity_id", new_column_name="session_id")
    op.create_index("ix_memory_facts_session_id", "memory_facts", ["session_id"])
