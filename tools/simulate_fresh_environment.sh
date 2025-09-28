#!/bin/bash

echo "🧪 SIMULATION ENVIRONNEMENT PROPRE - REPRODUCTION DU PROBLÈME"
echo "============================================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Arrêter et nettoyer complètement
print_step "1. Nettoyage complet de l'environnement Docker"
echo "   Arrêt des services..."
./deploy.sh stop > /dev/null 2>&1

echo "   Suppression des containers..."
docker rm -f password_manager_backend password_manager_frontend password_manager_db > /dev/null 2>&1

echo "   Suppression des volumes (données perdues - comme un nouvel utilisateur)"
docker volume rm -f gestionnaire-de-mot-de-passe_postgres_data > /dev/null 2>&1
docker volume prune -f > /dev/null 2>&1

echo "   Suppression des images (force rebuild complet)"
docker rmi -f gestionnaire-de-mot-de-passe-backend gestionnaire-de-mot-de-passe-frontend > /dev/null 2>&1

echo "   Nettoyage du cache Docker"
docker system prune -f > /dev/null 2>&1

print_success "Environnement Docker complètement nettoyé"
echo ""

# 2. Supprimer les fichiers de configuration locaux
print_step "2. Suppression des fichiers de configuration locaux"
rm -f .env 2>/dev/null
rm -f .env.local 2>/dev/null
rm -f backend/.env 2>/dev/null
rm -f frontend/.env 2>/dev/null
print_success "Fichiers de configuration supprimés"
echo ""

# 3. Simuler les problèmes courants d'un nouvel environnement
print_step "3. Test de démarrage - SIMULATION NOUVEL UTILISATEUR"
echo ""

# Vérifier les prérequis comme un nouvel utilisateur
print_step "Vérification des prérequis..."
if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose n'est pas disponible"
    exit 1
fi

print_success "Docker et Docker Compose disponibles"
echo ""

# Démarrage avec monitoring des erreurs
print_step "4. Démarrage avec monitoring d'erreurs"
echo "   Tentative de démarrage..."

# Créer un fichier temporaire pour capturer les erreurs
ERROR_LOG="/tmp/fresh_start_errors.log"
touch $ERROR_LOG

# Démarrer en arrière-plan et capturer les erreurs
timeout 60 ./deploy.sh start > $ERROR_LOG 2>&1 &
DEPLOY_PID=$!

echo "   Attente du démarrage (60s max)..."
sleep 10

# Vérifier les services progressivement
for i in {1..12}; do
    echo "   Test $i/12 - Vérification des services..."
    
    # Test base de données
    if ! docker ps | grep -q "password_manager_db.*healthy"; then
        print_warning "Base de données pas encore prête..."
        sleep 5
        continue
    fi
    
    # Test backend
    if ! curl -s http://localhost:8080/health > /dev/null; then
        print_warning "Backend pas encore prêt..."
        sleep 5
        continue
    fi
    
    # Test frontend
    if ! curl -s http://localhost:3000 > /dev/null; then
        print_warning "Frontend pas encore prêt..."
        sleep 5
        continue
    fi
    
    # Si on arrive ici, tout semble OK
    print_success "Tous les services semblent démarrés !"
    break
done

# Attendre que le processus de démarrage se termine
wait $DEPLOY_PID
DEPLOY_EXIT_CODE=$?

echo ""
print_step "5. Analyse des résultats"

if [ $DEPLOY_EXIT_CODE -ne 0 ]; then
    print_error "Échec du démarrage (code: $DEPLOY_EXIT_CODE)"
    echo ""
    echo "📋 ERREURS CAPTURÉES:"
    echo "===================="
    cat $ERROR_LOG
    echo ""
fi

# Tests de fonctionnalité comme un nouvel utilisateur
print_step "6. Tests de fonctionnalité (perspective nouvel utilisateur)"

# Test 1: API Health
print_step "Test API Health..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    print_success "API répond correctement"
else
    print_error "API ne répond pas - PROBLÈME DÉTECTÉ"
fi

# Test 2: Frontend accessible
print_step "Test Frontend..."
if curl -s http://localhost:3000 | grep -q "Password Manager"; then
    print_success "Frontend accessible"
else
    print_error "Frontend inaccessible - PROBLÈME DÉTECTÉ"
fi

# Test 3: Tentative d'enregistrement (comme votre camarade)
print_step "Test enregistrement utilisateur (simulation camarade)..."
REGISTER_RESULT=$(curl -s -X POST http://localhost:8080/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test_fresh@example.com",
        "password": "TestPassword123!",
        "nom": "Test Fresh User"
    }' | head -100)

if echo "$REGISTER_RESULT" | grep -q '"message".*"success"'; then
    print_success "Enregistrement fonctionne"
else
    print_error "Enregistrement échoue - PROBLÈME DÉTECTÉ"
    echo "Réponse: $REGISTER_RESULT"
fi

# Test 4: Tentative de connexion
print_step "Test connexion (simulation camarade)..."
LOGIN_RESULT=$(curl -s -X POST http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test_fresh@example.com", 
        "password": "TestPassword123!"
    }' | head -100)

if echo "$LOGIN_RESULT" | grep -q '"access_token"'; then
    print_success "Connexion fonctionne"
else
    print_error "Connexion échoue - PROBLÈME DÉTECTÉ"  
    echo "Réponse: $LOGIN_RESULT"
fi

echo ""
print_step "7. État final des services"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
print_step "8. Logs d'erreurs récentes"
echo "=========================="
# Afficher les dernières erreurs de chaque service
echo "📋 Backend errors:"
docker logs password_manager_backend 2>&1 | grep -i "error\|exception\|traceback" | tail -5

echo ""
echo "📋 Frontend errors:"
docker logs password_manager_frontend 2>&1 | grep -i "error\|failed" | tail -5

echo ""
echo "📋 Database errors:"
docker logs password_manager_db 2>&1 | grep -i "error\|fatal" | tail -5

echo ""
print_step "RECOMMANDATIONS POUR VOTRE CAMARADE"
echo "===================================="
echo "1. Vérifier que Docker fonctionne: docker --version"
echo "2. Vérifier les ports libres: netstat -tulpn | grep ':3000\\|:8080\\|:5432'"
echo "3. Nettoyer l'environnement: ./deploy.sh clean"  
echo "4. Redémarrer proprement: ./deploy.sh start"
echo "5. Vérifier les logs: ./deploy.sh logs"
echo ""
echo "🔧 Commande de diagnostic complète:"
echo "   ./tools/run_all_tests.sh"

# Nettoyage
rm -f $ERROR_LOG 2>/dev/null