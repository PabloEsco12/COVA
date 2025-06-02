from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Utilisateur
from ..extensions import db
from datetime import datetime

# Si tu utilises une fonction d’audit :
try:
    from .audit_utils import log_action
except ImportError:
    log_action = lambda *a, **kw: None  # Si pas d'audit dispo, no-op

admin_bp = Blueprint("admin", __name__)  # Nom explicite !

@admin_bp.route("/unlock/<int:user_id>", methods=["POST"])
@jwt_required()
def unlock_user(user_id):
    current_user_id = get_jwt_identity()
    admin = Utilisateur.query.get(current_user_id)

    # Vérifie si l'utilisateur courant est bien admin
    if not admin or getattr(admin, "role", None) != "admin":
        return jsonify({"error": "Accès refusé, privilège admin requis."}), 403

    user = Utilisateur.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    # Remise à zéro du compteur de tentatives et du verrouillage
    user.failed_totp_attempts = 0
    user.totp_locked_until = None
    db.session.commit()

    # Log d’audit (optionnel)
    log_action(admin.id_user, "admin_unlock", meta={
        "unlocked_user_id": user_id,
        "ip": request.remote_addr
    })

    return jsonify({"message": f"Utilisateur {user_id} débloqué avec succès"}), 200

@admin_bp.route("/locked", methods=["GET"])
@jwt_required()
def get_locked_users():
    current_user_id = get_jwt_identity()
    admin = Utilisateur.query.get(current_user_id)

    # Vérifie si l'utilisateur courant est bien admin
    if not admin or getattr(admin, "role", None) != "admin":
        return jsonify({"error": "Accès refusé, privilège admin requis."}), 403

    now = datetime.utcnow()
    locked_users = Utilisateur.query.filter(
        (Utilisateur.failed_totp_attempts >= 5) |
        ((Utilisateur.totp_locked_until != None) & (Utilisateur.totp_locked_until > now))
    ).all()

    return jsonify([
        {
            "id": user.id_user,
            "email": user.email,
            "pseudo": user.pseudo,
            "failed_totp_attempts": getattr(user, "failed_totp_attempts", 0),
            "totp_locked_until": user.totp_locked_until.isoformat() if user.totp_locked_until else None
        }
        for user in locked_users
    ]), 200