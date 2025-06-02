# backend/app/error_handlers.py

from flask import jsonify
from flask_jwt_extended.exceptions import (
    NoAuthorizationError, InvalidHeaderError, WrongTokenError,
    RevokedTokenError, FreshTokenRequired, CSRFError
)

def register_error_handlers(app):
    @app.errorhandler(NoAuthorizationError)
    def handle_missing_jwt(e):
        return jsonify({"error": "Token d’authentification manquant"}), 401

    @app.errorhandler(InvalidHeaderError)
    def handle_invalid_header(e):
        return jsonify({"error": "Token JWT invalide (header)"}), 422

    @app.errorhandler(WrongTokenError)
    def handle_wrong_token(e):
        return jsonify({"error": "Type de token incorrect"}), 422

    @app.errorhandler(RevokedTokenError)
    def handle_revoked_token(e):
        return jsonify({"error": "Token révoqué"}), 401

    @app.errorhandler(FreshTokenRequired)
    def handle_fresh_token(e):
        return jsonify({"error": "Token non “fresh”"}), 401

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return jsonify({"error": "Erreur CSRF"}), 401

    # Handler générique pour 401 non JWT
    @app.errorhandler(401)
    def handle_401(e):
        return jsonify({"error": "Non autorisé"}), 401

    # Handler générique pour 404
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Ressource non trouvée"}), 404

    # Handler générique pour 422
    @app.errorhandler(422)
    def handle_422(e):
        return jsonify({"error": "Requête invalide (422)"}), 422

    # Handler générique pour 500
    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Erreur interne du serveur"}), 500
