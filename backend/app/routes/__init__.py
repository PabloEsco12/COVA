from .auth import auth_bp
from .conversation import conversation_bp
from .message import messages_bp
from .contacts import contacts_bp
from .totp import totp_bp
from .audit import audit_bp
from .admin import admin_bp
from .reset import reset_bp
from .profile import profile_bp
from .devices import devices_bp
from .health import health_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(conversation_bp, url_prefix="/api/conversations")
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(contacts_bp, url_prefix="/api")
    app.register_blueprint(totp_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(reset_bp, url_prefix="/api")
    app.register_blueprint(profile_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(health_bp)
