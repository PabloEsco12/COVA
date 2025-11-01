# frontend/secure_messagerie/Dockerfile (LOCAL)
FROM node:20-bookworm-slim

WORKDIR /app

# Installer les dépendances
COPY package*.json ./
RUN npm install

# Copier le reste du projet
COPY . .

# Exposer le port de dev Vite
EXPOSE 5173

# Commande par défaut
CMD ["npm", "run", "dev", "--", "--host"]
