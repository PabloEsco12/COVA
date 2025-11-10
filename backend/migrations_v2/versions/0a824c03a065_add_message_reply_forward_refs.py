"""Add reply and forward references to messages table."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0a824c03a065"
down_revision = "b8c46d42ace9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("reply_to_message_id", sa.UUID(), nullable=True))
    op.add_column("messages", sa.Column("forward_from_message_id", sa.UUID(), nullable=True))

    op.create_foreign_key(
        "fk_messages_reply_to_message_id",
        "messages",
        "messages",
        ["reply_to_message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_messages_forward_from_message_id",
        "messages",
        "messages",
        ["forward_from_message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_messages_forward_from_message_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_reply_to_message_id", "messages", type_="foreignkey")
    op.drop_column("messages", "forward_from_message_id")
    op.drop_column("messages", "reply_to_message_id")
