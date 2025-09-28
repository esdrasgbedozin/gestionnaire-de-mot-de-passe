#!/bin/bash

# Script d'aide au déploiement et débogage
# Gestionnaire de mots de passe

set -e

echo "🔐 Gestionnaire de mots de passe - Script d'aide au déploiement"
echo "================================================================"

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start      - Démarrer l'application (build + up)"
    echo "  stop       - Arrêter l'application"
    echo "  restart    - Redémarrer l'application"
    echo "  logs       - Voir les logs"
    echo "  migrate    - Appliquer les migrations de base de données"
    echo "  clean      - Nettoyer les containers et volumes"
    echo "  debug      - Mode debug avec logs détaillés"
    echo "  health     - Vérifier la santé des services"
    echo "  help       - Afficher cette aide"
    echo ""
}

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker n'est pas installé ou non accessible"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose n'est pas installé ou non accessible"
        exit 1
    fi
    
    echo "✅ Docker et Docker Compose sont disponibles"
}

# Démarrer l'application
start_app() {
    echo "🚀 Démarrage de l'application..."
    
    # Arrêter les containers existants
    docker-compose down || true
    
    # Construire et démarrer
    docker-compose up --build -d
    
    echo "⏳ Attente du démarrage des services..."
    sleep 10
    
    echo "🔍 Vérification de la santé des services..."
    check_health
    
    echo "✅ Application démarrée!"
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend: http://localhost:8080"
}

# Arrêter l'application
stop_app() {
    echo "🛑 Arrêt de l'application..."
    docker-compose down
    echo "✅ Application arrêtée"
}

# Redémarrer l'application
restart_app() {
    echo "🔄 Redémarrage de l'application..."
    stop_app
    start_app
}

# Voir les logs
show_logs() {
    echo "📋 Logs des services..."
    docker-compose logs -f --tail=100
}

# Appliquer les migrations
migrate_db() {
    echo "🔧 Application des migrations de base de données..."
    
    # Attendre que la base soit prête
    echo "⏳ Attente de la disponibilité de la base de données..."
    sleep 5
    
    # Exécuter le script de migration
    if [ -f "./scripts/migrate_db.sh" ]; then
        ./scripts/migrate_db.sh
    else
        echo "❌ Script de migration non trouvé"
        return 1
    fi
    
    echo "✅ Migrations appliquées"
}

# Nettoyer
clean_all() {
    echo "🧹 Nettoyage des containers et volumes..."
    
    read -p "⚠️ Cela supprimera tous les données. Continuer? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo "✅ Nettoyage terminé"
    else
        echo "❌ Nettoyage annulé"
    fi
}

# Mode debug
debug_mode() {
    echo "🐛 Mode debug - Logs détaillés..."
    
    # Arrêter et redémarrer avec logs
    docker-compose down || true
    docker-compose up --build
}

# Vérifier la santé des services
check_health() {
    echo "🏥 Vérification de la santé des services..."
    
    # Vérifier la base de données
    echo "🗄️ Base de données..."
    if docker-compose exec -T database pg_isready -U admin -d password_manager &> /dev/null; then
        echo "  ✅ Base de données: OK"
    else
        echo "  ❌ Base de données: ERREUR"
    fi
    
    # Vérifier le backend
    echo "🔧 Backend..."
    if curl -s -f http://localhost:8080/health &> /dev/null; then
        echo "  ✅ Backend: OK"
    else
        echo "  ❌ Backend: ERREUR"
    fi
    
    # Vérifier le frontend
    echo "📱 Frontend..."
    if curl -s -f http://localhost:3000 &> /dev/null; then
        echo "  ✅ Frontend: OK"
    else
        echo "  ❌ Frontend: ERREUR"
    fi
    
    # Informations sur les containers
    echo ""
    echo "📊 État des containers:"
    docker-compose ps
}

# Fonction principale
main() {
    check_docker
    
    case "${1:-}" in
        "start")
            start_app
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            restart_app
            ;;
        "logs")
            show_logs
            ;;
        "migrate")
            migrate_db
            ;;
        "clean")
            clean_all
            ;;
        "debug")
            debug_mode
            ;;
        "health")
            check_health
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            echo "❌ Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter la fonction principale
main "$@"