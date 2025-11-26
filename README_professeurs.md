## Guide enseignants - Secure Messagerie (Frontend)

Ce document detaille comment tester l’application en production et en local. Il fournit les comptes de demonstration admin, les consignes de test utilisateur et les acces aux services relies.

### Presentation rapide
- Tableau de bord messagerie (Vue 3 + Vite) : conversations, contacts, appareils, reglages.
- Temps reel via WebSocket (messages, presence, notifications navigateur).
- Notifications push navigateur (bridge WebSocket) et GIFs Tenor optionnels.

### Acces production
- URL : https://covamessagerie.be
- Compte administrateur de demonstration :
  - Utilisateur : covamessages3@gmail.com
  - Mot de passe : 3&RXw0E*BHvUSRE^Vt@4
- Parcours recommande :
  1) Connexion via /login avec le compte admin.
  2) Ouvrir le tableau de bord messages, verifier la reception et l’envoi.
  3) Consulter Contacts et Devices pour valider les listings.
  4) Tester les reglages (statut/presence) et les notifications navigateur si autorisees.

### Acces utilisateur (creation de compte)
- Suivre le parcours d’inscription :
  1) Depuis /register, saisir email, mot de passe et nom d’affichage.
  2) Valider l’email si un lien de confirmation est requis (via la boite mail saisie).
  3) Se connecter ensuite via /login.
- Le guide utilisateur detaille est fourni dans le rapport de TFE.

### Services complementaires
- Minio (stockage) : les URL/identifiants
  - Utilisateur : admin
  - Mot de passe : changeme123
- Uptime Kuma (supervision) : 
  - Utilisateur : kuma
  - Mot de passe : KumaAdmin!2025

### Acces local (frontend)
1) Prerequis : Node.js 18+ et npm, API backend joignable (voir .env.example a la racine du repo).
2) Copier `.env.example` vers `frontend/secure_messagerie/.env.development` et definir au minimum `VITE_API_URL` (et `VITE_WS_BASE` si necessaire).
3) Installer et lancer :
```bash
cd frontend/secure_messagerie
npm install
npm run dev -- --host --port 5176
```
4) Ouvrir http://localhost:5176 (l’option `--host` permet l’acces depuis un conteneur ou une VM).
5) Pour tester en local, utiliser un backend local ou distant accessible via les variables Vite.

### Docker (optionnel)
- Dev : `docker build -f Dockerfile -t secure-messagerie-dev .` puis `docker run -p 5173:5173 secure-messagerie-dev`.
- Prod : `docker build -f Dockerfile.prod -t secure-messagerie-prod .` puis `docker run -p 8080:80 secure-messagerie-prod` (adapter `VITE_API_URL`/`VITE_WS_BASE` au build).

### Parcours de verification rapide
- Admin : connexion avec le compte de demonstration, envoi/lecture d’un message, modification du statut, verification des notifications navigateur.
- Utilisateur : creation d’un compte, confirmation email (si requise), envoi d’un message et reception dans une conversation partagee avec l’admin.
- Smoke test automatique : `node ../../scripts/debug-send.js` (necessite le backend et les identifiants de test configures).
