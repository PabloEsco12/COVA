"""
Facade AuthService regroupant les mixins spécialisés.
Les helpers (describe_ip, quiet_hours_active, etc.) sont exposés pour compatibilité.
"""

from .base import AuthBase
from .helpers import (
    DEFAULT_TIMEZONE,
    build_login_alert_payload,
    describe_ip,
    parse_user_agent,
    quiet_hours_active,
    should_send_login_alert,
)
from .models import AuthResult, RegisterResult, TotpRequiredError
from .notifications import AuthNotificationMixin
from .passwords import AuthPasswordsMixin
from .registration import AuthRegistrationMixin
from .tokens import AuthTokensMixin
from .totp import AuthTotpMixin


class AuthService(
    AuthNotificationMixin,
    AuthTokensMixin,
    AuthPasswordsMixin,
    AuthTotpMixin,
    AuthRegistrationMixin,
    AuthBase,
):
    """Gère l'inscription, l'authentification, les tokens et le cycle de vie des sessions."""

    pass


__all__ = [
    "AuthService",
    "AuthResult",
    "RegisterResult",
    "TotpRequiredError",
    "describe_ip",
    "parse_user_agent",
    "build_login_alert_payload",
    "quiet_hours_active",
    "should_send_login_alert",
    "DEFAULT_TIMEZONE",
]
