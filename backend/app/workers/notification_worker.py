"""
############################################################
# Worker : NotificationWorker (queue outbound)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Consomme la file outbound_notifications et declenche les envois (email/push).
# - Tourne en boucle async avec gestion elegante des interruptions (SIGINT/SIGTERM).
#
# Points de vigilance:
# - Nettoyer/mettre a jour les statuts en cas d'erreur pour eviter le stuck.
# - Respecter les quiet hours/ timezone des utilisateurs pour l'email de login.
############################################################
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import signal
import textwrap
import uuid
from typing import Any, Optional
import traceback

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from ..config import Settings, get_settings
from ..core.email import send_email
from ..db.session import _make_async_url
from app.models import NotificationChannel, OutboundNotification, UserAccount

try:
    from app_old.utils._cova_logo_b64 import LOGO_PNG_BASE64 as _COVA_LOGO_B64
except ImportError:
    _COVA_LOGO_B64 = None

# =====================
# DTOs / Jobs en file
# =====================
@dataclass
class NotificationJob:
    id: uuid.UUID
    channel: NotificationChannel
    user_id: Optional[uuid.UUID]
    organization_id: Optional[uuid.UUID]
    payload: dict[str, Any]


# =====================
# Worker principal
# =====================
class NotificationWorker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        db_url = _make_async_url(settings.DATABASE_URL)
        self.engine = create_async_engine(db_url, future=True, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self.running = True

    # --- Cycle principal ---
    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.stop)

        while self.running:
            try:
                job = await self._acquire_notification()
                if job is None:
                    await asyncio.sleep(2)
                    continue
                try:
                    await self._deliver_notification(job)
                except Exception as error:  # noqa: BLE001
                    await self._mark_failed(job.id, str(error))
                else:
                    await self._mark_sent(job.id)
            except Exception as error:  # noqa: BLE001
                traceback.print_exc()
                print(f"[notification-worker] error: {error}")
                await asyncio.sleep(5)

    def stop(self) -> None:
        self.running = False

    async def _acquire_notification(self) -> NotificationJob | None:
        async with self.session_factory() as session:
            async with session.begin():
                stmt = (
                    select(OutboundNotification)
                    .where(OutboundNotification.status == "pending")
                    .order_by(OutboundNotification.scheduled_at.asc())
                    .with_for_update(skip_locked=True)
                    .limit(1)
                )
                result = await session.execute(stmt)
                notification = result.scalars().first()
                if notification is None:
                    return None
                notification.status = "processing"
                notification.attempts += 1
                notification.last_error = None
                job = NotificationJob(
                    id=notification.id,
                    channel=notification.channel,
                    user_id=notification.user_id,
                    organization_id=notification.organization_id,
                    payload=dict(notification.payload or {}),
                )
            return job

    async def _deliver_notification(self, job: NotificationJob) -> None:
        """Route un job vers le canal cible et met a jour les stats."""
        if job.channel == NotificationChannel.EMAIL:
            await self._send_email(job)
        else:
            print(f"[notification-worker] channel {job.channel} not implemented")

    async def _send_email(self, job: NotificationJob) -> None:
        """Construit et envoie un email selon le payload."""
        if not self.settings.SMTP_HOST:
            raise RuntimeError("SMTP is not configured (missing SMTP_HOST)")

        payload = job.payload or {}
        template_type = payload.get("type")

        recipient_email: str | None = payload.get("email")
        display_name: str | None = payload.get("display_name")
        target_user_id: uuid.UUID | None = job.user_id

        if target_user_id is None and payload.get("user_id"):
            try:
                target_user_id = uuid.UUID(str(payload["user_id"]))
            except (TypeError, ValueError):
                target_user_id = None

        if target_user_id is not None:
            async with self.session_factory() as session:
                stmt = (
                    select(UserAccount)
                    .options(selectinload(UserAccount.profile))
                    .where(UserAccount.id == target_user_id)
                )
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    recipient_email = recipient_email or user.email
                    if user.profile:
                        display_name = display_name or user.profile.display_name
        elif recipient_email is None:
            raise RuntimeError("Unable to resolve recipient e-mail address")

        if not recipient_email:
            raise RuntimeError("Unable to resolve recipient e-mail address")

        if template_type == "email_confirmation":
            token = payload.get("token")
            if not token:
                raise RuntimeError("Missing confirmation token in payload")
            await self._send_confirmation_email(
                recipient_email,
                display_name,
                token,
                payload.get("confirmation_path"),
            )
        elif template_type == "password_reset":
            token = payload.get("token")
            if not token:
                raise RuntimeError("Missing reset token in payload")
            await self._send_password_reset_email(
                recipient_email,
                display_name,
                token,
                payload.get("reset_path"),
            )
        elif template_type == "security.login_alert":
            await self._send_login_alert_email(
                to_email=recipient_email,
                display_name=display_name,
                payload=payload,
            )
        else:
            raise RuntimeError(f"Unhandled email notification type: {template_type}")

    async def _send_confirmation_email(self, to_email: str, display_name: str | None, token: str, confirmation_path: str | None) -> None:
        frontend_origin = (self.settings.FRONTEND_ORIGIN or "").rstrip("/") or "http://localhost:5176"
        backend_origin = (self.settings.PUBLIC_BASE_URL or "").rstrip("/") or "http://localhost:8000"
        confirmation_path = confirmation_path or f"/api/auth/confirm/{token}"

        frontend_link = f"{frontend_origin}/confirm-email/{token}"
        backend_link = f"{backend_origin}{confirmation_path}"
        logo_data_url = f"data:image/png;base64,{_COVA_LOGO_B64}" if _COVA_LOGO_B64 else None

        recipient_name = (display_name or "").strip()
        safe_name_html = html.escape(recipient_name) if recipient_name else ""
        safe_name_text = recipient_name or "!"

        text_body = textwrap.dedent(
            f"""
            Bonjour {safe_name_text},

            Merci d'avoir rejoint COVA. Pour finaliser votre inscription et activer votre messagerie, ouvrez le lien ci-dessous :
            {frontend_link}

            Si le bouton ne fonctionne pas, copiez/collez ce lien dans votre navigateur (lien API : {backend_link}).

            Ce lien est valable 30 minutes. Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce message.

            À très vite en toute sérénité,
            L'équipe COVA
            """.strip()
        )

        if logo_data_url:
            brand_logo_markup = (
                f'<img src="{logo_data_url}" alt="Logo COVA" width="58" height="58" '
                'style="border-radius:16px;box-shadow:0 12px 28px rgba(25,89,194,0.35);display:block;" />'
            )
        else:
            brand_logo_markup = (
                '<div style="width:58px;height:58px;border-radius:16px;'
                "background:linear-gradient(135deg,#1959c2,#35a4f0);color:#fff;font-weight:700;font-size:1.2rem;"
                'display:flex;align-items:center;justify-content:center;">C</div>'
            )

        html_body = textwrap.dedent(
            f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Confirmez votre adresse e-mail</title>
            </head>
            <body style="margin:0;padding:0;background:#f5f7fb;font-family:'Segoe UI',Roboto,Arial,sans-serif;color:#0f172a;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;padding:32px 0;">
                <tr>
                  <td align="center">
                    <table role="presentation" cellpadding="0" cellspacing="0" style="width:560px;max-width:90%;background:#ffffff;border-radius:18px;box-shadow:0 25px 60px rgba(15,23,42,0.08);overflow:hidden;">
                      <tr>
                        <td style="padding:32px 32px 16px;text-align:center;">
                          <div style="display:inline-flex;align-items:center;gap:14px;">
                            {brand_logo_markup}
                            <div style="text-align:left;">
                              <p style="margin:0;font-size:0.82rem;color:#475569;letter-spacing:0.08em;text-transform:uppercase;">COVA Messagerie</p>
                              <p style="margin:0;font-size:1.35rem;font-weight:700;color:#0f172a;">Activation sécurisée</p>
                            </div>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 8px;font-size:1rem;line-height:1.5;color:#1e293b;">
                          <p style="margin:0 0 12px;">Bonjour {safe_name_html or ''},</p>
                          <p style="margin:0 0 18px;">Merci d'avoir créé un compte sur <strong>COVA</strong>. Pour activer votre accès, confirmez votre adresse e-mail via le bouton ci-dessous.</p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:10px 32px 26px;text-align:center;">
                          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
                            <tr>
                              <td bgcolor="#1b4ed0" style="border-radius:16px;background:linear-gradient(135deg,#1959c2,#4b7bdc);box-shadow:0 12px 30px rgba(25,89,194,0.28);">
                                <a href="{frontend_link}" style="display:inline-block;color:#ffffff;font-weight:600;text-decoration:none;padding:14px 32px;font-size:1rem;letter-spacing:0.02em;">
                                  Confirmer mon adresse e-mail
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 24px;font-size:0.95rem;color:#475569;">
                          <p style="margin:0 0 8px;">Le bouton ne fonctionne pas ? Copiez/collez ce lien dans votre navigateur :</p>
                          <p style="margin:0 0 16px;word-break:break-all;"><a href="{frontend_link}" style="color:#1959c2;text-decoration:none;">{frontend_link}</a></p>
                          <p style="margin:0 0 6px;font-size:0.85rem;color:#94a3b8;">Lien alternatif API : <a href="{backend_link}" style="color:#1959c2;text-decoration:none;">{backend_link}</a></p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 24px;font-size:0.9rem;color:#475569;">
                          <p style="margin:0 0 12px;">Rappels utiles :</p>
                          <ul style="padding-left:18px;margin:0 0 12px;">
                            <li>Le lien expire dans 30 minutes.</li>
                            <li>Connectez-vous ensuite avec la même adresse e-mail.</li>
                            <li>Ignorez ce message si vous n'êtes pas à l'origine de la demande.</li>
                          </ul>
                          <p style="margin:0;">À très vite sur la plateforme,<br><strong>L'équipe COVA</strong></p>
                        </td>
                      </tr>
                      <tr>
                        <td style="background:#f8fafc;padding:18px 32px;text-align:center;font-size:0.78rem;color:#9ca3af;">
                          Message automatique — merci de ne pas répondre.
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """
        ).strip()
        await send_email(
            self.settings,
            to=to_email,
            subject="Confirmez votre adresse e-mail",
            text_body=text_body,
            html_body=html_body,
        )
    async def _send_password_reset_email(self, to_email: str, display_name: str | None, token: str, reset_path: str | None) -> None:
        frontend_origin = (self.settings.FRONTEND_ORIGIN or "").rstrip("/") or "http://localhost:5176"
        backend_origin = (self.settings.PUBLIC_BASE_URL or "").rstrip("/") or "http://localhost:8000"
        if reset_path:
            reset_path = reset_path if reset_path.startswith("/") else f"/{reset_path.lstrip('/')}"
        else:
            reset_path = f"/new-password?token={token}"

        frontend_link = f"{frontend_origin}{reset_path}"
        api_link = f"{backend_origin}/api/auth/reset-password"

        recipient_name = display_name or ""

        text_body = textwrap.dedent(
            f"""
            Bonjour {recipient_name or '!' },

            Nous avons recu une demande pour reinitialiser votre mot de passe COVA.
            Pour continuer en toute securite :

            1. Cliquez sur le bouton ou copiez le lien suivant : {frontend_link}
            2. Choisissez un nouveau mot de passe robuste (12 caracteres minimum, chiffres + lettres + caracteres speciaux).
            3. Validez avant 30 minutes afin de garantir la protection de votre compte.

            Si vous n'etes pas a l'origine de cette demande, ignorez cet e-mail et contactez immediatement votre responsable securite.

            (Lien API : {api_link})

            A tres vite, en toute securite.
            L'equipe COVA
            """.strip()
        )

        html_body = textwrap.dedent(
            f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Reinitialisation du mot de passe COVA</title>
            </head>
            <body style="margin:0;padding:0;background:#f5f7fb;font-family:'Segoe UI',Roboto,Arial,sans-serif;color:#0f172a;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;padding:32px 0;">
                <tr>
                  <td align="center">
                    <table role="presentation" cellpadding="0" cellspacing="0" style="width:560px;max-width:90%;background:#ffffff;border-radius:18px;box-shadow:0 25px 60px rgba(15,23,42,0.08);overflow:hidden;">
                      <tr>
                        <td style="padding:32px 32px 16px;text-align:center;">
                          <div style="display:inline-flex;align-items:center;gap:12px;">
                            <div style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#1959c2,#4b7bdc);color:#fff;font-weight:700;font-size:1.1rem;display:flex;align-items:center;justify-content:center;">
                              C
                            </div>
                            <div style="text-align:left;">
                              <p style="margin:0;font-size:0.85rem;color:#475569;letter-spacing:0.08em;text-transform:uppercase;">COVA Messagerie</p>
                              <p style="margin:0;font-size:1.35rem;font-weight:700;color:#0f172a;">Réinitialisation sécurisée</p>
                            </div>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 8px;font-size:1rem;line-height:1.5;color:#1e293b;">
                          <p style="margin:0 0 12px;">Bonjour {recipient_name or ''},</p>
                          <p style="margin:0 0 18px;">Nous avons reçu une demande pour réinitialiser votre mot de passe <strong>COVA</strong>. Pour protéger l'accès à vos conversations, veuillez choisir un nouveau secret en cliquant sur le bouton ci-dessous.</p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:10px 32px 26px;text-align:center;">
                          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
                            <tr>
                              <td bgcolor="#1b4ed0" style="border-radius:16px;background:linear-gradient(135deg,#1959c2,#4b7bdc);box-shadow:0 12px 30px rgba(25,89,194,0.28);">
                                <a href="{frontend_link}" style="display:inline-block;color:#ffffff;font-weight:600;text-decoration:none;padding:14px 32px;font-size:1rem;letter-spacing:0.02em;">
                                  Choisir un nouveau mot de passe
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 24px;font-size:0.95rem;color:#475569;">
                          <p style="margin:0 0 8px;">Le bouton ne fonctionne pas ? Copiez/collez ce lien dans votre navigateur :</p>
                          <p style="margin:0 0 16px;word-break:break-all;"><a href="{frontend_link}" style="color:#1959c2;text-decoration:none;">{frontend_link}</a></p>
                          <p style="margin:0 0 6px;font-size:0.85rem;color:#94a3b8;">Lien API : <a href="{api_link}" style="color:#1959c2;text-decoration:none;">{api_link}</a></p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 32px 24px;font-size:0.9rem;color:#475569;">
                          <p style="margin:0 0 12px;">Pour votre tranquillite :</p>
                          <ul style="padding-left:18px;margin:0 0 12px;">
                            <li>Le lien est valable pendant 30 minutes.</li>
                            <li>Choisissez un mot de passe unique, comprenant au moins 12 caractères.</li>
                            <li>Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail et signalez-le à votre équipe sécurité.</li>
                          </ul>
                          <p style="margin:0;">À très vite en toute sécurité,<br><strong>L'équipe COVA</strong></p>
                        </td>
                      </tr>
                      <tr>
                        <td style="background:#f8fafc;padding:18px 32px;text-align:center;font-size:0.78rem;color:#9ca3af;">
                          Message généré automatiquement par COVA. Merci de ne pas répondre à cet e-mail.
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """
        ).strip()

        await send_email(
            self.settings,
            to=to_email,
            subject="Réinitialisez votre mot de passe",
            text_body=text_body,
            html_body=html_body,
        )

    async def _send_login_alert_email(self, *, to_email: str, display_name: str | None, payload: dict) -> None:
        frontend_origin = (self.settings.FRONTEND_ORIGIN or "").rstrip("/") or "http://localhost:5176"
        security_url = payload.get("security_url") or f"{frontend_origin}/dashboard/settings"
        devices_url = payload.get("devices_url") or f"{frontend_origin}/dashboard/devices"
        reset_url = payload.get("reset_url") or f"{frontend_origin}/reset-password"

        login_time_raw = payload.get("login_time")
        login_dt = None
        if isinstance(login_time_raw, str):
            try:
                login_dt = datetime.fromisoformat(login_time_raw)
            except ValueError:
                login_dt = None
        if login_dt and login_dt.tzinfo is None:
            login_dt = login_dt.replace(tzinfo=timezone.utc)

        login_dt_utc = login_dt.astimezone(timezone.utc) if login_dt else None
        time_utc = (
            login_dt_utc.strftime("%d/%m/%Y · %H:%M:%S UTC") if login_dt_utc else "Non disponible"
        )

        timezone_name = payload.get("timezone")
        time_local = None
        if login_dt_utc and isinstance(timezone_name, str) and timezone_name:
            try:
                zone = ZoneInfo(timezone_name)
                time_local = login_dt_utc.astimezone(zone).strftime("%d/%m/%Y · %H:%M:%S %Z")
            except (ZoneInfoNotFoundError, ValueError):
                time_local = None

        ip_address = payload.get("ip_address") or "Non disponible"
        ip_label = payload.get("ip_label") or ""
        approx_location = payload.get("approx_location") or ip_label or "Non determinee"
        user_agent = (payload.get("user_agent") or "").strip() or "Non renseigne"
        user_agent = user_agent[:180]
        session_id = payload.get("session_id") or "Non disponible"
        session_display = str(session_id).upper()

        safe_name = (display_name or "").strip()
        name_txt = safe_name if safe_name else "Bonjour"
        name_html = html.escape(safe_name) if safe_name else "Bonjour"

        details_lines = [
            f"- Horodatage (UTC) : {time_utc}",
        ]
        if time_local:
            details_lines.append(f"- Horodatage ({timezone_name}) : {time_local}")
        details_lines.extend(
            [
                f"- Adresse IP : {ip_address}{f' ({ip_label})' if ip_label else ''}",
                f"- Localisation : {approx_location}",
                f"- Appareil : {user_agent}",
                f"- Session ID : {session_display}",
            ]
        )

        text_body = "\n".join(
            [
                f"{name_txt},",
                "",
                "Une connexion vient d'être vérifiée sur votre compte COVA.",
                "",
                "Détails :",
                *details_lines,
                "",
                "Si vous êtes à l'origine de cette connexion, aucune action supplémentaire n'est nécessaire.",
                "Si vous ne reconnaissez pas cette activité :",
                f"1. réinitialisez votre mot de passe : {reset_url}",
                f"2. révoquez les sessions inconnues : {devices_url}",
                f"3. Activez ou vérifiez la double authentification : {security_url}",
                "",
                "Cet e-mail automatique protège l'intégrité de vos échanges chiffrés sur COVA.",
                "",
                "Équipe COVA",
            ]
        )

        ip_cell = f"{html.escape(ip_address)}"
        if ip_label:
            ip_cell += f" <span style=\"color:#94a3b8;font-weight:400;\">({html.escape(ip_label)})</span>"

        details_rows = [
            "<tr>"
            f"<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Horodatage (UTC)</td>"
            f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{html.escape(time_utc)}</td>"
            "</tr>"
        ]
        if time_local:
            label = timezone_name or "Local"
            details_rows.append(
                "<tr>"
                f"<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Horodatage ({html.escape(label)})</td>"
                f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{html.escape(time_local)}</td>"
                "</tr>"
            )
        details_rows.extend(
            [
                "<tr>"
                "<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Adresse IP</td>"
                f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{ip_cell}</td>"
                "</tr>",
                "<tr>"
                "<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Localisation</td>"
                f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{html.escape(approx_location)}</td>"
                "</tr>",
                "<tr>"
                "<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Appareil</td>"
                f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{html.escape(user_agent)}</td>"
                "</tr>",
                "<tr>"
                "<td style=\"padding:6px 0;color:#64748b;font-size:14px;\">Session ID</td>"
                f"<td style=\"padding:6px 0;font-weight:600;color:#0f172a;font-size:14px;\">{html.escape(session_display)}</td>"
                "</tr>",
            ]
        )
        details_table = "".join(details_rows)

        html_body = textwrap.dedent(
            f"""
            <html>
              <body style="margin:0;padding:0;background:#f5f7fb;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:32px 0;">
                  <tr>
                    <td align="center">
                      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:16px;box-shadow:0 18px 48px rgba(15,23,42,0.12);overflow:hidden;">
                        <tr>
                          <td style="padding:32px 32px 12px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
                            <p style="margin:0 0 16px;font-size:16px;color:#0f172a;">{name_html},</p>
                            <p style="margin:0;font-size:15px;color:#334155;">Une connexion vient d'etre validee sur votre compte <strong>COVA</strong>. Voici les informations importantes :</p>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding:0 32px 24px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
                            <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
                              <div style="flex:1 1 220px;background:#eef2ff;border-radius:12px;padding:14px 16px;">
                                <p style="margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:#475569;">Horodatage</p>
                                <p style="margin:0;font-size:15px;font-weight:600;color:#0f172a;">{html.escape(time_utc)}</p>
                                {"<p style='margin:4px 0 0;font-size:13px;color:#475569;'>" + html.escape(time_local or '') + "</p>" if time_local else ""}
                              </div>
                              <div style="flex:1 1 220px;background:#ecfdf5;border-radius:12px;padding:14px 16px;">
                                <p style="margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:#047857;">Adresse IP</p>
                                <p style="margin:0;font-size:15px;font-weight:600;color:#064e3b;">{ip_cell}</p>
                                <p style="margin:4px 0 0;font-size:13px;color:#047857;">{html.escape(approx_location)}</p>
                              </div>
                            </div>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                              {details_table}
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding:0 32px 24px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;border-radius:12px;">
                              <tr>
                                <td style="padding:20px 24px;">
                                  <p style="margin:0 0 12px;font-size:15px;color:#e2e8f0;font-weight:600;">Vous n'êtes pas à l'origine de cette connexion ?</p>
                                  <p style="margin:0 0 12px;font-size:14px;color:#cbd5f5;">Pour protéger vos conversations chiffrées, nous vous recommandons :</p>
                                  <ul style="margin:0;padding-left:20px;color:#e2e8f0;font-size:14px;line-height:1.6;">
                                    <li>réinitialisez votre mot de passe depuis <a href="{html.escape(reset_url)}" style="color:#38bdf8;">la page dédiée</a>.</li>
                                    <li>révoquez les sessions inconnues via <a href="{html.escape(devices_url)}" style="color:#38bdf8;">vos appareils</a>.</li>
                                    <li>Activez ou contrôlez votre double authentification dans <a href="{html.escape(security_url)}" style="color:#38bdf8;">les paramètres</a>.</li>
                                  </ul>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding:0 32px 32px;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;">
                            <a href="{html.escape(devices_url)}" style="display:inline-block;background:#1d4ed8;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:10px;font-size:14px;font-weight:600;">
                              Examiner les sessions
                            </a>
                            <p style="margin:16px 0 0;font-size:12px;color:#94a3b8;">Ce message automatique garantit la securite de votre messagerie COVA.</p>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </body>
            </html>
            """
        ).strip()

        await send_email(
            self.settings,
            to=to_email,
            subject="[COVA] Nouvelle connexion detectee",
            text_body=text_body,
            html_body=html_body,
        )

    async def _mark_failed(self, notification_id: uuid.UUID, error: str) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(OutboundNotification)
                .where(OutboundNotification.id == notification_id)
                .values(
                    status="failed",
                    last_error=error[:500],
                    processed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()

    async def _mark_sent(self, notification_id: uuid.UUID) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(OutboundNotification)
                .where(OutboundNotification.id == notification_id)
                .values(
                    status="sent",
                    last_error=None,
                    processed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()


async def main() -> None:
    settings = get_settings()
    worker = NotificationWorker(settings)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())


