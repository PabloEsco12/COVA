# app/__main__.py

from . import create_app
from .extensions import socketio


def main():
    app = create_app()
    # Use Socket.IO server to support WebSockets and proper CORS handling
    socketio.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
