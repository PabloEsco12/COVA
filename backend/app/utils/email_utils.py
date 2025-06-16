import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_reset_email(dest_email, reset_link):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USER = "covamessages@gmail.com"
    SMTP_PASSWORD = "fsfrucysebbjvdqj"  # Ton mot de passe d’application

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = dest_email
    msg["Subject"] = "Réinitialisation de mot de passe - COVA"

    html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;background:#f8fafc;padding:32px;">
        <div style="background:#fff;border-radius:13px;padding:28px 36px;max-width:460px;margin:auto;box-shadow:0 2px 16px #2b6cb021;">
          <img src='https://i.imgur.com/ENajk29.png' width='56' style='margin-bottom:15px;border-radius:8px;box-shadow:0 2px 10px #1959c278;' alt='COVA logo' />
          <h2 style="color:#183c87;margin-bottom:12px;">Réinitialisation de mot de passe</h2>
          <p style="color:#1b2845;font-size:1.1em;">
            Bonjour,<br><br>
            Tu as demandé la réinitialisation de ton mot de passe pour ton compte <b>COVA</b>.
          </p>
          <p style="margin:20px 0;">
            <a href="{reset_link}" style="background:#1959c2;color:#fff;padding:13px 30px;border-radius:9px;text-decoration:none;font-size:1.14em;font-weight:600;">
              Réinitialiser mon mot de passe
            </a>
          </p>
          <div style="color:#8a93a3;font-size:0.99em;">
            Ce lien est valable 1h. Si tu n’es pas à l’origine de cette demande, ignore simplement ce mail.<br><br>
            Merci de ta confiance.<br>
            <b>L’équipe COVA</b>
          </div>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

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
