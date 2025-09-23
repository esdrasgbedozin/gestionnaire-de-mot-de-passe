g# 🚀 Guide de Déploiement - Gestionnaire de Mots de Passe

## 📋 Prérequis

### Environnement de Production
- **OS :** Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **RAM :** Minimum 2GB, recommandé 4GB
- **CPU :** 2 cores minimum
- **Stockage :** 20GB minimum (SSD recommandé)
- **Réseau :** Ports 80, 443 ouverts

### Logiciels Requis
- Docker 20.10+
- Docker Compose 1.29+
- Git
- Nginx (reverse proxy)
- Certbot (SSL/TLS)

---

## 🛠️ Installation Étape par Étape

### 1. Préparation du Serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y git curl wget ufw nginx certbot python3-certbot-nginx

# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installation de Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Redémarrage pour appliquer les groupes
sudo reboot
```

### 2. Configuration du Firewall

```bash
# Configuration UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Vérification
sudo ufw status
```

### 3. Clonage du Projet

```bash
# Création du répertoire de déploiement
sudo mkdir -p /opt/password-manager
sudo chown $USER:$USER /opt/password-manager
cd /opt/password-manager

# Clonage du repository
git clone <URL_DU_REPOSITORY> .

# Vérification de la structure
ls -la
```

---

## 🔧 Configuration

### 1. Variables d'Environnement de Production

```bash
# Copier le template
cp .env.example .env

# Éditer les variables de production
nano .env
```

**Fichier `.env` de production :**
```bash
# Base de données
POSTGRES_DB=password_manager_prod
POSTGRES_USER=pm_admin
POSTGRES_PASSWORD=<MOT_DE_PASSE_FORT_32_CARACTERES>
POSTGRES_HOST=database
POSTGRES_PORT=5432

# Flask
FLASK_ENV=production
SECRET_KEY=<CLE_SECRETE_64_CARACTERES_ALEATOIRE>
JWT_SECRET_KEY=<CLE_JWT_64_CARACTERES_ALEATOIRE>

# Sécurité
BCRYPT_LOG_ROUNDS=12
CORS_ORIGINS=https://votre-domaine.com

# Logs
LOG_LEVEL=INFO
```

### 2. Génération des Clés Sécurisées

```bash
# Génération de clés aléatoires sécurisées
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
```

### 3. Docker Compose pour la Production

**Créer `docker-compose.prod.yml` :**
```yaml
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - backend-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    env_file: .env
    depends_on:
      database:
        condition: service_healthy
    networks:
      - backend-network
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    expose:
      - "5000"

volumes:
  postgres_data:
    driver: local

networks:
  backend-network:
    driver: bridge
```

### 4. Dockerfile de Production

**Créer `backend/Dockerfile.prod` :**
```dockerfile
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Port d'exposition
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

---

## 🌐 Configuration Nginx

### 1. Configuration du Reverse Proxy

**Créer `/etc/nginx/sites-available/password-manager` :**
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # SSL Security Headers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';";
    
    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # CORS Headers (si nécessaire)
        add_header Access-Control-Allow-Origin "https://votre-domaine.com";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    }
    
    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
    
    # Frontend (à configurer quand prêt)
    location / {
        root /var/www/password-manager/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Logs
    access_log /var/log/nginx/password-manager.access.log;
    error_log /var/log/nginx/password-manager.error.log;
}
```

### 2. Activation de la Configuration

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/password-manager /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

---

## 🔒 Configuration SSL/TLS

### 1. Certificat Let's Encrypt

```bash
# Obtenir le certificat SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Vérifier le renouvellement automatique
sudo certbot renew --dry-run

# Configurer le renouvellement automatique
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null
```

---

## 🚀 Déploiement

### 1. Construction et Démarrage

```bash
# Démarrage en mode production
docker-compose -f docker-compose.prod.yml up -d --build

# Vérification des services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs

# Test de santé
curl -k https://votre-domaine.com/health
```

### 2. Migration de Base de Données

```bash
# Exécuter les migrations
docker-compose -f docker-compose.prod.yml exec backend flask db upgrade

# Vérifier la base de données
docker-compose -f docker-compose.prod.yml exec database psql -U pm_admin -d password_manager_prod -c "\dt"
```

---

## 📊 Monitoring et Logs

### 1. Configuration des Logs

```bash
# Créer le répertoire de logs
sudo mkdir -p /var/log/password-manager
sudo chown $USER:$USER /var/log/password-manager

# Rotation des logs
sudo tee /etc/logrotate.d/password-manager > /dev/null << EOF
/var/log/password-manager/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
```

### 2. Monitoring avec Scripts

**Créer `scripts/monitor.sh` :**
```bash
#!/bin/bash

# Vérification de santé
curl -s https://votre-domaine.com/health > /dev/null
if [ $? -eq 0 ]; then
    echo "$(date): API OK" >> /var/log/password-manager/monitor.log
else
    echo "$(date): API DOWN!" >> /var/log/password-manager/monitor.log
    # Alerte (email, Slack, etc.)
fi

# Vérification des services Docker
if ! docker-compose -f /opt/password-manager/docker-compose.prod.yml ps | grep -q "Up"; then
    echo "$(date): Docker services issue!" >> /var/log/password-manager/monitor.log
    # Redémarrage automatique
    docker-compose -f /opt/password-manager/docker-compose.prod.yml restart
fi
```

### 3. Cron de Monitoring

```bash
# Ajouter au crontab
echo "*/5 * * * * /opt/password-manager/scripts/monitor.sh" | crontab -
```

---

## 💾 Sauvegarde

### 1. Script de Sauvegarde

**Créer `scripts/backup.sh` :**
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/password-manager"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
docker-compose -f /opt/password-manager/docker-compose.prod.yml exec -T database pg_dump -U pm_admin password_manager_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Sauvegarde des fichiers de configuration
cp /opt/password-manager/.env $BACKUP_DIR/env_backup_$DATE
cp -r /opt/password-manager/logs $BACKUP_DIR/logs_backup_$DATE/

# Compression
tar -czf $BACKUP_DIR/full_backup_$DATE.tar.gz $BACKUP_DIR/*_$DATE*

# Nettoyage (garder 30 jours)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup completed - $BACKUP_DIR/full_backup_$DATE.tar.gz"
```

### 2. Cron de Sauvegarde

```bash
# Sauvegarde quotidienne à 2h du matin
echo "0 2 * * * /opt/password-manager/scripts/backup.sh" | sudo crontab -
```

---

## 🔧 Maintenance

### 1. Mise à Jour

```bash
# Arrêt des services
docker-compose -f docker-compose.prod.yml down

# Mise à jour du code
git pull origin main

# Reconstruction et redémarrage
docker-compose -f docker-compose.prod.yml up -d --build

# Migrations si nécessaire
docker-compose -f docker-compose.prod.yml exec backend flask db upgrade
```

### 2. Redémarrage des Services

```bash
# Redémarrage complet
docker-compose -f docker-compose.prod.yml restart

# Redémarrage d'un service spécifique
docker-compose -f docker-compose.prod.yml restart backend

# Vérification des logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 🛡️ Sécurité en Production

### 1. Hardening du Serveur

```bash
# Désactiver SSH par mot de passe (utiliser les clés)
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PermitRootLogin no

# Redémarrer SSH
sudo systemctl restart ssh

# Fail2ban pour la protection SSH
sudo apt install fail2ban
```

### 2. Monitoring de Sécurité

```bash
# Installer des outils de monitoring
sudo apt install -y auditd aide rkhunter

# Configuration d'aide pour l'intégrité des fichiers
sudo aide --init
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

---

## 📋 Checklist de Déploiement

### Pré-déploiement
- [ ] Serveur configuré avec les prérequis
- [ ] Nom de domaine pointant vers le serveur
- [ ] Firewall configuré
- [ ] Variables d'environnement sécurisées
- [ ] Certificats SSL obtenus

### Déploiement
- [ ] Code déployé et testé
- [ ] Base de données migrée
- [ ] Services Docker démarrés
- [ ] Nginx configuré
- [ ] SSL/TLS fonctionnel
- [ ] Tests d'API réussis

### Post-déploiement
- [ ] Monitoring configuré
- [ ] Sauvegardes programmées
- [ ] Logs opérationnels
- [ ] Tests de charge basiques
- [ ] Documentation mise à jour
- [ ] Équipe formée

---

## 🆘 Dépannage

### Problèmes Courants

**Service ne démarre pas :**
```bash
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml exec backend flask db upgrade
```

**Base de données non accessible :**
```bash
docker-compose -f docker-compose.prod.yml exec database psql -U pm_admin -d password_manager_prod
```

**SSL non fonctionnel :**
```bash
sudo certbot certificates
sudo nginx -t
sudo systemctl status nginx
```

**API lente :**
```bash
# Vérifier les ressources
docker stats
htop
```

---

## 📞 Support

Pour toute question sur le déploiement :
1. Vérifier les logs d'application
2. Consulter la documentation API
3. Vérifier les issues GitHub
4. Contacter l'équipe de développement

**Logs importants :**
- `/var/log/nginx/password-manager.error.log`
- `docker-compose logs backend`
- `/opt/password-manager/logs/app.log`