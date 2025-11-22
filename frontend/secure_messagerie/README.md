## secure_messagerie (frontend)

Vue 3 + Vite app for the secure messaging dashboard (conversations, contacts, devices, settings).

### Prerequisites
- Node.js 18+
- Backend API reachable (`VITE_API_URL`), WebSocket base (`VITE_WS_BASE` if you override the default)

### Environment
- Copy `.env.example` at repo root to `frontend/secure_messagerie/.env.development` or set at least:
  - `VITE_API_URL=http://localhost:8000/api` (or `http://localhost:18000/api` when using the local compose)
  - Optional: `VITE_WS_BASE=ws://localhost:18000/api/ws` to force the WS endpoint
  - Optional: `VITE_TENOR_API_KEY` for GIF search (leave empty to use the local emoji/GIF library only)

### Install and run (dev)
```bash
npm install
npm run dev -- --host --port 5176
```

### Build (production bundle)
```bash
npm run build
```
Outputs go to `dist/` (served by the prod image or a static host).

### Smoke test
With backend running and demo creds set in `scripts/debug-send.js`, you can run:
```bash
node ../../scripts/debug-send.js
```
It opens the app headlessly, logs in, and posts a message.
