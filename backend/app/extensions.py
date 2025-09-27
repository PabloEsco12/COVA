from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(get_remote_address, storage_uri="memory://")

# Origines autorisées (surchargeables via CORS_ALLOWED_ORIGINS)
def _parse_origins(value: str):
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]

_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://covamessagerie.be",
    "https://www.covamessagerie.be"
]
ALLOWED_ORIGINS = _parse_origins(os.getenv("CORS_ALLOWED_ORIGINS", "")) or _DEFAULT_ORIGINS

# Init Socket.IO (CORS appliqué plus tard dans __init__.py)
socketio = SocketIO(async_mode="eventlet")

from .models import RefreshToken

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = RefreshToken.query.filter_by(jti=jti).first()
    return token is not None and token.revoked
