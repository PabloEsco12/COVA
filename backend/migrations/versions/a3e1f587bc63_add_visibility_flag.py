"""Add visibility flag to contact links."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3e1f587bc63"
down_revision = "4f4e8b1604bb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contact_links",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("contact_links", "is_hidden", server_default=None)


def downgrade() -> None:
    op.drop_column("contact_links", "is_hidden")
