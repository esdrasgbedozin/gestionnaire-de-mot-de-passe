#!/bin/bash

# Script de déploiement en production
# Usage: ./deploy-production.sh [start|stop|restart|status|logs|backup|restore]

set -e

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deployment.log"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Vérifications préalables
check_requirements() {
    log "🔍 Vérification des prérequis..."
    
    # Docker et Docker Compose
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    # Fichier de configuration
    if [ ! -f "$ENV_FILE" ]; then
        error "Fichier $ENV_FILE manquant. Copiez .env.production.example et configurez-le."
        exit 1
    fi
    
    # Vérifier les variables critiques
    source "$ENV_FILE"
    
    if [[ "$SECRET_KEY" == *"change-this"* ]] || [[ ${#SECRET_KEY} -lt 32 ]]; then
        error "SECRET_KEY doit être changée et faire au moins 32 caractères"
        exit 1
    fi
    
    if [[ "$JWT_SECRET_KEY" == *"change-this"* ]] || [[ ${#JWT_SECRET_KEY} -lt 32 ]]; then
        error "JWT_SECRET_KEY doit être changée et faire au moins 32 caractères"
        exit 1
    fi
    
    if [[ "$ENCRYPTION_KEY" == *"change"* ]] || [[ ${#ENCRYPTION_KEY} -ne 32 ]]; then
        error "ENCRYPTION_KEY doit être changée et faire exactement 32 caractères"
        exit 1
    fi
    
    log "✅ Prérequis vérifiés"
}

# Génération des clés de sécurité
generate_keys() {
    log "🔑 Génération des clés de sécurité..."
    
    echo "# Clés générées automatiquement - $(date)" > .env.generated
    echo "SECRET_KEY=$(openssl rand -base64 48)" >> .env.generated
    echo "JWT_SECRET_KEY=$(openssl rand -base64 48)" >> .env.generated
    echo "ENCRYPTION_KEY=$(openssl rand -base64 32 | cut -c1-32)" >> .env.generated
    echo "EMERGENCY_RESET_KEY=$(openssl rand -base64 32)" >> .env.generated
    
    log "✅ Clés générées dans .env.generated - Copiez-les dans $ENV_FILE"
}

# Démarrage
start() {
    log "🚀 Démarrage en production..."
    check_requirements
    
    # Créer les répertoires nécessaires
    mkdir -p logs backups ssl
    
    # Démarrer les services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    # Attendre le démarrage
    log "⏳ Attente du démarrage des services..."
    sleep 30
    
    # Vérification de santé
    check_health
    
    log "✅ Application démarrée en production!"
    log "🌐 Accès: https://your-domain.com"
}

# Arrêt
stop() {
    log "🛑 Arrêt de l'application..."
    docker-compose -f "$COMPOSE_FILE" down
    log "✅ Application arrêtée"
}

# Redémarrage
restart() {
    log "🔄 Redémarrage de l'application..."
    stop
    sleep 5
    start
}

# Statut
status() {
    log "📊 Statut des services..."
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log "🏥 Vérification de santé..."
    check_health
}

# Vérification de santé
check_health() {
    local backend_health
    local frontend_health
    local db_health
    
    # Backend
    if backend_health=$(curl -s -f http://localhost:8080/health 2>/dev/null); then
        log "✅ Backend: OK"
    else
        warning "❌ Backend: Non accessible"
        return 1
    fi
    
    # Base de données (via backend)
    if echo "$backend_health" | grep -q "database.*ok" 2>/dev/null; then
        log "✅ Base de données: OK"
    else
        warning "❌ Base de données: Problème détecté"
    fi
    
    # Frontend (check if nginx is serving)
    if curl -s -f http://localhost 2>/dev/null | grep -q "<!DOCTYPE html>" 2>/dev/null; then
        log "✅ Frontend: OK"
    else
        warning "❌ Frontend: Non accessible"
        return 1
    fi
}

# Logs
show_logs() {
    local service=${2:-""}
    
    if [ -n "$service" ]; then
        log "📋 Logs du service $service..."
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "$service"
    else
        log "📋 Logs de tous les services..."
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=50
    fi
}

# Sauvegarde
backup() {
    log "💾 Sauvegarde de la base de données..."
    
    local backup_file="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$BACKUP_DIR"
    
    docker-compose -f "$COMPOSE_FILE" exec -T database pg_dump -U prod_admin prod_password_manager > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Sauvegarde créée: $backup_file"
        
        # Compression
        gzip "$backup_file"
        log "✅ Sauvegarde compressée: $backup_file.gz"
        
        # Nettoyage (garder seulement les 10 dernières)
        ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +11 | xargs rm -f
        log "✅ Anciennes sauvegardes nettoyées"
    else
        error "❌ Échec de la sauvegarde"
        return 1
    fi
}

# Restauration
restore() {
    local backup_file="$2"
    
    if [ -z "$backup_file" ]; then
        error "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Fichier de sauvegarde non trouvé: $backup_file"
        exit 1
    fi
    
    warning "⚠️  ATTENTION: Cette opération va écraser la base de données actuelle!"
    read -p "Êtes-vous sûr? (oui/non): " confirm
    
    if [ "$confirm" != "oui" ]; then
        log "❌ Restauration annulée"
        exit 0
    fi
    
    log "🔄 Restauration de la base de données..."
    
    # Décompression si nécessaire
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | docker-compose -f "$COMPOSE_FILE" exec -T database psql -U prod_admin prod_password_manager
    else
        docker-compose -f "$COMPOSE_FILE" exec -T database psql -U prod_admin prod_password_manager < "$backup_file"
    fi
    
    if [ $? -eq 0 ]; then
        log "✅ Restauration terminée"
    else
        error "❌ Échec de la restauration"
        return 1
    fi
}

# Menu principal
case "$1" in
    "start")
        start
        ;;
    "stop")
        stop
        ;;
    "restart")
        restart
        ;;
    "status")
        status
        ;;
    "logs")
        show_logs "$@"
        ;;
    "backup")
        backup
        ;;
    "restore")
        restore "$@"
        ;;
    "generate-keys")
        generate_keys
        ;;
    "health")
        check_health
        ;;
    *)
        echo "🔐 Script de déploiement Production - Gestionnaire de Mots de Passe"
        echo "================================================================"
        echo ""
        echo "Usage: $0 [start|stop|restart|status|logs|backup|restore|generate-keys|health]"
        echo ""
        echo "Commandes disponibles:"
        echo "  start           - Démarrer l'application en production"
        echo "  stop            - Arrêter l'application"
        echo "  restart         - Redémarrer l'application"
        echo "  status          - Afficher le statut des services"
        echo "  logs [service]  - Afficher les logs (optionnel: service spécifique)"
        echo "  backup          - Sauvegarder la base de données"
        echo "  restore <file>  - Restaurer depuis une sauvegarde"
        echo "  generate-keys   - Générer des clés de sécurité"
        echo "  health          - Vérifier la santé de l'application"
        echo ""
        echo "Exemples:"
        echo "  $0 start                    # Démarrer l'application"
        echo "  $0 logs backend            # Voir les logs du backend"
        echo "  $0 backup                  # Sauvegarder la DB"
        echo "  $0 restore backup.sql.gz   # Restaurer la DB"
        ;;
esac