from flask import request, session
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token

from ..extensions import socketio, db
from ..models import Conversation, Participation, MessageStatus, Message


def _require_auth_from_socketio_auth(auth):
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")
    if not token:
        # Try from query string as fallback
        token = request.args.get("token")
    if not token:
        return None
    try:
        decoded = decode_token(token)
        identity = decoded.get("sub")
        return int(identity) if identity is not None else None
    except Exception:
        return None


@socketio.on("connect")
def on_connect(auth):
    user_id = _require_auth_from_socketio_auth(auth)
    if not user_id:
        return False  # Refuse connection
    session["user_id"] = user_id
    emit("connected", {"user_id": user_id})


@socketio.on("disconnect")
def on_disconnect():
    # Nothing persistent yet. Client rooms will be left automatically.
    pass


@socketio.on("join_conversation")
def on_join_conversation(data):
    user_id = session.get("user_id")
    conv_id = int(data.get("conv_id"))
    if not user_id or not conv_id:
        return
    # Check participation
    is_participant = db.session.query(Participation).filter_by(id_conv=conv_id, id_user=user_id).first() is not None
    if not is_participant:
        emit("error", {"message": "Accès refusé"})
        return
    room = f"conv_{conv_id}"
    join_room(room)
    emit("user_joined", {"user_id": user_id}, to=room, include_self=False)


@socketio.on("leave_conversation")
def on_leave_conversation(data):
    user_id = session.get("user_id")
    conv_id = int(data.get("conv_id"))
    if not user_id or not conv_id:
        return
    room = f"conv_{conv_id}"
    leave_room(room)
    emit("user_left", {"user_id": user_id}, to=room, include_self=False)


@socketio.on("typing")
def on_typing(data):
    user_id = session.get("user_id")
    conv_id = int(data.get("conv_id"))
    is_typing = bool(data.get("is_typing", True))
    if not user_id or not conv_id:
        return
    room = f"conv_{conv_id}"
    emit(
        "typing",
        {"user_id": user_id, "is_typing": is_typing, "conv_id": conv_id},
        to=room,
        include_self=False,
    )


@socketio.on("mark_read")
def on_mark_read(data):
    user_id = session.get("user_id")
    conv_id = int(data.get("conv_id"))
    message_ids = data.get("message_ids") or []
    if not user_id or not conv_id or not message_ids:
        return

    # Verify participation
    is_participant = db.session.query(Participation).filter_by(id_conv=conv_id, id_user=user_id).first() is not None
    if not is_participant:
        emit("error", {"message": "Accès refusé"})
        return

    # Update or create MessageStatus rows
    updated = []
    for mid in message_ids:
        msg = db.session.query(Message).filter_by(id_msg=mid, conv_id=conv_id).first()
        if not msg:
            continue
        # do not mark own message (harmless but skip)
        if msg.sender_id == user_id:
            continue
        st = db.session.query(MessageStatus).filter_by(id_msg=mid, id_user=user_id).first()
        if not st:
            st = MessageStatus(id_msg=mid, id_user=user_id, etat="read")
            db.session.add(st)
        else:
            if st.etat != "read":
                st.etat = "read"
        updated.append(mid)
    if updated:
        db.session.commit()
        emit(
            "message_read",
            {"user_id": user_id, "message_ids": updated, "conv_id": conv_id},
            to=f"conv_{conv_id}",
        )
