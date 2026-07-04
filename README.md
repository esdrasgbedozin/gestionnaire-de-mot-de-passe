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
python3 tools/security_test.py        # Audit sécurité complet
python3 tools/test_functional.py      # Tests fonctionnels
./tools/migrate_database.sh           # Migration manuelle BDD
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

### Architecture zero-knowledge (chiffrement au repos)

Le serveur **ne peut pas** déchiffrer le coffre sans le master password de l'utilisateur :

- Chaque coffre est protégé par une **VMK** (Vault Master Key, 256 bits aléatoires) qui chiffre les entrées en **AES-256-GCM**.
- La VMK n'est jamais stockée en clair : elle est **enveloppée** par une **KEK** dérivée du master password via **Argon2id** (mémoire-dur, sel par utilisateur). Seul `Argon2id(master_password, sel)` permet de la déballer.
- Le **master password n'est jamais stocké** (ni en clair, ni haché) : l'authentification = déballage réussi de la VMK (le tag GCM prouve l'identité). Un dump de la base ne révèle donc que des données chiffrées.
- Pendant une session, la VMK réside uniquement en **mémoire (Redis, sans persistance disque)** ; sa révocation évince la clé.
- **Conséquence** : si le master password est oublié, le coffre est **irrécupérable** (par conception).

### Autres protections

- **Force du master password** évaluée par zxcvbn (score ≥ 3 exigé), longueur ≥ 12.
- **Rate-limiting** backé Redis (login, register, refresh, suppression de compte).
- **Ré-authentification** (déballage VMK + confirmation) exigée avant la suppression du compte.
- En-têtes de sécurité (CSP stricte, HSTS en prod), protection XSS (bleach) et injection SQL (ORM paramétré).

### `EMERGENCY_RESET_KEY`

Cette clé d'urgence autorise **uniquement** l'endpoint admin de **réinitialisation du rate-limiter** (débloquer une IP faussement bloquée). Elle **ne donne aucun accès au coffre** ni aux données chiffrées.

```bash
# Audit complet
./tools/security_test.py
```

---

## 🛠️ Développement

### 🚀 Démarrage Rapide pour Développeurs
```bash
# Cloner le projet
git clone https://github.com/esdrasgbedozin/gestionnaire-de-mot-de-passe
cd gestionnaire-de-mot-de-passe

# Lancement en mode développement
./deploy.sh start

# Accès aux applications
# Frontend: http://localhost:3000
# API: http://localhost:8080
# Base de données: localhost:5432 (interne seulement)
```

### 🧪 Tests et Validation
```bash
# Tests fonctionnels complets
python3 tools/test_functional.py

# Audit de sécurité
python3 tools/security_test.py

# Vérification santé des services
./deploy.sh health
```

### 🔧 Structure du Code
```
backend/
├── app.py              # Point d'entrée Flask
├── config.py           # Configuration environnement
├── extensions.py       # Extensions Flask (DB, JWT, etc.)
└── app/
    ├── routes/         # Endpoints API (auth, passwords, users)
    ├── services/       # Logique métier (encryption, JWT, etc.)
    └── models/         # (Future implémentation SQLAlchemy)

frontend/src/
├── components/         # Composants React réutilisables
├── pages/             # Pages de l'application
├── services/          # Appels API
├── contexts/          # Gestion d'état (Auth, Theme)
└── utils/             # Utilitaires
```

## 🆘 Résolution de Problèmes

| Problème | Solution |
|----------|----------|
| "Error loading passwords" | `./deploy.sh restart` (migration auto) |
| "Rate limit exceeded" | `./tools/rate_limit_helper.sh reset` |
| "Internal Server Error" | `./deploy.sh clean && ./deploy.sh start` |
| Problème de migration BDD | `./tools/migrate_database.sh` |
| Logs détaillés | `docker logs password_manager_backend` |

---

## 📚 Documentation

- **� Ce README** : Guide complet du projet
- **�📋 API :** [docs/API-DOCUMENTATION.md](docs/API-DOCUMENTATION.md) - Référence complète des endpoints
- **🏭 Production :** [PRODUCTION-GUIDE.md](PRODUCTION-GUIDE.md) - Déploiement sécurisé
- **📊 Spécifications :** [cahier_des_charges.md](cahier_des_charges.md) - Exigences du projet

---

## 🎖️ Architecture Technique

### 🏗️ Stack Technologique
**Backend:** Flask (Python 3.11) + PostgreSQL 15 + JWT + AES-256-GCM  
**Frontend:** React 18 + TailwindCSS + Context API  
**Déploiement:** Docker Compose + Nginx + SSL/TLS

### 🔐 Sécurité Intégrée
- **Chiffrement**: AES-256-GCM pour les mots de passe
- **Authentification**: JWT avec expiration
- **Rate Limiting**: Adaptatif (dev: 20/5min, prod: 5/5min)
- **Protection**: CORS, CSP, XSS, injection SQL
- **Migration BDD**: Automatique au démarrage

### 📊 Base de Données
- **PostgreSQL 15** avec chiffrement
- **Migration automatique** des schémas
- **Sauvegarde** intégrée
- **Index optimisés** pour les performances

---

## 📄 Licence

MIT License - Libre d'utilisation pour tous projets.

---

**🚀 Prêt à sécuriser vos mots de passe ?**

```bash
./deploy.sh start
```