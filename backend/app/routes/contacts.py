# backend/app/routes/contacts.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Contact, Utilisateur
from ..extensions import db

contacts_bp = Blueprint("contacts", __name__)

# Ajouter un contact (envoyer une invitation)
@contacts_bp.route("/contacts", methods=["POST"])
@jwt_required()
def add_contact():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    ami_id = data.get("ami_id")
    if not ami_id or user_id == ami_id:
        return jsonify({"error": "ami_id requis ou identique à soi-même"}), 400

    # Vérifier que le contact n'existe pas déjà dans les deux sens
    existing = Contact.query.filter(
        ((Contact.user_id == user_id) & (Contact.ami_id == ami_id)) |
        ((Contact.user_id == ami_id) & (Contact.ami_id == user_id))
    ).first()
    if existing:
        return jsonify({"error": "Déjà ajouté ou invitation en attente"}), 409

    c = Contact(user_id=user_id, ami_id=ami_id, statut="pending")
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Contact ajouté, en attente de validation", "id_contact": c.id_contact}), 201

# Accepter/refuser une invitation (uniquement par le destinataire)
@contacts_bp.route("/contacts/<int:contact_id>", methods=["PATCH"])
@jwt_required()
def update_contact(contact_id):
    user_id = int(get_jwt_identity())
    c = Contact.query.get(contact_id)
    if not c:
        return jsonify({"error": "Invitation non trouvée"}), 404
    if c.ami_id != user_id:
        return jsonify({"error": "Non autorisé"}), 403

    statut = request.json.get("statut")
    if statut not in ("accepted", "blocked", "pending"):
        return jsonify({"error": "Statut invalide"}), 400
    c.statut = statut
    db.session.commit()
    return jsonify({"message": f"Statut changé en {statut}"}), 200

# Lister tous ses contacts (possibilité de filtrer par statut)
@contacts_bp.route("/contacts", methods=["GET"])
@jwt_required()
def list_contacts():
    user_id = int(get_jwt_identity())
    statut = request.args.get("statut")
    q = Contact.query.filter(
        ((Contact.user_id == user_id) | (Contact.ami_id == user_id))
    )
    if statut:
        q = q.filter_by(statut=statut)
    contacts = q.all()

    # On récupère les infos utiles de chaque contact
    res = []
    for c in contacts:
        if c.user_id == user_id:
            other_id = c.ami_id
            is_sender = True
        else:
            other_id = c.user_id
            is_sender = False
        res.append({
            "id_contact": c.id_contact,
            "autre_utilisateur": other_id,
            "statut": c.statut,
            "is_sender": is_sender
        })
    return jsonify(res), 200

# Lister les invitations reçues (contacts en attente dont je suis l'ami à valider)
@contacts_bp.route("/contacts/invitations", methods=["GET"])
@jwt_required()
def invitations_recues():
    user_id = int(get_jwt_identity())
    invitations = Contact.query.filter_by(ami_id=user_id, statut="pending").all()
    res = [{
        "id_contact": c.id_contact,
        "demandeur": c.user_id
    } for c in invitations]
    return jsonify(res), 200

# (Optionnel) Supprimer un contact (pour l'un ou l'autre)
@contacts_bp.route("/contacts/<int:contact_id>", methods=["DELETE"])
@jwt_required()
def delete_contact(contact_id):
    user_id = int(get_jwt_identity())
    c = Contact.query.get(contact_id)
    if not c or (c.user_id != user_id and c.ami_id != user_id):
        return jsonify({"error": "Non autorisé"}), 403
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Contact supprimé"}), 200
