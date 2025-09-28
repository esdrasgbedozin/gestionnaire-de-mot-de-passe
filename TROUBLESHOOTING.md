# 🆘 GUIDE DE DÉBOGAGE - "Internal Server Error" & "Error Loading Passwords"

## 🎯 **Problème Fréquent avec Docker**

Vous rencontrez des erreurs alors que l'application fonctionne chez le développeur ? **C'est normal !** Docker peut avoir des comportements différents selon l'environnement.

---

## 🔧 **SOLUTION RAPIDE (90% des cas)**

```bash
# 1. Nettoyage complet
./deploy.sh clean

# 2. Redémarrage propre  
./deploy.sh start

# 3. Vérification
./deploy.sh health
```

---

## 🕵️ **DIAGNOSTIC DÉTAILLÉ**

### **Étape 1: Vérifier les prérequis**
```bash
# Docker installé et fonctionnel ?
docker --version
docker-compose --version  # ou "docker compose version"

# Ports disponibles ?
netstat -tulpn | grep ':3000\|:8080\|:5432'
# Rien ne doit utiliser ces ports !
```

### **Étape 2: Environnement propre**
```bash
# Simuler un environnement complètement neuf
./tools/simulate_fresh_environment.sh
```

### **Étape 3: Analyse des logs**
```bash
# Voir toutes les erreurs
./deploy.sh logs

# Logs spécifiques par service
docker logs password_manager_backend
docker logs password_manager_frontend  
docker logs password_manager_db
```

---

## 🐛 **ERREURS COURANTES & SOLUTIONS**

### **1. "Internal Server Error" (500)**

**Causes possibles:**
- Base de données pas prête
- Problème de configuration
- Erreur de chiffrement
- Variables d'environnement manquantes

**Solutions:**
```bash
# Vérifier que la DB est healthy
docker ps | grep postgres

# Redémarrer le backend seulement
docker restart password_manager_backend

# Vérifier la configuration
ls -la .env*
```

### **2. "Error Loading Passwords"**

**Causes possibles:**
- API backend inaccessible
- Token JWT expiré
- Problème de CORS
- Rate limiting actif

**Solutions:**
```bash
# Tester l'API directement
curl http://localhost:8080/health

# Réinitialiser le rate limiting
./tools/rate_limit_helper.sh reset

# Vérifier les tokens
# → Déconnexion/reconnexion dans l'interface
```

### **3. Services qui ne démarrent pas**

**Causes possibles:**
- Ports déjà utilisés
- Permissions insuffisantes
- Images Docker corrompues

**Solutions:**
```bash
# Libérer les ports
sudo lsof -ti:3000,8080,5432 | xargs kill -9

# Reconstruire les images
./deploy.sh clean
docker system prune -a
./deploy.sh start
```

---

## 📋 **CHECKLIST DE DÉBOGAGE**

### **Niveau 1: Basique**
- [ ] Docker fonctionne: `docker ps`
- [ ] Ports libres: `netstat -tulpn | grep ':3000\|:8080'`
- [ ] Application démarrée: `./deploy.sh health`
- [ ] Services healthy: `docker ps` (voir colonne STATUS)

### **Niveau 2: Logs**  
- [ ] Pas d'erreurs backend: `docker logs password_manager_backend`
- [ ] Pas d'erreurs frontend: `docker logs password_manager_frontend`
- [ ] Database connectée: `docker logs password_manager_db`
- [ ] API répond: `curl http://localhost:8080/health`

### **Niveau 3: Fonctionnel**
- [ ] Interface accessible: http://localhost:3000
- [ ] Enregistrement fonctionne
- [ ] Connexion fonctionne  
- [ ] Chargement des mots de passe OK

---

## 🚀 **SCRIPT DE TESTS AUTOMATIQUE**

```bash
# Lancer tous les tests de validation
./tools/run_all_tests.sh

# Test spécifique de connexion
python3 tools/test_login.py

# Test fonctionnel complet
python3 tools/test_functional.py
```

---

## 🔄 **PROCÉDURE DE RESET COMPLET**

Si rien ne fonctionne, procédure de reset total :

```bash
# 1. Arrêt et nettoyage
./deploy.sh stop
docker system prune -a --volumes
docker volume prune

# 2. Suppression des fichiers temporaires  
rm -f .env .env.local
rm -rf backend/__pycache__
rm -rf frontend/node_modules/.cache

# 3. Redémarrage complet
./deploy.sh start

# 4. Attendre 2-3 minutes pour le build complet
./deploy.sh health
```

---

## 📞 **AIDE SUPPLÉMENTAIRE**

### **Variables d'environnement**
Copier `.env.example` vers `.env` si nécessaire:
```bash
cp .env.example .env
```

### **Problèmes de permissions (Linux/Mac)**
```bash  
sudo chown -R $USER:$USER .
chmod +x deploy.sh
```

### **Problèmes réseau**
Vérifier que Docker peut accéder au réseau:
```bash
docker run --rm busybox nslookup google.com
```

---

## 🎯 **CONTACT DÉVELOPPEUR**

Si le problème persiste après ces étapes:

1. **Exécuter**: `./tools/simulate_fresh_environment.sh`
2. **Capturer**: Les logs complets avec `./deploy.sh logs`  
3. **Partager**: Les résultats avec le développeur

**L'application est containerisée, elle DOIT fonctionner partout identiquement !**

---

## 📊 **Différences d'Environnement Possibles**

| Aspect | Développeur | Votre Machine |
|--------|-------------|---------------|
| Cache Docker | Images/volumes existants | Environnement vierge |
| Base de données | Données de test présentes | Base vide |
| Variables ENV | Configurées localement | Peut-être manquantes |
| Ports | Libres et configurés | Conflits possibles |
| Permissions | Paramétrées | Restrictions OS |

**💡 Le script `simulate_fresh_environment.sh` reproduit EXACTEMENT votre situation !**