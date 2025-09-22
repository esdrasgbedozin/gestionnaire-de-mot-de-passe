#!/usr/bin/env python3
"""
Test complet de l'API Password Manager
"""

import json
import requests
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        
    def test_health(self):
        """Test de santé de l'API"""
        print("\n🏥 Test de santé...")
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ API en bonne santé")
                return True
            else:
                print(f"❌ Problème de santé: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_register(self, username="test_user", password="Test123!@#"):
        """Test d'inscription"""
        print(f"\n👤 Test d'inscription pour {username}...")
        try:
            data = {
                "username": username,
                "password": password,
                "email": f"{username}@test.com"
            }
            response = self.session.post(f"{API_URL}/auth/register", json=data)
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Inscription réussie")
                return True
            elif response.status_code == 409:
                print("ℹ️ Utilisateur déjà existant (normal)")
                return True
            else:
                print(f"❌ Échec d'inscription: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'inscription: {e}")
            return False
    
    def test_login(self, username="test_user", password="Test123!@#"):
        """Test de connexion"""
        print(f"\n🔑 Test de connexion pour {username}...")
        try:
            data = {
                "username": username,
                "password": password
            }
            response = self.session.post(f"{API_URL}/auth/login", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.user_id = result.get('user_id')
                
                # Configurer l'en-tête d'autorisation
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                
                print("✅ Connexion réussie")
                print(f"   Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Échec de connexion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_password_generation(self):
        """Test de génération de mots de passe"""
        print("\n🎲 Test de génération de mots de passe...")
        try:
            # Test génération par défaut
            response = self.session.post(f"{API_URL}/passwords/generate")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mot de passe généré: {result['password']} (force: {result['strength']})")
            
            # Test génération avec paramètres
            params = {
                "length": 20,
                "include_uppercase": True,
                "include_lowercase": True,
                "include_digits": True,
                "include_special": True
            }
            response = self.session.post(f"{API_URL}/passwords/generate", json=params)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mot de passe personnalisé généré: {result['password']} (force: {result['strength']})")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur de génération: {e}")
            return False
    
    def test_password_creation(self):
        """Test de création de mot de passe"""
        print("\n💾 Test de création de mot de passe...")
        try:
            password_data = {
                "site": "example.com",
                "username": "mon_username",
                "password": "MotDePasseSecret123!",
                "category": "work",
                "tags": ["important", "website"],
                "notes": "Compte de test créé via API",
                "is_favorite": True
            }
            
            response = self.session.post(f"{API_URL}/passwords", json=password_data)
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Mot de passe créé avec succès")
                print(f"   ID: {result['password']['id']}")
                print(f"   Site: {result['password']['site']}")
                print(f"   Catégorie: {result['password']['category']}")
                return result['password']['id']
            else:
                print(f"❌ Échec de création: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur de création: {e}")
            return None
    
    def test_password_listing(self):
        """Test de listing des mots de passe"""
        print("\n📋 Test de listing des mots de passe...")
        try:
            response = self.session.get(f"{API_URL}/passwords")
            
            if response.status_code == 200:
                result = response.json()
                passwords = result.get('passwords', [])
                print(f"✅ {len(passwords)} mot(s) de passe trouvé(s)")
                
                for pwd in passwords[:3]:  # Afficher max 3
                    print(f"   - {pwd['site']} ({pwd['username']}) - {pwd['category']}")
                
                return len(passwords) > 0
            else:
                print(f"❌ Échec de listing: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de listing: {e}")
            return False
    
    def test_categories(self):
        """Test de récupération des catégories"""
        print("\n🗂️ Test des catégories...")
        try:
            response = self.session.get(f"{API_URL}/passwords/categories")
            
            if response.status_code == 200:
                result = response.json()
                categories = result.get('categories', [])
                print(f"✅ {len(categories)} catégorie(s) trouvée(s)")
                
                for cat in categories:
                    print(f"   - {cat['category']}: {cat['count']} mot(s) de passe")
                
                return True
            else:
                print(f"❌ Échec catégories: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur catégories: {e}")
            return False
    
    def test_complete_workflow(self):
        """Test du workflow complet"""
        print("🚀 Test du workflow complet de l'API Password Manager")
        print("=" * 60)
        
        # Tests séquentiels
        tests = [
            self.test_health,
            self.test_register,
            self.test_login,
            self.test_password_generation,
            self.test_password_creation,
            self.test_password_listing,
            self.test_categories,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Erreur dans {test.__name__}: {e}")
                results.append(False)
        
        # Résultats
        print("\n" + "=" * 60)
        print("📊 Résultats des tests")
        print("=" * 60)
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"✅ Tests réussis: {success_count}/{total_count}")
        print(f"❌ Tests échoués: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("\n🎉 Tous les tests sont passés ! L'API fonctionne parfaitement.")
        else:
            print(f"\n⚠️ {total_count - success_count} test(s) ont échoué. Vérifiez les logs ci-dessus.")
        
        return success_count == total_count


if __name__ == "__main__":
    tester = APITester()
    success = tester.test_complete_workflow()
    
    sys.exit(0 if success else 1)