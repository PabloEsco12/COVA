# Étape de build
FROM node:18-alpine AS builder

WORKDIR /app

# Copier les fichiers package*.json
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier tout le reste (src, public, etc.)
COPY . .

# Construire l'application
RUN npm run build

# Étape de runtime
FROM nginx:1.23-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
