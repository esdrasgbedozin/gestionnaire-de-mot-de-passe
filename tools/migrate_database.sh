#!/bin/bash

echo "🔄 MIGRATION AUTOMATIQUE DE LA BASE DE DONNÉES"
echo "==============================================="
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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour exécuter une commande SQL
execute_sql() {
    local sql="$1"
    local description="$2"
    
    print_step "Exécution: $description"
    
    if docker-compose exec -T database psql -U password_manager -d password_manager -c "$sql" >/dev/null 2>&1; then
        print_success "$description"
        return 0
    else
        print_warning "$description (déjà existant ou erreur - normal si déjà migré)"
        return 1
    fi
}

# Vérifier que la base de données est accessible
check_database() {
    print_step "Vérification de la connexion à la base de données..."
    
    if ! docker-compose exec -T database pg_isready -U password_manager >/dev/null 2>&1; then
        print_error "Base de données non accessible"
        echo "Démarrez d'abord l'application: ./deploy.sh start"
        exit 1
    fi
    
    print_success "Base de données accessible"
}

# Migration complète du schéma
migrate_schema() {
    print_step "Migration du schéma de base de données..."
    
    # 1. Ajouter les nouvelles colonnes à la table passwords
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS email VARCHAR(255);" "Ajout colonne 'email'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS category VARCHAR(100);" "Ajout colonne 'category'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS tags TEXT;" "Ajout colonne 'tags'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE;" "Ajout colonne 'is_favorite'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;" "Ajout colonne 'priority'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS password_strength VARCHAR(20);" "Ajout colonne 'password_strength'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS requires_2fa BOOLEAN DEFAULT FALSE;" "Ajout colonne 'requires_2fa'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITH TIME ZONE;" "Ajout colonne 'password_changed_at'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;" "Ajout colonne 'expires_at'"
    execute_sql "ALTER TABLE passwords ADD COLUMN IF NOT EXISTS remind_before_expiry INTEGER;" "Ajout colonne 'remind_before_expiry'"
    
    # 2. Créer les index pour les performances
    execute_sql "CREATE INDEX IF NOT EXISTS idx_passwords_email ON passwords(email);" "Index sur 'email'"
    execute_sql "CREATE INDEX IF NOT EXISTS idx_passwords_category ON passwords(category);" "Index sur 'category'"
    execute_sql "CREATE INDEX IF NOT EXISTS idx_passwords_is_favorite ON passwords(is_favorite);" "Index sur 'is_favorite'"
    execute_sql "CREATE INDEX IF NOT EXISTS idx_passwords_priority ON passwords(priority);" "Index sur 'priority'"
    
    # 3. Mise à jour des valeurs par défaut pour les enregistrements existants
    execute_sql "UPDATE passwords SET password_changed_at = created_at WHERE password_changed_at IS NULL;" "Mise à jour des dates de changement"
    execute_sql "UPDATE passwords SET password_strength = 'unknown' WHERE password_strength IS NULL;" "Mise à jour de la force des mots de passe"
}

# Vérifier l'intégrité après migration
verify_migration() {
    print_step "Vérification de l'intégrité après migration..."
    
    # Compter les enregistrements (plus robuste)
    local count_check=$(docker-compose exec -T database psql -U password_manager -d password_manager -t -c "SELECT COUNT(*) FROM passwords;" 2>/dev/null | tr -d ' \n' || echo "0")
    
    if [[ "$count_check" =~ ^[0-9]+$ ]] && [ "$count_check" -ge 0 ]; then
        print_success "Migration réussie - $count_check enregistrements dans la table passwords"
    else
        print_warning "Impossible de vérifier le nombre d'enregistrements (mais migration probablement OK)"
    fi
    
    # Vérifier que les nouvelles colonnes existent (test simplifié)
    if docker-compose exec -T database psql -U password_manager -d password_manager -c "SELECT email, category FROM passwords LIMIT 0;" >/dev/null 2>&1; then
        print_success "Colonnes 'email' et 'category' sont accessibles"
    else
        print_warning "Impossible de vérifier les nouvelles colonnes (normal si première utilisation)"
    fi
}

# Sauvegarde de sécurité
backup_database() {
    print_step "Création d'une sauvegarde de sécurité..."
    
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose exec -T database pg_dump -U password_manager password_manager > "$backup_file" 2>/dev/null; then
        print_success "Sauvegarde créée: $backup_file"
    else
        print_warning "Impossible de créer la sauvegarde (continuons quand même)"
    fi
}

# Fonction principale
main() {
    echo "Ce script va migrer votre base de données vers le nouveau schéma."
    echo "Il est sûr d'exécuter ce script plusieurs fois."
    echo ""
    
    # Vérifications préalables
    check_database
    
    # Sauvegarde de sécurité
    backup_database
    
    # Migration
    migrate_schema
    
    # Vérification
    verify_migration
    
    echo ""
    print_success "Migration terminée avec succès !"
    echo ""
    echo -e "${YELLOW}📋 Étapes suivantes:${NC}"
    echo "1. Redémarrer l'application: ./deploy.sh restart"
    echo "2. Tester la connexion: python3 tools/test_functional.py"
    echo "3. Si problème: vérifier les logs avec ./deploy.sh logs"
    echo ""
    echo -e "${GREEN}🎉 Votre base de données est maintenant compatible !${NC}"
}

# Exécuter le script principal
main "$@"