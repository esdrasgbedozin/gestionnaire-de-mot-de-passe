# 🔧 BACKEND DEVELOPER - TODO LIST

## 📊 Ma progression globale : 10% (2/21 tâches)

### 🎯 Tâche actuelle : BE-AUTH-02 (Routes d'authentification)
**Deadline** : Fin de semaine 1  
**Bloquants** : Aucun  
**Next** : BE-AUTH-03 (Service JWT)

---

# 🔥 PRIORITÉ HAUTE - À faire maintenant

## ✅ Tâches terminées

### BE-SETUP-01 : Configuration de base ✅
- [x] Structure des dossiers backend
- [x] Configuration Docker
- [x] Requirements.txt
- [x] Configuration Flask

### BE-SETUP-02 : Modèles de base ✅  
- [x] Modèle User
- [x] Modèle Password
- [x] Modèle AuditLog
- [x] Relations entre tables

---

## 🔄 EN COURS

### BE-AUTH-02 : Routes d'authentification 🔄 (50%)
**Fichier** : `backend/app/routes/auth.py`

**À implémenter :**
- [ ] Blueprint auth_bp
- [x] Route POST /api/auth/register
  - [x] Validation des données (email, password)
  - [x] Création utilisateur avec hash bcrypt
  - [ ] Génération token JWT
  - [ ] Retour JSON avec token
- [ ] Route POST /api/auth/login  
  - [ ] Validation credentials
  - [ ] Vérification mot de passe
  - [ ] Génération tokens (access + refresh)
  - [ ] Mise à jour last_login
- [ ] Route POST /api/auth/logout
  - [ ] Invalidation token (blacklist)
- [ ] Route POST /api/auth/refresh
  - [ ] Validation refresh token
  - [ ] Génération nouveau access token

**Code à ajouter :**
```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, db
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

# TODO: Implémenter les routes
```

---

## ⏳ TODO - Prochaines tâches

### BE-AUTH-03 : Service JWT (Priorité HIGH)
**Fichier à créer** : `backend/app/services/auth_service.py`

**Fonctions à implémenter :**
- [ ] `generate_tokens(user_id)` -> access + refresh tokens
- [ ] `validate_token(token)` -> user_id ou erreur
- [ ] `refresh_access_token(refresh_token)` -> nouveau access token
- [ ] `blacklist_token(token)` -> invalider token

### BE-AUTH-04 : Middleware d'authentification (Priorité HIGH)
**Fichier à créer** : `backend/app/middleware/auth_middleware.py`

**Fonctions à implémenter :**
- [ ] Décorateur `@auth_required`
- [ ] Validation automatique des tokens
- [ ] Extraction user_id du token
- [ ] Gestion des erreurs (expired, invalid, etc.)

### BE-AUTH-05 : Tests unitaires authentification (Priorité MEDIUM)
**Fichier à créer** : `backend/tests/test_auth.py`

**Tests à écrire :**
- [ ] Test registration valide
- [ ] Test registration email déjà existant
- [ ] Test login valide
- [ ] Test login credentials invalides
- [ ] Test refresh token
- [ ] Test logout

---

# 🔑 PROCHAINE FONCTIONNALITÉ : Gestion des mots de passe

## BE-PWD-01 : Service de chiffrement AES (Préparation)
**Fichier à créer** : `backend/app/services/encryption_service.py`

**Fonctions à prévoir :**
- [ ] `encrypt_password(plain_password, user_key)` -> encrypted
- [ ] `decrypt_password(encrypted_password, user_key)` -> plain
- [ ] `generate_user_key()` -> clé de chiffrement unique
- [ ] `derive_key_from_master(master_key, user_id)` -> clé dérivée

---

# 📝 NOTES DE DÉVELOPPEMENT

## 🔧 Configuration actuelle
- **Flask** : Configuré avec JWT, CORS, SQLAlchemy
- **Database** : PostgreSQL avec tables créées
- **Docker** : Service backend opérationnel
- **Tests** : pytest configuré

## ⚠️ Points d'attention
1. **Sécurité JWT** : Utiliser des clés fortes (64+ chars)
2. **Chiffrement** : Implémenter AES-256 pour les mots de passe
3. **Validation** : Toujours valider les inputs utilisateur
4. **Logs** : Ajouter des logs pour l'audit trail
5. **Tests** : Écrire les tests en parallèle du développement

## 🔗 Dépendances avec Frontend
- **BE-AUTH-02** → **FE-AUTH-03** : API login doit être prête
- **BE-AUTH-03** → **FE-AUTH-05** : Service JWT pour ProtectedRoute
- **BE-PWD-01** → **FE-PWD-01** : Service chiffrement pour API mots de passe

## 📞 Communication avec Frontend Dev
**À synchroniser :**
- Format des réponses JSON (structure des erreurs)
- Gestion des tokens JWT côté client
- Endpoints API et paramètres

---

**🎯 FOCUS CETTE SEMAINE** : Terminer l'authentification complète (BE-AUTH-02 à BE-AUTH-05)

**Deadline Sprint 1** : Fin semaine 2  
**Review** : Demo authentification avec Frontend Dev

**Dernière mise à jour** : 22 Septembre 2025