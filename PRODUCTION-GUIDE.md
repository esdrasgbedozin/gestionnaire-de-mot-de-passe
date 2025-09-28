# 🚀 Guide de Déploiement en Production

## ⚡ Démarrage Rapide

```bash
# 1. Générer les clés de sécurité
./deploy-production.sh generate-keys

# 2. Configurer .env.production avec les clés générées
cp .env.production .env.production.backup
# Éditez .env.production avec vos vraies valeurs

# 3. Démarrer en production
./deploy-production.sh start

# 4. Vérifier le statut
./deploy-production.sh status
```

## 🔧 Configuration Détaillée

### 1. Variables d'Environnement Critiques

**⚠️ OBLIGATOIRE à changer en production :**

```bash
# Générer des clés sécurisées :
openssl rand -base64 48   # Pour SECRET_KEY et JWT_SECRET_KEY
openssl rand -base64 32 | cut -c1-32   # Pour ENCRYPTION_KEY (exactement 32 chars)

# Dans .env.production :
SECRET_KEY=your-real-secret-key-here-minimum-32-characters-required
JWT_SECRET_KEY=your-jwt-secret-different-from-flask-secret-key
ENCRYPTION_KEY=your32characterencryptionkeyhere!
DATABASE_URL=postgresql://prod_user:strong_password@prod_host:5432/prod_db
```

### 2. Certificats SSL

**Option A: Let's Encrypt (Gratuit)**
```bash
# Installer Certbot
sudo apt install certbot

# Obtenir le certificat
sudo certbot certonly --standalone -d your-domain.com

# Copier les certificats
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
```

**Option B: Certificats existants**
```bash
mkdir -p ssl
cp your-certificate.pem ssl/cert.pem
cp your-private-key.pem ssl/key.pem
```

### 3. Base de Données Production

**PostgreSQL externe (recommandé) :**
```bash
# Sur votre serveur de base de données
sudo -u postgres createdb prod_password_manager
sudo -u postgres createuser prod_admin
sudo -u postgres psql -c "ALTER USER prod_admin WITH ENCRYPTED PASSWORD 'strong_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE prod_password_manager TO prod_admin;"
```

### 4. Nginx Configuration

Éditez `nginx/nginx.prod.conf` :
- Changez `your-domain.com` par votre vrai domaine
- Ajustez les chemins SSL si nécessaire
- Configurez les IPs autorisées pour `/api/admin/`

## 🔒 Sécurité Production

### Checklist de Sécurité

- [ ] ✅ Toutes les clés secrètes changées
- [ ] ✅ HTTPS configuré avec certificats valides  
- [ ] ✅ Base de données sécurisée avec mot de passe fort
- [ ] ✅ Rate limiting strict activé
- [ ] ✅ Headers de sécurité configurés
- [ ] ✅ CORS limité aux domaines autorisés
- [ ] ✅ Endpoints admin protégés par IP
- [ ] ✅ Logs de sécurité activés
- [ ] ✅ Sauvegardes automatiques configurées

### Configuration Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 5432/tcp     # PostgreSQL (ne pas exposer)
sudo ufw enable
```

## 📊 Monitoring et Maintenance

### Commandes de Monitoring

```bash
# Statut général
./deploy-production.sh status

# Health check détaillé
./deploy-production.sh health

# Logs en temps réel
./deploy-production.sh logs

# Logs d'un service spécifique
./deploy-production.sh logs backend
./deploy-production.sh logs nginx
```

### Sauvegarde Automatique

```bash
# Sauvegarde manuelle
./deploy-production.sh backup

# Crontab pour sauvegarde automatique (tous les jours à 2h)
0 2 * * * /path/to/deploy-production.sh backup >> /var/log/backup.log 2>&1
```

### Mise à Jour

```bash
# 1. Sauvegarder avant mise à jour
./deploy-production.sh backup

# 2. Mettre à jour le code
git pull origin main

# 3. Redémarrer avec reconstruction
./deploy-production.sh restart

# 4. Vérifier le statut
./deploy-production.sh status
```

## 🚨 Dépannage

### Problèmes Courants

**1. Rate Limit en Production**
```bash
# Avec clé d'urgence
curl -X POST https://your-domain.com/api/admin/rate-limit-reset \
  -H "X-Emergency-Key: your-emergency-key"
```

**2. Base de Données Inaccessible**
```bash
# Vérifier les logs
./deploy-production.sh logs database

# Tester la connexion
docker-compose -f docker-compose.production.yml exec database psql -U prod_admin -d prod_password_manager
```

**3. Certificats SSL Expirés**
```bash
# Renouveler avec Certbot
sudo certbot renew

# Copier les nouveaux certificats
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem

# Redémarrer Nginx
docker-compose -f docker-compose.production.yml restart nginx
```

## 📈 Optimisations Avancées

### Performance
- Configuration PostgreSQL optimisée
- Cache Redis pour les sessions
- CDN pour les assets statiques
- Compression Gzip activée

### Haute Disponibilité
- Load balancer multiple instances
- Base de données en cluster
- Réplication géographique
- Monitoring avec Prometheus/Grafana

### CI/CD
- Pipeline GitHub Actions
- Tests automatisés en pré-production
- Déploiement Blue/Green
- Rollback automatique en cas d'erreur

---

## 🎯 Résumé des Commandes Essentielles

```bash
# Configuration initiale
./deploy-production.sh generate-keys
# Éditez .env.production
./deploy-production.sh start

# Opérations courantes
./deploy-production.sh status        # Vérifier l'état
./deploy-production.sh health        # Health check complet
./deploy-production.sh backup        # Sauvegarder
./deploy-production.sh logs backend  # Voir les logs
./deploy-production.sh restart       # Redémarrer
```

🚀 **Votre gestionnaire de mots de passe est maintenant prêt pour la production !**