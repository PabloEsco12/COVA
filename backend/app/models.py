"""
backend/app/models.py
Représentation ORM complète de la base SecureChat.
Toutes les classes utilisent l’instance unique `db` partagée
(définie dans backend/app/extensions.py).
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .extensions import db

from sqlalchemy import Enum

# Enums
MessageState = Enum("delivered", "read", name="msg_state")
ContactState = Enum("pending", "accepted", "blocked", name="contact_state")
UserRole     = Enum("owner", "admin", "member", name="user_role")

# Tables
class Utilisateur(db.Model):
    __tablename__ = "utilisateur"
    id_user       = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    pseudo        = db.Column(db.String(50), nullable=False)
    role          = db.Column(UserRole, nullable=False, default="member")
    password_hash = db.Column(db.String(200), nullable=False)
    cle_publique  = db.Column(db.Text)
    date_crea     = db.Column(db.DateTime, default=datetime.utcnow)
    failed_totp_attempts = db.Column(db.Integer, default=0)
    totp_locked_until = db.Column(db.DateTime, nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    notification_login = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False)

    sent_messages     = db.relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    devices           = db.relationship("Device", back_populates="user")
    refresh_tokens = db.relationship(
    "RefreshToken",
    back_populates="user",
    cascade="all, delete-orphan",       # <--- important !
    passive_deletes=True                # <--- optionnel mais conseillé
)
    totp_secret       = db.relationship("TotpSecret", uselist=False, back_populates="user")
    key_pair          = db.relationship("KeyPair",  uselist=False, back_populates="user")

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_token"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)
    token = db.Column(db.String(128), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    user = db.relationship("Utilisateur")

class PasswordResetAttempt(db.Model):
    __tablename__ = "password_reset_attempt"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(45))

class Contact(db.Model):
    __tablename__ = "contact"
    id_contact = db.Column(db.Integer, primary_key=True)
    statut     = db.Column(ContactState, nullable=False, default="pending")
    date_maj   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)
    ami_id  = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)

    user = db.relationship("Utilisateur", foreign_keys=[user_id])
    ami  = db.relationship("Utilisateur", foreign_keys=[ami_id])

class Conversation(db.Model):
    __tablename__ = "conversation"
    id_conv   = db.Column(db.Integer, primary_key=True)
    titre     = db.Column(db.String(100))
    is_group  = db.Column(db.Boolean, default=False)
    date_crea = db.Column(db.DateTime, default=datetime.utcnow)

    participations = db.relationship("Participation", back_populates="conversation", cascade="all, delete-orphan")
    messages       = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    settings       = db.relationship("ConvSettings", uselist=False, back_populates="conversation", cascade="all, delete-orphan")

class Participation(db.Model):
    __tablename__ = "participation"
    id_conv = db.Column(db.Integer, db.ForeignKey("conversation.id_conv"), primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    role    = db.Column(UserRole, nullable=False, default="member")

    conversation = db.relationship("Conversation", back_populates="participations")
    user         = db.relationship("Utilisateur", backref=db.backref("participations", cascade="all, delete-orphan"))

class Message(db.Model):
    __tablename__ = "message"
    id_msg          = db.Column(db.Integer, primary_key=True)
    contenu_chiffre = db.Column(db.Text, nullable=False)
    ts_msg          = db.Column(db.DateTime, default=datetime.utcnow)

    sender_id   = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"))
    conv_id     = db.Column(db.Integer, db.ForeignKey("conversation.id_conv"))

    sender       = db.relationship("Utilisateur", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver     = db.relationship("Utilisateur", foreign_keys=[receiver_id], back_populates="received_messages")
    conversation = db.relationship("Conversation", back_populates="messages")

    files     = db.relationship("File", back_populates="message", cascade="all, delete-orphan")
    statuses  = db.relationship("MessageStatus", back_populates="message", cascade="all, delete-orphan")
    reactions = db.relationship("Reaction", back_populates="message", cascade="all, delete-orphan")

class File(db.Model):
    __tablename__ = "file"
    id_file = db.Column(db.Integer, primary_key=True)
    id_msg  = db.Column(db.Integer, db.ForeignKey("message.id_msg"), nullable=False)
    path    = db.Column(db.String(255), nullable=False)
    mime    = db.Column(db.String(80))
    taille  = db.Column(db.Integer)
    sha256  = db.Column(db.String(64))

    message = db.relationship("Message", back_populates="files")

class MessageStatus(db.Model):
    __tablename__ = "message_status"
    id_msg  = db.Column(db.Integer, db.ForeignKey("message.id_msg"), primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    etat    = db.Column(MessageState, nullable=False, default="delivered")
    ts      = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship("Message", back_populates="statuses")
    user    = db.relationship("Utilisateur")

class Reaction(db.Model):
    __tablename__ = "reaction"
    id_msg  = db.Column(db.Integer, db.ForeignKey("message.id_msg"), primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    emoji   = db.Column(db.String(8), primary_key=True)
    ts      = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship("Message", back_populates="reactions")
    user    = db.relationship("Utilisateur")

class RefreshToken(db.Model):
    __tablename__ = "refresh_token"
    jti = db.Column(db.String(36), primary_key=True)  # Le JTI du token JWT
    id_user = db.Column(
    db.Integer,
    db.ForeignKey("utilisateur.id_user", ondelete="CASCADE"),  # <--- important
    nullable=False
)
    expires = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Utilisateur", back_populates="refresh_tokens")

class TotpSecret(db.Model):
    __tablename__ = "totp_secret"
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    secret_base32 = db.Column(db.String(32), nullable=False)
    confirmed     = db.Column(db.Boolean, default=False)

    user = db.relationship("Utilisateur", back_populates="totp_secret")

class Device(db.Model):
    __tablename__ = "device"
    id_device  = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    id_user    = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)
    push_token = db.Column(db.Text, nullable=False)
    platform   = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Utilisateur", back_populates="devices")

class Invitation(db.Model):
    __tablename__ = "invitation"
    uuid_invite = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    email_cible = db.Column(db.String(120), nullable=False)
    id_conv     = db.Column(db.Integer, db.ForeignKey("conversation.id_conv"), nullable=False)
    role_init   = db.Column(UserRole, nullable=False, default="member")
    expire_at   = db.Column(db.DateTime, nullable=False)

    conversation = db.relationship("Conversation")

class LogAudit(db.Model):
    __tablename__ = "log_audit"
    id_log  = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_user = db.Column(
    db.Integer, 
    db.ForeignKey("utilisateur.id_user", ondelete="SET NULL"),
    nullable=True
)
    action  = db.Column(db.String(50), nullable=False)
    ip      = db.Column(db.String(45))
    ts      = db.Column(db.DateTime, default=datetime.utcnow)
    meta    = db.Column(db.JSON)

class KeyPair(db.Model):
    __tablename__ = "key_pair"
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    priv_enc = db.Column(db.LargeBinary, nullable=False)
    pub_key  = db.Column(db.Text, nullable=False)
    algo     = db.Column(db.String(20), nullable=False)
    updated  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("Utilisateur", back_populates="key_pair")

class ConvSettings(db.Model):
    __tablename__ = "conv_settings"
    id_conv        = db.Column(db.Integer, db.ForeignKey("conversation.id_conv"), primary_key=True)
    history_mode   = db.Column(db.Boolean, default=True)
    slow_mode_sec  = db.Column(db.Integer, default=0)
    allowed_files  = db.Column(db.Boolean, default=True)

    conversation = db.relationship("Conversation", back_populates="settings")

class Archive(db.Model):
    __tablename__ = "archive"
    id_user = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), primary_key=True)
    id_conv = db.Column(db.Integer, db.ForeignKey("conversation.id_conv"), primary_key=True)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailConfirmToken(db.Model):
    __tablename__ = "email_confirm_token"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id_user"), nullable=False)
    token = db.Column(db.String(128), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    user = db.relationship("Utilisateur")
