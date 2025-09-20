"""
backend/app/__main__.py
Point d’entrée du conteneur : `python -m app`
"""
from . import create_app
from .extensions import socketio

app = create_app()

if __name__ == "__main__":
    # Utilise SocketIO pour activer WebSocket/long-polling
    socketio.run(app, host="0.0.0.0", port=5000)
