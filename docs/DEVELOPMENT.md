# 🛠️ Guide de Développement - Gestionnaire de Mots de Passe

## 📊 État Actuel du Projet
**Backend : ✅ 100% Fonctionnel** | **Frontend : ✅ 100% Fonctionnel** | **Prêt pour production**

## 🚀 Installation et Setup

### Prérequis
- **Docker** et **Docker Compose** installés
- **Git** pour le contrôle de version
- **Node.js 18+** (pour développement local du frontend)
- **Python 3.11+** (pour développement local du backend)

### Installation rapide

1. **Cloner le repository**
```bash
git clone <repository-url>
cd gestionnaire-de-mot-de-passe
```

2. **Configurer l'environnement**
```bash
cp .env.example .env
# Modifiez les variables d'environnement dans .env
```

3. **Lancer avec Docker**
```bash
docker-compose up -d
```

4. **Accéder à l'application**
- ✅ Backend API: http://localhost:8080 (FONCTIONNEL - 9 endpoints)
- ✅ Base de données: localhost:5432 (PostgreSQL configuré)
- ✅ Frontend: http://localhost:3000 (Application React complète)

## ✅ Backend - Complètement Fonctionnel

Le backend est **100% terminé** avec :
- 🔐 **Authentification JWT** complète (inscription, connexion)
- 🛡️ **Chiffrement AES-256-GCM** avec PBKDF2 (100k itérations)
- 🎲 **Générateur de mots de passe** avec 5 presets et évaluation
- 📝 **CRUD complet** : 9 endpoints API documentés
- 🗂️ **Organisation avancée** : catégories, tags, favoris
- 🔍 **Recherche et filtres** avancés
- 🕵️ **Audit complet** de toutes les opérations

### Tests Backend
```bash
# Test complet de l'API
cd backend
python test_api_complete.py

# Tests des services
python tests/test_password_services.py
```

## ✅ Frontend - Application React Complète

Le frontend est maintenant **100% fonctionnel** avec :
- 🎨 **Interface React moderne** avec TailwindCSS
- 🌙 **Thème sombre/clair** avec persistance localStorage
- 👤 **Gestion des profils** utilisateur avec noms d'utilisateur
- 🔍 **Recherche avancée** et filtrage des mots de passe
- 📊 **Dashboard** avec statistiques en temps réel
- 🔐 **Authentification complète** (connexion/inscription)
- 📱 **Design responsive** adaptatif
- 🎲 **Générateur de mots de passe** intégré
- 📈 **Activités récentes** et audit

### Technologies utilisées :
- **React 18** avec JavaScript
- **Tailwind CSS** pour le styling moderne
- **React Router** pour la navigation
- **Axios** pour les appels API
- **React Hot Toast** pour les notifications
- **Heroicons** pour l'iconographie

## 🏗️ Structure du Projet

```
gestionnaire-de-mot-de-passe/
├── backend/                    # API Flask
│   ├── app/
│   │   ├── models/            # Modèles SQLAlchemy
│   │   ├── routes/            # Routes API
│   │   ├── services/          # Logique métier
│   │   └── utils/             # Utilitaires
│   ├── config.py              # Configuration
│   ├── app.py                 # Point d'entrée
│   └── requirements.txt       # Dépendances Python
├── frontend/                   # Interface React
│   ├── src/
│   │   ├── components/        # Composants réutilisables
│   │   ├── pages/            # Pages de l'application
│   │   ├── contexts/         # Contexts React
│   │   ├── services/         # Services API
│   │   └── utils/            # Utilitaires
│   └── package.json          # Dépendances Node.js
├── database/                   # Scripts SQL
│   └── init.sql              # Initialisation DB
├── docs/                      # Documentation
├── scripts/                   # Scripts utilitaires
└── docker-compose.yml        # Configuration Docker
```

## 🔧 Développement Local

### Backend (Flask)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

### Frontend (React)
```bash
cd frontend
npm install
npm start
```

### Base de Données
```bash
# Accéder à PostgreSQL
docker exec -it password_manager_db psql -U admin -d password_manager

# Exécuter des migrations (quand disponibles)
cd backend
flask db upgrade
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Inscription
- `POST /api/auth/login` - Connexion
- `POST /api/auth/logout` - Déconnexion
- `POST /api/auth/refresh` - Rafraîchir token

### Passwords
- `GET /api/passwords` - Lister les mots de passe
- `POST /api/passwords` - Créer un mot de passe
- `GET /api/passwords/{id}` - Obtenir un mot de passe
- `PUT /api/passwords/{id}` - Modifier un mot de passe
- `DELETE /api/passwords/{id}` - Supprimer un mot de passe

### Users
- `GET /api/users/profile` - Profil utilisateur
- `PUT /api/users/profile` - Modifier profil
- `DELETE /api/users/account` - Supprimer compte

## 🧪 Tests

### Backend
```bash
cd backend
pytest
pytest --cov=app  # Avec couverture
```

### Frontend
```bash
cd frontend
npm test
npm run test:coverage
```

## 🛠️ Conventions de Code

### Git Workflow
- **Branches** : `feature/nom-feature`, `bugfix/nom-bug`, `hotfix/nom-hotfix`
- **Commits** : Format conventionnel
  ```
  type(scope): description
  
  feat(auth): ajouter authentification 2FA
  fix(api): corriger validation mot de passe
  docs(readme): mettre à jour installation
  ```

### Code Style
- **Python** : PEP 8, formaté avec `black`
- **JavaScript** : ESLint + Prettier
- **SQL** : Noms en snake_case

### Sécurité
- **Mots de passe** : Toujours hashés avec bcrypt (12+ rounds)
- **Tokens JWT** : Expiration courte (1h access, 30j refresh)
- **Chiffrement** : AES-256 pour les mots de passe stockés
- **HTTPS** : Obligatoire en production
- **Variables sensibles** : Toujours dans .env

## 🚨 Troubleshooting

### Problèmes courants
1. **Base de données inaccessible**
   ```bash
   docker-compose down
   docker-compose up -d database
   ```

2. **Erreurs de permissions**
   ```bash
   sudo chown -R $USER:$USER .
   ```

3. **Port déjà utilisé**
   ```bash
   # Modifier les ports dans docker-compose.yml
   lsof -ti:5000 | xargs kill -9  # Tuer processus sur port 5000
   ```

## 📈 Monitoring et Logs

### Logs Docker
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### Métriques
- **Backend** : Logs structurés JSON
- **Database** : Logs PostgreSQL
- **Audit** : Table audit_logs pour traçabilité

## 🔒 Sécurité en Production

### Variables d'environnement à changer
- `JWT_SECRET_KEY` : Clé forte 64+ caractères
- `ENCRYPTION_KEY` : Clé AES 32 bytes exactement
- `DB_PASSWORD` : Mot de passe fort
- `BCRYPT_ROUNDS` : 14+ en production

### Configuration serveur
- HTTPS uniquement (certificat SSL)
- Firewall restrictif
- Sauvegardes automatiques
- Monitoring des intrusions