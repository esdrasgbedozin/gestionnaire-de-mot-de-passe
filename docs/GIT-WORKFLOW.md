# 🌿 GIT WORKFLOW - Gestionnaire de Mots de Passe

## 🏗️ Stratégie de Branches

### 📋 Structure des branches
```
main (production)
 └── dev (développement)
     ├── feature/auth-backend (Backend Developer)
     ├── feature/auth-frontend (Frontend Developer)
     ├── feature/passwords-backend (Backend Developer)
     ├── feature/passwords-frontend (Frontend Developer)
     └── ... (autres fonctionnalités)
```

### 🎯 Rôle de chaque branche

- **`main`** : Code de production stable ✅
- **`dev`** : Intégration des fonctionnalités 🔄
- **`feature/xxx-backend`** : Développement Backend d'une fonctionnalité 🔧
- **`feature/xxx-frontend`** : Développement Frontend d'une fonctionnalité 🎨

---

## 🔄 Workflow par Fonctionnalité

### 1. 🚀 Démarrer une nouvelle fonctionnalité

**Backend Developer :**
```bash
# Partir de dev à jour
git checkout dev
git pull origin dev

# Créer sa branche fonctionnalité
git checkout -b feature/auth-backend
```

**Frontend Developer :**
```bash
# Partir de dev à jour  
git checkout dev
git pull origin dev

# Créer sa branche fonctionnalité
git checkout -b feature/auth-frontend
```

### 2. 💻 Développement

**Commits réguliers :**
```bash
# Faire ses développements
git add .
git commit -m "feat(auth): add login route with JWT validation"

# Pousser régulièrement sa branche
git push origin feature/auth-backend  # ou feature/auth-frontend
```

### 3. 🔄 Synchronisation pendant le développement

**Si besoin du code de l'autre développeur :**
```bash
# Récupérer les dernières mises à jour de dev
git checkout dev
git pull origin dev

# Revenir sur sa branche et merger les changements
git checkout feature/auth-backend
git merge dev
```

### 4. ✅ Fin de fonctionnalité - Merge vers dev

**Quand la partie Backend/Frontend est terminée :**
```bash
# Vérifier que dev est à jour
git checkout dev  
git pull origin dev

# Merger sa branche
git merge feature/auth-backend  # ou feature/auth-frontend
git push origin dev

# Supprimer sa branche de fonctionnalité (optionnel)
git branch -d feature/auth-backend
```

### 5. 🎉 Intégration complète - PR vers main

**Quand la fonctionnalité est complète (Backend + Frontend) :**
```bash
# Depuis dev, créer une PR vers main
# Ou via l'interface GitHub
git checkout dev
git push origin dev
# → Créer Pull Request dev → main
```

---

## 📋 Branches par Fonctionnalité

### 🔐 FONCTIONNALITÉ 1 : Authentification

**Backend Developer :**
```bash
git checkout -b feature/auth-backend
# Travaille sur : BE-AUTH-01 à BE-AUTH-05
```

**Frontend Developer :**
```bash
git checkout -b feature/auth-frontend  
# Travaille sur : FE-AUTH-01 à FE-AUTH-06
```

### 🔑 FONCTIONNALITÉ 2 : Gestion des mots de passe

**Backend Developer :**
```bash
git checkout -b feature/passwords-backend
# Travaille sur : BE-PWD-01 à BE-PWD-07
```

**Frontend Developer :**
```bash
git checkout -b feature/passwords-frontend
# Travaille sur : FE-PWD-01 à FE-PWD-08
```

### 👤 FONCTIONNALITÉ 3 : Gestion profil

**Backend Developer :**
```bash
git checkout -b feature/profile-backend
# Travaille sur : BE-PROF-01 à BE-PROF-04
```

**Frontend Developer :**
```bash
git checkout -b feature/profile-frontend
# Travaille sur : FE-PROF-01 à FE-PROF-05
```

### 🛡️ FONCTIONNALITÉ 4 : Sécurité avancée

**Backend Developer :**
```bash
git checkout -b feature/security-backend
# Travaille sur : BE-SEC-01 à BE-SEC-05
```

**Frontend Developer :**
```bash
git checkout -b feature/security-frontend
# Travaille sur : FE-SEC-01 à FE-SEC-04
```

---

## 💡 Bonnes Pratiques Git

### ✅ Conventions de commits
```bash
# Types de commits
feat(scope): nouvelle fonctionnalité
fix(scope): correction de bug
docs(scope): documentation
style(scope): formatage, pas de changement de logique
refactor(scope): refactoring sans nouveau feature
test(scope): ajout de tests
chore(scope): maintenance

# Exemples
git commit -m "feat(auth): add JWT token generation service"
git commit -m "fix(login): handle invalid credentials error"
git commit -m "docs(api): update authentication endpoints documentation"
```

### 🔄 Messages de commits détaillés
```bash
git commit -m "feat(auth): implement login route with JWT

- Add POST /api/auth/login endpoint
- Validate email and password format
- Generate JWT access and refresh tokens
- Handle invalid credentials with proper error messages
- Add unit tests for login functionality

Resolves: BE-AUTH-02"
```

### 🚫 Ce qu'il faut éviter
- Commits trop gros (> 10 fichiers modifiés)
- Messages vagues ("fix", "update", "changes")
- Merge direct sur main sans passer par dev
- Oublier de pousser sa branche régulièrement
- Travailler sur la même branche à deux

---

## 🛠️ Scripts Git Utiles

### Créer automatiquement la branche de fonctionnalité

**Script pour Backend Developer :**
```bash
#!/bin/bash
# scripts/create-backend-branch.sh
FEATURE_NAME=$1
if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: ./scripts/create-backend-branch.sh <feature-name>"
    exit 1
fi

git checkout dev
git pull origin dev
git checkout -b feature/${FEATURE_NAME}-backend
echo "✅ Branche feature/${FEATURE_NAME}-backend créée et activée"
```

**Script pour Frontend Developer :**
```bash
#!/bin/bash  
# scripts/create-frontend-branch.sh
FEATURE_NAME=$1
if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: ./scripts/create-frontend-branch.sh <feature-name>"
    exit 1
fi

git checkout dev
git pull origin dev  
git checkout -b feature/${FEATURE_NAME}-frontend
echo "✅ Branche feature/${FEATURE_NAME}-frontend créée et activée"
```

---

## 🎯 Cycle de Développement Complet

### 📅 Semaine Type
```
Lundi : 
├── Créer branches feature/auth-backend et feature/auth-frontend
├── Daily standup : plan de la semaine
└── Développement en parallèle

Mardi-Jeudi :
├── Développement continu sur les branches
├── Commits réguliers
├── Daily standup quotidien
└── Push des branches

Vendredi :
├── Finalisation des développements
├── Merge vers dev (backend puis frontend)
├── Tests d'intégration sur dev
├── Demo de la fonctionnalité
└── PR dev → main si OK
```

### 🎉 Fin de Sprint
```
1. Valider que la fonctionnalité est complète sur dev
2. Tests d'intégration front + back
3. Demo client/équipe  
4. Pull Request dev → main
5. Review de code
6. Merge sur main
7. Tag de version (v1.1.0, v1.2.0, etc.)
8. Déploiement en production
```

---

## 🚀 Démarrage - Fonctionnalité Authentification

### Commands pour commencer MAINTENANT :

**Backend Developer :**
```bash
# Tu es déjà sur dev, crée ta branche
git checkout -b feature/auth-backend
git push -u origin feature/auth-backend

# Commence tes développements selon BACKEND-TODO.md
# Focus sur BE-AUTH-02 : Routes d'authentification
```

**Frontend Developer :**  
```bash
# Crée ta branche depuis dev
git checkout dev  # si pas déjà dessus
git checkout -b feature/auth-frontend
git push -u origin feature/auth-frontend

# Commence tes développements selon FRONTEND-TODO.md  
# Focus sur FE-AUTH-03 : Composant Login
```

---

**🎯 Objectif Semaine 1 :** Merger les deux branches `feature/auth-*` vers `dev` avec l'authentification complète !

**Dernière mise à jour :** 22 Septembre 2025