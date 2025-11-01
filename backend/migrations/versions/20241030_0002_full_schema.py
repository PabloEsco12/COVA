"""full security and messaging schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241030_0002"
down_revision = "20241029_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    user_role_enum = sa.Enum("owner", "admin", "member", name="user_role")
    contact_status_enum = sa.Enum("pending", "accepted", "blocked", name="contact_status")
    message_state_enum = sa.Enum("sent", "delivered", "read", "deleted", name="message_state")
    invitation_role_enum = postgresql.ENUM("owner", "admin", "member", name="invitation_role", create_type=False)

    user_role_enum.create(bind, checkfirst=True)
    contact_status_enum.create(bind, checkfirst=True)
    message_state_enum.create(bind, checkfirst=True)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invitation_role') THEN
                CREATE TYPE invitation_role AS ENUM ('owner', 'admin', 'member');
            END IF;
        END $$;
        """
    )

    # users table enhancements
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default=sa.text("'member'")),
    )
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("public_key", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("notification_login", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("failed_totp_attempts", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("users", sa.Column("totp_locked_until", sa.DateTime(timezone=True), nullable=True))

    # contacts table enhancements
    op.add_column(
        "contacts",
        sa.Column("status", contact_status_enum, nullable=False, server_default=sa.text("'pending'")),
    )
    op.add_column(
        "contacts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
    )
    op.create_check_constraint("ck_contacts_not_self", "contacts", "owner_id <> contact_id")

    # devices additional metadata
    op.add_column("devices", sa.Column("platform", sa.String(length=16), nullable=True))
    op.add_column("devices", sa.Column("push_token", sa.Text(), nullable=True))

    # conversations additions
    op.add_column(
        "conversations",
        sa.Column("is_group", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("conversations", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "conversations",
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversations_owner_id_users",
        "conversations",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # conversation members invitations
    op.add_column(
        "conversation_members",
        sa.Column("invited_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversation_members_invited_by",
        "conversation_members",
        "users",
        ["invited_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("ALTER TABLE conversation_members ALTER COLUMN role DROP DEFAULT")
    op.alter_column(
        "conversation_members",
        "role",
        existing_type=sa.String(length=32),
        type_=user_role_enum,
        existing_nullable=False,
        postgresql_using="role::text::user_role",
    )
    op.execute("ALTER TABLE conversation_members ALTER COLUMN role SET DEFAULT 'member'::user_role")

    # messages additions
    op.add_column(
        "messages",
        sa.Column("encryption_header", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("messages", sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("messages", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("ALTER TABLE messages ALTER COLUMN state DROP DEFAULT")
    op.alter_column(
        "messages",
        "state",
        existing_type=sa.String(length=32),
        type_=message_state_enum,
        existing_nullable=False,
        postgresql_using="state::text::message_state",
    )
    op.execute("ALTER TABLE messages ALTER COLUMN state SET DEFAULT 'sent'::message_state")

    # New tables
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "email_confirmation_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "password_reset_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_jti", sa.String(length=36), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_jti", name="uix_refresh_token_jti"),
    )

    op.create_table(
        "totp_secrets",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("secret", sa.String(length=32), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "user_key_pairs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("private_blob", sa.LargeBinary(), nullable=False),
        sa.Column("algorithm", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "archived_conversations",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "conversation_id", name="pk_archived_conversations"),
        sa.UniqueConstraint("user_id", "conversation_id", name="uix_archive_conversation"),
    )

    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inviter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", invitation_role_enum, nullable=False, server_default=sa.text("'member'")),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("token", name="uix_invitation_token"),
    )

    op.create_table(
        "message_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "message_reactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("emoji", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("message_id", "user_id", "emoji", name="uix_message_reaction"),
    )

    # Clean server defaults where appropriate
    op.alter_column("users", "role", server_default=None)
    op.alter_column("users", "notification_login", server_default=None)
    op.alter_column("users", "is_confirmed", server_default=None)
    op.alter_column("users", "failed_totp_attempts", server_default=None)
    op.alter_column("conversations", "is_group", server_default=None)
    op.alter_column("contacts", "status", server_default=None)
    op.alter_column("invitations", "role", server_default=None)
    op.alter_column("messages", "state", server_default=None)


def downgrade() -> None:
    # Drop new tables
    op.drop_table("message_reactions")
    op.drop_table("message_attachments")
    op.drop_table("invitations")
    op.drop_table("archived_conversations")
    op.drop_table("user_key_pairs")
    op.drop_table("totp_secrets")
    op.drop_table("refresh_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("password_reset_attempts")
    op.drop_table("email_confirmation_tokens")
    op.drop_table("audit_logs")

    # Revert messages modifications
    op.execute("ALTER TABLE messages ALTER COLUMN state DROP DEFAULT")
    op.alter_column(
        "messages",
        "state",
        existing_type=sa.Enum(name="message_state"),
        type_=sa.String(length=32),
        existing_nullable=False,
        server_default=sa.text("'sent'"),
        postgresql_using="state::text",
    )
    op.drop_column("messages", "deleted_at")
    op.drop_column("messages", "edited_at")
    op.drop_column("messages", "encryption_header")

    # Revert conversation members
    op.execute("ALTER TABLE conversation_members ALTER COLUMN role DROP DEFAULT")
    op.alter_column(
        "conversation_members",
        "role",
        existing_type=sa.Enum(name="user_role"),
        type_=sa.String(length=32),
        existing_nullable=False,
        server_default=sa.text("'member'"),
        postgresql_using="role::text",
    )
    op.drop_constraint("fk_conversation_members_invited_by", "conversation_members", type_="foreignkey")
    op.drop_column("conversation_members", "invited_by_id")

    # Revert conversations
    op.drop_constraint("fk_conversations_owner_id_users", "conversations", type_="foreignkey")
    op.drop_column("conversations", "settings")
    op.drop_column("conversations", "owner_id")
    op.drop_column("conversations", "is_group")

    # Revert devices
    op.drop_column("devices", "push_token")
    op.drop_column("devices", "platform")

    # Revert contacts
    op.drop_constraint("ck_contacts_not_self", "contacts", type_="check")
    op.drop_column("contacts", "updated_at")
    op.drop_column("contacts", "status")

    # Revert users
    op.drop_column("users", "totp_locked_until")
    op.drop_column("users", "failed_totp_attempts")
    op.drop_column("users", "is_confirmed")
    op.drop_column("users", "notification_login")
    op.drop_column("users", "public_key")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "role")

    # Drop enums
    invitation_role_enum = sa.Enum(name="invitation_role")
    message_state_enum = sa.Enum(name="message_state")
    contact_status_enum = sa.Enum(name="contact_status")
    user_role_enum = sa.Enum(name="user_role")

    invitation_role_enum.drop(op.get_bind(), checkfirst=True)
    message_state_enum.drop(op.get_bind(), checkfirst=True)
    contact_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
