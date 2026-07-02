"""
H2.1 — rate limiting backé Redis, atomique et partagé entre workers.
"""

import pytest
import json
import fakeredis
from app_entry import create_app
from rate_limiter import RateLimiter


@pytest.fixture
def app():
    app = create_app("testing")
    app.redis = fakeredis.FakeStrictRedis()
    app.rate_limiter = RateLimiter(app.redis)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


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


RESET_URL = "/api/admin/rate-limit-reset"


class TestEmergencyResetSecurity:
    """H3 : reset d'urgence fail-closed + comparaison à temps constant + rate-limité."""

    def test_reset_refused_when_server_key_absent(self, client, monkeypatch):
        """PREUVE : sans clé serveur configurée, tout reset est refusé (avant le fix : None==None → 200)."""
        monkeypatch.delenv("EMERGENCY_RESET_KEY", raising=False)
        r = client.post(RESET_URL)  # aucune X-Emergency-Key fournie
        assert r.status_code == 403

    def test_reset_wrong_key_403(self, client, monkeypatch):
        monkeypatch.setenv("EMERGENCY_RESET_KEY", "the-real-emergency-key")
        r = client.post(RESET_URL, headers={"X-Emergency-Key": "wrong-key"})
        assert r.status_code == 403

    def test_reset_correct_key_200(self, client, monkeypatch):
        monkeypatch.setenv("EMERGENCY_RESET_KEY", "the-real-emergency-key")
        r = client.post(RESET_URL, headers={"X-Emergency-Key": "the-real-emergency-key"})
        assert r.status_code == 200
        assert json.loads(r.data)["status"] == "success"

    def test_reset_missing_provided_key_no_500(self, client, monkeypatch):
        """Clé serveur configurée mais rien fourni → 403 (jamais 500 via compare_digest)."""
        monkeypatch.setenv("EMERGENCY_RESET_KEY", "the-real-emergency-key")
        r = client.post(RESET_URL)  # pas de header
        assert r.status_code == 403

    def test_reset_endpoint_is_rate_limited(self, client, monkeypatch):
        """L'endpoint a sa propre limite ; les tentatives échouées comptent → 429 au dépassement."""
        monkeypatch.setenv("EMERGENCY_RESET_KEY", "the-real-emergency-key")
        statuses = [
            client.post(RESET_URL, headers={"X-Emergency-Key": "wrong"}).status_code
            for _ in range(12)
        ]
        assert 429 in statuses


class TestProxyFix:
    """M1 : ProxyFix(x_for=1) — l'IP client vient du proxy de confiance, pas du header brut."""

    def _register_route(self, app):
        from flask import request, current_app, jsonify

        def whoami():
            return jsonify(
                client_id=current_app.rate_limiter._get_client_id(request),
                remote_addr=request.remote_addr,
            )

        app.add_url_rule("/__client_id__", "whoami_ci", whoami)
        return app.test_client()

    def test_forged_xff_ignored_same_real_ip_grouped(self, app):
        """Gauches forgées différentes, même IP réelle (droite) → même client_id (forgé ignoré)."""
        c = self._register_route(app)
        a = json.loads(c.get("/__client_id__", headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.5"}).data)
        b = json.loads(c.get("/__client_id__", headers={"X-Forwarded-For": "7.7.7.7, 203.0.113.5"}).data)
        assert a["remote_addr"] == "203.0.113.5"
        assert b["remote_addr"] == "203.0.113.5"
        assert a["client_id"] == b["client_id"]

    def test_distinct_real_ips_not_grouped(self, app):
        """Deux vraies IP différentes (droite) → client_id différents (pas de sur-regroupement)."""
        c = self._register_route(app)
        a = json.loads(c.get("/__client_id__", headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.5"}).data)
        b = json.loads(c.get("/__client_id__", headers={"X-Forwarded-For": "9.9.9.9, 198.51.100.7"}).data)
        assert a["remote_addr"] == "203.0.113.5"
        assert b["remote_addr"] == "198.51.100.7"
        assert a["client_id"] != b["client_id"]

    def test_no_xff_uses_direct_remote_addr(self, app):
        """Sans X-Forwarded-For (dev/test direct) → pas de crash, IP directe utilisée."""
        c = self._register_route(app)
        r = c.get("/__client_id__")
        assert r.status_code == 200
        assert json.loads(r.data)["remote_addr"]
