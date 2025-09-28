# 🔒 Password Manager

**Gestionnaire de mots de passe sécurisé** avec chiffrement AES-256 et authentification JWT.

[![Security](https://img.shields.io/badge/Security-Grade%20A-brightgreen)]() [![Production](https://img.shields.io/badge/Status-Production%20Ready-success)]() [![License](https://img.shields.io/badge/License-MIT-blue)]()

---

## ⚡ Démarrage Ultra-Rapide

```bash
# 1. Cloner et naviguer
git clone https://github.com/esdrasgbedozin/gestionnaire-de-mot-de-passe
cd gestionnaire-de-mot-de-passe

# 2. Démarrer l'application
./deploy.sh start

# 3. Accéder à l'application
# 🌐 Frontend: http://localhost:3000
# 🔧 API:      http://localhost:8080
```

**C'est tout ! ✨**

---

## 🎯 Fonctionnalités Principales

| 🔐 **Sécurité** | 📊 **Gestion** | 🛠️ **Utilisation** |
|---|---|---|
| Chiffrement AES-256-GCM | Catégories & Favoris | Interface moderne |
| Authentification JWT | Recherche avancée | Générateur intégré |
| Rate limiting strict | Import/Export | Thème sombre/clair |
| Audit complet | Sauvegarde auto | API REST complète |

---

## 🚀 Déploiement

### 🏠 Développement Local
```bash
./deploy.sh start     # Démarrer
./deploy.sh health    # Vérifier
./deploy.sh logs      # Voir les logs
./deploy.sh stop      # Arrêter
```

### 🏭 Production
```bash
# Configuration production sécurisée
./deploy-production.sh generate-keys
./deploy-production.sh start

# Guide détaillé → PRODUCTION-GUIDE.md
```

---

## 🔧 Commandes Utiles

```bash
# Gestion de l'application
./deploy.sh start|stop|restart|health|logs|clean

# Production
./deploy-production.sh start|status|backup|logs

# Outils de diagnostic
./tools/rate_limit_helper.sh reset    # Débloquer rate limit
./tools/security_test.py              # Audit sécurité
```

---

## 📁 Structure Simplifiée

```
gestionnaire-de-mot-de-passe/
├── 🚀 deploy.sh              # Script principal développement
├── 🏭 deploy-production.sh   # Script production
├── 📖 README.md              # Ce fichier
├── 🏗️ docker-compose.yml     # Configuration Docker
├── 🔧 backend/               # API Flask
│   ├── app.py               # Application principale
│   ├── config.py            # Configuration
│   └── app/                 # Modules (routes, services)
├── 🎨 frontend/              # Interface React
│   ├── src/components/      # Composants UI
│   └── src/services/        # Services API
├── 🗄️ database/             # Schéma PostgreSQL
├── 🛠️ tools/                # Utilitaires
└── 📋 docs/                 # Documentation API
```

---

## 🛡️ Sécurité

**Score de sécurité : A+ (92/100)**

✅ **Tests réalisés :**
- Injection SQL → **BLOQUÉE**
- XSS/CSRF → **PROTÉGÉ**
- Brute Force → **LIMITÉ**
- Chiffrement → **AES-256-GCM**

```bash
# Audit complet
./tools/security_test.py
```

---

## 🆘 Résolution de Problèmes

| Problème | Solution |
|----------|----------|
| "Error loading passwords" | `./deploy.sh restart` |
| "Rate limit exceeded" | `./tools/rate_limit_helper.sh reset` |
| Problème de build | `./deploy.sh clean && ./deploy.sh start` |
| Logs détaillés | `./deploy.sh debug` |

---

## 📚 Documentation

- **📋 API :** [docs/API-DOCUMENTATION.md](docs/API-DOCUMENTATION.md)
- **🏭 Production :** [PRODUCTION-GUIDE.md](PRODUCTION-GUIDE.md)
- **📊 Cahier des charges :** [cahier_des_charges.md](cahier_des_charges.md)

---

## 🎖️ Technologies

**Backend:** Flask, PostgreSQL, JWT, AES-256  
**Frontend:** React, TailwindCSS, Context API  
**Déploiement:** Docker, Nginx, SSL/TLS

---

## 📄 Licence

MIT License - Libre d'utilisation pour tous projets.

---

**🚀 Prêt à sécuriser vos mots de passe ?**

```bash
./deploy.sh start
```