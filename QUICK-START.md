# 🚀 GUIDE DE DÉMARRAGE - POUR VOTRE CAMARADE

## ⚡ **DÉMARRAGE EN 3 ÉTAPES**

```bash
# 1. Cloner le projet
git clone https://github.com/esdrasgbedozin/gestionnaire-de-mot-de-passe
cd gestionnaire-de-mot-de-passe

# 2. Démarrer (patience : 1ère fois = 2-3 minutes)
./deploy.sh start

# 3. Accéder
# Frontend: http://localhost:3000
# API: http://localhost:8080
```

---

## ⏰ **PREMIER DÉMARRAGE = PLUS LONG**

**Normal !** Le premier démarrage prend 2-3 minutes car Docker doit :
- ✅ Télécharger les images de base (Node.js, Python, PostgreSQL)
- ✅ Construire les containers backend et frontend  
- ✅ Installer toutes les dépendances
- ✅ Initialiser la base de données

**Les démarrages suivants** : 10-15 secondes seulement ! 🚀

---

## 🔧 **SI ÇA NE MARCHE PAS**

### **1. Vérifier Docker**
```bash
docker --version        # Doit afficher une version
docker ps               # Doit fonctionner sans erreur
```

### **2. Libérer les ports**
```bash
# Vérifier que les ports sont libres
netstat -tulpn | grep ':3000\|:8080\|:5432'
# Si quelque chose utilise ces ports → tuer le processus
```

### **3. Reset complet**
```bash
./deploy.sh clean       # Nettoyage
./deploy.sh start       # Redémarrage propre
```

### **4. Diagnostic complet**
```bash
./tools/run_all_tests.sh    # Tests automatiques
./TROUBLESHOOTING.md        # Guide détaillé
```

---

## 📱 **UTILISATION**

### **Première utilisation :**
1. 🌐 Aller sur http://localhost:3000
2. 📝 Cliquer "S'inscrire" 
3. ✅ Créer un compte (email + mot de passe fort)
4. 🔐 Se connecter
5. ➕ Ajouter des mots de passe

### **Commandes utiles :**
```bash
./deploy.sh start       # Démarrer
./deploy.sh stop        # Arrêter  
./deploy.sh restart     # Redémarrer
./deploy.sh health      # Vérifier l'état
./deploy.sh logs        # Voir les erreurs
```

---

## 🆘 **PROBLÈMES FRÉQUENTS**

| Erreur | Cause | Solution |
|--------|-------|----------|
| "Internal Server Error" | Backend pas prêt | Attendre 30s de plus |
| "Error loading passwords" | API inaccessible | `./deploy.sh restart` |
| "Port already in use" | Conflit de port | Fermer autres apps |
| "Rate limit exceeded" | Trop de tentatives | `./tools/rate_limit_helper.sh reset` |
| Services lents | Premier démarrage | Patience (2-3 min) |

---

## 💡 **CONSEILS**

### **Performance :**
- **1er démarrage** : Patience, c'est normal !
- **Démarrages suivants** : Très rapides
- **Si lent** : Redémarrer Docker

### **Sécurité :**
- Utiliser un **mot de passe fort** pour le compte
- L'app chiffre tout avec **AES-256**
- Rate limiting contre les attaques

### **Support :**
- **Logs détaillés** : `./deploy.sh logs`
- **Tests automatiques** : `./tools/run_all_tests.sh`
- **Documentation** : `TROUBLESHOOTING.md`

---

## 🎯 **CHECKLIST DE VALIDATION**

Après démarrage, vérifier :
- [ ] ✅ http://localhost:3000 → Interface visible
- [ ] ✅ http://localhost:8080/health → API répond  
- [ ] ✅ Inscription fonctionne
- [ ] ✅ Connexion fonctionne
- [ ] ✅ Ajout mot de passe OK

**Si tous les ✅ → Parfait ! Sinon → TROUBLESHOOTING.md**

---

## 🔄 **EN CAS DE BLOCAGE TOTAL**

```bash
# Reset ultracomplet (dernier recours)
docker system prune -a --volumes
rm -f .env .env.local
./deploy.sh start
# Attendre 3-5 minutes
```

---

**🎉 L'application DOIT fonctionner - elle est containerisée !**  
**💪 Si problème persist → c'est un problème d'environnement, pas de l'app**