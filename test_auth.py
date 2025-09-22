#!/usr/bin/env python3
"""
Script de test pour déboguer les routes d'authentification
"""

import requests
import json

def test_registration():
    """Tester l'inscription"""
    url = "http://localhost:8080/api/auth/register"
    data = {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.headers.get('content-type') == 'application/json':
            print(f"JSON: {response.json()}")
    
    except Exception as e:
        print(f"Erreur: {e}")

def test_health():
    """Tester l'endpoint de santé"""
    url = "http://localhost:8080/health"
    
    try:
        response = requests.get(url)
        print(f"Health Status Code: {response.status_code}")
        print(f"Health Response: {response.text}")
    
    except Exception as e:
        print(f"Erreur health: {e}")

if __name__ == "__main__":
    print("=== Test Health ===")
    test_health()
    
    print("\n=== Test Registration ===")
    test_registration()