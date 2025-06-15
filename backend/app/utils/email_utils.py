import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_reset_email(dest_email, reset_link):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465  # Utilisation de SMTP_SSL
    SMTP_USER = "covamessages@gmail.com"
    SMTP_PASSWORD = "fsfrucysebbjvdqj"  # Mot de passe d’application

    # Construction du message
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = dest_email
    msg["Subject"] = "Réinitialisation de votre mot de passe - SecureChat"

    body = f"""\
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe SecureChat.

Cliquez sur ce lien pour réinitialiser votre mot de passe (valable 1h) :
{reset_link}

Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.

Cordialement,
L’équipe SecureChat
"""
    msg.attach(MIMEText(body, "plain"))

    # Envoi de l’e-mail (connexion sécurisée SSL)
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_confirm_email(dest_email, confirm_link):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USER = "covamessages@gmail.com"
    SMTP_PASSWORD = "fsfrucysebbjvdqj"  # ton mot de passe d’application

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = dest_email
    msg["Subject"] = "Confirmation d'inscription - SecureChat"

    body = f"""Bonjour,

Merci pour votre inscription sur SecureChat.

Veuillez confirmer votre inscription en cliquant sur ce lien :
{confirm_link}

Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.

Cordialement,
L’équipe SecureChat
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_login_notification(dest_email, ip_addr, ts, user_agent=None, location=None):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USER = "covamessages@gmail.com"
    SMTP_PASSWORD = "fsfrucysebbjvdqj"

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = dest_email
    msg["Subject"] = "Nouvelle connexion à votre compte SecureChat"

    details = f"""Adresse IP : {ip_addr}
Date et heure : {ts}
"""
    if user_agent:
        details += f"Appareil : {user_agent}\n"
    if location:
        details += f"Localisation : {location}\n"

    body = f"""Bonjour,

Votre compte SecureChat a été accédé avec succès.

{details}
Si ce n’est pas vous, modifiez immédiatement votre mot de passe !

Cordialement,
L’équipe SecureChat
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
