"""
H4 — en-têtes de sécurité réellement servis en production (CSP stricte, HSTS,
force-HTTPS), sans casser le dev.

On teste la LOGIQUE des en-têtes en forçant ENVIRONMENT='production' sur une app
de test (DB sqlite valide, pas de fail-fast secrets), plus le fait que les
classes de config portent bien l'attribut ENVIRONMENT.
"""

import fakeredis
from app_entry import create_app
from app.services.session_key_store import SessionKeyStore
from rate_limiter import RateLimiter
from app.services.session_service import RefreshRegistry


def _wire_redis(app):
    app.redis = fakeredis.FakeStrictRedis()
    app.session_key_store = SessionKeyStore(client=app.redis)
    app.rate_limiter = RateLimiter(app.redis)
    app.refresh_registry = RefreshRegistry(app.redis)
    return app


def _prod_headers_app():
    """App de test dont la logique d'en-têtes se comporte comme en production."""
    app = _wire_redis(create_app("testing"))
    app.config["ENVIRONMENT"] = "production"
    app.config["FORCE_SSL"] = True
    return app


class TestConfigEnvironment:
    def test_config_classes_carry_environment(self):
        from config import DevelopmentConfig, ProductionConfig, TestingConfig

        assert ProductionConfig.ENVIRONMENT == "production"
        assert DevelopmentConfig.ENVIRONMENT == "development"
        assert TestingConfig.ENVIRONMENT == "testing"


class TestProdSecurityHeaders:
    def test_prod_serves_hsts_and_strict_csp(self):
        """PROD : CSP stricte ET HSTS servis (avant le fix : CSP DEV + pas de HSTS)."""
        client = _prod_headers_app().test_client()
        r = client.get(
            "/", base_url="https://localhost"
        )  # sécurisé → pas de redirection
        assert r.status_code == 200

        csp = r.headers.get("Content-Security-Policy", "")
        # C'est bien la CSP PROD, pas la DEV (le vrai bug : DEV servie en prod)
        assert "unsafe-eval" not in csp
        assert "localhost:" not in csp
        assert "frame-ancestors 'none'" in csp
        assert "upgrade-insecure-requests" in csp

        assert (
            r.headers.get("Strict-Transport-Security")
            == "max-age=31536000; includeSubDomains; preload"
        )

    def test_prod_forces_https_redirect(self):
        """PROD + HTTP non sécurisé → 301 vers HTTPS (avant le fix : pas de redirection)."""
        client = _prod_headers_app().test_client()
        r = client.get("/", base_url="http://localhost")
        assert r.status_code == 301
        assert r.headers["Location"].startswith("https://")

    def test_forwarded_proto_https_not_redirected(self):
        """Derrière Nginx (X-Forwarded-Proto: https) → pas de boucle de redirection."""
        client = _prod_headers_app().test_client()
        r = client.get(
            "/", base_url="http://localhost", headers={"X-Forwarded-Proto": "https"}
        )
        assert r.status_code == 200

    def test_health_exact_path_excluded_from_redirect(self):
        """/health (chemin EXACT) n'est PAS redirigé (healthcheck interne en HTTP)."""
        client = _prod_headers_app().test_client()
        r = client.get("/health", base_url="http://localhost")
        assert r.status_code != 301


class TestDevSecurityHeaders:
    def test_dev_no_hsts_no_redirect(self):
        """DEV/testing : pas de HSTS, pas de redirection (HTTP local intact)."""
        client = _wire_redis(create_app("testing")).test_client()
        r = client.get("/", base_url="http://localhost")
        assert r.status_code == 200
        assert "Strict-Transport-Security" not in r.headers


class TestScriptSrcNoUnsafeInline:
    """H5 : la CSP prod Flask n'autorise plus 'unsafe-inline' sur script-src."""

    def _directives(self):
        client = _prod_headers_app().test_client()
        r = client.get("/", base_url="https://localhost")
        csp = r.headers.get("Content-Security-Policy", "")
        directives = {}
        for part in csp.split(";"):
            part = part.strip()
            if part:
                directives[part.split()[0]] = part
        return directives

    def test_script_src_has_no_unsafe_inline(self):
        script_src = self._directives().get("script-src", "")
        assert "'self'" in script_src
        assert "unsafe-inline" not in script_src  # RED avant : script-src 'self' 'unsafe-inline'

    def test_style_src_unsafe_inline_unchanged(self):
        # H5 ne touche PAS style-src (styles inline React) — garde-fou
        assert "unsafe-inline" in self._directives().get("style-src", "")
