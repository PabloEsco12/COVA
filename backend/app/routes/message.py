# backend/app/routes/messages.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Message, Conversation, Utilisateur, Participation
from ..extensions import db
from ..schemas_message import MessageSchema
from marshmallow import ValidationError

messages_bp = Blueprint("messages", __name__)

# Lister les messages d'une conversation
@messages_bp.route("/conversations/<int:conv_id>/messages/", methods=["GET"])
@jwt_required()
def list_messages(conv_id):
    # Vérification que la conversation existe et que l'utilisateur y participe
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    # Optionnel: vérifier la participation
    if not any(p.id_user == user_id for p in conv.participations):
        return jsonify({"error": "Accès refusé"}), 403

    messages = Message.query.filter_by(conv_id=conv_id).order_by(Message.ts_msg.asc()).all()
    return jsonify(MessageSchema(many=True).dump(messages)), 200

# Envoyer un message
@messages_bp.route("/conversations/<int:conv_id>/messages/", methods=["POST"])
@jwt_required()
def send_message(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    # Optionnel: vérifier la participation
    if not any(p.id_user == user_id for p in conv.participations):
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json()
    try:
        data = MessageSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation", "messages": err.messages}), 422

    msg = Message(
        contenu_chiffre=data["contenu_chiffre"],
        sender_id=user_id,
        conv_id=conv_id,
        ts_msg=None  # Laisse la valeur par défaut (maintenant)
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify(MessageSchema().dump(msg)), 201

@messages_bp.route("/conversations/<int:conv_id>/messages/<int:msg_id>", methods=["PUT", "DELETE"])
@jwt_required()
def update_or_delete_message(conv_id, msg_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.filter_by(id_msg=msg_id, conv_id=conv_id).first()
    if not msg:
        return jsonify({"error": "Message introuvable"}), 404

    # Ensuite selon la méthode...
    if request.method == "PUT":
        if msg.sender_id != user_id:
            return jsonify({"error": "Non autorisé"}), 403
        data = request.get_json()
        msg.contenu_chiffre = data["contenu_chiffre"]
        db.session.commit()
        return jsonify(MessageSchema().dump(msg)), 200
    elif request.method == "DELETE":
        is_author = (msg.sender_id == user_id)
        is_admin = any(
            p.id_user == user_id and p.role == "admin"
            for p in msg.conversation.participations
        ) if msg.conversation else False

        if not (is_author or is_admin):
            return jsonify({"error": "Non autorisé"}), 403
        db.session.delete(msg)
        db.session.commit()
        return jsonify({"message": "Message supprimé"}), 200
    
# ─────────────────────────── Nombre de messages non lus ──────────────────────
@messages_bp.route("/messages/unread_count", methods=["GET"])  # CORS preflight handled globally
@jwt_required()
def unread_count():
    """Retourne un compte très simple de messages non lus pour l'utilisateur"""
    user_id = int(get_jwt_identity())

    conv_ids = [p.id_conv for p in Participation.query.filter_by(id_user=user_id)]
    if not conv_ids:
        return jsonify({"count": 0}), 200

    count = Message.query.filter(
        Message.conv_id.in_(conv_ids),
        Message.sender_id != user_id
    ).count()

    return jsonify({"count": count}), 200


