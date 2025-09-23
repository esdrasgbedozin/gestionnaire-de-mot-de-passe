#!/bin/bash

# 🚀 Script de démarrage unifié pour Password Manager
# Auteur: GitHub Copilot
# Usage: ./start.sh [--dev|--prod|--stop|--logs]

set -e

PROJECT_NAME="password_manager"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions d'affichage
print_header() {
    echo -e "${BLUE}"
    echo "🔐 PASSWORD MANAGER"
    echo "=================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    print_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé. Installez Docker Desktop."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé."
    fi
    
    # Vérifier que Docker est en cours d'exécution
    if ! docker info &> /dev/null; then
        print_error "Docker n'est pas en cours d'exécution. Démarrez Docker Desktop."
    fi
    
    print_success "Prérequis validés"
}

# Configurer l'environnement
setup_environment() {
    print_info "Configuration de l'environnement..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Fichier .env créé depuis .env.example"
        else
            print_warning "Aucun fichier .env trouvé"
        fi
    else
        print_info "Fichier .env existant trouvé"
    fi
}

# Démarrer l'application
start_app() {
    local mode=${1:-"prod"}
    
    print_header
    print_info "Démarrage de l'application en mode $mode..."
    
    check_prerequisites
    setup_environment
    
    # Arrêter les conteneurs existants
    print_info "Arrêt des conteneurs existants..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    if [ "$mode" = "dev" ]; then
        print_info "Mode développement - Build et démarrage..."
        docker-compose up --build -d
    else
        print_info "Mode production - Démarrage..."
        docker-compose up -d
    fi
    
    # Attendre que les services démarrent
    print_info "Attente du démarrage des services..."
    sleep 10
    
    # Vérifier la santé des services
    check_health
    
    print_success "Application démarrée avec succès!"
    show_urls
}

# Vérifier la santé des services
check_health() {
    print_info "Vérification de la santé des services..."
    
    # Vérifier le backend
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Backend: OK"
    else
        print_warning "Backend: En cours de démarrage..."
        sleep 5
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            print_success "Backend: OK (après attente)"
        else
            print_error "Backend: Échec de démarrage"
        fi
    fi
    
    # Vérifier la base de données
    if docker-compose exec -T db pg_isready -U password_manager > /dev/null 2>&1; then
        print_success "Base de données: OK"
    else
        print_warning "Base de données: Non disponible"
    fi
}

# Afficher les URLs
show_urls() {
    echo ""
    echo "🌐 Application accessible sur :"
    echo "   Backend API: http://localhost:8080"
    echo "   Frontend:    http://localhost:3000 (en développement)"
    echo ""
    echo "📊 Commandes utiles :"
    echo "   ./start.sh --logs     # Voir les logs"
    echo "   ./start.sh --stop     # Arrêter l'application"
    echo "   ./start.sh --dev      # Mode développement"
    echo ""
    echo "🧪 Test rapide :"
    echo "   curl http://localhost:8080/health"
    echo ""
}

# Arrêter l'application
stop_app() {
    print_header
    print_info "Arrêt de l'application..."
    
    docker-compose down --remove-orphans
    
    print_success "Application arrêtée"
}

# Afficher les logs
show_logs() {
    print_header
    print_info "Affichage des logs (Ctrl+C pour quitter)..."
    
    docker-compose logs -f
}

# Nettoyer complètement
clean_all() {
    print_header
    print_warning "Nettoyage complet (supprime les volumes)..."
    
    read -p "Êtes-vous sûr? Cela supprimera toutes les données. (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --volumes --remove-orphans
        docker system prune -f
        print_success "Nettoyage terminé"
    else
        print_info "Nettoyage annulé"
    fi
}

# Lancer les tests de sécurité
run_security_tests() {
    print_header
    print_info "Lancement des tests de sécurité..."
    
    if [ ! -f "backend/security_test.sh" ]; then
        print_error "Script de test de sécurité introuvable"
    fi
    
    cd backend
    chmod +x security_test.sh
    ./security_test.sh
    cd ..
}

# Menu principal
case "${1}" in
    --dev)
        start_app "dev"
        ;;
    --prod|"")
        start_app "prod"
        ;;
    --stop)
        stop_app
        ;;
    --logs)
        show_logs
        ;;
    --clean)
        clean_all
        ;;
    --security)
        run_security_tests
        ;;
    --help)
        print_header
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --dev        Démarrer en mode développement (avec rebuild)"
        echo "  --prod       Démarrer en mode production (défaut)"
        echo "  --stop       Arrêter l'application"
        echo "  --logs       Afficher les logs en temps réel"
        echo "  --clean      Nettoyage complet (supprime les volumes)"
        echo "  --security   Lancer les tests de sécurité"
        echo "  --help       Afficher cette aide"
        echo ""
        ;;
    *)
        print_error "Option inconnue: $1. Utilisez --help pour l'aide."
        ;;
esac