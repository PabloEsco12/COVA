# backend/app/routes/messages.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Message, Conversation, Participation
from ..extensions import db, socketio, limiter
from ..schemas_message import MessageSchema
from marshmallow import ValidationError

messages_bp = Blueprint("messages", __name__)


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
    socketio.emit("message_created", payload, to=f"conv_{conv_id}")
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
            as_attachment=True,
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

    conv_ids = [p.id_conv for p in Participation.query.filter_by(id_user=user_id)]
    if not conv_ids:
        return jsonify({"count": 0}), 200

    count = (
        Message.query.filter(
            Message.conv_id.in_(conv_ids),
            Message.sender_id != user_id,
        ).count()
    )

    return jsonify({"count": count}), 200


# Utilities imported late to avoid circular import
from werkzeug.utils import secure_filename  # noqa: E402  pylint: disable=wrong-import-position

# Utilities imported late to avoid circular import
from werkzeug.utils import secure_filename 