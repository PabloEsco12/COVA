# Dockerfile de dev frontend (Vite en mode --host)
# Etapes minimales pour lancer la SPA en local dans un conteneur
FROM node:18-alpine

WORKDIR /app

# Installer les dependances de package.json/package-lock
COPY package*.json ./
RUN npm install

# Copier le reste du projet (src, config, assets)
COPY . .

# Exposer le port de dev Vite
EXPOSE 5173

# Commande par defaut: Vite en mode --host pour accepter les connexions externes
CMD ["npm", "run", "dev", "--", "--host"]
