# 🛡️ Gestionnaire de mots de passe

## 🎯 Objectif
> Concevoir et déployer une application **sécurisée** de gestion de mots de passe, permettant à chaque utilisateur de stocker, consulter et gérer ses identifiants de manière confidentielle.

## 🛠️ Technologies retenues
- **Langage principal** : Python
- **Déploiement** : Docker 🐳 (3 services)
    - **Base de données** : PostgreSQL 🗄️
    - **Backend** : Flask (API REST sécurisée) 🔒
    - **Frontend** : À définir (React, Vue.js, ...) 🎨

## 🏗️ Architecture technique

### 🗄️ Base de données (PostgreSQL)

**Table Utilisateurs :**
| Champ                  | Description                        |
|------------------------|------------------------------------|
| 🆔 ID utilisateur      | Clé primaire                       |
| 📧 Email               | Unique                             |
| 🔑 Mot de passe        | Hashé et salé                      |
| 📅 Date de création    |                                    |

**Table Mots de passe :**
| Champ                  | Description                        |
|------------------------|------------------------------------|
| 🆔 ID mot de passe     | Clé primaire                       |
| 🌐 Site/Service        | Nom du site ou service associé     |
| 👤 Identifiant         | Email ou pseudo                    |
| 🗝️ Mot de passe        | Chiffré                            |
| 📅 Création            | Date de création                   |
| 🕒 Modification        | Date de dernière modification      |
| 🔗 Utilisateur         | Référence à l'utilisateur          |

### 🔗 Backend (Flask)
- API RESTful sécurisée (JWT ou OAuth2) 🛡️
- Logique métier : CRUD sur les mots de passe 📝
- Sécurité avancée : validation, prévention des failles 🚨
- Chiffrement/déchiffrement côté serveur 🔐

### 💻 Frontend
- Interface moderne & responsive 📱
- **Parcours utilisateur :**
    1. 🔏 Inscription & connexion sécurisées
    2. 📋 Tableau de bord des mots de passe
    3. ✏️ CRUD sur les mots de passe
    4. 👁️‍🗨️ Visualisation sécurisée (masqué/démasqué)
    5. 🚪 Déconnexion & gestion du compte

## 🛡️ Sécurité
- Hashage fort des mots de passe utilisateurs (bcrypt, Argon2) 🧂
- Chiffrement AES des mots de passe stockés 🔒
- Communication chiffrée (HTTPS, SSL/TLS) 🔗
- Séparation des rôles et accès 👥
- Journalisation des accès et opérations sensibles 📜

## 🛠️ Maintenance
- Documentation technique et utilisateur à jour 📚
- Procédures de sauvegarde régulières 💾
- Suivi des mises à jour de sécurité 🔔
- Support utilisateur et correction des bugs 🛠️
