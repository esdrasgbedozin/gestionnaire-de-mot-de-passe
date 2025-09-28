#!/bin/bash

# Script d'aide pour le dépannage du rate limiting
# Usage: ./rate_limit_helper.sh [reset|status|test]

BACKEND_URL="http://localhost:8080"

case "$1" in
    "reset")
        echo "🔄 Réinitialisation du rate limiter..."
        response=$(curl -s -X POST "${BACKEND_URL}/api/admin/rate-limit-reset" \
            -H "Content-Type: application/json" \
            -d '{}')
        
        if echo "$response" | grep -q "success"; then
            echo "✅ Rate limiter réinitialisé avec succès"
        else
            echo "❌ Échec de la réinitialisation du rate limiter"
            echo "Réponse: $response"
        fi
        ;;
        
    "status")
        echo "📊 Vérification du statut du rate limiter..."
        response=$(curl -s "${BACKEND_URL}/api/admin/rate-limit-stats")
        
        if [ $? -eq 0 ]; then
            echo "✅ Statistiques du rate limiter:"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
        else
            echo "❌ Impossible de récupérer les statistiques"
        fi
        ;;
        
    "test")
        echo "🧪 Test de connexion (5 tentatives)..."
        for i in {1..5}; do
            echo "Tentative $i:"
            response=$(curl -s -X POST "${BACKEND_URL}/api/auth/login" \
                -H "Content-Type: application/json" \
                -d '{"email":"test@example.com","password":"wrong"}')
            
            if echo "$response" | grep -q "rate limit"; then
                echo "⚠️  Rate limit atteint"
                break
            elif echo "$response" | grep -q "Invalid credentials"; then
                echo "✅ Connexion tentée (identifiants incorrects - normal)"
            else
                echo "📝 Réponse: $response"
            fi
            
            sleep 1
        done
        ;;
        
    *)
        echo "🔧 Script d'aide pour le rate limiting"
        echo ""
        echo "Usage: $0 [reset|status|test]"
        echo ""
        echo "Commandes disponibles:"
        echo "  reset  - Réinitialiser le rate limiter"
        echo "  status - Afficher les statistiques du rate limiter"
        echo "  test   - Tester le rate limiting avec 5 tentatives de connexion"
        echo ""
        echo "Exemples:"
        echo "  $0 reset   # Pour débloquer si vous obtenez 'rate limit exceeded'"
        echo "  $0 test    # Pour vérifier si le rate limiting fonctionne"
        ;;
esac