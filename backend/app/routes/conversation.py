# backend/app/routes/conversation.py

from flask import Blueprint, request, jsonify, current_app
from uuid import uuid4

from ..models import Conversation, Participation, Utilisateur, CallSession
from ..extensions import db, socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

conversation_bp = Blueprint("conversation", __name__)


def _serialize_call(call: CallSession) -> dict:
    if not call:
        return {}
    initiator = getattr(call, "initiator", None)
    return {
        "id": call.id_call,
        "conv_id": call.conv_id,
        "initiator_id": call.initiator_id,
        "initiator": {
            "id_user": getattr(initiator, "id_user", None),
            "pseudo": getattr(initiator, "pseudo", None),
        } if initiator else None,
        "initiator_pseudo": getattr(initiator, "pseudo", None) if initiator else None,
        "call_type": call.call_type,
        "room_name": call.room_name,
        "join_url": call.join_url,
        "started_at": call.started_at.isoformat() if call.started_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
    }

# ─────────────────────────── Liste toutes les conversations de l’utilisateur ───────────────────────────
@conversation_bp.route("/", methods=["GET"])
@jwt_required()
def list_conversations():
    user_id = get_jwt_identity()
    participations = Participation.query.filter_by(id_user=int(user_id)).all()
    conversations = [
        {
            "id": p.conversation.id_conv,
            "titre": p.conversation.titre,
            "is_group": p.conversation.is_group,
            "date_crea": p.conversation.date_crea.isoformat()
        }
        for p in participations
    ]
    return jsonify(conversations), 200

# ─────────────────────────── Crée une nouvelle conversation ───────────────────────────
@conversation_bp.route("/", methods=["POST"])
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    titre = data.get("titre")
    is_group = bool(data.get("is_group", False))
    participants = data.get("participants", [])

    if not titre:
        return jsonify({"error": "Titre requis"}), 400

    # Toujours ajouter le créateur s'il n'est pas déjà dans la liste
    participants = set([int(user_id)] + [int(pid) for pid in participants if int(pid) != int(user_id)])

    conv = Conversation(
        titre=titre,
        is_group=is_group,
        date_crea=datetime.utcnow()
    )
    db.session.add(conv)
    db.session.flush()  # On flush pour avoir l'ID avant d'ajouter les participations

    # Ajoute les participations (créateur et membres)
    for pid in participants:
        db.session.add(Participation(
            id_conv=conv.id_conv,
            id_user=pid,
            role="owner" if pid == int(user_id) else "member"
        ))

    db.session.commit()
    return jsonify({"id": conv.id_conv, "message": "Conversation créée"}), 201

# ─────────────────────────── Récupère les infos d’une conversation ───────────────────────────
@conversation_bp.route("/<int:id_conv>", methods=["GET"])
@jwt_required()
def get_conversation(id_conv):
    user_id = get_jwt_identity()
    participation = Participation.query.filter_by(id_conv=id_conv, id_user=int(user_id)).first()
    if not participation:
        return jsonify({"error": "Accès interdit"}), 403

    conv = participation.conversation
    participants = [
        {
            "id_user": p.user.id_user,
            "pseudo": p.user.pseudo,
            "role": p.role
        }
        for p in conv.participations
    ]
    return jsonify({
        "id": conv.id_conv,
        "titre": conv.titre,
        "is_group": conv.is_group,
        "date_crea": conv.date_crea.isoformat(),
        "participants": participants
    }), 200


@conversation_bp.route("/<int:conv_id>/calls", methods=["POST"])
@jwt_required()
def create_call(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    raw_type = data.get("type", "video")
    call_type = raw_type.lower() if isinstance(raw_type, str) else "video"
    if call_type not in {"video", "audio"}:
        return jsonify({"error": "Type d'appel invalide"}), 400

    base_url = (current_app.config.get("CALL_BASE_URL") or "https://meet.jit.si").rstrip("/")
    room_name = f"cova-{conv_id}-{uuid4().hex[:10]}"
    join_url = f"{base_url}/{room_name}"
    if call_type == "audio":
        join_url = f"{join_url}#config.startWithVideoMuted=true&config.startAudioOnly=true"

    try:
        CallSession.__table__.create(db.session.get_bind(), checkfirst=True)
    except Exception:
        current_app.logger.exception("call_session table creation failed")

    call = CallSession(
        conv_id=conv_id,
        initiator_id=user_id,
        call_type=call_type,
        room_name=room_name,
        join_url=join_url,
    )
    db.session.add(call)
    db.session.commit()

    payload = _serialize_call(call)
    socketio.emit("call_created", payload, to=f"conv_{conv_id}")

    return jsonify(payload), 201


@conversation_bp.route("/<int:conv_id>/calls", methods=["GET"])
@jwt_required()
def list_calls(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation:
        return jsonify({"error": "Accès refusé"}), 403

    try:
        CallSession.__table__.create(db.session.get_bind(), checkfirst=True)
    except Exception:
        current_app.logger.exception("call_session table creation failed")

    calls = (
        CallSession.query.filter_by(conv_id=conv_id)
        .order_by(CallSession.started_at.asc())
        .all()
    )
    return jsonify([_serialize_call(call) for call in calls]), 200


@conversation_bp.route("/<int:conv_id>/calls/<int:call_id>/end", methods=["POST"])
@jwt_required()
def end_call(conv_id, call_id):
    """Mark an ongoing call session as ended and notify participants."""
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation:
        return jsonify({"error": "Accès refusé"}), 403

    try:
        CallSession.__table__.create(db.session.get_bind(), checkfirst=True)
    except Exception:
        current_app.logger.exception("call_session table creation failed")

    call = CallSession.query.filter_by(id_call=call_id, conv_id=conv_id).first()
    if not call:
        return jsonify({"error": "Appel introuvable"}), 404

    if call.ended_at:
        payload = _serialize_call(call)
        socketio.emit("call_ended", payload, to=f"conv_{conv_id}")
        return jsonify(payload), 200

    call.ended_at = datetime.utcnow()
    db.session.commit()

    payload = _serialize_call(call)
    socketio.emit("call_ended", payload, to=f"conv_{conv_id}")
    return jsonify(payload), 200


@conversation_bp.route("/<int:conv_id>/add_member", methods=["POST"])
@jwt_required()
def add_member(conv_id):
    data = request.get_json()
    user_id_to_add = data.get("user_id")
    if not user_id_to_add:
        return jsonify({"error": "user_id requis"}), 400

    conv = Conversation.query.get(conv_id)
    if not conv or not conv.is_group:
        return jsonify({"error": "Conversation de groupe introuvable"}), 404

    # Vérifier que le demandeur est bien membre
    user_id = int(get_jwt_identity())
    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation:
        return jsonify({"error": "Accès refusé"}), 403

    # Ne pas ajouter si déjà dedans
    if Participation.query.filter_by(id_conv=conv_id, id_user=user_id_to_add).first():
        return jsonify({"error": "Déjà membre"}), 409

    new_part = Participation(id_conv=conv_id, id_user=user_id_to_add, role="member")
    db.session.add(new_part)
    db.session.commit()
    return jsonify({"message": "Membre ajouté"}), 201

@conversation_bp.route("/<int:conv_id>/remove_member", methods=["POST"])
@jwt_required()
def remove_member(conv_id):
    data = request.get_json()
    user_id_to_remove = data.get("user_id")
    if not user_id_to_remove:
        return jsonify({"error": "user_id requis"}), 400

    conv = Conversation.query.get(conv_id)
    if not conv or not conv.is_group:
        return jsonify({"error": "Conversation de groupe introuvable"}), 404

    # Seul l’owner ou un admin peut retirer
    user_id = int(get_jwt_identity())
    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation or participation.role not in ("owner", "admin"):
        return jsonify({"error": "Accès refusé"}), 403

    to_remove = Participation.query.filter_by(id_conv=conv_id, id_user=user_id_to_remove).first()
    if not to_remove:
        return jsonify({"error": "Membre à retirer introuvable"}), 404

    db.session.delete(to_remove)
    db.session.commit()
    return jsonify({"message": "Membre retiré"}), 200

@conversation_bp.route("/<int:conv_id>/title", methods=["PATCH"])
@jwt_required()
def update_title(conv_id):
    data = request.get_json()
    titre = data.get("titre")
    if not titre:
        return jsonify({"error": "Titre requis"}), 400

    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    # Seul admin/owner
    user_id = int(get_jwt_identity())
    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation or participation.role not in ("owner", "admin"):
        return jsonify({"error": "Accès refusé"}), 403

    conv.titre = titre
    db.session.commit()
    return jsonify({"message": "Titre modifié"}), 200

@conversation_bp.route("/<int:conv_id>/leave", methods=["POST"])
@jwt_required()
def leave(conv_id):
    user_id = int(get_jwt_identity())
    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation:
        return jsonify({"error": "Non membre"}), 404

    db.session.delete(participation)
    db.session.commit()
    return jsonify({"message": "Vous avez quitté la conversation"}), 200

@conversation_bp.route("/<int:conv_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conv_id):
    user_id = int(get_jwt_identity())
    participation = Participation.query.filter_by(id_conv=conv_id, id_user=user_id).first()
    if not participation or participation.role != "owner":
        return jsonify({"error": "Seul le propriétaire peut supprimer"}), 403

    conv = Conversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation introuvable"}), 404

    db.session.delete(conv)
    db.session.commit()
    return jsonify({"message": "Conversation supprimée"}), 200



