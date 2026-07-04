#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate limiting backé Redis (Lot 4 / H2.1).

État partagé entre workers gunicorn via Redis. Le compteur de fenêtre est créé
avec son TTL en une opération atomique (SET … NX EX), puis incrémenté (INCR) —
il n'existe donc jamais de clé sans TTL (pas de course INCR/EXPIRE).
La blacklist de blocage utilise SET … EX (atomique).

Identification du client : basée sur request.remote_addr, fiabilisé par ProxyFix
(x_for=1) au niveau de l'app — l'en-tête X-Forwarded-For brut du client n'est plus
lu directement (M1).
"""

import hashlib
import hmac
import os
import time
from functools import wraps

from flask import request, jsonify, g, current_app
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter à fenêtre fixe, état en Redis (partagé multi-worker)."""

    COUNT_PREFIX = "rl:count:"
    BLOCK_PREFIX = "rl:block:"

    def __init__(self, redis_client):
        self.redis = redis_client

        is_development = (
            os.environ.get("FLASK_ENV") == "development"
            or os.environ.get("ENV") != "production"
        )
        if is_development:
            self.limits = {
                "/api/auth/login": {
                    "requests": 20,
                    "window": 300,
                    "block_duration": 60,
                },
                "/api/auth/register": {
                    "requests": 10,
                    "window": 300,
                    "block_duration": 60,
                },
                "/api/auth/refresh": {
                    "requests": 50,
                    "window": 300,
                    "block_duration": 30,
                },
                "/api/admin/rate-limit-reset": {
                    "requests": 10,
                    "window": 300,
                    "block_duration": 300,
                },
                # D2 : destruction totale du compte — cible de brute-force du master
                # password, isolée du quota de login (bucket dédié strict, calibré H3).
                "/api/users/account": {
                    "requests": 10,
                    "window": 300,
                    "block_duration": 300,
                },
                "/api/passwords": {"requests": 100, "window": 60, "block_duration": 30},
                "/api/passwords/*": {
                    "requests": 100,
                    "window": 60,
                    "block_duration": 30,
                },
                "/api/users/profile": {
                    "requests": 100,
                    "window": 60,
                    "block_duration": 30,
                },
                "default": {"requests": 200, "window": 60, "block_duration": 30},
            }
        else:
            self.limits = {
                "/api/auth/login": {
                    "requests": 5,
                    "window": 300,
                    "block_duration": 300,
                },
                "/api/auth/register": {
                    "requests": 3,
                    "window": 300,
                    "block_duration": 300,
                },
                "/api/auth/refresh": {
                    "requests": 10,
                    "window": 300,
                    "block_duration": 120,
                },
                "/api/admin/rate-limit-reset": {
                    "requests": 5,
                    "window": 300,
                    "block_duration": 900,
                },
                # D2 : destruction totale du compte — bucket dédié strict (calibré H3).
                "/api/users/account": {
                    "requests": 5,
                    "window": 300,
                    "block_duration": 900,
                },
                "/api/passwords": {"requests": 30, "window": 60, "block_duration": 120},
                "/api/passwords/*": {
                    "requests": 20,
                    "window": 60,
                    "block_duration": 120,
                },
                "/api/users/profile": {
                    "requests": 20,
                    "window": 60,
                    "block_duration": 120,
                },
                "default": {"requests": 60, "window": 60, "block_duration": 120},
            }

    def _get_client_id(self, request):
        """Identifiant client (IP + User-Agent hashés)."""
        # request.remote_addr est fiable grâce à ProxyFix (M1) ; ne PAS relire l'en-tête brut
        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")
        return hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()[:16]

    def _normalize_endpoint(self, path):
        """Normaliser le chemin (retirer query + remplacer les IDs par *)."""
        import re

        if "?" in path:
            path = path.split("?")[0]
        path = re.sub(r"/[a-f0-9\-]{8,}", "/*", path)
        path = re.sub(r"/\d+", "/*", path)
        return path

    def _get_rate_limit_config(self, endpoint):
        if endpoint in self.limits:
            return self.limits[endpoint]
        for pattern, config in self.limits.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return config
        return self.limits["default"]

    def is_allowed(self, request):
        """Vérifier si la requête est autorisée (état en Redis)."""
        client_id = self._get_client_id(request)
        endpoint = self._normalize_endpoint(request.path)
        config = self._get_rate_limit_config(endpoint)

        block_key = f"{self.BLOCK_PREFIX}{client_id}:{endpoint}"
        block_ttl = self.redis.ttl(block_key)
        if block_ttl and block_ttl > 0:
            return False, {
                "allowed": False,
                "reason": "blocked",
                "retry_after": int(block_ttl),
            }

        # Compteur de fenêtre : création atomique AVEC TTL (SET NX EX) puis INCR.
        count_key = f"{self.COUNT_PREFIX}{client_id}:{endpoint}"
        self.redis.set(count_key, 0, nx=True, ex=config["window"])
        count = self.redis.incr(count_key)

        if count > config["requests"]:
            # Bloquer le client (SET EX atomique)
            self.redis.set(block_key, 1, ex=config["block_duration"])
            logger.warning("Rate limit exceeded for %s on %s", client_id, endpoint)
            return False, {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "limit": config["requests"],
                "window": config["window"],
                "retry_after": config["block_duration"],
            }

        return True, {
            "allowed": True,
            "remaining": max(0, config["requests"] - count),
            "reset_time": time.time() + config["window"],
        }

    def get_stats(self):
        """Statistiques minimales (clés actives en Redis + limites)."""
        count_keys = list(self.redis.scan_iter(match=f"{self.COUNT_PREFIX}*"))
        block_keys = list(self.redis.scan_iter(match=f"{self.BLOCK_PREFIX}*"))
        return {
            "active_counters": len(count_keys),
            "blocked_clients": len(block_keys),
            "endpoint_limits": self.limits,
        }

    def reset_client(self, client_id=None):
        """Réinitialiser un client (ses clés) ou tous."""
        if client_id:
            patterns = [
                f"{self.COUNT_PREFIX}{client_id}:*",
                f"{self.BLOCK_PREFIX}{client_id}:*",
            ]
        else:
            patterns = [f"{self.COUNT_PREFIX}*", f"{self.BLOCK_PREFIX}*"]
        for pattern in patterns:
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
        logger.info("Rate limiter reset for: %s", client_id if client_id else "ALL")

    def unblock_client(self, client_id):
        """Débloquer un client (supprime ses clés de blocage)."""
        removed = False
        for key in self.redis.scan_iter(match=f"{self.BLOCK_PREFIX}{client_id}:*"):
            self.redis.delete(key)
            removed = True
        return removed


def rate_limit_middleware(f):
    """Décorateur appliquant le rate limiting via le limiter de l'app."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed, info = current_app.rate_limiter.is_allowed(request)

        if not allowed:
            response = jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "details": info,
                }
            )
            response.status_code = 429
            response.headers["Retry-After"] = str(info["retry_after"])
            if "limit" in info:
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = "0"
            return response

        g.rate_limit_info = info
        return f(*args, **kwargs)

    return decorated_function


def add_rate_limit_headers(response):
    """Ajouter les headers de rate limiting aux réponses autorisées."""
    if hasattr(g, "rate_limit_info") and g.rate_limit_info.get("allowed"):
        info = g.rate_limit_info
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        if "reset_time" in info:
            response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
    return response


def setup_rate_limiting(app):
    """Configurer le rate limiting (limiter backé Redis attaché à l'app)."""
    app.rate_limiter = RateLimiter(app.redis)

    @app.after_request
    def after_request(response):
        return add_rate_limit_headers(response)

    @app.route("/api/admin/rate-limit-stats")
    @rate_limit_middleware
    def rate_limit_stats():
        return jsonify(current_app.rate_limiter.get_stats())

    @app.route("/api/admin/rate-limit-reset", methods=["POST"])
    @rate_limit_middleware
    def reset_rate_limit():
        # H3 : fail-closed. Sans clé d'urgence CONFIGURÉE côté serveur, aucun reset.
        server_key = os.environ.get("EMERGENCY_RESET_KEY")
        if not server_key or not server_key.strip():
            return jsonify(
                {
                    "error": "Access denied",
                    "message": "Emergency reset key not configured",
                }
            ), 403

        # Comparaison à temps constant ; clé fournie absente/malformée → refus (pas de 500).
        provided_key = request.headers.get("X-Emergency-Key")
        if not provided_key or not hmac.compare_digest(provided_key, server_key):
            return jsonify(
                {"error": "Access denied", "message": "Invalid emergency key"}
            ), 403

        data = request.get_json(silent=True) or {}
        client_id = data.get("client_id")

        if client_id:
            current_app.rate_limiter.unblock_client(client_id)
            return jsonify(
                {"message": f"Client {client_id} unblocked", "status": "success"}
            )
        else:
            current_app.rate_limiter.reset_client()
            return jsonify(
                {"message": "Rate limiter reset for all clients", "status": "success"}
            )

    logger.info("Rate limiting middleware configured (Redis-backed)")
    return app
