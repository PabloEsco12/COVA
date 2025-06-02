# backend/app/audit_utils.py

from flask import request
from ..models import LogAudit
from ..extensions import db

def log_action(user_id, action, meta=None):
    """
    Enregistre une action d’audit (log) dans la base.
    - user_id : id de l’utilisateur concerné
    - action  : nom de l’action (ex : 'login', 'logout', 'activate_totp', etc.)
    - meta    : données complémentaires (dictionnaire)
    """
    log = LogAudit(
        id_user=user_id,
        action=action,
        ip=request.remote_addr,
        meta=meta
    )
    db.session.add(log)
    db.session.commit()
