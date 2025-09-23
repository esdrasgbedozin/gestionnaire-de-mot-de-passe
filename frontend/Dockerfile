FROM node:18-alpine

WORKDIR /app

# Copier les fichiers de configuration des dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 3000

# Variables d'environnement
ENV REACT_APP_API_URL=http://localhost:5000/api
ENV CHOKIDAR_USEPOLLING=true

# Commande de démarrage
CMD ["npm", "start"]