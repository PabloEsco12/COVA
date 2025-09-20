from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from ..models import Utilisateur
from ..extensions import db, limiter


users_bp = Blueprint("users", __name__)


@users_bp.route("/users/search", methods=["GET"])
@jwt_required()
@limiter.limit("60/minute")
def search_users():
    """Simple recherche d'utilisateurs par email ou pseudo.

    Query params:
      - q: chaîne recherchée (min 2 car.)
      - limit: optionnel, défaut 10
    Retourne: liste [{ id_user, pseudo, email, avatar_url }]
    """
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit") or 10)
    except Exception:
        limit = 10

    if len(q) < 2:
        return jsonify([]), 200

    current_id = int(get_jwt_identity())

    results = (
        Utilisateur.query
        .filter(Utilisateur.id_user != current_id)
        .filter(or_(
            Utilisateur.email.ilike(f"%{q}%"),
            Utilisateur.pseudo.ilike(f"%{q}%"),
        ))
        .order_by(Utilisateur.pseudo.asc())
        .limit(limit)
        .all()
    )

    payload = []
    for u in results:
        avatar_url = None
        try:
            if getattr(u, "avatar", None):
                avatar_url = url_for("static", filename=f"avatars/{u.avatar}", _external=True)
        except Exception:
            avatar_url = None
        payload.append({
            "id_user": u.id_user,
            "pseudo": u.pseudo,
            "email": u.email,
            "avatar_url": avatar_url,
        })

    return jsonify(payload), 200

