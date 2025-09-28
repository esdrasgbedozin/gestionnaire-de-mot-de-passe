"""
Configuration de l'application Flask
"""

import os
from datetime import timedelta


class Config:
    """Configuration de base"""
    
    # Configuration Flask
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://admin:secure_password_2024@localhost:5432/password_manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Configuration de chiffrement
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'change-this-32-byte-key-in-prod!'
    
    # Configuration de sécurité
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 12))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION = int(os.environ.get('LOCKOUT_DURATION', 900))  # 15 minutes
    
    # Configuration CORS
    CORS_ORIGINS = [
        'http://localhost:3000', 
        'http://127.0.0.1:3000',
        'http://localhost:8080',
        'http://127.0.0.1:8080'
    ]


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False
    
    # Sécurité renforcée en production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)  # Tokens plus courts
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)     # Refresh plus court
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 14))  # Plus sécurisé
    
    # Rate limiting strict
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 3))
    LOCKOUT_DURATION = int(os.environ.get('LOCKOUT_DURATION', 1800))  # 30 minutes
    
    # Logs de sécurité
    ENABLE_AUDIT_LOGS = os.environ.get('ENABLE_AUDIT_LOGS', 'true').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # Forcer HTTPS
    FORCE_SSL = os.environ.get('FORCE_SSL', 'true').lower() == 'true'
    
    # CORS strict pour production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []


class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4  # Plus rapide pour les tests


# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}