"""Add initiated_by_owner flag to contact links."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4f4e8b1604bb"
down_revision = "0a824c03a065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contact_links",
        sa.Column("initiated_by_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("contact_links", "initiated_by_owner", server_default=None)


def downgrade() -> None:
    op.drop_column("contact_links", "initiated_by_owner")
