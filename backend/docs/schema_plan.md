# Secure Messaging Data Model – Target Schema (Step 1)

This document captures the target relational model we will implement on top of
the new async FastAPI stack, while reintroducing the security and business
features that existed on the legacy Flask code base. All columns are stored in
PostgreSQL, using `UUID` primary keys for new tables to align with the existing
async models. Timestamps are timezone-aware (`TIMESTAMPTZ`) and default to
`timezone.utc`.

## 1. Core user & authentication tables

### `users`
| Column               | Type            | Notes |
|----------------------|-----------------|-------|
| `id`                 | UUID PK         | Existing column with `gen_random_uuid()` default |
| `email`              | VARCHAR(255)    | Unique, lower-cased |
| `hashed_password`    | TEXT            | bcrypt hash (≤72 bytes raw password) |
| `display_name`       | VARCHAR(255)    | Public name; replaces legacy `pseudo` |
| `role`               | VARCHAR(32)     | Enum: `owner`, `admin`, `member` |
| `avatar_url`         | TEXT NULL       | Optional CDN/storage path |
| `public_key`         | TEXT NULL       | Encoded E2EE public key |
| `is_active`          | BOOLEAN         | Accounts disabled by admin |
| `is_confirmed`       | BOOLEAN         | Email confirmation status |
| `notification_login` | BOOLEAN         | Legacy login alert toggle |
| `failed_totp_attempts` | SMALLINT      | Guard for brute force |
| `totp_locked_until`  | TIMESTAMPTZ     | Lock timestamp if too many TOTP failures |
| `created_at`         | TIMESTAMPTZ     | Existing |
| `updated_at`         | TIMESTAMPTZ     | Existing |

### `email_confirmation_tokens`
| Column        | Type       | Notes |
|---------------|------------|-------|
| `id`          | UUID PK    | Generated server-side |
| `user_id`     | UUID FK    | References `users.id` cascade delete |
| `token`       | VARCHAR(128) | URL-safe string, unique |
| `expires_at`  | TIMESTAMPTZ | 24 h default |
| `consumed_at` | TIMESTAMPTZ NULL | When token used |
| `created_at`  | TIMESTAMPTZ | Audit trail |

### `refresh_tokens`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | Instead of legacy string PK |
| `user_id`     | UUID FK     | References `users.id`, cascade delete |
| `token_jti`   | VARCHAR(36) | JWT ID, unique |
| `user_agent`  | TEXT NULL   | Login metadata |
| `ip_address`  | VARCHAR(45) | IPv4/IPv6 |
| `expires_at`  | TIMESTAMPTZ | |
| `revoked_at`  | TIMESTAMPTZ NULL | |
| `created_at`  | TIMESTAMPTZ | |

### `password_reset_tokens`
| Column       | Type        | Notes |
|--------------|-------------|-------|
| `id`         | UUID PK     | |
| `user_id`    | UUID FK     | |
| `token`      | VARCHAR(128)| Unique |
| `expires_at` | TIMESTAMPTZ | |
| `used_at`    | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

### `password_reset_attempts`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | |
| `email`       | VARCHAR(255)| Lower-cased lookup |
| `ip_address`  | VARCHAR(45) | |
| `requested_at`| TIMESTAMPTZ | |

### `totp_secrets`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `user_id`     | UUID PK/FK  | References `users.id` |
| `secret`      | VARCHAR(32) | Base32-encoded secret |
| `confirmed_at`| TIMESTAMPTZ NULL | When TOTP verified |
| `created_at`  | TIMESTAMPTZ | |

### `user_key_pairs`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `user_id`     | UUID PK/FK  | |
| `public_key`  | TEXT        | |
| `private_blob`| BYTEA       | Encrypted private key |
| `algorithm`   | VARCHAR(32) | e.g., `curve25519` |
| `updated_at`  | TIMESTAMPTZ | |


## 2. Contacts & invitations

### `contacts`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | |
| `owner_id`    | UUID FK     | References `users.id` |
| `contact_id`  | UUID FK     | References `users.id` |
| `status`      | VARCHAR(16) | Enum `pending`, `accepted`, `blocked` |
| `alias`       | VARCHAR(255)| Optional |
| `created_at`  | TIMESTAMPTZ | |
| `updated_at`  | TIMESTAMPTZ | |

### `invitations`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | |
| `conversation_id` | UUID FK | |
| `email`       | VARCHAR(255)| Target email |
| `role`        | VARCHAR(32) | Default conversation role |
| `token`       | VARCHAR(128)| Unique join token |
| `expires_at`  | TIMESTAMPTZ | |
| `accepted_at` | TIMESTAMPTZ NULL | |
| `created_at`  | TIMESTAMPTZ | |


## 3. Messaging & realtime

Existing tables (`conversations`, `conversation_members`, `messages`,
`message_reads`) stay but gain some additions:

- `conversations`: add boolean `is_group`, nullable `owner_id` (UUID) and JSONB
  `settings` for future-proofing (slow mode, history).
- `conversation_members`: keep `role` (enum) and add `invited_by` + metadata for
  join timestamps.
- `messages`: support end-to-end payloads via `content_json` (already) plus
  optional `edited_at`, `deleted_at`, `encryption_header` (JSONB) and soft delete
  flag. Index on `(conversation_id, created_at DESC)` remains.
- `message_reads`: unchanged.

Additional supporting tables:

### `message_reactions`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | |
| `message_id`  | UUID FK     | |
| `user_id`     | UUID FK     | |
| `emoji`       | VARCHAR(16) | |
| `created_at`  | TIMESTAMPTZ | |
| Unique constraint on `(message_id, user_id, emoji)`.

### `message_attachments`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | |
| `message_id`  | UUID FK     | |
| `storage_path`| TEXT        | Reference to object store |
| `filename`    | VARCHAR(255)| Original file name |
| `mime_type`   | VARCHAR(128)| |
| `size_bytes`  | BIGINT      | |
| `created_at`  | TIMESTAMPTZ | |

### `archived_conversations`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `user_id`     | UUID PK/FK  | |
| `conversation_id` | UUID PK/FK | |
| `archived_at` | TIMESTAMPTZ | |


## 4. Devices & security logging

### `devices`
We will merge legacy push tokens with the new structure:
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | UUID PK     | Existing |
| `user_id`     | UUID FK     | |
| `name`        | VARCHAR(255)| Friendly name |
| `platform`    | VARCHAR(16) | `ios`, `android`, `web`, etc. |
| `user_agent`  | TEXT NULL   | |
| `push_token`  | TEXT NULL   | APNS/FCM token |
| `trusted`     | BOOLEAN     | |
| `created_at`  | TIMESTAMPTZ | |
| `last_seen_at`| TIMESTAMPTZ | |

### `audit_logs`
| Column        | Type        | Notes |
|---------------|-------------|-------|
| `id`          | BIGSERIAL PK| |
| `user_id`     | UUID FK NULL| |
| `action`      | VARCHAR(64) | e.g., `login`, `message_sent` |
| `ip_address`  | VARCHAR(45) | |
| `user_agent`  | TEXT NULL   | |
| `metadata`    | JSONB       | Extra context |
| `created_at`  | TIMESTAMPTZ | |


## 5. Constraints & indices overview

- Unique indices on all token columns (`token`, `token_jti`) and
  `(owner_id, contact_id)`, `(message_id, user_id, emoji)`.
- Check constraint on `contacts` to prevent self-link (`owner_id <> contact_id`).
- Enum types stored as `CHECK` constraints or PostgreSQL enums (depending on
  implementation detail chosen during migration).
- Cascading deletes where safe (e.g., deleting a user removes tokens, devices,
  TOTP secrets) but keep audit logs with `SET NULL`.


## 6. Next steps

1. Update SQLAlchemy models to reflect the structure above (users, auth,
   messaging, logging).
2. Generate Alembic migration(s) to transform the existing initial schema into
   this richer model.
3. Wire the activation and authentication services to the new tables (email
   confirmation, refresh token revocation, password reset, TOTP).

This specification will serve as the contract before moving on to the
implementation phase.

## 7. Email confirmation & authentication flow (preview)

To prepare step 2 of the feature work (API/services implementation) we will
align on the critical flow:

1. **Registration (`POST /auth/register`)**
   - Validate payload via Pydantic (`email`, `password`, `display_name`).
   - Create `users` row with `is_confirmed=False`, `is_active=True`, `role=member`.
   - Generate `EmailConfirmationToken` (random 48–64 bytes URL-safe string),
     expire after 24 h, store hashed digest if we decide to harden further.
   - Persist token and dispatch branded email using SMTP settings.
2. **Confirmation (`GET /auth/confirm/{token}`)**
   - Look up token (case-sensitive) ensuring `expires_at > now` and `consumed_at
     is NULL`.
   - Mark the token as consumed (timestamp).
   - Flip `users.is_confirmed` to `True`, optionally activate login notifications.
   - Return a redirect (front) or JSON success.
3. **Login (`POST /auth/token`)**
   - Reject if `is_confirmed=False` or `is_active=False`.
   - Verify password (bcrypt ≤72 bytes) and optional TOTP.
   - Issue access & refresh JWT, store refresh metadata.
   - Log event in `audit_logs`, optionally send login email alert when
     `notification_login=True`.
4. **Refresh / logout**
   - Refresh endpoint validates non-revoked token entry before issuing new JWT.
   - Logout revokes the specific token by setting `revoked_at`.
   - Logout-all flips all active refresh tokens for the user.
5. **Password reset flow**
   - Rate limit using `password_reset_attempts`.
   - Store one-time `password_reset_tokens` with 1 h expiry, hashed if required.
6. **TOTP lifecycle**
   - Provision secret row in `totp_secrets`, mark `confirmed_at` once validated.
   - Use `failed_totp_attempts` and `totp_locked_until` columns to throttle brute
     force attempts.

These behavioural rules will guide the upcoming service-layer implementation and
ensure compatibility with the legacy expectations while leveraging the new
schema.
