"""Add search_text column for messages search index.

Revision ID: 1f2b3c4d5e6f
Revises: a3e1f587bc63
Create Date: 2025-05-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1f2b3c4d5e6f"
down_revision = "a3e1f587bc63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("search_text", sa.Text(), nullable=True))
    op.create_index(
        "ix_messages_search_text",
        "messages",
        [sa.text("to_tsvector('simple', coalesce(search_text, ''))")],
        postgresql_using="gin",
    )
    # Backfill existing plaintext messages so search continues to work.
    op.execute("update messages set search_text = convert_from(ciphertext, 'UTF8') where encryption_scheme = 'plaintext'")


def downgrade() -> None:
    op.drop_index("ix_messages_search_text", table_name="messages")
    op.drop_column("messages", "search_text")
