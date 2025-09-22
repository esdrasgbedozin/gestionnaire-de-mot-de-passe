# 📡 API Documentation - Gestionnaire de Mots de Passe

## 🔗 Base URL
```
http://localhost:8080/api
```

## 🔐 Authentification
Toutes les routes (sauf authentification) nécessitent un token JWT dans l'en-tête :
```
Authorization: Bearer <JWT_TOKEN>
```

---

## 📚 Endpoints Disponibles

### 🔑 Authentification

#### `POST /auth/register`
Créer un nouveau compte utilisateur.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "MotDePasseSecurise123!"
}
```

**Response (201):**
```json
{
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": "db3abef3-ab5d-4418-9652-83f743ec5984",
    "email": "user@example.com",
    "created_at": "2023-09-23T14:30:00Z",
    "is_active": true
  }
}
```

#### `POST /auth/login`
Se connecter et obtenir un token JWT.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "MotDePasseSecurise123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "db3abef3-ab5d-4418-9652-83f743ec5984",
    "email": "user@example.com"
  }
}
```

---

### 🗝️ Gestion des Mots de Passe

#### `GET /passwords`
Récupérer la liste des mots de passe (paginée).

**Paramètres de requête:**
- `page` (int): Numéro de page (défaut: 1)
- `per_page` (int): Éléments par page (défaut: 20, max: 100)
- `search` (string): Recherche dans site_name, username, notes
- `category` (string): Filtrer par catégorie
- `favorites` (bool): Afficher seulement les favoris
- `sort` (string): Champ de tri (site_name, updated_at, etc.)
- `order` (string): Ordre (asc, desc)

**Response (200):**
```json
{
  "passwords": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "site_name": "GitHub",
      "site_url": "https://github.com",
      "username": "mon_username",
      "email": "user@example.com",
      "category": "development",
      "tags": ["coding", "important"],
      "notes": "Compte principal de développement",
      "is_favorite": true,
      "priority": 2,
      "password_strength": 5,
      "requires_2fa": true,
      "created_at": "2023-09-23T14:30:00Z",
      "updated_at": "2023-09-23T14:30:00Z",
      "last_used": null,
      "password_changed_at": "2023-09-23T14:30:00Z",
      "expires_at": null,
      "remind_before_expiry": 30
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 87,
    "has_next": true,
    "has_prev": false
  }
}
```

#### `POST /passwords`
Créer un nouveau mot de passe.

**Request:**
```json
{
  "site_name": "Facebook",
  "site_url": "https://facebook.com",
  "username": "mon_email@example.com",
  "email": "mon_email@example.com",
  "password": "MotDePasseSecret123!",
  "category": "social",
  "tags": ["social", "personnel"],
  "notes": "Compte Facebook personnel",
  "is_favorite": false,
  "priority": 1,
  "requires_2fa": true
}
```

**Response (201):**
```json
{
  "message": "Mot de passe créé avec succès",
  "password": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "site_name": "Facebook",
    // ... autres champs
    "password_strength": 4
  }
}
```

#### `GET /passwords/<id>`
Récupérer un mot de passe spécifique (déchiffré).

**Response (200):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "site_name": "Facebook",
  "username": "mon_email@example.com",
  "password": "MotDePasseSecret123!",
  // ... autres champs
}
```

#### `POST /passwords/generate`
Générer un nouveau mot de passe.

**Request (optionnel):**
```json
{
  "length": 20,
  "include_uppercase": true,
  "include_lowercase": true,
  "include_digits": true,
  "include_special": true,
  "exclude_ambiguous": true,
  "safe_special_only": false
}
```

**Response (200):**
```json
{
  "password": "[6j6dD<Z}@'=Qgkv",
  "strength": 5,
  "entropy": 104.9,
  "feedback": ["Excellent mot de passe!"]
}
```

#### `POST /passwords/strength`
Évaluer la force d'un mot de passe.

**Request:**
```json
{
  "password": "TestPassword123!"
}
```

**Response (200):**
```json
{
  "strength": 4,
  "entropy": 104.9,
  "feedback": ["Évitez les séquences"],
  "has_lowercase": true,
  "has_uppercase": true,
  "has_digits": true,
  "has_special": true,
  "length": 16
}
```

#### `GET /passwords/categories`
Récupérer les catégories avec statistiques.

**Response (200):**
```json
{
  "categories": [
    {
      "category": "development",
      "count": 15
    },
    {
      "category": "social",
      "count": 8
    },
    {
      "category": "finance",
      "count": 3
    }
  ]
}
```

#### `GET /passwords/presets`
Récupérer les presets de génération.

**Response (200):**
```json
{
  "presets": {
    "weak": {
      "length": 8,
      "include_uppercase": true,
      "include_lowercase": true,
      "include_digits": true,
      "include_special": false
    },
    "strong": {
      "length": 16,
      "include_uppercase": true,
      "include_lowercase": true,
      "include_digits": true,
      "include_special": true,
      "exclude_ambiguous": true,
      "min_special": 2
    },
    "maximum": {
      "length": 24,
      "include_uppercase": true,
      "include_lowercase": true,
      "include_digits": true,
      "include_special": true,
      "exclude_ambiguous": true,
      "min_uppercase": 2,
      "min_lowercase": 2,
      "min_digits": 2,
      "min_special": 3
    }
  }
}
```

---

## 🚨 Codes d'Erreur

| Code | Signification | Description |
|------|---------------|-------------|
| 400 | Bad Request | Données invalides ou manquantes |
| 401 | Unauthorized | Token JWT manquant ou invalide |
| 403 | Forbidden | Accès refusé à la ressource |
| 404 | Not Found | Ressource non trouvée |
| 409 | Conflict | Ressource déjà existante |
| 500 | Internal Server Error | Erreur serveur |

**Format d'erreur standard:**
```json
{
  "error": "Description de l'erreur",
  "details": ["Détail 1", "Détail 2"]
}
```

---

## 🔒 Sécurité

### Chiffrement
- **Algorithme:** AES-256-GCM
- **Dérivation de clé:** PBKDF2 avec 100,000 itérations
- **Salt:** Généré aléatoirement pour chaque mot de passe
- **IV:** Unique pour chaque opération de chiffrement

### JWT Tokens
- **Algorithme:** HS256
- **Expiration:** 15 minutes (access), 7 jours (refresh)
- **Claims:** user_id, email, iat, exp, type

### Audit
Toutes les opérations sensibles sont enregistrées avec :
- Action effectuée
- User ID
- IP address
- User-Agent
- Timestamp
- Statut (succès/échec)

---

## 📝 Exemples d'Utilisation

### Script de test complet
```bash
#!/bin/bash

# Inscription
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!@#"}')

# Connexion
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!@#"}')

# Extraire le token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# Générer un mot de passe
curl -s -X POST http://localhost:8080/api/passwords/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Créer un mot de passe
curl -s -X POST http://localhost:8080/api/passwords \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "Example.com",
    "username": "mon_user",
    "password": "GeneratedPassword123!",
    "category": "work",
    "tags": ["important"]
  }'

# Lister les mots de passe
curl -s -X GET "http://localhost:8080/api/passwords?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Tests

L'API inclut des tests automatisés couvrant :
- ✅ Authentification (inscription, connexion, JWT)
- ✅ CRUD mots de passe
- ✅ Génération et évaluation
- ✅ Chiffrement/déchiffrement
- ✅ Validation des données
- ✅ Gestion d'erreurs

**Lancer les tests :**
```bash
cd backend
python -m pytest tests/ -v
# ou
python test_api_complete.py
```

---

## 📊 Performance

- **Base de données :** Index sur user_id, category, site_name, is_favorite
- **Pagination :** Max 100 éléments par requête
- **Chiffrement :** ~1-2ms par opération
- **JWT :** Validation ~0.1ms

---

## 🔗 Liens Utiles

- [Code source Backend](/backend)
- [Tests automatisés](/backend/tests)
- [Docker Compose](/docker-compose.yml)
- [Guide de déploiement](/docs/DEPLOYMENT-GUIDE.md)