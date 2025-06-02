# seed.py
from backend.app import create_app
from app.extensions import db
from app.models import User, Message
from passlib.hash import bcrypt

def seed_data():
    # On lance l'application Flask
    app = create_app()
    with app.app_context():
        # 1) Créer les tables si elles n'existent pas déjà
        db.drop_all()     # <-- optionnel : efface tout, à ne pas faire en prod
        db.create_all()

        # 2) Insérer des utilisateurs
        u1 = User(
            email="alice@example.com", 
            password_hash=bcrypt.hash("alice123")
        )
        u2 = User(
            email="bob@example.com", 
            password_hash=bcrypt.hash("bob456")
        )
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        # 3) Insérer des messages
        #   Imaginons qu'Alice (u1.id=1) envoie un message à Bob (u2.id=2)
        msg1 = Message(
            content="Hello Bob, how are you?",
            sender_id=u1.id,
            receiver_id=u2.id
        )
        #   Bob répond
        msg2 = Message(
            content="Hi Alice! I'm good, thanks. You?",
            sender_id=u2.id,
            receiver_id=u1.id
        )

        db.session.add(msg1)
        db.session.add(msg2)
        db.session.commit()

        print("✅ Tables créées et données insérées avec succès !")


if __name__ == "__main__":
    seed_data()
