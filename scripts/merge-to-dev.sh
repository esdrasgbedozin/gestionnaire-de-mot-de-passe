#!/bin/bash

# Script pour merger une branche de fonctionnalité vers dev
# Usage: ./scripts/merge-to-dev.sh <nom-branche>

set -e

BRANCH_NAME=$1

if [ -z "$BRANCH_NAME" ]; then
    echo "❌ Usage: ./scripts/merge-to-dev.sh <nom-branche>"
    echo ""
    echo "Exemples:"
    echo "  ./scripts/merge-to-dev.sh feature/auth-backend"
    echo "  ./scripts/merge-to-dev.sh feature/auth-frontend"
    exit 1
fi

echo "🔄 MERGE VERS DEV"
echo "================"
echo "Branche : $BRANCH_NAME"
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

# Vérifier que la branche existe
if ! git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo "❌ La branche $BRANCH_NAME n'existe pas localement"
    exit 1
fi

# Vérifier qu'il n'y a pas de modifications non commitées
if ! git diff-index --quiet HEAD --; then
    echo "❌ Il y a des modifications non commitées. Commite d'abord tes changements."
    git status
    exit 1
fi

echo "📥 Récupération des dernières mises à jour..."
# Récupérer les dernières mises à jour de dev
git checkout dev
git pull origin dev

echo "🔄 Merge de $BRANCH_NAME vers dev..."
# Merger la branche de fonctionnalité
git merge $BRANCH_NAME --no-ff -m "feat: merge $BRANCH_NAME into dev

Integration of feature branch $BRANCH_NAME into development branch.
All tests should be passing and functionality should be complete."

echo "🚀 Push des changements vers origin/dev..."
# Pousser les changements
git push origin dev

echo ""
echo "✅ Merge réussi ! $BRANCH_NAME a été intégré dans dev"
echo ""
echo "📋 Prochaines étapes :"
echo "  1. Teste la fonctionnalité sur la branche dev"
echo "  2. Si tout est OK, supprime ta branche de fonctionnalité :"
echo "     git branch -d $BRANCH_NAME"
echo "     git push origin --delete $BRANCH_NAME"
echo "  3. Passe à la fonctionnalité suivante"
echo ""
echo "🎯 Si la fonctionnalité complète (front+back) est prête :"
echo "   → Créer une Pull Request dev → main sur GitHub"