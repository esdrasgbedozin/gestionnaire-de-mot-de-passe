# � Password Manager

Application sécurisée de gestion de mots de passe avec chiffrement AES-256 et authentification JWT.

## � Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Git

### Installation et lancement
```bash
# 1. Cloner le projet
git clone <votre-repo>
cd gestionnaire-de-mot-de-passe

# 2. Configurer l'environnement
cp .env.example .env
# Modifier .env si nécessaire

# 3. Démarrer l'application
./start.sh
```

L'application sera accessible sur :
- **Backend API** : http://localhost:8080
- **Frontend** : http://localhost:3000 (en développement)
- **Base de données** : PostgreSQL sur port interne uniquement

## ✨ Fonctionnalités

- 🔐 **Authentification sécurisée** (JWT)
- 🛡️ **Chiffrement AES-256-GCM** des mots de passe
- 🎲 **Générateur de mots de passe** robustes
- 📊 **Évaluation de la force** des mots de passe
- 🗂️ **Organisation** par catégories et favoris
- � **Recherche et filtres** avancés
- � **Audit complet** des actions
- � **API REST** documentée

## 🛠️ Développement

```bash
# Arrêter l'application
docker-compose down

# Redémarrer en mode développement
docker-compose up --build

# Voir les logs
docker-compose logs -f

# Accéder au conteneur backend
docker-compose exec backend bash
```

## 📊 Tests de sécurité

```bash
# Tester la sécurité de l'application
cd backend && ./security_test.sh
```

## � Plus d'informations

- **Cahier des charges** : [cahier_des_charges.md](./cahier_des_charges.md)
- **Documentation API** : [docs/API-DOCUMENTATION.md](./docs/API-DOCUMENTATION.md)
- **Guide de déploiement** : [docs/DEPLOYMENT-GUIDE.md](./docs/DEPLOYMENT-GUIDE.md)

## 🛡️ Sécurité

- Chiffrement AES-256-GCM
- PBKDF2 (100k itérations)
- Protection anti-XSS
- Rate limiting
- Headers de sécurité
- Audit complet

## � Support

Score de sécurité actuel : **95%** 🟢
