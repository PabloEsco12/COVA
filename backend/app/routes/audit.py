from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import LogAudit, Utilisateur   # Assure-toi que ces modèles existent
from ..extensions import db  # Si besoin pour d'autres opérations

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")

# Récupérer les logs de l'utilisateur courant
@audit_bp.route("/logs", methods=["GET"])
@jwt_required()
def get_my_logs():
    user_id = get_jwt_identity()
    logs = LogAudit.query.filter_by(id_user=user_id).order_by(LogAudit.ts.desc()).all()
    return jsonify([{
        "id": l.id_log,
        "action": l.action,
        "ip": l.ip,
        "ts": l.ts.isoformat(),
        "meta": l.meta
    } for l in logs]), 200

# Récupérer tous les logs (réservé à l'admin)
@audit_bp.route("/logs/all", methods=["GET"])
@jwt_required()
def get_all_logs():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Accès interdit"}), 403
    logs = LogAudit.query.order_by(LogAudit.ts.desc()).all()
    return jsonify([{
        "id": l.id_log,
        "user_id": l.id_user,
        "action": l.action,
        "ip": l.ip,
        "ts": l.ts.isoformat(),
        "meta": l.meta
    } for l in logs]), 200
