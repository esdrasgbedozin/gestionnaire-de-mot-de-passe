#!/bin/bash

# Script pour créer une branche frontend pour une fonctionnalité
# Usage: ./scripts/create-frontend-branch.sh <nom-fonctionnalité>

set -e

FEATURE_NAME=$1

if [ -z "$FEATURE_NAME" ]; then
    echo "❌ Usage: ./scripts/create-frontend-branch.sh <nom-fonctionnalité>"
    echo ""
    echo "Exemples:"
    echo "  ./scripts/create-frontend-branch.sh auth"
    echo "  ./scripts/create-frontend-branch.sh passwords" 
    echo "  ./scripts/create-frontend-branch.sh profile"
    echo "  ./scripts/create-frontend-branch.sh security"
    exit 1
fi

echo "🎨 CRÉATION BRANCHE FRONTEND"
echo "==========================="
echo "Fonctionnalité : $FEATURE_NAME"
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

# Aller sur dev et récupérer les dernières mises à jour
echo "📥 Récupération des dernières mises à jour sur dev..."
git checkout dev
git pull origin dev

# Créer et basculer sur la nouvelle branche
BRANCH_NAME="feature/${FEATURE_NAME}-frontend"
echo "🌿 Création de la branche $BRANCH_NAME..."
git checkout -b $BRANCH_NAME

# Pousser la branche vers le remote
echo "🚀 Push de la branche vers origin..."
git push -u origin $BRANCH_NAME

echo ""
echo "✅ Branche $BRANCH_NAME créée et activée !"
echo ""
echo "📋 Prochaines étapes :"
echo "  1. Consulte docs/FRONTEND-TODO.md pour tes tâches"
echo "  2. Commence le développement"
echo "  3. Fais des commits réguliers :"
echo "     git commit -m 'feat($FEATURE_NAME): description'"
echo "  4. Pousse tes commits :"
echo "     git push origin $BRANCH_NAME"
echo ""
echo "📊 Pour suivre tes progrès : ./scripts/track-progress.sh"