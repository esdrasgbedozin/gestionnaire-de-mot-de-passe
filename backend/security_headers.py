#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security headers middleware pour Flask
Ajoute les headers de sécurité essentiels pour protéger contre diverses attaques
"""

from flask import Flask
import logging

logger = logging.getLogger(__name__)

class SecurityHeaders:
    """Gestionnaire des headers de sécurité"""
    
    # Configuration des headers de sécurité
    SECURITY_HEADERS = {
        # Protection XSS
        'X-XSS-Protection': '1; mode=block',
        
        # Prévention du MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Protection contre le clickjacking
        'X-Frame-Options': 'DENY',
        
        # Référrer policy pour protéger les URLs privées
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Permissions policy pour contrôler les fonctionnalités du navigateur
        'Permissions-Policy': (
            'camera=(), '
            'microphone=(), '
            'geolocation=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=(), '
            'ambient-light-sensor=(), '
            'autoplay=(), '
            'display-capture=(), '
            'fullscreen=(self), '
            'clipboard-write=()'
        ),
        
        # Cache control pour les données sensibles
        'Cache-Control': 'no-cache, no-store, must-revalidate, private',
        'Pragma': 'no-cache',
        'Expires': '0',
        
        # Server header removal (sécurité par obscurité)
        'Server': 'SecureServer/1.0'
    }
    
    # CSP pour production (à ajuster selon les besoins)
    CSP_POLICY_PRODUCTION = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "  # Peut être rendu plus strict
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    )
    
    # CSP pour développement (plus permissif)
    CSP_POLICY_DEVELOPMENT = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: localhost:* 127.0.0.1:*; "
        "connect-src 'self' localhost:* 127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
        "frame-ancestors 'none'"
    )
    
    # HSTS pour HTTPS (uniquement en production avec HTTPS)
    HSTS_HEADER = 'max-age=31536000; includeSubDomains; preload'

    @classmethod
    def get_csp_policy(cls, env='development'):
        """Obtenir la politique CSP selon l'environnement"""
        if env == 'production':
            return cls.CSP_POLICY_PRODUCTION
        return cls.CSP_POLICY_DEVELOPMENT

def add_security_headers(response, app_config=None):
    """Ajouter les headers de sécurité à la réponse"""
    
    # Headers de base toujours appliqués
    for header, value in SecurityHeaders.SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # CSP selon l'environnement
    env = app_config.get('ENV', 'development') if app_config else 'development'
    csp_policy = SecurityHeaders.get_csp_policy(env)
    response.headers['Content-Security-Policy'] = csp_policy
    
    # HSTS uniquement en HTTPS production
    if (app_config and 
        app_config.get('ENV') == 'production' and 
        app_config.get('FORCE_HTTPS', False)):
        response.headers['Strict-Transport-Security'] = SecurityHeaders.HSTS_HEADER
    
    # Headers API spécifiques pour les réponses JSON
    if response.content_type and 'application/json' in response.content_type:
        # Prévention du cross-site request forgery pour les API
        response.headers['X-Requested-With'] = 'XMLHttpRequest'
    
    return response

def setup_security_headers(app: Flask):
    """Configurer les headers de sécurité pour l'application Flask"""
    
    @app.after_request
    def security_headers(response):
        """Middleware pour ajouter les headers de sécurité"""
        return add_security_headers(response, app.config)
    
    # Configuration HTTPS forcée pour la production
    @app.before_request
    def force_https():
        """Forcer HTTPS en production"""
        from flask import request, redirect, url_for
        
        if (app.config.get('ENV') == 'production' and 
            app.config.get('FORCE_HTTPS', False) and
            not request.is_secure):
            
            # Rediriger vers HTTPS
            return redirect(request.url.replace('http://', 'https://'), code=301)
    
    # Suppression des headers révélateurs d'information
    @app.after_request
    def remove_server_header(response):
        """Supprimer/modifier les headers qui révèlent des informations sur le serveur"""
        # Le header 'Server' est déjà remplacé dans SECURITY_HEADERS
        # Supprimer d'autres headers potentiellement révélateurs
        headers_to_remove = ['X-Powered-By', 'X-Runtime']
        for header in headers_to_remove:
            response.headers.pop(header, None)
        
        return response
    
    logger.info(f"Security headers configured for environment: {app.config.get('ENV', 'development')}")
    return app

def create_nginx_config():
    """Générer une configuration Nginx avec headers de sécurité pour la production"""
    
    nginx_config = """
# Configuration Nginx pour la production avec headers de sécurité
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirection forcée vers HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # Configuration SSL/TLS
    ssl_certificate /path/to/certificate.pem;
    ssl_certificate_key /path/to/private-key.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de sécurité (redondants avec Flask mais garantis)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # CSP (à ajuster selon vos besoins)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    
    # Cacher la version de Nginx
    server_tokens off;
    
    # Configuration du proxy vers l'application Flask
    location / {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Fichiers statiques (optionnel)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Bloquer les fichiers sensibles
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ^/(config|env|docker-compose) {
        deny all;
        access_log off;
        log_not_found off;
    }
}
"""
    
    return nginx_config

def create_docker_compose_https():
    """Configuration Docker Compose avec HTTPS"""
    
    docker_compose = """
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      - FLASK_ENV=production
      - FORCE_HTTPS=true
      - DATABASE_URL=postgresql://user:pass@database:5432/dbname
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - database
    restart: unless-stopped
    # Port non exposé publiquement
    expose:
      - "5000"

  frontend:
    build: ./frontend
    # Port non exposé publiquement
    expose:
      - "3000"
    restart: unless-stopped

  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=password_manager_db
      - POSTGRES_USER=password_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    # Port non exposé publiquement
    expose:
      - "5432"

volumes:
  postgres_data:
"""
    
    return docker_compose