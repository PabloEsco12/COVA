import pyotp
import qrcode
import io

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import Utilisateur, TotpSecret
from ..extensions import db

totp_bp = Blueprint("totp", __name__, url_prefix="/api/auth/totp")


# Générer un secret et afficher un QR Code pour Google Authenticator, etc.
@totp_bp.route("/activate", methods=["POST"])
@jwt_required()
def activate_totp():
    try:
        user_id = int(get_jwt_identity())
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        print("user_id:", user_id, "user:", user)

        if user.totp_secret and user.totp_secret.secret_base32:
            secret = user.totp_secret.secret_base32
        else:
            secret = pyotp.random_base32()
            new_secret = TotpSecret(id_user=user_id, secret_base32=secret)
            db.session.add(new_secret)
            db.session.commit()

        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="COVA",
        )
        img = qrcode.make(otp_uri)
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

@totp_bp.route("/confirm", methods=["POST"])
@jwt_required()
def confirm_totp():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    code = str(data.get("code", "")).strip()
    if not code:
        return jsonify({"error": "Code requis"}), 400
    secret = TotpSecret.query.filter_by(id_user=user_id).first()
    if not secret:
        return jsonify({"error": "Aucun secret TOTP"}), 404

    totp = pyotp.TOTP(secret.secret_base32)
    if totp.verify(code, valid_window=1):
        secret.confirmed = True
        db.session.commit()
        return jsonify({"message": "TOTP activé avec succès"}), 200
    else:
        return jsonify({"error": "Code incorrect"}), 400

@totp_bp.route("/deactivate", methods=["POST"])
@jwt_required()
def deactivate_totp():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user or not user.totp_secret:
        return jsonify({"error": "Aucune double authentification activée"}), 400
    db.session.delete(user.totp_secret)
    db.session.commit()
    return jsonify({"message": "Double authentification désactivée"}), 200