"""
Configuration de l'application Flask
"""

import os
from datetime import timedelta


# Secrets obligatoires : aucune valeur par défaut autorisée.
# Si l'un d'eux manque, l'application refuse de démarrer (fail-fast).
REQUIRED_SECRETS = ("SECRET_KEY", "JWT_SECRET_KEY", "ENCRYPTION_KEY", "DATABASE_URL")


def require_env(name):
    """Lit une variable d'environnement OBLIGATOIRE.

    Lève une RuntimeError explicite si elle est absente ou vide,
    afin de ne jamais démarrer avec un secret par défaut non sécurisé.
    """
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"{name} is required but not set. "
            f"Refusing to start with an insecure default — provide it via the environment (.env)."
        )
    return value


def validate_required_secrets():
    """Vérifie la présence de TOUS les secrets requis. À appeler au démarrage (hors tests)."""
    missing = [
        name for name in REQUIRED_SECRETS if not (os.environ.get(name) or "").strip()
    ]
    if missing:
        raise RuntimeError(
            "Missing required secret(s): " + ", ".join(missing) + ". "
            "Refusing to start with insecure defaults — provide them via the environment (.env)."
        )


class Config:
    """Configuration de base"""

    # Secrets lus depuis l'environnement, SANS valeur de repli (validés au démarrage).
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Configuration de chiffrement
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

    # Configuration de sécurité (valeurs non sensibles : défauts acceptables)
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", 12))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
    LOCKOUT_DURATION = int(os.environ.get("LOCKOUT_DURATION", 900))  # 15 minutes

    # Durée de détention de la VMK en session (Redis), en secondes (Lot 3/C1)
    VAULT_SESSION_TTL_SECONDS = int(os.environ.get("VAULT_SESSION_TTL_SECONDS", 3600))

    # Configuration CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
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
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # Refresh plus court
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", 14))  # Plus sécurisé

    # Rate limiting strict
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 3))
    LOCKOUT_DURATION = int(os.environ.get("LOCKOUT_DURATION", 1800))  # 30 minutes

    # Logs de sécurité
    ENABLE_AUDIT_LOGS = os.environ.get("ENABLE_AUDIT_LOGS", "true").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")

    # Forcer HTTPS
    FORCE_SSL = os.environ.get("FORCE_SSL", "true").lower() == "true"

    # CORS strict pour production
    CORS_ORIGINS = (
        os.environ.get("CORS_ORIGINS", "").split(",")
        if os.environ.get("CORS_ORIGINS")
        else []
    )


class TestingConfig(Config):
    """Configuration pour les tests.

    Valeurs de test explicites et NON sensibles : elles ne servent qu'aux tests
    automatisés et ne doivent jamais être utilisées en production.
    """

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key-not-for-production"
    JWT_SECRET_KEY = "test-jwt-secret-key-not-for-production"
    ENCRYPTION_KEY = "test-encryption-key-not-for-prod!"
    BCRYPT_LOG_ROUNDS = 4  # Plus rapide pour les tests


# Dictionnaire des configurations
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
