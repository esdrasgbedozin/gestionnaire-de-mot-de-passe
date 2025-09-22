#!/bin/bash

# Script d'installation et de démarrage du gestionnaire de mots de passe
# Usage: ./scripts/setup.sh

set -e

echo "🛡️  Configuration du Gestionnaire de Mots de Passe"
echo "=================================================="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

echo "✅ Docker et Docker Compose détectés"

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Modifiez le fichier .env avec vos propres valeurs sécurisées !"
    echo "   Surtout en production : JWT_SECRET_KEY et ENCRYPTION_KEY"
else
    echo "✅ Fichier .env trouvé"
fi

# Construire et démarrer les services
echo "🔨 Construction et démarrage des services Docker..."
docker-compose down --remove-orphans
docker-compose build
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente que les services soient prêts..."
sleep 10

# Vérifier l'état des services
echo "🔍 Vérification de l'état des services..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services démarrés avec succès !"
    echo ""
    echo "🌐 Accès à l'application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8080"
    echo "   Base de données: localhost:5432"
    echo ""
    echo "📚 Consultez docs/DEVELOPMENT.md pour plus d'informations"
else
    echo "❌ Erreur lors du démarrage des services"
    echo "📋 Logs des services:"
    docker-compose logs
    exit 1
fi