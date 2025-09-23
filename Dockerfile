# 🚀 Dockerfile unifié pour Password Manager
# Build frontend + backend dans un seul conteneur avec Nginx

# ===== ÉTAPE 1: BUILD FRONTEND =====
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Copier les fichiers de config
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copier le code et builder
COPY frontend/ ./
RUN npm run build

# ===== ÉTAPE 2: SETUP BACKEND =====
FROM python:3.11-slim AS backend-builder

WORKDIR /backend

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code backend
COPY backend/ ./

# ===== ÉTAPE 3: CONTENEUR FINAL =====
FROM nginx:alpine AS production

# Installer Python et les dépendances
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    curl

# Copier Python et les packages depuis le builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copier le frontend buildé vers Nginx
COPY --from=frontend-builder /frontend/build /usr/share/nginx/html

# Copier le backend
COPY --from=backend-builder /backend /app

# Configuration Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Scripts de démarrage
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'cd /app' >> /start.sh && \
    echo 'python3 app.py &' >> /start.sh && \
    echo 'nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

WORKDIR /app

# Exposer les ports
EXPOSE 80 3000 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Démarrage
CMD ["/start.sh"]