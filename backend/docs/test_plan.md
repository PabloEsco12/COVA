# Platform Test Plan

This checklist covers the new backend flows introduced for authentication,
contacts, conversations, and invitations.

## 1. Environment bootstrap

```bash
pip install -r backend/requirements.txt
# Only needed when upgrading from the legacy Flask schema:
# alembic stamp base
alembic upgrade head
```

If the upgrade fails because the previous revision pointer is inconsistent, run
`alembic stamp base` once and re-try the upgrade. Restart the backend
container/service after applying migrations.

## 2. Automated checks

```bash
pytest
```

The asynchronous test-suite should pass before running manual validation.

## 3. Authentication workflow (curl examples)

1. **Register**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"Secret123!","display_name":"Demo User"}'
   ```
   Expected: `201` with `user_id` and a confirmation message.

2. **Retrieve confirmation token (dev only)**
   ```sql
   SELECT token FROM email_confirmation_tokens ORDER BY created_at DESC LIMIT 1;
   ```
   Tokens are stored hashed; log the raw token in development or inspect server
   logs before sending the email.

3. **Confirm email**
   ```bash
   curl http://localhost:8000/api/auth/confirm/<raw-token>
   ```
   Expected: `200`, message `"Adresse e-mail confirmée."`.

4. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"Secret123!"}'
   ```
   Expected: JSON with access/refresh tokens and the authenticated user. Include
   `"totp_code":"123456"` when TOTP is enabled.

5. **Refresh session**
   ```bash
   curl -X POST http://localhost:8000/api/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"<refresh-token>"}'
   ```

6. **Logout**
   ```bash
   curl -X POST http://localhost:8000/api/auth/logout \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"<refresh-token>"}'
   ```

7. **Logout all devices**
   ```bash
   curl -X POST http://localhost:8000/api/auth/logout-all \
     -H "Authorization: Bearer <access-token>"
   ```

8. **Current user**
   ```bash
   curl http://localhost:8000/api/auth/me \
     -H "Authorization: Bearer <access-token>"
   ```

### Additional auth scenarios

- Login before confirmation → expect HTTP `403`.
- Enter five invalid TOTP codes → account locks for 15 minutes.
- Enable `notification_login` and verify that the login e-mail is delivered when
  SMTP credentials are configured.

## 4. Contacts workflow

Assume two confirmed accounts (`alice@example.com`, `bob@example.com`) and note
their access tokens and user IDs.

1. **Send contact request (Alice → Bob)**
   ```bash
   curl -X POST http://localhost:8000/api/contacts \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"email":"bob@example.com","alias":"Bob"}'
   ```

2. **List contacts**
   ```bash
   curl "http://localhost:8000/api/contacts?status=pending" \
     -H "Authorization: Bearer <alice-access-token>"

   curl http://localhost:8000/api/contacts/pending \
     -H "Authorization: Bearer <bob-access-token>"
   ```

3. **Accept invitation (Bob)**
   ```bash
   curl -X PATCH http://localhost:8000/api/contacts/<contact-id>/status \
     -H "Authorization: Bearer <bob-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"status":"accepted"}'
   ```

4. **Update alias (Alice)**
   ```bash
   curl -X PATCH http://localhost:8000/api/contacts/<contact-id>/alias \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"alias":"Bob - Support"}'
   ```

5. **Delete contact**
   ```bash
   curl -X DELETE http://localhost:8000/api/contacts/<contact-id> \
     -H "Authorization: Bearer <alice-access-token>"
   ```

## 5. Conversations & messages

1. **Create conversation**
   ```bash
   curl -X POST http://localhost:8000/api/conversations \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"title":"Support interne","participant_ids":["<bob-id>"]}'
   ```

2. **Send message**
   ```bash
   curl -X POST http://localhost:8000/api/conversations/<conv-id>/messages \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"content_json":{"type":"text","body":"Bonjour"}}'
   ```

3. **Add reaction (Bob)**
   ```bash
   curl -X POST http://localhost:8000/api/conversations/<conv-id>/messages/<msg-id>/reactions \
     -H "Authorization: Bearer <bob-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"emoji":"👍"}'
   ```

4. **Attach file metadata**
   ```bash
   curl -X POST http://localhost:8000/api/conversations/<conv-id>/messages/<msg-id>/attachments \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"storage_path":"s3://bucket/doc.pdf","filename":"doc.pdf","mime_type":"application/pdf","size_bytes":10240}'
   ```

5. **Toggle archive**
   ```bash
   curl -X POST http://localhost:8000/api/conversations/<conv-id>/archive \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"archived": true}'
   ```

6. **Update settings**
   ```bash
   curl -X PATCH http://localhost:8000/api/conversations/<conv-id>/settings \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"settings":{"slow_mode_sec":10,"history_mode":false}}'
   ```

## 6. Conversation invitations

1. **Create invitation**
   ```bash
   curl -X POST http://localhost:8000/api/conversations/<conv-id>/invitations \
     -H "Authorization: Bearer <alice-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"email":"carol@example.com","role":"member"}'
   ```
   Response includes the invitation metadata and the raw `token` for
   distribution.

2. **List invitations**
   ```bash
   curl http://localhost:8000/api/conversations/<conv-id>/invitations \
     -H "Authorization: Bearer <alice-access-token>"
   ```

Use these end-to-end scenarios to verify behaviour whenever the backend or
schema evolves, and adapt the list as you reintroduce password reset flows,
invitation acceptance endpoints, or realtime websocket changes.
