"""
H2.1 — rate limiting backé Redis, atomique et partagé entre workers.
"""

import pytest
import fakeredis
from app_entry import create_app
from rate_limiter import RateLimiter


@pytest.fixture
def app():
    app = create_app("testing")
    app.redis = fakeredis.FakeStrictRedis()
    return app


def _ctx(app, path):
    return app.test_request_context(
        path,
        environ_base={"REMOTE_ADDR": "1.2.3.4"},
        headers={"User-Agent": "pytest"},
    )


class TestRedisRateLimit:
    def test_counter_has_ttl_after_first_hit(self, app):
        """Atomicité : dès le 1er hit, la clé de compteur a un TTL (pas de course INCR/EXPIRE)."""
        limiter = RateLimiter(app.redis)
        with _ctx(app, "/api/auth/login"):
            from flask import request

            allowed, info = limiter.is_allowed(request)
        assert allowed is True
        keys = list(app.redis.keys("rl:count:*"))
        assert keys, "aucune clé de compteur créée en Redis"
        ttl = app.redis.ttl(keys[0])
        assert 0 < ttl <= 300

    def test_state_shared_between_workers(self, app):
        """Deux instances (workers) sur le même Redis partagent les compteurs."""
        w1 = RateLimiter(app.redis)
        w2 = RateLimiter(app.redis)
        with _ctx(app, "/api/auth/login"):
            from flask import request

            w1.is_allowed(request)
            _, info2 = w2.is_allowed(request)
        assert info2["remaining"] <= 18  # limite dev login = 20, déjà 2 hits

    def test_limit_exceeded_blocks(self, app):
        """Au-delà de la limite, is_allowed bloque (→ 429 côté HTTP)."""
        limiter = RateLimiter(app.redis)
        with _ctx(app, "/api/auth/login"):
            from flask import request

            results = [limiter.is_allowed(request)[0] for _ in range(25)]
        assert results[0] is True
        assert results[-1] is False
