FROM node:18-alpine

WORKDIR /app

# Copier les fichiers de configuration des dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code source
COPY . .

# M4 : exécuter en utilisateur non-root. L'image node fournit l'utilisateur
# `node` (uid 1000). Il doit posséder /app pour écrire le cache de react-scripts
# (node_modules/.cache) et le build sans perte d'accès.
RUN chown -R node:node /app
USER node

# Exposer le port
EXPOSE 3000

# Variables d'environnement
ENV REACT_APP_API_URL=http://localhost:8080/api
ENV CHOKIDAR_USEPOLLING=true

# Commande de démarrage
CMD ["npm", "start"]