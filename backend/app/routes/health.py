from flask import Blueprint, jsonify
from ..extensions import db
from sqlalchemy import text


health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health() -> tuple:
    response = {"status": "ok"}
    try:
        db.session.execute(text("SELECT 1"))
        response["database"] = "ok"
    except Exception as exc:  # pragma: no cover - fallback path
        db.session.rollback()
        response["database"] = "error"
        response["details"] = str(exc)
        return jsonify(response), 503
    return jsonify(response), 200
