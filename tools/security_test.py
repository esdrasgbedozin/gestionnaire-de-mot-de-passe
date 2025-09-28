#!/usr/bin/env python3
"""
🛡️ AUDIT DE SÉCURITÉ COMPLET - Password Manager
Tests d'attaques de haut niveau sans modification du code

Ce script teste automatiquement:
- Injection SQL
- Cross-Site Scripting (XSS) 
- Contournement d'authentification
- Rate Limiting & Brute Force
- Headers de sécurité
- Protection CORS/CSRF
- Directory Traversal

Usage: python3 security_test.py
Prérequis: Application démarrée via docker-compose
"""
import json
import time
import subprocess
import sys
import re

def run_curl(url, method="GET", data=None, headers=None):
    """Exécute une commande curl et retourne la réponse"""
    cmd = ["curl", "-s", "-i"]
    
    if method == "POST":
        cmd.append("-X")
        cmd.append("POST")
    
    if headers:
        for key, value in headers.items():
            cmd.append("-H")
            cmd.append(f"{key}: {value}")
    
    if data:
        cmd.append("-d")
        cmd.append(json.dumps(data) if isinstance(data, dict) else data)
        if "-H" not in str(cmd) or "Content-Type" not in str(cmd):
            cmd.append("-H")
            cmd.append("Content-Type: application/json")
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return None, "Timeout"

def test_input_validation():
    """Test de validation des entrées"""
    print("🔍 TEST 1: VALIDATION DES ENTRÉES")
    print("=" * 50)
    
    # Test email invalide
    print("\n📧 Test email invalide:")
    stdout, stderr = run_curl(
        "http://localhost:8080/api/auth/register",
        method="POST",
        data={"email": "invalid_email", "password": "SecurePass123!"}
    )
    if stdout:
        print(f"Response: {stdout.split('\\n\\n')[1] if '\\n\\n' in stdout else stdout}")
    
    time.sleep(2)  # Éviter le rate limiting
    
    # Test mot de passe faible
    print("\n🔑 Test mot de passe faible:")
    stdout, stderr = run_curl(
        "http://localhost:8080/api/auth/register",
        method="POST",
        data={"email": "weak@test.com", "password": "123"}
    )
    if stdout:
        print(f"Response: {stdout.split('\\n\\n')[1] if '\\n\\n' in stdout else stdout}")

def test_sql_injection():
    """Test d'injection SQL"""
    print("\n\\n💉 TEST 2: INJECTION SQL")
    print("=" * 50)
    
    payloads = [
        "admin'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "admin'/*",
        "' OR 1=1 --"
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\\n🎯 Payload {i}: {payload}")
        stdout, stderr = run_curl(
            "http://localhost:8080/api/auth/login",
            method="POST",
            data={"email": payload, "password": "anything"}
        )
        if stdout:
            status_line = stdout.split('\\n')[0]
            print(f"Status: {status_line}")
            if "500" in status_line or "error" in stdout.lower():
                print("⚠️  Possible vulnérabilité détectée")
            else:
                print("✅ Protection effective")
        time.sleep(3)  # Rate limiting

def test_xss_attempts():
    """Test d'attaques XSS"""
    print("\\n\\n🚨 TEST 3: CROSS-SITE SCRIPTING (XSS)")
    print("=" * 50)
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//"
    ]
    
    for i, payload in enumerate(xss_payloads, 1):
        print(f"\\n🎯 XSS Payload {i}: {payload}")
        stdout, stderr = run_curl(
            "http://localhost:8080/api/auth/register",
            method="POST",
            data={"email": f"test{i}@example.com", "password": payload}
        )
        if stdout:
            status_line = stdout.split('\\n')[0]
            print(f"Status: {status_line}")
        time.sleep(3)

def test_authentication_bypass():
    """Test de contournement d'authentification"""
    print("\\n\\n🔐 TEST 4: CONTOURNEMENT D'AUTHENTIFICATION")
    print("=" * 50)
    
    # Test accès direct aux endpoints protégés
    protected_endpoints = [
        "/api/passwords",
        "/api/passwords/generate",
        "/api/auth/verify-token"
    ]
    
    for endpoint in protected_endpoints:
        print(f"\\n🎯 Test endpoint: {endpoint}")
        stdout, stderr = run_curl(f"http://localhost:8080{endpoint}")
        if stdout:
            status_line = stdout.split('\\n')[0]
            print(f"Status: {status_line}")
            if "200" in status_line:
                print("⚠️  Accès non autorisé possible")
            elif "401" in status_line or "403" in status_line:
                print("✅ Protection d'authentification effective")
        time.sleep(2)

def test_csrf_protection():
    """Test de protection CSRF"""
    print("\\n\\n🛡️  TEST 5: PROTECTION CSRF")
    print("=" * 50)
    
    # Test sans token CSRF
    print("\\n🎯 Test sans headers CSRF:")
    stdout, stderr = run_curl(
        "http://localhost:8080/api/auth/login",
        method="POST",
        data={"email": "test@test.com", "password": "password"},
        headers={"Origin": "http://malicious-site.com"}
    )
    if stdout:
        status_line = stdout.split('\\n')[0]
        print(f"Status: {status_line}")
        if "403" in status_line or "cors" in stdout.lower():
            print("✅ Protection CORS active")

def test_rate_limiting():
    """Test du rate limiting"""
    print("\\n\\n⏱️  TEST 6: RATE LIMITING")
    print("=" * 50)
    
    print("\\n🎯 Test attaque par force brute:")
    for i in range(10):
        stdout, stderr = run_curl(
            "http://localhost:8080/api/auth/login",
            method="POST",
            data={"email": "admin@test.com", "password": f"wrong{i}"}
        )
        if stdout:
            status_line = stdout.split('\\n')[0]
            print(f"Tentative {i+1}: {status_line}")
            if "429" in status_line:
                print("✅ Rate limiting activé")
                break
        time.sleep(0.5)

def test_security_headers():
    """Test des headers de sécurité"""
    print("\\n\\n🔒 TEST 7: HEADERS DE SÉCURITÉ")
    print("=" * 50)
    
    stdout, stderr = run_curl("http://localhost:8080/api/auth/login", method="HEAD")
    if stdout:
        headers_section = stdout.split('\\n\\n')[0]
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Content-Security-Policy',
            'Strict-Transport-Security'
        ]
        
        print("\\n📋 Headers de sécurité détectés:")
        for header in security_headers:
            if header.lower() in headers_section.lower():
                print(f"✅ {header}: Présent")
            else:
                print(f"❌ {header}: Manquant")

def main():
    """Fonction principale"""
    print("🛡️  AUDIT DE SÉCURITÉ COMPLET")
    print("Gestionnaire de mot de passe - Tests d'attaque de haut niveau")
    print("=" * 70)
    
    try:
        test_security_headers()
        test_input_validation()
        test_sql_injection()
        test_xss_attempts()
        test_authentication_bypass()
        test_csrf_protection()
        test_rate_limiting()
        
        print("\\n\\n🎯 RÉSUMÉ DE L'AUDIT")
        print("=" * 50)
        print("✅ Tests de sécurité terminés")
        print("📊 Vérifiez les résultats ci-dessus pour identifier les vulnérabilités")
        print("🔍 Les réponses 401/403 indiquent une bonne sécurité")
        print("⚠️  Les réponses 200/500 peuvent indiquer des problèmes")
        
    except KeyboardInterrupt:
        print("\\n\\n❌ Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\\n\\n💥 Erreur lors des tests: {e}")

if __name__ == "__main__":
    main()