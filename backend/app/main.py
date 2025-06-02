"""
backend/app/__main__.py
Point d’entrée du conteneur : `python -m app`
"""
from . import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
