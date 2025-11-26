## Secure Messagerie - Frontend

Single Page Application Vue 3 + Vite pour la messagerie securisee : conversations, reactions, presence, notifications navigateur et gestion des contacts/appareils.

### Presentation
- Tableau de bord complet (conversations, contacts, devices, reglages, FAQ).
- Flux temps reel via WebSocket (messages, presence, notifications).
- Bridge notifications navigateur et recherche GIF Tenor optionnelle.
- UI Bootstrap 5 + Icons, emoji-picker custom element.

### Prerequis
- Node.js 18+ et npm.
- API backend accessible : `VITE_API_URL`.
- WebSocket base optionnelle : `VITE_WS_BASE`.
- Cle Tenor optionnelle : `VITE_TENOR_API_KEY` (GIF).

### Configuration environnement
Copier `.env.example` (racine du repo) vers `frontend/secure_messagerie/.env.development`, puis ajuster :
```
VITE_API_URL=http://localhost:8000/api        # ou http://localhost:18000/api via docker-compose local
VITE_WS_BASE=ws://localhost:18000/api/ws      # optionnel si WS != API
VITE_TENOR_API_KEY=<cle-tenor>                # optionnel
```

### Commandes
- `npm run dev -- --host --port 5176` : serveur Vite de dev (accessible depuis host/conteneurs).
- `npm run build` : bundle de production (dist/).
- `npm run preview` : previsualisation locale du bundle.

### Docker
- Dev : `Dockerfile` (npm install + `npm run dev -- --host`, expose 5173).
- Prod : `Dockerfile.prod` (build Vite puis Nginx servant `dist/`, expose 80). Injecter au besoin `VITE_API_URL`, `VITE_WS_BASE`, `VITE_TENOR_API_KEY` au build.

### Test rapide (smoke)
Backend en marche et identifiants de test dans `scripts/debug-send.js` :
```bash
node ../../scripts/debug-send.js
```
Le script ouvre l’app en headless, se connecte et poste un message pour valider le flux de bout en bout.

### Guide enseignants
Un guide detaille pour les professeurs (acces production, comptes de demonstration, Minio/Uptime Kuma, utilisation en mode admin et utilisateur, et mode local) se trouve dans `README_professeurs.md`.
