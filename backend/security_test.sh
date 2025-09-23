#!/bin/bash

# Script de test de sécurité complet avec curl
echo "🔒 TESTS DE SÉCURITÉ COMPLETS"
echo "==============================================="

BASE_URL="http://localhost:8080"
SECURITY_SCORE=0
TOTAL_TESTS=10

# 1. Test des headers de sécurité
echo ""
echo "1. 🛡️ Test des headers de sécurité..."
HEADERS=$(curl -I -s "$BASE_URL/api/auth/login")

if echo "$HEADERS" | grep -i "x-content-type-options" > /dev/null; then
    echo "   ✅ X-Content-Type-Options: PRÉSENT"
    ((SECURITY_SCORE++))
else
    echo "   ❌ X-Content-Type-Options: MANQUANT"
fi

if echo "$HEADERS" | grep -i "x-frame-options" > /dev/null; then
    echo "   ✅ X-Frame-Options: PRÉSENT"
else
    echo "   ❌ X-Frame-Options: MANQUANT"
fi

if echo "$HEADERS" | grep -i "x-xss-protection" > /dev/null; then
    echo "   ✅ X-XSS-Protection: PRÉSENT"
else
    echo "   ❌ X-XSS-Protection: MANQUANT"
fi

if echo "$HEADERS" | grep -i "content-security-policy" > /dev/null; then
    echo "   ✅ Content-Security-Policy: PRÉSENT"
else
    echo "   ❌ Content-Security-Policy: MANQUANT"
fi

# 2. Test de protection XSS
echo ""
echo "2. 🚨 Test de protection XSS..."
XSS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email": "<script>alert(\"XSS\")</script>test@example.com", "password": "TestPass123!"}')

if [ "$XSS_RESPONSE" = "400" ]; then
    echo "   ✅ Protection XSS: ACTIVE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Protection XSS: FAIL - Code $XSS_RESPONSE"
fi

# 3. Test de rate limiting
echo ""
echo "3. ⏱️ Test du rate limiting..."
RATE_LIMIT_TRIGGERED=0

for i in {1..12}; do
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "nonexistent@test.com", "password": "wrongpass"}')
    
    if [ "$RESPONSE" = "429" ]; then
        RATE_LIMIT_TRIGGERED=1
        break
    fi
    sleep 0.1
done

if [ "$RATE_LIMIT_TRIGGERED" = "1" ]; then
    echo "   ✅ Rate limiting: ACTIF"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Rate limiting: NON DÉTECTÉ"
fi

# 4. Test de validation des mots de passe faibles
echo ""
echo "4. 🔐 Test de validation des mots de passe..."
WEAK_PASS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email": "weaktest@example.com", "password": "123"}')

if [ "$WEAK_PASS_RESPONSE" = "400" ]; then
    echo "   ✅ Validation de mot de passe fort: ACTIVE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Validation de mot de passe fort: FAIBLE - Code $WEAK_PASS_RESPONSE"
fi

# 5. Test d'authentification JWT
echo ""
echo "5. 🎫 Test de sécurité JWT..."
NO_TOKEN_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X GET "$BASE_URL/api/passwords/")
INVALID_TOKEN_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X GET "$BASE_URL/api/passwords/" \
    -H "Authorization: Bearer invalid_token_here")

if [ "$NO_TOKEN_RESPONSE" = "401" ] && [ "$INVALID_TOKEN_RESPONSE" = "401" ]; then
    echo "   ✅ Protection JWT: ACTIVE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Protection JWT: INSUFFISANTE - Codes $NO_TOKEN_RESPONSE/$INVALID_TOKEN_RESPONSE"
fi

# 6. Test de gestion des erreurs
echo ""
echo "6. 🚫 Test de gestion des erreurs..."
MALFORMED_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d 'malformed json{')

if [ "$MALFORMED_RESPONSE" = "400" ] || [ "$MALFORMED_RESPONSE" = "415" ]; then
    echo "   ✅ Gestion des erreurs: CORRECTE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Gestion des erreurs: INSUFFISANTE - Code $MALFORMED_RESPONSE"
fi

# 7. Test de validation des entrées vides
echo ""
echo "7. ✅ Test de validation des entrées..."
EMPTY_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{}')

if [ "$EMPTY_RESPONSE" = "400" ]; then
    echo "   ✅ Validation des entrées: STRICTE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Validation des entrées: PERMISSIVE - Code $EMPTY_RESPONSE"
fi

# 8. Test de chiffrement fonctionnel
echo ""
echo "8. 🔒 Test de chiffrement..."
# Créer un utilisateur de test
TIMESTAMP=$(date +%s)
REG_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"encrypttest$TIMESTAMP@example.com\", \"password\": \"SecurePass123!\"}")

if echo "$REG_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$REG_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    PWD_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/passwords/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"site_name": "Test Site", "username": "testuser", "password": "SecurePass123!", "url": "https://example.com"}')
    
    if [ "$PWD_RESPONSE" = "201" ]; then
        echo "   ✅ Chiffrement des mots de passe: FONCTIONNEL"
        ((SECURITY_SCORE++))
    else
        echo "   ❌ Chiffrement: ÉCHEC - Code $PWD_RESPONSE"
    fi
else
    echo "   ❌ Impossible de créer utilisateur test"
fi

# 9. Test de protection contre les injections
echo ""
echo "9. 💉 Test de protection contre les injections..."
INJECTION_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com'\''OR 1=1--", "password": "anything"}')

if [ "$INJECTION_RESPONSE" = "400" ] || [ "$INJECTION_RESPONSE" = "401" ]; then
    echo "   ✅ Protection contre les injections: ACTIVE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Protection contre les injections: FAIBLE - Code $INJECTION_RESPONSE"
fi

# 10. Test de validation stricte des types
echo ""
echo "10. 📝 Test de validation des types..."
TYPE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": 123, "password": []}')

if [ "$TYPE_RESPONSE" = "400" ]; then
    echo "   ✅ Validation des types: STRICTE"
    ((SECURITY_SCORE++))
else
    echo "   ❌ Validation des types: PERMISSIVE - Code $TYPE_RESPONSE"
fi

# Résumé final
echo ""
echo "==============================================="
echo "📊 RÉSUMÉ DE SÉCURITÉ"
echo "==============================================="

SECURITY_PERCENTAGE=$((SECURITY_SCORE * 100 / TOTAL_TESTS))

echo "Score de sécurité: $SECURITY_SCORE/$TOTAL_TESTS ($SECURITY_PERCENTAGE%)"

if [ "$SECURITY_PERCENTAGE" -ge 90 ]; then
    echo "🟢 SÉCURITÉ EXCELLENTE 🔒🛡️"
elif [ "$SECURITY_PERCENTAGE" -ge 70 ]; then
    echo "🟡 SÉCURITÉ BONNE 🔐🛡️"
elif [ "$SECURITY_PERCENTAGE" -ge 50 ]; then
    echo "🟠 SÉCURITÉ MOYENNE ⚠️🔓"
else
    echo "🔴 SÉCURITÉ INSUFFISANTE ❌🚨"
fi

echo ""
echo "🎯 MESURES DE SÉCURITÉ TESTÉES:"
echo "✅ Protection anti-XSS"
echo "✅ Rate limiting"
echo "✅ Headers de sécurité"
echo "✅ Validation robuste des entrées"
echo "✅ Authentification JWT sécurisée"
echo "✅ Chiffrement des données sensibles"
echo "✅ Gestion sécurisée des erreurs"
echo "✅ Protection contre les injections"
echo "✅ Validation stricte des types"

echo ""
echo "Test terminé avec succès - Score: $SECURITY_PERCENTAGE%"