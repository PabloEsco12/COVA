"""Email delivery service."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable

import anyio

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Utility responsible for delivering transactional emails."""

    def __init__(self) -> None:
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._username = settings.SMTP_USERNAME
        self._password = settings.SMTP_PASSWORD
        self._use_tls = settings.SMTP_USE_TLS
        self._from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        self._from_name = settings.SMTP_FROM_NAME or "COVA Notifications"

    def _build_sender(self) -> str:
        if not self._from_email:
            return "no-reply@localhost"
        return formataddr((self._from_name, self._from_email))

    async def send_email_confirmation(self, recipient: str, confirm_link: str, display_name: str | None = None) -> bool:
        subject = "Confirmation d'inscription - COVA"
        paragraphs = [
            f"Bonjour {display_name or ''}".strip(),
            "Merci de rejoindre la plateforme sécurisée COVA.",
            "Pour finaliser la création de votre compte et garantir la sécurité de vos échanges, merci de confirmer votre adresse e-mail.",
        ]
        html = self._build_branded_html(
            title="Confirmez votre adresse e-mail",
            subtitle="Votre espace sécurisé vous attend.",
            paragraphs=paragraphs,
            button_label="Confirmer mon compte",
            button_link=confirm_link,
            footer_note="Le lien reste valable 24 heures.",
        )
        plain_text = self._build_plain_text(
            paragraphs,
            confirm_link,
            outro="Ce lien restera actif 24 heures.",
        )
        return await self._send(subject, recipient, plain_text, html)

    async def send_login_notification(
        self,
        recipient: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        location: str | None = None,
        timestamp: str | None = None,
    ) -> bool:
        subject = "Nouvelle connexion à votre compte COVA"
        details = [
            f"Adresse IP : {ip_address}" if ip_address else None,
            f"Appareil : {user_agent}" if user_agent else None,
            f"Localisation : {location}" if location else None,
            f"Horodatage : {timestamp}" if timestamp else None,
        ]
        paragraphs = [
            "Nous avons détecté une connexion à votre compte COVA.",
            "Si vous êtes à l'origine de cette connexion, aucune action n'est nécessaire. Dans le cas contraire, changez immédiatement votre mot de passe et contactez le support.",
        ]
        html = self._build_branded_html(
            title="Connexion détectée",
            subtitle="Alerte de sécurité COVA",
            paragraphs=paragraphs + [self._format_list_html(details)],
            button_label="Protéger mon compte",
            button_link=f"{settings.FRONTEND_URL.rstrip('/')}/reset-password",
            footer_note="Besoin d'aide ? Contactez support@cova.sn",
        )
        plain_text = self._build_plain_text(
            paragraphs + list(self._compact(details)),
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password",
            outro="Si vous n'êtes pas à l'origine de cette connexion, prenez immédiatement les mesures nécessaires.",
        )
        return await self._send(subject, recipient, plain_text, html)

    def _build_branded_html(
        self,
        *,
        title: str,
        subtitle: str,
        paragraphs: Iterable[str],
        button_label: str,
        button_link: str,
        footer_note: str,
    ) -> str:
        paragraph_markup = "".join(
            f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#273041;">{para}</p>'
            for para in self._compact(paragraphs)
        )
        return f"""
        <html>
          <body style="background:#f5f7fb;padding:32px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:18px;box-shadow:0 20px 45px rgba(27,43,88,0.12);overflow:hidden;">
              <tr>
                <td style="padding:32px;">
                  <h1 style="margin:0 0 12px;font-size:24px;color:#152a6d;">{title}</h1>
                  <p style="margin:0 0 24px;font-size:16px;color:#536082;">{subtitle}</p>
                  {paragraph_markup}
                  <div style="margin:32px 0;">
                    <a href="{button_link}" style="display:inline-block;padding:14px 28px;background:#2555ff;color:#ffffff;text-decoration:none;border-radius:12px;font-weight:600;">
                      {button_label}
                    </a>
                  </div>
                </td>
              </tr>
              <tr>
                <td style="padding:24px 32px;background:#f0f2f8;color:#6e7791;font-size:13px;">
                  {footer_note}
                </td>
              </tr>
            </table>
          </body>
        </html>
        """.strip()

    def _build_plain_text(self, paragraphs: Iterable[str], link: str, outro: str) -> str:
        body_parts = [para for para in self._compact(paragraphs)]
        body_parts.append(f"Lien sécurisé : {link}")
        body_parts.append(outro)
        body_parts.append("")
        body_parts.append("L'équipe COVA")
        return "\n\n".join(body_parts)

    async def _send(self, subject: str, recipient: str, plain_body: str, html_body: str | None = None) -> bool:
        if not all([self._host, self._port, self._username, self._password, recipient]):
            logger.warning("SMTP credentials missing; unable to send email to %s", recipient)
            return False

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._build_sender()
        message["To"] = recipient
        message.set_content(plain_body, subtype="plain", charset="utf-8")
        if html_body:
            message.add_alternative(html_body, subtype="html")

        async def _run_send() -> bool:
            try:
                if self._use_tls:
                    with smtplib.SMTP(self._host, self._port) as smtp:
                        smtp.starttls()
                        smtp.login(self._username, self._password)
                        smtp.send_message(message)
                else:
                    with smtplib.SMTP_SSL(self._host, self._port) as smtp:
                        smtp.login(self._username, self._password)
                        smtp.send_message(message)
            except smtplib.SMTPException:
                logger.exception("Failed to deliver email to %s", recipient)
                return False
            except Exception:  # pragma: no cover - defensive guard
                logger.exception("Unexpected error while sending email to %s", recipient)
                return False
            return True

        return await anyio.to_thread.run_sync(_run_send)

    @staticmethod
    def _compact(items: Iterable[str | None]) -> list[str]:
        return [item for item in items if item]

    @staticmethod
    def _format_list_html(items: Iterable[str | None]) -> str:
        filtered = [item for item in items if item]
        if not filtered:
            return ""
        items_markup = "".join(f"<li>{item}</li>" for item in filtered)
        return f"<ul style='padding-left:18px;margin:16px 0;color:#273041;'>{items_markup}</ul>"
