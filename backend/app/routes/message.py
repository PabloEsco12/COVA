from __future__ import annotations

import hashlib
import os
from typing import Iterable, Tuple
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased

from ..extensions import db, limiter, socketio
from ..models import Conversation, File, Message, Participation, Reaction, MessageStatus
from ..schemas_message import MessageSchema

messages_bp = Blueprint("messages", __name__)


def _message_schema(user_id: int | None = None, *, many: bool = False) -> MessageSchema:
    context = {"user_id": user_id} if user_id is not None else {}
    return MessageSchema(many=many, context=context)


def _user_is_participant(conv: Conversation, user_id: int) -> bool:
    return any(p.id_user == user_id for p in conv.participations)


def _original_name(path: str) -> str:
    _, _, original = path.partition("_")
    return original or path


def _extract_payload_and_files() -> Tuple[dict, list]:
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        payload = {"contenu_chiffre": request.form.get("contenu_chiffre", "")}
        files = request.files.getlist("files")
    else:
        payload = request.get_json() or {}
        files = []
    return payload, files


def _store_uploaded_file(upload) -> dict | None:
    if upload is None or not getattr(upload, "filename", ""):
        return None
    filename = upload.filename
    safe_name = secure_filename(filename or "")
    if not safe_name:
        return None
    data = upload.read()
    if not data:
        return None
    stored_name = f"{uuid4().hex}_{safe_name}"
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    destination = os.path.join(upload_dir, stored_name)
    with open(destination, "wb") as fh:
        fh.write(data)
    return {
        "stored_name": stored_name,
        "mime": upload.mimetype,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "original": filename,
    }


def _delete_files_from_storage(files: Iterable[File]) -> None:
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    for file_obj in files or []:
        stored_name = getattr(file_obj, "path", None)
        if not stored_name:
            continue
        full_path = os.path.join(upload_dir, stored_name)
        try:
            os.remove(full_path)
        except FileNotFoundError:
            continue
        except OSError:
            continue


# Lister les messages d'une conversation
@messages_bp.route("/conversations/<int:conv_id>/messages/", methods=["GET"])
@jwt_required()
def list_messages(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404
    if not _user_is_participant(conv, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    messages = (
        Message.query.filter_by(conv_id=conv_id)
        .order_by(Message.ts_msg.asc())
        .all()
    )
    schema = _message_schema(user_id, many=True)
    return jsonify(schema.dump(messages)), 200


# Envoyer un message
@messages_bp.route("/conversations/<int:conv_id>/messages/", methods=["POST"])
@jwt_required()
@limiter.limit("30/minute")
def send_message(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404
    if not _user_is_participant(conv, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    raw_payload, uploaded_files = _extract_payload_and_files()
    try:
        data = MessageSchema().load(raw_payload)
    except ValidationError as err:
        return jsonify({"error": "Validation", "messages": err.messages}), 422

    if not data.get("contenu_chiffre", "").strip() and not uploaded_files:
        return jsonify({"error": "Message vide"}), 400

    msg = Message(
        contenu_chiffre=data["contenu_chiffre"],
        sender_id=user_id,
        conv_id=conv_id,
        ts_msg=None,
    )
    db.session.add(msg)
    db.session.flush()

    for upload in uploaded_files:
        saved = _store_uploaded_file(upload)
        if not saved:
            continue
        file_rec = File(
            id_msg=msg.id_msg,
            path=saved["stored_name"],
            mime=saved.get("mime"),
            taille=saved.get("size"),
            sha256=saved.get("sha256"),
        )
    db.session.add(file_rec)

    db.session.commit()
    payload = _message_schema(user_id).dump(msg)
    rooms = {f"conv_{conv_id}"}
    try:
        participants = conv.participations if conv and hasattr(conv, "participations") else []
        for participation in participants or []:
            rooms.add(f"user_{participation.id_user}")
    except Exception:
        participants = []
    for room in rooms:
        socketio.emit("message_created", payload, to=room)
    return jsonify(payload), 201


@messages_bp.route("/conversations/<int:conv_id>/messages/<int:msg_id>", methods=["PUT", "DELETE"])
@jwt_required()
def update_or_delete_message(conv_id, msg_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.filter_by(id_msg=msg_id, conv_id=conv_id).first()
    if not msg:
        return jsonify({"error": "Message introuvable"}), 404

    if request.method == "PUT":
        if msg.sender_id != user_id:
            return jsonify({"error": "Non autorisé"}), 403
        data = request.get_json() or {}
        if "contenu_chiffre" not in data:
            return jsonify({"error": "Contenu manquant"}), 400
        msg.contenu_chiffre = data["contenu_chiffre"]
        db.session.commit()
        return jsonify(_message_schema(user_id).dump(msg)), 200

    is_author = msg.sender_id == user_id
    is_admin = any(
        p.id_user == user_id and p.role == "admin"
        for p in (msg.conversation.participations if msg.conversation else [])
    )
    if not (is_author or is_admin):
        return jsonify({"error": "Non autorisé"}), 403

    _delete_files_from_storage(msg.files)
    db.session.delete(msg)
    db.session.commit()
    return jsonify({"message": "Message supprimé"}), 200


@messages_bp.route("/messages/files/<int:file_id>", methods=["GET"])
@jwt_required()
def download_file(file_id):
    user_id = int(get_jwt_identity())
    file_obj = File.query.get(file_id)
    if not file_obj or not file_obj.message:
        return jsonify({"error": "Fichier introuvable"}), 404

    conv = file_obj.message.conversation
    if not conv or not _user_is_participant(conv, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    stored_name = file_obj.path
    if not stored_name:
        return jsonify({"error": "Fichier introuvable"}), 404
    original = _original_name(stored_name)
    try:
        return send_from_directory(
            upload_dir,
            stored_name,
            mimetype=file_obj.mime or None,
            as_attachment=False,
            download_name=original,
        )
    except FileNotFoundError:
        return jsonify({"error": "Fichier introuvable"}), 404


@messages_bp.route("/messages/<int:msg_id>/reactions", methods=["POST"])
@jwt_required()
@limiter.limit("60/minute")
def toggle_reaction(msg_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"error": "Message introuvable"}), 404
    conv = msg.conversation
    if not conv or not _user_is_participant(conv, user_id):
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    emoji = (data.get("emoji") or "").strip()
    if not emoji:
        return jsonify({"error": "Emoji requis"}), 400
    if len(emoji) > 8:
        return jsonify({"error": "Emoji invalide"}), 400

    existing = Reaction.query.filter_by(id_msg=msg_id, id_user=user_id, emoji=emoji).first()
    if existing:
        db.session.delete(existing)
        action = "removed"
    else:
        new_reaction = Reaction(id_msg=msg_id, id_user=user_id, emoji=emoji)
        db.session.add(new_reaction)
        action = "added"

    db.session.commit()
    schema = _message_schema(user_id)
    message_payload = schema.dump(msg)
    payload = {
        "message_id": msg_id,
        "status": action,
        "reactions": message_payload.get("reactions", []),
        "reaction_summary": message_payload.get("reaction_summary", []),
        "conv_id": msg.conv_id,
        "user_id": user_id,
    }
    socketio.emit("reaction_updated", payload, to=f"conv_{msg.conv_id}")
    return jsonify(payload), 200


# Nombre de messages non lus
@messages_bp.route("/messages/unread_count", methods=["GET"])  # CORS preflight handled globally
@jwt_required()
@limiter.limit("60/minute")
def unread_count():
    user_id = int(get_jwt_identity())
    status_alias = aliased(MessageStatus)
    count = (
        db.session.query(func.count(Message.id_msg))
        .join(Participation, Participation.id_conv == Message.conv_id)
        .outerjoin(
            status_alias,
            (status_alias.id_msg == Message.id_msg) & (status_alias.id_user == user_id),
        )
        .filter(
            Participation.id_user == user_id,
            Message.sender_id != user_id,
            or_(status_alias.id_msg.is_(None), status_alias.etat != "read"),
        )
        .scalar()
    )
    return jsonify({"count": int(count or 0)}), 200


@messages_bp.route("/messages/unread_summary", methods=["GET"])
@jwt_required()
@limiter.limit("60/minute")
def unread_summary():
    user_id = int(get_jwt_identity())
    status_alias = aliased(MessageStatus)
    rows = (
        db.session.query(
            Message.conv_id.label("conv_id"),
            func.count(Message.id_msg).label("unread_count"),
        )
        .join(Participation, Participation.id_conv == Message.conv_id)
        .outerjoin(
            status_alias,
            (status_alias.id_msg == Message.id_msg) & (status_alias.id_user == user_id),
        )
        .filter(
            Participation.id_user == user_id,
            Message.sender_id != user_id,
            or_(status_alias.id_msg.is_(None), status_alias.etat != "read"),
        )
        .group_by(Message.conv_id)
        .all()
    )
    by_conv = {str(conv_id): int(count or 0) for conv_id, count in rows}
    total = int(sum(by_conv.values()))
    return jsonify({"total": total, "by_conversation": by_conv}), 200


# Utilities imported late to avoid circular import
from werkzeug.utils import secure_filename  # noqa: E402  pylint: disable=wrong-import-position
