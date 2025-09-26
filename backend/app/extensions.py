from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(get_remote_address, storage_uri="memory://")

# Origines autorisées
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://covamessagerie.be",
    "https://www.covamessagerie.be"
]

# Init Socket.IO (CORS appliqué plus tard dans __init__.py)
socketio = SocketIO(async_mode="eventlet")

from .models import RefreshToken

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = RefreshToken.query.filter_by(jti=jti).first()
    return token is not None and token.revoked
