#!/bin/bash

# Script de suivi des TODO pour le gestionnaire de mots de passe
# Usage: ./scripts/track-progress.sh

set -e

echo "📊 GESTIONNAIRE DE MOTS DE PASSE - SUIVI DES PROGRÈS"
echo "=================================================="
echo "Dernière mise à jour : $(date '+%d/%m/%Y à %H:%M')"
echo ""

# Fonction pour calculer le pourcentage
calculate_percentage() {
    local completed=$1
    local total=$2
    if [ $total -eq 0 ]; then
        echo "0"
    else
        echo $(( (completed * 100) / total ))
    fi
}

# Compter les TODO par statut dans les fichiers
count_backend_todos() {
    echo "🔧 BACKEND DEVELOPER"
    echo "==================="
    
    # Compter les tâches terminées (✅)
    completed=$(grep -c "✅" docs/BACKEND-TODO.md || echo "0")
    
    # Compter les tâches en cours (🔄)
    in_progress=$(grep -c "🔄" docs/BACKEND-TODO.md || echo "0")
    
    # Compter les tâches à faire (⏳ ou - \[ \])
    todo=$(grep -c "⏳\|^\- \[ \]" docs/BACKEND-TODO.md || echo "0")
    
    total=$((completed + in_progress + todo))
    percentage=$(calculate_percentage $completed $total)
    
    echo "✅ Terminées     : $completed tâches"
    echo "🔄 En cours      : $in_progress tâches"
    echo "⏳ À faire       : $todo tâches"
    echo "📊 TOTAL         : $total tâches"
    echo "📈 PROGRESSION   : $percentage%"
    
    # Afficher la tâche actuelle
    current_task=$(grep -A1 "🎯 Tâche actuelle" docs/BACKEND-TODO.md | tail -1 || echo "Aucune tâche définie")
    echo "🎯 Tâche actuelle: $current_task"
    echo ""
}

count_frontend_todos() {
    echo "🎨 FRONTEND DEVELOPER"
    echo "===================="
    
    # Compter les tâches terminées (✅)
    completed=$(grep -c "✅" docs/FRONTEND-TODO.md || echo "0")
    
    # Compter les tâches en cours (🔄)
    in_progress=$(grep -c "🔄" docs/FRONTEND-TODO.md || echo "0")
    
    # Compter les tâches à faire (⏳ ou - \[ \])
    todo=$(grep -c "⏳\|^\- \[ \]" docs/FRONTEND-TODO.md || echo "0")
    
    total=$((completed + in_progress + todo))
    percentage=$(calculate_percentage $completed $total)
    
    echo "✅ Terminées     : $completed tâches"
    echo "🔄 En cours      : $in_progress tâches"
    echo "⏳ À faire       : $todo tâches"
    echo "📊 TOTAL         : $total tâches"
    echo "📈 PROGRESSION   : $percentage%"
    
    # Afficher la tâche actuelle
    current_task=$(grep -A1 "🎯 Tâche actuelle" docs/FRONTEND-TODO.md | tail -1 || echo "Aucune tâche définie")
    echo "🎯 Tâche actuelle: $current_task"
    echo ""
}

show_global_progress() {
    echo "🌍 PROGRESSION GLOBALE"
    echo "====================="
    
    # Calculer les totaux
    backend_completed=$(grep -c "✅" docs/BACKEND-TODO.md || echo "0")
    backend_total=$(grep -c "✅\|🔄\|⏳\|^\- \[ \]" docs/BACKEND-TODO.md || echo "0")
    
    frontend_completed=$(grep -c "✅" docs/FRONTEND-TODO.md || echo "0")
    frontend_total=$(grep -c "✅\|🔄\|⏳\|^\- \[ \]" docs/FRONTEND-TODO.md || echo "0")
    
    total_completed=$((backend_completed + frontend_completed))
    total_tasks=$((backend_total + frontend_total))
    
    global_percentage=$(calculate_percentage $total_completed $total_tasks)
    
    echo "📊 Tâches terminées : $total_completed / $total_tasks"
    echo "📈 Progression      : $global_percentage%"
    echo ""
    
    # Barre de progression visuelle
    progress_bar=""
    filled=$((global_percentage / 5))
    for ((i=1; i<=20; i++)); do
        if [ $i -le $filled ]; then
            progress_bar+="█"
        else
            progress_bar+="░"
        fi
    done
    echo "[$progress_bar] $global_percentage%"
    echo ""
}

show_next_steps() {
    echo "🎯 PROCHAINES ÉTAPES"
    echo "==================="
    
    echo "Backend Developer:"
    # Trouver la première tâche ⏳ ou 🔄
    next_backend=$(grep -m1 "🔄\|⏳" docs/BACKEND-TODO.md | head -1 || echo "Toutes les tâches terminées!")
    echo "  → $next_backend"
    
    echo ""
    echo "Frontend Developer:"
    # Trouver la première tâche ⏳ ou 🔄
    next_frontend=$(grep -m1 "🔄\|⏳" docs/FRONTEND-TODO.md | head -1 || echo "Toutes les tâches terminées!")
    echo "  → $next_frontend"
    echo ""
}

check_blockers() {
    echo "🚧 BLOQUANTS DÉTECTÉS"
    echo "====================)"
    
    # Chercher les mentions de bloquants
    blockers_backend=$(grep -i "bloquant\|bloqué\|attendre" docs/BACKEND-TODO.md || echo "")
    blockers_frontend=$(grep -i "bloquant\|bloqué\|attendre" docs/FRONTEND-TODO.md || echo "")
    
    if [ -n "$blockers_backend" ] || [ -n "$blockers_frontend" ]; then
        echo "⚠️  Des bloquants ont été détectés:"
        if [ -n "$blockers_backend" ]; then
            echo "Backend: $blockers_backend"
        fi
        if [ -n "$blockers_frontend" ]; then
            echo "Frontend: $blockers_frontend"
        fi
    else
        echo "✅ Aucun bloquant détecté"
    fi
    echo ""
}

# Exécuter toutes les fonctions
count_backend_todos
count_frontend_todos
show_global_progress
show_next_steps
check_blockers

echo "📋 Pour plus de détails:"
echo "  → Backend : cat docs/BACKEND-TODO.md"
echo "  → Frontend: cat docs/FRONTEND-TODO.md"
echo "  → Global  : cat docs/TODO-TRACKER.md"
echo ""
echo "🔄 Relancer ce script : ./scripts/track-progress.sh"