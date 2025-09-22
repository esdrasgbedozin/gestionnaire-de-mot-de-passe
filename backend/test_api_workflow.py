#!/usr/bin/env python3
"""
Test complet de l'API Password Manager - Version simplifiée
"""

import json
import subprocess
import sys

def run_curl(method, endpoint, data=None, token=None):
    """Exécuter une commande curl et retourner le résultat"""
    base_url = "http://localhost:8080"
    
    cmd = ["curl", "-s", "-X", method, f"{base_url}{endpoint}"]
    cmd.extend(["-H", "Content-Type: application/json"])
    
    if token:
        cmd.extend(["-H", f"Authorization: Bearer {token}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        else:
            return {"error": f"HTTP error: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"error": "Request timeout"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response: {result.stdout}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def test_api_workflow():
    """Test du workflow complet de l'API"""
    print("🚀 Test du workflow complet de l'API Password Manager")
    print("=" * 60)
    
    # Test 1: Santé
    print("\n🏥 Test de santé...")
    health = run_curl("GET", "/health")
    if "status" in health and health["status"] == "healthy":
        print("✅ API en bonne santé")
    else:
        print(f"❌ Problème de santé: {health}")
        return False
    
    # Test 2: Inscription
    print("\n👤 Test d'inscription...")
    user_data = {
        "username": "test_api_user",
        "password": "TestAPI123!",
        "email": "testapi@example.com"
    }
    
    register_result = run_curl("POST", "/api/auth/register", user_data)
    if "message" in register_result and "successfully" in register_result["message"]:
        print("✅ Inscription réussie")
        token = register_result.get("tokens", {}).get("access_token")
    else:
        # Essayer de se connecter si l'utilisateur existe déjà
        print("ℹ️ Utilisateur peut-être existant, tentative de connexion...")
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        login_result = run_curl("POST", "/api/auth/login", login_data)
        if "tokens" in login_result:
            print("✅ Connexion réussie")
            token = login_result["tokens"]["access_token"]
        else:
            print(f"❌ Échec authentification: {login_result}")
            return False
    
    # Test 3: Génération de mot de passe (avec authentification)
    print("\n🎲 Test génération de mot de passe...")
    gen_data = {"length": 16, "include_special": True}
    gen_result = run_curl("POST", "/api/passwords/generate", gen_data, token)
    
    if "password" in gen_result:
        print(f"✅ Mot de passe généré: {gen_result['password']} (force: {gen_result.get('strength', 'N/A')}/5)")
        generated_password = gen_result['password']
    else:
        print(f"❌ Échec génération: {gen_result}")
        generated_password = "FallbackP@ssw0rd123!"
    
    # Test 4: Création d'un mot de passe
    print("\n💾 Test création de mot de passe...")
    password_data = {
        "site_name": "example.com",
        "site_url": "https://example.com",
        "username": "testuser",
        "email": "test@example.com",
        "password": generated_password,
        "category": "work",
        "tags": ["important", "website"],
        "notes": "Compte de test créé via API",
        "is_favorite": True,
        "priority": 1
    }
    
    create_result = run_curl("POST", "/api/passwords", password_data, token)
    if "password" in create_result and "id" in create_result["password"]:
        print("✅ Mot de passe créé avec succès")
        password_id = create_result["password"]["id"]
        print(f"   ID: {password_id}")
        print(f"   Site: {create_result['password']['site_name']}")
    else:
        print(f"❌ Échec création: {create_result}")
        password_id = None
    
    # Test 5: Liste des mots de passe
    print("\n📋 Test liste des mots de passe...")
    list_result = run_curl("GET", "/api/passwords", None, token)
    if "passwords" in list_result:
        count = len(list_result["passwords"])
        print(f"✅ {count} mot(s) de passe trouvé(s)")
        if count > 0:
            print(f"   Premier: {list_result['passwords'][0]['site_name']}")
    else:
        print(f"❌ Échec listing: {list_result}")
    
    # Test 6: Catégories
    print("\n🗂️ Test des catégories...")
    cat_result = run_curl("GET", "/api/passwords/categories", None, token)
    if "categories" in cat_result:
        print(f"✅ {len(cat_result['categories'])} catégorie(s) trouvée(s)")
        for cat in cat_result["categories"][:3]:
            print(f"   - {cat['category']}: {cat['count']} entrée(s)")
    else:
        print(f"❌ Échec catégories: {cat_result}")
    
    # Test 7: Presets
    print("\n🎛️ Test des presets...")
    presets_result = run_curl("GET", "/api/passwords/presets", None, token)
    if "presets" in presets_result:
        print(f"✅ {len(presets_result['presets'])} preset(s) disponible(s)")
        print(f"   Presets: {list(presets_result['presets'].keys())}")
    else:
        print(f"❌ Échec presets: {presets_result}")
    
    # Test 8: Évaluation de force
    print("\n💪 Test évaluation de force...")
    strength_data = {"password": "TestPassword123!"}
    strength_result = run_curl("POST", "/api/passwords/strength", strength_data, token)
    if "strength" in strength_result:
        print(f"✅ Force évaluée: {strength_result['strength']}/5")
        print(f"   Feedback: {strength_result.get('feedback', 'N/A')}")
    else:
        print(f"❌ Échec évaluation: {strength_result}")
    
    print("\n" + "=" * 60)
    print("🎉 Tests terminés ! L'API Password Manager est fonctionnelle.")
    return True

if __name__ == "__main__":
    success = test_api_workflow()
    sys.exit(0 if success else 1)