# Next-Generation Schema Overview

This document tracks the new database architecture introduced under
`backend/app/db_v2`. It serves as the foundation for the future FastAPI /
Redis real-time stack and for upcoming MCD/MLD/UML diagrams.

## Core Principles

- **Multi-tenant** : `organizations` and `workspaces` partition all data.
- **Zero-trust** : messages are stored encrypted (`conversation_encryption_keys`,
  `member_key_wraps`, `messages.ciphertext`).
- **Device-aware** : devices, sessions, and push subscriptions are tracked
  separately for revocation and anomaly detection.
- **Compliance ready** : audit trail, privacy requests, configurable retention.
- **Extensible** : webhook endpoints, bot agents, notification pipeline.

## Entity Highlights

| Domain | Tables | Key Attributes |
| --- | --- | --- |
| Tenancy | `organizations`, `organization_memberships`, `workspaces`, `workspace_memberships` | role-based membership, per-workspace joins |
| Users | `user_accounts`, `user_profiles`, `user_security_states` | separation of credentials vs profile vs security |
| Security | `email_confirmation_tokens`, `password_reset_tokens`, `refresh_tokens`, `totp_secrets` | full auth lifecycle |
| Devices | `devices`, `session_tokens`, `push_subscriptions` | per-device trust, session linkage |
| Contacts | `contact_links`, `contact_invitations` | mutual relationships, guest onboarding |
| Conversations | `conversations`, `conversation_members`, `conversation_encryption_keys`, `member_key_wraps`, `conversation_invites` | encryption generation, key wraps per member |
| Messages | `messages`, `message_deliveries`, `message_attachments`, `message_reactions`, `message_pins` | E2EE payload, per-recipient delivery, metadata |
| Calls | `call_sessions`, `call_participants` | audio/video session metadata |
| Notifications | `notification_preferences`, `outbound_notifications` | queue + per-user preferences |
| Integrations | `webhook_endpoints`, `bot_agents` | automation targets |
| Compliance | `audit_logs`, `privacy_requests` | audit & GDPR support |

## Next Steps

1. Produce MCD/MLD/UML diagrams aligned with these models.
2. Generate Alembic migrations to materialise the schema.
3. Port backend services/routes to the new data layer.
4. Implement Redis/WebSocket real-time messaging on top of the new tables.
