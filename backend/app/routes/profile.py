# backend/app/routes/profile.py

import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..models import Utilisateur, LogAudit
from ..extensions import db, bcrypt

profile_bp = Blueprint("profile", __name__, url_prefix="/api/me")

AVATAR_FOLDER = os.path.join("static", "avatars")

# Voir profil
@profile_bp.route("", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({
        "id": user.id_user,
        "email": user.email,
        "pseudo": user.pseudo,
        "avatar": user.avatar if hasattr(user, "avatar") else None,
        "date_crea": user.date_crea.isoformat(),
    }), 200

# Modifier pseudo
@profile_bp.route("/pseudo", methods=["PUT"])
@jwt_required()
def update_pseudo():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    data = request.get_json()
    pseudo = data.get("pseudo", "").strip()
    if not pseudo or len(pseudo) < 2 or len(pseudo) > 50:
        return jsonify({"error": "Le pseudo doit faire entre 2 et 50 caractères"}), 400
    user.pseudo = pseudo
    db.session.commit()
    return jsonify({"message": "Pseudo mis à jour"}), 200

# Modifier email
@profile_bp.route("/email", methods=["PUT"])
@jwt_required()
def update_email():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    data = request.get_json()
    email = data.get("email", "").strip()
    from marshmallow import validate
    try:
        validate.Email()(email)
    except Exception:
        return jsonify({"error": "Email invalide"}), 400
    if Utilisateur.query.filter_by(email=email).first():
        return jsonify({"error": "Email déjà utilisé"}), 409
    user.email = email
    db.session.commit()
    return jsonify({"message": "Email mis à jour"}), 200

# Modifier mot de passe
@profile_bp.route("/password", methods=["PUT"])
@jwt_required()
def update_password():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    data = request.get_json()
    old_pw = data.get("old_password")
    new_pw = data.get("new_password")
    if not old_pw or not bcrypt.check_password_hash(user.password_hash, old_pw):
        return jsonify({"error": "Ancien mot de passe incorrect"}), 401
    # Tu peux importer ta fonction validate_password_strength depuis reset.py si tu veux
    from ..routes.reset import validate_password_strength
    errors = validate_password_strength(new_pw or "")
    if errors:
        return jsonify({"error": "Nouveau mot de passe trop faible", "details": errors}), 400
    user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
    db.session.commit()
    return jsonify({"message": "Mot de passe mis à jour"}), 200

# Upload avatar (image)
@profile_bp.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if "avatar" not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    file = request.files["avatar"]
    if file.filename == "":
        return jsonify({"error": "Fichier vide"}), 400
    filename = secure_filename(f"user_{user_id}_{file.filename}")
    avatar_path = os.path.join(current_app.root_path, AVATAR_FOLDER)
    os.makedirs(avatar_path, exist_ok=True)
    filepath = os.path.join(avatar_path, filename)
    file.save(filepath)
    user.avatar = filename
    db.session.commit()
    return jsonify({
        "message": "Avatar mis à jour",
        "filename": filename,
        "avatar_url": url_for("static", filename=f"avatars/{filename}", _external=True)
    }), 200

# Récupérer l’avatar (protégé, renvoie le fichier)
@profile_bp.route("/avatar", methods=["GET"])
@jwt_required()
def get_avatar():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user or not user.avatar:
        return jsonify({"error": "Aucun avatar"}), 404

    avatar_folder = os.path.join(current_app.root_path, AVATAR_FOLDER)
    avatar_filename = user.avatar
    avatar_full_path = os.path.join(avatar_folder, avatar_filename)
    if not os.path.isfile(avatar_full_path):
        return jsonify({"error": "Fichier avatar manquant sur le serveur"}), 404

    return send_from_directory(avatar_folder, avatar_filename)

# Supprimer avatar
@profile_bp.route("/avatar", methods=["DELETE"])
@jwt_required()
def delete_avatar():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user.avatar:
        return jsonify({"error": "Aucun avatar à supprimer"}), 404
    avatar_path = os.path.join(current_app.root_path, AVATAR_FOLDER, user.avatar)
    if os.path.exists(avatar_path):
        os.remove(avatar_path)
    user.avatar = None
    db.session.commit()
    return jsonify({"message": "Avatar supprimé"}), 200


# Supprimer son compte
@profile_bp.route("", methods=["DELETE"])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    # Suppression en cascade si besoin (messages, tokens, etc.)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Compte supprimé"}), 200

@profile_bp.route("/security", methods=["GET"])
@jwt_required()
def get_security_settings():
    """Retourne les paramètres de sécurité de l’utilisateur"""
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    # Exemple : TOTP activé, notification login
    return jsonify({
        "totp_enabled": bool(user.totp_secret and user.totp_secret.confirmed),
        "notification_login": getattr(user, "notification_login", False)
    }), 200

@profile_bp.route("/security", methods=["PUT"])
@jwt_required()
def update_security_settings():
    """Permet de modifier les options de sécurité simples (notifications, etc.)"""
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    data = request.get_json() or {}
    # Ici, seul notification_login, mais tu peux étendre !
    notif = data.get("notification_login")
    if notif is not None:
        user.notification_login = bool(notif)
    db.session.commit()
    return jsonify({"message": "Paramètres de sécurité mis à jour"}), 200

# ======== LOGS D'AUDIT (consultation) ========

@profile_bp.route("/audit", methods=["GET"])
@jwt_required()
def get_audit_logs():
    """Affiche les derniers logs de l’utilisateur (par défaut 50)"""
    user_id = get_jwt_identity()
    logs = LogAudit.query.filter_by(id_user=user_id).order_by(LogAudit.ts.desc()).limit(50).all()
    logs_list = [{
        "action": l.action,
        "ip": l.ip,
        "timestamp": l.ts.isoformat(),
        "meta": l.meta
    } for l in logs]
    return jsonify(logs_list), 200