# backend/app/routes/devices.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Utilisateur, Device
from ..extensions import db

devices_bp = Blueprint("devices", __name__, url_prefix="/api/me/devices")

# GET /api/me/devices : liste des devices
@devices_bp.route("", methods=["GET"])
@jwt_required()
def list_devices():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    devices = [
        {
            "id": device.id_device,
            "platform": device.platform,
            "push_token": device.push_token,
            "created_at": device.created_at.isoformat(),
        }
        for device in user.devices
    ]
    return jsonify({"devices": devices}), 200

# POST /api/me/devices : enregistrer un nouvel appareil
@devices_bp.route("", methods=["POST"])
@jwt_required()
def register_device():
    user_id = get_jwt_identity()
    data = request.get_json()
    device_id = data.get("device_id")
    push_token = data.get("push_token")
    platform = data.get("platform", "Web")

    if not device_id or not push_token:
        return jsonify({"error": "device_id et push_token requis"}), 400

    device = Device.query.filter_by(id_device=device_id, id_user=user_id).first()
    if not device:
        device = Device(
            id_device=device_id,
            id_user=user_id,
            push_token=push_token,
            platform=platform
        )
        db.session.add(device)
    else:
        device.push_token = push_token
        device.platform = platform
    db.session.commit()

    return jsonify({"message": "Appareil enregistré"}), 200

# DELETE /api/me/devices/<device_id> : révoquer un appareil
@devices_bp.route("/<device_id>", methods=["DELETE"])
@jwt_required()
def revoke_device(device_id):
    user_id = get_jwt_identity()
    device = Device.query.filter_by(id_device=device_id, id_user=user_id).first()
    if not device:
        return jsonify({"error": "Appareil introuvable"}), 404

    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": "Appareil révoqué"}), 200
