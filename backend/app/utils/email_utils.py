import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


logger = logging.getLogger(__name__)


def _get_smtp_settings():
    """Read SMTP configuration from Flask config or environment."""
    try:
        app = current_app._get_current_object()  # type: ignore[attr-defined]
    except Exception:
        app = None

    server = None
    port = None
    user = None
    password = None

    if app is not None:
        server = app.config.get('SMTP_SERVER')
        port = app.config.get('SMTP_PORT')
        user = app.config.get('SMTP_USER')
        password = app.config.get('SMTP_PASSWORD')

    server = server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    port = port or os.getenv('SMTP_PORT', '465')
    user = user or os.getenv('SMTP_USER')
    password = password or os.getenv('SMTP_PASSWORD')

    if not user or not password:
        raise RuntimeError('Missing SMTP credentials; set SMTP_USER and SMTP_PASSWORD')

    return server, int(port), user, password


def _send_message(msg: MIMEMultipart) -> bool:
    server, port, user, password = _get_smtp_settings()
    try:
        with smtplib.SMTP_SSL(server, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.exception('SMTP authentication failed for %s', user)
    except smtplib.SMTPException:
        logger.exception('SMTP error while sending email to %s', msg.get('To'))
    except Exception:
        logger.exception('Unexpected error while sending email to %s', msg.get('To'))
    return False


def _build_from_header():
    return os.getenv('SMTP_FROM') or os.getenv('SMTP_USER', '')


def send_reset_email(dest_email, reset_link) -> bool:
    msg = MIMEMultipart('alternative')
    msg['From'] = _build_from_header()
    msg['To'] = dest_email
    msg['Subject'] = 'Réinitialisation de mot de passe - COVA'

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
            Ce lien est valable 1h. Si tu n'es pas à l'origine de cette demande, ignore simplement ce mail.<br><br>
            Merci de ta confiance.<br>
            <b>L'équipe COVA</b>
          </div>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    return _send_message(msg)


def send_confirm_email(dest_email, confirm_link) -> bool:
    msg = MIMEMultipart('alternative')
    msg['From'] = _build_from_header()
    msg['To'] = dest_email
    msg['Subject'] = "Confirmation d'inscription - COVA"

    html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;background:#f8fafc;padding:32px;">
        <div style="background:#fff;border-radius:13px;padding:28px 36px;max-width:460px;margin:auto;box-shadow:0 2px 16px #2b6cb021;">
          <img src='https://i.imgur.com/ENajk29.png' width='56' style='margin-bottom:15px;border-radius:8px;box-shadow:0 2px 10px #1959c278;' alt='COVA logo' />
          <h2 style="color:#183c87;margin-bottom:12px;">Confirme ton adresse e-mail</h2>
          <p style="color:#1b2845;font-size:1.1em;">
            Bonjour,<br><br>
            Merci de t'être inscrit sur <b>COVA</b>. Clique sur le bouton ci-dessous pour confirmer ton adresse e-mail.
          </p>
          <p style="margin:20px 0;">
            <a href="{confirm_link}" style="background:#1959c2;color:#fff;padding:13px 30px;border-radius:9px;text-decoration:none;font-size:1.14em;font-weight:600;">
              Confirmer mon e-mail
            </a>
          </p>
          <div style="color:#8a93a3;font-size:0.99em;">
            Ce lien est valable 24h. Si tu n'es pas à l'origine de cette inscription, ignore simplement ce message.<br><br>
            Merci de ta confiance.<br>
            <b>L'équipe COVA</b>
          </div>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    return _send_message(msg)


def send_login_notification(dest_email, ip_addr, ts, user_agent=None, location=None) -> bool:
    msg = MIMEMultipart()
    msg['From'] = _build_from_header()
    msg['To'] = dest_email
    msg['Subject'] = 'Nouvelle connexion à votre compte SecureChat'

    details = f"Adresse IP : {ip_addr}\nDate et heure : {ts}\n"
    if user_agent:
        details += f"Appareil : {user_agent}\n"
    if location:
        details += f"Localisation : {location}\n"

    body = f"""Bonjour,

Votre compte SecureChat a été accédé avec succès.

{details}Si ce n'est pas vous, modifiez immédiatement votre mot de passe !

Cordialement,
L'équipe SecureChat
"""
    msg.attach(MIMEText(body, 'plain'))

    return _send_message(msg)
