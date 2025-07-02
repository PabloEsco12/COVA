# backend/app/routes/auth.py

from flask import Blueprint, request, jsonify, current_app
from ..models import Utilisateur, RefreshToken,EmailConfirmToken
from ..extensions import db, bcrypt
from ..schemas import RegisterSchema, LoginSchema
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
import pyotp
from marshmallow import ValidationError
from .audit_utils import log_action
from ..utils.email_utils import send_confirm_email,send_login_notification
from ..utils.geoip_utils import geoip_lookup
import secrets
import requests


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"}), 200

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = RegisterSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Validation", "messages": err.messages}), 422

    role = "member"
    if "role" in data and data["role"] == "admin":
        admin_exists = Utilisateur.query.filter_by(role="admin").first()
        if not admin_exists or data["email"].endswith("@tondomaine.com"):
            role = "admin"
        else:
            return jsonify({"error": "Création admin refusée"}), 403

    if Utilisateur.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email déjà utilisé"}), 409

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    user = Utilisateur(
        email=data["email"],
        pseudo=data["pseudo"],
        password_hash=hashed_pw,
        role=role,
        date_crea=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()

    # 1. Génère un token de confirmation

    token = secrets.token_urlsafe(48)
    expires = datetime.utcnow() + timedelta(hours=24)
    confirm_token = EmailConfirmToken(
        user_id=user.id_user,
        token=token,
        expires_at=expires,
        used=False
    )
    db.session.add(confirm_token)
    db.session.commit()

    # 2. Envoie l’e-mail
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    confirm_link = f"{frontend_url}/confirm-email/{token}"
    send_confirm_email(user.email, confirm_link)

    return jsonify({"message": "Inscription réussie. Un e-mail de confirmation a été envoyé."}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    code = data.get("code")  # Code TOTP (facultatif)

    user = Utilisateur.query.filter_by(email=email).first()

    # 1. Vérifie blocage du TOTP
    if user and user.totp_locked_until and user.totp_locked_until > datetime.utcnow():
        return jsonify({
            "error": "Compte verrouillé suite à trop de tentatives TOTP",
            "unlock_at": user.totp_locked_until.isoformat()
        }), 403

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Identifiants invalides"}), 401
    
    if user and not getattr(user, "is_confirmed", True):
        return jsonify({"error": "Compte non confirmé. Vérifie tes emails."}), 403

    # 2. Vérifie le TOTP si activé
    if user.totp_secret and user.totp_secret.confirmed:
        if not code:
            return jsonify({"require_totp": True, "message": "TOTP requis"}), 401
        totp = pyotp.TOTP(user.totp_secret.secret_base32)
        if not totp.verify(code, valid_window=1):
            # Incrémente le compteur d'échecs
            user.failed_totp_attempts = (user.failed_totp_attempts or 0) + 1
            if user.failed_totp_attempts >= 5:
                user.totp_locked_until = datetime.utcnow() + timedelta(minutes=15)
                user.failed_totp_attempts = 0  # Remise à zéro pour le prochain essai après délai
            db.session.commit()
            log_action(user.id_user, "login_failed_totp", meta={"email": email})
            return jsonify({
                "error": "Code TOTP invalide",
                "failed_attempts": user.failed_totp_attempts,
                "locked_until": user.totp_locked_until.isoformat() if user.totp_locked_until else None
            }), 401
        else:
            # Succès TOTP : remise à zéro du compteur
            user.failed_totp_attempts = 0
            user.totp_locked_until = None
            db.session.commit()

    # 3. Log la connexion réussie
    log_action(user.id_user, "login", meta={"email": email})

    # 4. Génération JWT
    access_token = create_access_token(identity=str(user.id_user), expires_delta=timedelta(hours=1))
    refresh_token = create_refresh_token(identity=str(user.id_user), expires_delta=timedelta(days=30))

    # 5. Enregistre le refresh_token pour révocation future
    from flask_jwt_extended.utils import get_jti
    jti = get_jti(refresh_token)
    token_obj = RefreshToken(jti=jti, id_user=user.id_user, expires=datetime.utcnow() + timedelta(days=30))
    db.session.add(token_obj)
    db.session.commit()

    # 6. Notifie l'utilisateur par e-mail avec toutes les infos
    ip_addr = request.remote_addr
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    user_agent = request.headers.get("User-Agent", "Inconnu")
    location = geoip_lookup(ip_addr)

    send_login_notification(
        user.email,
        ip_addr=ip_addr,
        ts=ts,
        user_agent=user_agent,
        location=location
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id_user,
            "email": user.email,
            "pseudo": user.pseudo
        }
    }), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except Exception:
        return jsonify({"error": "Token invalide"}), 400

    access_token = create_access_token(identity=str(user_id), expires_delta=timedelta(hours=1))
    return jsonify({"access_token": access_token}), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    token = RefreshToken.query.filter_by(jti=jti).first()
    if token:
        token.revoked = True
        db.session.commit()
    return jsonify({"message": "Déconnecté"}), 200

@auth_bp.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token):
    from ..models import EmailConfirmToken
    from datetime import datetime
    confirm_token = EmailConfirmToken.query.filter_by(token=token, used=False).first()
    if not confirm_token or confirm_token.expires_at < datetime.utcnow():
        return jsonify({"error": "Token invalide ou expiré"}), 400

    user = Utilisateur.query.get(confirm_token.user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    # Tu peux prévoir un champ user.is_confirmed = True dans ta table utilisateur
    user.is_confirmed = True
    confirm_token.used = True
    db.session.commit()
    return jsonify({"message": "E-mail confirmé, tu peux maintenant te connecter !"}), 200
