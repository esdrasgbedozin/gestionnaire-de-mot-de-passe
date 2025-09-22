# 📝 TEMPLATE - Mise à jour quotidienne

Copie ce template et remplis-le chaque jour pour tenir à jour tes TODO.

## 📅 Date : ___________

### 🎯 Développeur : Backend / Frontend _(rayer la mention inutile)_

---

## ✅ Tâches terminées aujourd'hui
- [ ] Tâche 1 : _Description et temps passé_
- [ ] Tâche 2 : _Description et temps passé_
- [ ] Tâche 3 : _Description et temps passé_

## 🔄 Tâches en cours
- [ ] Tâche en cours : _Avancement % et prochaine étape_
- [ ] Problème rencontré : _Description du problème_

## 🚧 Bloquants identifiés
- [ ] Bloquant 1 : _Description et impact_
- [ ] Dépendance : _Attente de quelle tâche/personne_

## 📋 Plan pour demain
- [ ] Priorité 1 : _Tâche à commencer/continuer_
- [ ] Priorité 2 : _Tâche suivante_
- [ ] Objectif : _Ce que je veux accomplir_

## 💬 Points à discuter en équipe
- [ ] Question technique : _Besoin d'aide ou de clarification_
- [ ] Synchronisation : _Points à aligner avec l'autre dev_

---

## 📊 Comment mettre à jour tes TODO

### 1. Marquer les tâches terminées
Dans ton fichier TODO (BACKEND-TODO.md ou FRONTEND-TODO.md) :
- Remplace `⏳` par `✅` pour les tâches terminées
- Remplace `🔄` par `✅` si la tâche en cours est finie
- Ajoute `🔄 (XX%)` pour indiquer l'avancement d'une tâche

### 2. Mettre à jour ta progression
- Change le pourcentage global en haut de ton fichier
- Mets à jour ta "Tâche actuelle"
- Ajoute les nouveaux bloquants

### 3. Vérifier le tracking
Exécute le script de suivi pour voir tes progrès :
```bash
./scripts/track-progress.sh
```

### 4. Format des tâches
- `✅ Tâche terminée` : Tâche complètement finie
- `🔄 Tâche en cours (XX%)` : Tâche partiellement terminée
- `⏳ TODO` : Tâche pas encore commencée
- `🚧 BLOQUÉ` : Tâche bloquée par dépendance

---

## 🎯 Exemples d'updates

### Exemple Backend :
```
### BE-AUTH-02 : Routes d'authentification 🔄 (75%)
- [x] Route POST /register terminée
- [x] Route POST /login terminée
- [ ] Route POST /logout (en cours)
- [ ] Tests unitaires
```

### Exemple Frontend :
```
### FE-AUTH-03 : Composant Login ✅ TERMINÉ
- [x] Formulaire avec validation
- [x] Intégration API
- [x] Gestion des erreurs
- [x] Tests manuels OK
```

### Exemple bloquant :
```
**Bloquants** : 🚧 Attente BE-AUTH-02 pour tester l'intégration
**Next** : FE-AUTH-04 dès que BE-AUTH-02 est prêt
```

---

## ⏰ Routine quotidienne recommandée

### 🌅 Le matin (5 min)
1. Lire ses TODO du jour précédent
2. Planifier les 2-3 tâches du jour
3. Vérifier s'il y a des bloquants

### 🌆 Le soir (10 min)
1. Mettre à jour ses TODO avec les tâches terminées
2. Noter les problèmes rencontrés
3. Planifier le lendemain
4. Exécuter `./scripts/track-progress.sh` pour voir ses progrès

### 💬 Communication équipe
- **Daily standup** : Partager avancement et bloquants
- **Fin de journée** : Message sur le statut si des bloquants
- **Fin de sprint** : Demo des fonctionnalités terminées

---

**Bon développement ! 🚀**