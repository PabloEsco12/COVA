from __future__ import annotations

import ipaddress
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models import NotificationChannel, UserAccount, UserProfile
from ...config import settings

DEFAULT_TIMEZONE = "UTC"


def describe_ip(raw_ip: str) -> tuple[str, str | None]:
    """Décrit une adresse IP et retourne une étiquette lisible et une localisation approximative."""
    try:
        parsed = ipaddress.ip_address(raw_ip)
    except ValueError:
        return "Adresse non valide", None
    if parsed.is_loopback:
        return "Boucle locale", "Connexion locale"
    if parsed.is_private:
        return "Réseau privé ou VPN", "Localisation non disponible (adresse privée)"
    if parsed.is_reserved or parsed.is_unspecified:
        return "Adresse réservée", None
    return "Adresse publique", None


def parse_user_agent(ua: str | None) -> tuple[str | None, str | None]:
    """Extrait un navigateur et un OS lisible à partir d'un user-agent brut."""
    if not ua:
        return None, None
    ua_lower = ua.lower()
    browser = None
    os_label = None

    if "chrome" in ua_lower and "edg" not in ua_lower and "opr" not in ua_lower:
        browser = "Chrome"
    elif "edg" in ua_lower:
        browser = "Edge"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "opr" in ua_lower or "opera" in ua_lower:
        browser = "Opera"

    if "windows" in ua_lower:
        os_label = "Windows"
    elif "mac os" in ua_lower or "macos" in ua_lower:
        os_label = "macOS"
    elif "android" in ua_lower:
        os_label = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
        os_label = "iOS"
    elif "linux" in ua_lower:
        os_label = "Linux"

    return browser, os_label


def build_login_alert_payload(
    *,
    user: UserAccount,
    session_id: str,
    login_time: datetime,
    ip_address: str | None,
    user_agent: str | None,
    timezone_pref: str | None = None,
) -> dict:
    """Construit le payload d'alerte de connexion pour le canal email."""
    frontend_origin = (settings.FRONTEND_ORIGIN or "").rstrip("/") or "http://localhost:5176"
    security_url = f"{frontend_origin}/dashboard/settings"
    devices_url = f"{frontend_origin}/dashboard/devices"
    reset_url = f"{frontend_origin}/reset-password"

    ip_value = ip_address or ""
    ip_label, location_hint = describe_ip(ip_value) if ip_value else ("Adresse inconnue", None)
    profile = user.profile
    tz_pref = timezone_pref or (profile.timezone if profile else None)

    browser, os_label = parse_user_agent(user_agent)

    return {
        "type": "security.login_alert",
        "login_time": login_time.astimezone(timezone.utc).isoformat(),
        "ip_address": ip_value,
        "ip_label": ip_label,
        "approx_location": location_hint,
        "user_agent": user_agent or "",
        "agent_browser": browser,
        "agent_os": os_label,
        "session_id": str(session_id),
        "timezone": tz_pref,
        "security_url": security_url,
        "devices_url": devices_url,
        "reset_url": reset_url,
        "display_name": profile.display_name if profile else None,
        "email": user.email,
    }


def quiet_hours_active(
    quiet_hours: dict,
    now_utc: datetime,
    profile: UserProfile | None,
) -> bool:
    """Détermine si une plage de silence est active en tenant compte du fuseau souhaité."""
    start = (quiet_hours.get("start") or "").strip()
    end = (quiet_hours.get("end") or "").strip()
    if not start or not end or start == end:
        return False
    try:
        start_time = time.fromisoformat(start)
        end_time = time.fromisoformat(end)
    except ValueError:
        return False
    tz_name = (
        (quiet_hours.get("timezone") or "").strip()
        or (profile.timezone if profile and profile.timezone else None)
        or DEFAULT_TIMEZONE
    )
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = timezone.utc
    local_time = now_utc.astimezone(zone).time()
    if start_time < end_time:
        return start_time <= local_time < end_time
    # Cas où la plage déborde après minuit (ex: 22h-06h).
    return local_time >= start_time or local_time < end_time


def should_send_login_alert(user: UserAccount, now_utc: datetime | None = None) -> bool:
    """Évalue si une alerte de connexion doit partir selon les préférences et horaires de silence."""
    profile = user.profile
    profile_data = dict(profile.profile_data or {}) if profile and profile.profile_data else {}
    notify_login = bool(profile_data.get("notify_login"))
    if not notify_login:
        return False
    current = now_utc or datetime.now(timezone.utc)
    for pref in user.notification_preferences or []:
        if pref.channel != NotificationChannel.EMAIL:
            continue
        if not pref.is_enabled:
            return False
        if pref.quiet_hours and quiet_hours_active(pref.quiet_hours, current, profile):
            return False
    return True


__all__ = [
    "DEFAULT_TIMEZONE",
    "describe_ip",
    "parse_user_agent",
    "build_login_alert_payload",
    "quiet_hours_active",
    "should_send_login_alert",
]
