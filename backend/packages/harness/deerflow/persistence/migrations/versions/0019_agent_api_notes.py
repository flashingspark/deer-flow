"""agent-facing notes example.

Revision ID: 0019_agent_api_notes
Revises: 0018_oauth_identity_pg_partial
Create Date: 2026-09-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_agent_api_notes"
down_revision: str | Sequence[str] | None = "0018_oauth_identity_pg_partial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("agent_api_notes"):
        return
    op.create_table(
        "agent_api_notes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_api_notes_user_id", "agent_api_notes", ["user_id"], unique=False)
    op.create_index("ix_agent_api_notes_updated_at", "agent_api_notes", ["updated_at"], unique=False)


def downgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("agent_api_notes"):
        return
    op.drop_index("ix_agent_api_notes_updated_at", table_name="agent_api_notes")
    op.drop_index("ix_agent_api_notes_user_id", table_name="agent_api_notes")
    op.drop_table("agent_api_notes")
