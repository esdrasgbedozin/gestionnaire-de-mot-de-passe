"""
Fabrique du client Redis partagé (Lot 4 / H2.0).

Un seul client Redis est créé au démarrage (`app.redis`) et réutilisé par tous
les services qui ont besoin d'un état partagé entre workers gunicorn :
session key store (VMK), rate limiting, registre des refresh tokens.
"""

import os

import redis


def make_redis_client():
    """Construit un client Redis à partir de REDIS_URL (connexion paresseuse)."""
    return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
