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

# Autoriser frontend local ET domaine en prod
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://covamessagerie.be",
    "https://www.covamessagerie.be"
]

socketio = SocketIO(cors_allowed_origins=ALLOWED_ORIGINS, async_mode="eventlet")


# --- Callbacks pour la révocation ---
from .models import RefreshToken


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = RefreshToken.query.filter_by(jti=jti).first()
    # Si le token existe ET qu'il est révoqué → bloque-le
    return token is not None and token.revoked

