#!/usr/bin/env python3
"""
Test de connexion pour vérifier le problème de rate limiting résolu
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

def test_registration():
    """Test d'enregistrement d'un utilisateur"""
    print("🧪 Test d'enregistrement...")
    
    data = {
        "email": f"test{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "nom": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        if response.status_code == 201:
            print("✅ Enregistrement: SUCCÈS")
            return data
        else:
            print(f"❌ Enregistrement échoué: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement: {e}")
        return None

def test_first_login(user_data):
    """Test de première connexion - le problème original"""
    print("\n🎯 Test de PREMIÈRE connexion (problème original)...")
    
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ PREMIÈRE connexion: SUCCÈS - Problème résolu !")
            return response.json()
        else:
            print(f"❌ PREMIÈRE connexion échouée: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de la première connexion: {e}")
        return None

def test_rate_limiting():
    """Test du rate limiting - doit être plus permissif en développement"""
    print("\n🚦 Test du rate limiting (doit être permissif en dev)...")
    
    # Données de test
    login_data = {
        "email": "inexistant@example.com",
        "password": "wrongpassword"
    }
    
    attempts = 0
    max_attempts = 15  # En dev, on doit pouvoir faire plus de tentatives
    
    for i in range(max_attempts):
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
            attempts += 1
            
            if response.status_code == 429:  # Rate limited
                print(f"🚫 Rate limiting activé après {attempts} tentatives")
                if attempts >= 10:  # En dev, on accepte 10+ tentatives
                    print("✅ Rate limiting: Configuration DÉVELOPPEMENT OK")
                else:
                    print("⚠️ Rate limiting trop strict pour le développement")
                break
            elif response.status_code == 401:  # Unauthorized (attendu)
                print(f"📝 Tentative {attempts}: Échec d'authentification (normal)")
                time.sleep(0.1)  # Petite pause
            else:
                print(f"🤔 Réponse inattendue: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur lors du test {attempts}: {e}")
            break
    
    if attempts >= max_attempts:
        print("✅ Rate limiting: Très permissif en développement (15+ tentatives)")

def test_health_endpoints():
    """Test des endpoints de santé"""
    print("\n🏥 Test des endpoints de santé...")
    
    endpoints = [
        "/health",
        "/api/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: OK - {data.get('status', 'unknown')}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Erreur - {e}")

def test_cors():
    """Test de la configuration CORS"""
    print("\n🌐 Test de la configuration CORS...")
    
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options(f"{BASE_URL}/api/auth/login", headers=headers)
        if response.status_code in [200, 204]:
            print("✅ CORS: Configuration OK")
        else:
            print(f"⚠️ CORS: {response.status_code}")
    except Exception as e:
        print(f"❌ CORS: Erreur - {e}")

def main():
    print("🔐 TEST COMPLET DU GESTIONNAIRE DE MOTS DE PASSE")
    print("=" * 55)
    
    # Test 1: Health check
    test_health_endpoints()
    
    # Test 2: CORS
    test_cors()
    
    # Test 3: Enregistrement
    user_data = test_registration()
    
    if user_data:
        # Test 4: Première connexion (le problème original)
        login_result = test_first_login(user_data)
        
        if login_result:
            print(f"🎉 Token reçu: {login_result.get('tokens', {}).get('access_token', 'N/A')[:20]}...")
    
    # Test 5: Rate limiting
    test_rate_limiting()
    
    print("\n" + "=" * 55)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    main()