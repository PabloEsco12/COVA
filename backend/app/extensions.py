# backend/app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# --- Extensions principales ---
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(get_remote_address, storage_uri="memory://")

# --- Origines autorisées (dev + prod) ---
ALLOWED_ORIGINS = [
    "http://localhost:5173",        # frontend en dev
    "https://covamessagerie.be",    # domaine principal prod
    "https://www.covamessagerie.be" # domaine avec www
]

# --- Socket.IO (mêmes origines que l’API REST) ---
socketio = SocketIO(cors_allowed_origins=ALLOWED_ORIGINS, async_mode="eventlet")

# --- Callbacks pour la révocation JWT ---
from .models import RefreshToken


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """
    Vérifie si un token JWT est révoqué.
    Retourne True si le token doit être refusé.
    """
    jti = jwt_payload["jti"]
    token = RefreshToken.query.filter_by(jti=jti).first()
    return token is not None and token.revoked
