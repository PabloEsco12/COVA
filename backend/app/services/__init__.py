"""
Facade d'import pour les services backend.

Infos utiles:
- Re-exporte les classes principales pour des imports simplifies dans l'app.
- N'instancie rien par defaut; chaque service requiert ses dependances (session, etc.).
"""

from .auth_service import AuthService
from .contact_service import ContactService
from .conversation import ConversationService
from .audit_service import AuditService
from .notification_service import NotificationService
from .device_service import DeviceService
from .security_service import SecurityService
from .attachment_service import AttachmentService
from .organization_service import OrganizationService

__all__ = [
    'AuthService',
    'ContactService',
    'ConversationService',
    'AuditService',
    'NotificationService',
    'DeviceService',
    'SecurityService',
    'AttachmentService',
    'OrganizationService',
]

