"""Email sending utilities."""

from __future__ import annotations

from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable

import aiosmtplib

from ..config import Settings


def _resolve_sender(settings: Settings) -> tuple[str, str]:
    name = settings.SMTP_FROM_NAME or settings.SMTP_USERNAME or ""
    address = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    if not address:
        raise RuntimeError("SMTP_FROM_EMAIL or SMTP_USERNAME must be configured")
    return name, address


async def send_email(
    settings: Settings,
    *,
    to: Iterable[str] | str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    recipients = [to] if isinstance(to, str) else list(to)
    if not recipients:
        raise ValueError("No recipients provided")

    sender_name, sender_address = _resolve_sender(settings)

    message = EmailMessage()
    message["From"] = formataddr((sender_name, sender_address)) if sender_name else sender_address
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    smtp = aiosmtplib.SMTP(
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        use_tls=settings.SMTP_USE_SSL,
    )
    await smtp.connect()
    try:
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            try:
                await smtp.starttls()
            except aiosmtplib.errors.SMTPException as exc:
                if "already using TLS" not in str(exc):
                    raise
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        await smtp.send_message(message)
    finally:
        await smtp.quit()
