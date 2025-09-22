#!/bin/bash
# Test final complet du gestionnaire de mots de passe

echo "🚀 Test Final du Gestionnaire de Mots de Passe"
echo "=============================================="

# 1. Test de santé
echo
echo "🏥 Test de santé..."
HEALTH=$(curl -s http://localhost:8080/health)
echo "$HEALTH"

# 2. Inscription ou connexion
echo
echo "👤 Connexion..."
LOGIN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "validation@test.com", "password": "TestValidation123!"}')

# Extraire le token (simple grep/cut)
TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
    echo "✅ Connexion réussie, token obtenu"
    echo "Token: ${TOKEN:0:20}..."
else
    echo "❌ Problème de connexion"
    exit 1
fi

# 3. Création de mot de passe
echo
echo "💾 Création de mot de passe..."
CREATE=$(curl -s -X POST http://localhost:8080/api/passwords/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "site_name": "TestSite",
    "username": "testuser",
    "password": "TestP@ssw0rd123!",
    "category": "test",
    "tags": ["validation", "demo"],
    "is_favorite": true,
    "notes": "Test de validation complète"
  }')

echo "$CREATE"

# 4. Liste des mots de passe
echo
echo "📋 Liste des mots de passe..."
LIST=$(curl -s -X GET http://localhost:8080/api/passwords/ \
  -H "Authorization: Bearer $TOKEN")

echo "$LIST"

# 5. Génération de mot de passe
echo
echo "🎲 Génération de mot de passe..."
GENERATE=$(curl -s -X POST http://localhost:8080/api/passwords/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"length": 16}')

echo "$GENERATE"

echo
echo "🎉 Tests terminés !"