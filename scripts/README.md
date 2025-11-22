Scripts utiles
==============

- `debug-send.js` : script Playwright pour ouvrir l'app locale, se connecter avec un compte de démo et envoyer un message dans le module Messages. Idéal pour vérifier rapidement qu'un build front et l'API sont opérationnels (adresse par défaut : `http://localhost:5176`).

Exécution
---------

Depuis la racine du repo, avec les dépendances `frontend/secure_messagerie` installées (Playwright inclus) :

```bash
node scripts/debug-send.js
```

Vous pouvez adapter les identifiants ou l'URL directement dans le script si besoin.
