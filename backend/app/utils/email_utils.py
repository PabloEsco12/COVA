
import base64

import logging
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

from backend.app.utils._cova_logo_b64 import LOGO_PNG_BASE64


logger = logging.getLogger(__name__)


LOGO_CONTENT_ID = 'cova-brand-logo'
_LOGO_IMAGE_BYTES: bytes | None = None


def _get_logo_bytes() -> bytes | None:
    """Decode the embedded COVA logo once and cache the bytes."""
    global _LOGO_IMAGE_BYTES

    if _LOGO_IMAGE_BYTES is None:
        try:
            _LOGO_IMAGE_BYTES = base64.b64decode(LOGO_PNG_BASE64)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception('Unable to decode the embedded COVA logo asset')
            _LOGO_IMAGE_BYTES = b''

    return _LOGO_IMAGE_BYTES or None


def _attach_logo(msg: MIMEMultipart, logo_bytes: bytes, *, content_id: str = LOGO_CONTENT_ID) -> None:
    """Attach the inline logo to the MIME message."""
    try:
        logo = MIMEImage(logo_bytes, _subtype='png')
    except Exception:  # pragma: no cover - defensive guard
        logger.exception('Unable to create MIMEImage for the COVA logo')
        return

    logo.add_header('Content-ID', f'<{content_id}>')
    logo.add_header('Content-Disposition', 'inline', filename='cova-logo.png')
    msg.attach(logo)


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


def _build_branded_email_html(
    *,
    title: str,
    subtitle: str,
    preheader: str,
    paragraphs: list[str],
    button_label: str,
    button_link: str,
    validity_note: str,
    logo_src: str | None = None,
) -> str:
    paragraph_html = "".join(
        f"<p style=\"margin:0 0 16px;line-height:1.6;color:#273041;font-size:15px;\">{para}</p>"
        for para in paragraphs
    )

    if logo_src:
        logo_markup = (
            f"<img src=\"{logo_src}\" width=\"56\" alt=\"Logo COVA\" "
            "style=\"display:block;border-radius:14px;border:1px solid rgba(255,255,255,0.35);"
            "box-shadow:0 10px 30px rgba(10,35,82,0.45);\" />"
        )
    else:
        logo_markup = (
            "<div style=\"width:56px;height:56px;display:flex;align-items:center;justify-content:center;"
            "font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;font-weight:700;font-size:14px;color:#143f8c;"
            "background:#ffffff;border-radius:14px;border:1px solid rgba(255,255,255,0.35);"
            "box-shadow:0 10px 30px rgba(10,35,82,0.45);\">COVA</div>"
        )

    html = f"""
    <html>
      <body style="margin:0;padding:0;background:#eef2f7;">
        <div style="display:none;font-size:1px;color:#eef2f7;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
          {preheader}
        </div>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef2f7;padding:40px 0;">
          <tr>
            <td align="center" style="padding:0 16px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 18px 45px rgba(12,57,131,0.18);">
                <tr>
                  <td style="background:linear-gradient(135deg,#143f8c,#2566cf);padding:28px 32px 32px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td align="left">
                          {logo_markup}
                        </td>
                        <td align="right" style="font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;font-size:13px;letter-spacing:0.18em;text-transform:uppercase;color:#d2e1ff;">
                          Plateforme COVA
                        </td>
                      </tr>
                    </table>
                    <h1 style="margin:24px 0 4px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;font-size:26px;line-height:1.35;color:#ffffff;font-weight:700;">
                      {title}
                    </h1>
                    <p style="margin:0;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#e4ecff;line-height:1.6;">
                      {subtitle}
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:36px 32px 32px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;color:#273041;">
                    <p style="margin:0 0 16px;line-height:1.6;color:#273041;font-size:15px;">Bonjour,</p>
                    {paragraph_html}
                    <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin:24px auto 28px;">
                      <tr>
                        <td align="center" style="border-radius:14px;background:linear-gradient(135deg,#1959c2,#143f8c);">
                          <a href="{button_link}" style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
                            {button_label}
                          </a>
                        </td>
                      </tr>
                    </table>
                    <p style="margin:0 0 16px;line-height:1.6;color:#1f2a3d;font-size:14px;">
                      {validity_note}
                    </p>
                    <p style="margin:0 0 12px;line-height:1.6;color:#62708f;font-size:13px;">
                      Si le bouton ne fonctionne pas, copiez et collez le lien suivant dans votre navigateur :
                    </p>
                    <p style="margin:0 0 24px;word-break:break-all;line-height:1.6;">
                      <a href="{button_link}" style="color:#1959c2;text-decoration:none;font-size:13px;">{button_link}</a>
                    </p>
                    <p style="margin:0;line-height:1.6;color:#273041;font-size:15px;">
                      À très vite,<br /><strong>L'équipe COVA</strong>
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:22px 32px;background:#f5f7fb;border-top:1px solid #e3e7ef;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;font-size:12px;color:#7b8498;">
                    Besoin d'aide ? Écrivez-nous à <a href="mailto:support@cova.sn" style="color:#1959c2;text-decoration:none;font-weight:600;">support@cova.sn</a>.<br />
                    © {os.getenv('PLATFORM_NAME', 'COVA')} - Tous droits réservés.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    return html


def send_reset_email(dest_email, reset_link) -> bool:
    msg = MIMEMultipart('related')
    msg['From'] = _build_from_header()
    msg['To'] = dest_email
    msg['Subject'] = 'Réinitialisation de mot de passe - COVA'

    paragraphs = [
        "Nous avons reçu une demande de réinitialisation de votre mot de passe pour votre espace <strong>COVA</strong>.",
        "Pour des raisons de sécurité, ce lien est personnel et ne doit pas être partagé.",
    ]

    logo_bytes = _get_logo_bytes()
    html = _build_branded_email_html(
        title="Réinitialisez votre mot de passe",
        subtitle="Sécurisez votre accès à la plateforme COVA en quelques secondes.",
        preheader="Réinitialisez votre mot de passe COVA en toute sécurité.",
        paragraphs=paragraphs,
        button_label="Réinitialiser mon mot de passe",
        button_link=reset_link,
        validity_note="Ce lien sécurisé restera actif pendant 1 heure. Passé ce délai, vous devrez effectuer une nouvelle demande.",
        logo_src=f"cid:{LOGO_CONTENT_ID}" if logo_bytes else None,
    )

    plain_text = (
        "Bonjour,\n\n"
        "Vous avez demandé la réinitialisation de votre mot de passe pour votre compte COVA. "
        "Cliquez sur le lien ci-dessous ou copiez-le dans votre navigateur :\n"
        f"{reset_link}\n\n"
        "Ce lien est valable 1 heure. Si vous n'êtes pas à l'origine de cette démarche, vous pouvez ignorer ce message.\n\n"
        "L'équipe COVA"
    )

    alternative_part = MIMEMultipart('alternative')
    alternative_part.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    alternative_part.attach(MIMEText(html, 'html', 'utf-8'))
    msg.attach(alternative_part)

    if logo_bytes:
        _attach_logo(msg, logo_bytes)

    return _send_message(msg)


def send_confirm_email(dest_email, confirm_link) -> bool:
    msg = MIMEMultipart('related')
    msg['From'] = _build_from_header()
    msg['To'] = dest_email
    msg['Subject'] = "Confirmation d'inscription - COVA"

    paragraphs = [
        "Nous sommes ravis de vous compter parmi nos membres.",
        "Pour finaliser votre inscription et sécuriser votre compte, merci de confirmer votre adresse e-mail." ,
    ]

    logo_bytes = _get_logo_bytes()
    html = _build_branded_email_html(
        title="Confirmez votre adresse e-mail",
        subtitle="Bienvenue sur COVA, la plateforme dédiée au suivi et à l'accompagnement.",
        preheader="Bienvenue sur COVA ! Confirmez votre adresse e-mail pour finaliser votre inscription.",
        paragraphs=paragraphs,
        button_label="Confirmer mon e-mail",
        button_link=confirm_link,
        validity_note="Le lien de confirmation est valable pendant 24 heures. Passé ce délai, il faudra effectuer une nouvelle demande depuis la plateforme.",
        logo_src=f"cid:{LOGO_CONTENT_ID}" if logo_bytes else None,
    )

    plain_text = (
        "Bonjour,\n\n"
        "Merci de vous être inscrit sur COVA. Pour activer votre compte, cliquez sur le lien ci-dessous "
        "ou copiez-le dans votre navigateur :\n"
        f"{confirm_link}\n\n"
        "Ce lien est valable 24 heures. Si vous n'êtes pas à l'origine de cette inscription, ignorez ce message.\n\n"
        "L'équipe COVA"
    )

    alternative_part = MIMEMultipart('alternative')
    alternative_part.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    alternative_part.attach(MIMEText(html, 'html', 'utf-8'))
    msg.attach(alternative_part)

    if logo_bytes:
        _attach_logo(msg, logo_bytes)

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
