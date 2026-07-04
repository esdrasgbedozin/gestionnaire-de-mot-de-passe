"""
H4 — en-têtes de sécurité réellement servis en production (CSP stricte, HSTS,
force-HTTPS), sans casser le dev.

On teste la LOGIQUE des en-têtes en forçant ENVIRONMENT='production' sur une app
de test (DB sqlite valide, pas de fail-fast secrets), plus le fait que les
classes de config portent bien l'attribut ENVIRONMENT.
"""

import os
import re

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
    def test_prod_flask_delegates_security_headers_to_nginx(self):
        """PROD : Flask N'ÉMET PLUS les en-têtes de sécurité — source UNIQUE = nginx
        à l'edge (cf. TestNginxSecurityHeaders). Avant HSTS : Flask les servait AUSSI
        (duplication + incohérence preload nginx↔Flask). La redirection force-HTTPS,
        elle, reste côté Flask (cf. tests ci-dessous)."""
        client = _prod_headers_app().test_client()
        r = client.get(
            "/", base_url="https://localhost"
        )  # sécurisé → pas de redirection
        assert r.status_code == 200
        assert "Content-Security-Policy" not in r.headers
        assert "Strict-Transport-Security" not in r.headers
        assert "Permissions-Policy" not in r.headers
        assert "X-Frame-Options" not in r.headers

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
    def test_dev_serves_headers_but_no_hsts(self):
        """DEV/testing : pas de nginx frontal → Flask émet TOUJOURS les en-têtes
        (CSP présente, protection dev intacte) mais JAMAIS de HSTS ni redirection."""
        client = _wire_redis(create_app("testing")).test_client()
        r = client.get("/", base_url="http://localhost")
        assert r.status_code == 200
        assert "Content-Security-Policy" in r.headers  # dev toujours protégé par Flask
        assert "X-Frame-Options" in r.headers
        assert "Strict-Transport-Security" not in r.headers


_NGINX_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "nginx")


def _read_nginx(name):
    with open(os.path.join(_NGINX_DIR, name), encoding="utf-8") as f:
        return f.read()


def _header_value(conf, header):
    m = re.search(r"add_header\s+" + re.escape(header) + r'\s+"([^"]*)"', conf)
    return m.group(1) if m else None


class TestNginxSecurityHeaders:
    """HSTS : nginx est la SOURCE UNIQUE des en-têtes de sécurité en prod.
    Assertions statiques EXHAUSTIVES sur les fichiers de conf (nginx n'est pas
    exercé par pytest ; l'émission effective à l'exécution est prouvée par le run
    nginx + curl documenté au commit). Vérifie la PRÉSENCE de chaque en-tête ET
    l'ABSENCE de unsafe-inline sur script-src et de preload sur HSTS."""

    def _csp_directives(self):
        csp = _header_value(
            _read_nginx("security-headers.conf"), "Content-Security-Policy"
        )
        assert csp, "CSP absente du snippet nginx"
        directives = {}
        for part in csp.split(";"):
            part = part.strip()
            if part:
                directives[part.split()[0]] = part
        return directives

    def test_all_security_headers_present(self):
        h = _read_nginx("security-headers.conf")
        assert _header_value(h, "X-Frame-Options") == "DENY"
        assert _header_value(h, "X-Content-Type-Options") == "nosniff"
        assert _header_value(h, "X-XSS-Protection") == "1; mode=block"
        assert _header_value(h, "Referrer-Policy") == "strict-origin-when-cross-origin"
        pp = _header_value(h, "Permissions-Policy")
        assert pp and "camera=()" in pp and "geolocation=()" in pp  # valeur non vide
        assert _header_value(h, "Content-Security-Policy")
        assert _header_value(h, "Strict-Transport-Security")

    def test_hsts_exact_value_without_preload(self):
        hsts = _header_value(
            _read_nginx("security-headers.conf"), "Strict-Transport-Security"
        )
        assert (
            hsts == "max-age=31536000; includeSubDomains"
        )  # valeur exacte, SANS preload
        assert "preload" not in hsts

    def test_csp_script_src_self_without_unsafe_inline(self):
        d = self._csp_directives()
        assert d.get("default-src") == "default-src 'self'"
        script_src = d.get("script-src", "")
        assert "'self'" in script_src
        assert "unsafe-inline" not in script_src  # script-src strict
        assert "frame-ancestors 'none'" in "; ".join(d.values())
        # style-src conserve unsafe-inline (styles inline React) — garde-fou inchangé
        assert "unsafe-inline" in d.get("style-src", "")

    def test_api_responses_are_no_store(self):
        conf = _read_nginx("nginx.prod.conf")
        assert 'add_header Cache-Control "no-store"' in conf  # /api/ non cacheable
        # snippet ré-inclus dans les blocs à add_header propre (piège d'héritage nginx)
        assert conf.count("include /etc/nginx/security-headers.conf;") >= 3
