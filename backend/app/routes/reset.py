import secrets
from flask import Blueprint, request, jsonify, url_for
from datetime import datetime, timedelta
from ..models import Utilisateur, PasswordResetToken, PasswordResetAttempt
from ..extensions import db, bcrypt
from .audit_utils import log_action
from ..utils.email_utils import send_reset_email

reset_bp = Blueprint("reset", __name__)

def validate_password_strength(password):
    import re
    errors = []
    if len(password) < 8:
        errors.append("Le mot de passe doit faire au moins 8 caractères")
    if not re.search(r'[A-Z]', password):
        errors.append("Au moins une majuscule")
    if not re.search(r'[a-z]', password):
        errors.append("Au moins une minuscule")
    if not re.search(r'\d', password):
        errors.append("Au moins un chiffre")
    if not re.search(r'[@$!%*?&.,;:+=_-]', password):
        errors.append("Au moins un caractère spécial (@$!%*?&.,;:+=_-)")
    return errors

@reset_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get("email")
        ip_addr = request.remote_addr

        # --- Anti-bruteforce ---
        une_heure_avant = datetime.utcnow() - timedelta(hours=1)
        tentatives = PasswordResetAttempt.query.filter(
            PasswordResetAttempt.email == email,
            PasswordResetAttempt.requested_at >= une_heure_avant
        ).count()
        if tentatives >= 3:
            return jsonify({"error": "Trop de demandes de réinitialisation. Réessaie plus tard."}), 429

        # Log la tentative (anti-bruteforce)
        db.session.add(PasswordResetAttempt(email=email, ip=ip_addr))
        db.session.commit()

        user = Utilisateur.query.filter_by(email=email).first()
        if not user:
            # Toujours la même réponse
            return jsonify({"message": "Si ce compte existe, un email a été envoyé."}), 200

        # Génère le token
        token = secrets.token_urlsafe(48)
        expires = datetime.utcnow() + timedelta(hours=1)
        PasswordResetToken.query.filter_by(user_id=user.id_user, used=False).update({"used": True})
        reset_token = PasswordResetToken(
            user_id=user.id_user,
            token=token,
            expires_at=expires,
            used=False
        )
        db.session.add(reset_token)
        db.session.commit()

        FRONTEND_URL = "http://localhost:5173/reset-password/"
        reset_link = f"{FRONTEND_URL}{token}"
        send_reset_email(user.email, reset_link)

        # --- Log l’audit ---
        log_action(
            user.id_user,
            "password_reset_requested",
            meta={"email": email, "ip": ip_addr}
        )

        return jsonify({"message": "Si ce compte existe, un email a été envoyé."}), 200
    except Exception as e:
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

@reset_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    try:
        data = request.get_json()
        new_password = data.get("password")

        # Vérifie la complexité
        errors = validate_password_strength(new_password or "")
        if errors:
            return jsonify({"error": "Mot de passe trop faible", "details": errors}), 400

        reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
        if not reset_token or reset_token.expires_at < datetime.utcnow():
            return jsonify({"error": "Token invalide ou expiré"}), 400

        user = Utilisateur.query.get(reset_token.user_id)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        # Change le mot de passe
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        reset_token.used = True
        db.session.commit()

        # Log l’action ici si tu veux (audit)
        # log_action(user.id_user, "reset_password", meta={"ip": request.remote_addr})

        return jsonify({"message": "Mot de passe mis à jour"}), 200
    except Exception as e:
        import traceback
        return jsonify({"error": "Erreur interne", "details": str(e), "trace": traceback.format_exc()}), 500
