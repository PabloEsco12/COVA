# Dockerfile de dev frontend (Vite en mode --host)
FROM node:18-alpine

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
