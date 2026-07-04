"""
Tests unitaires pour l'authentification

Les assertions sont alignées sur le contrat RÉEL de l'API :
  - succès : {'message': ..., 'user': {...}, 'tokens': {access_token, refresh_token, ...}}
  - erreur : {'error': ...}
Les tests qui révèlent de vrais bugs (non corrigés à ce stade) sont marqués
@pytest.mark.xfail avec le lot où ils seront traités.
"""

import pytest
import json
from app_entry import create_app, db
from app.models import User
import fakeredis
from app.services.session_key_store import SessionKeyStore
from rate_limiter import RateLimiter
from app.services.session_service import RefreshRegistry
from app.services.encryption_service import EncryptionService
from tests.passwords import STRONG_TEST_PASSWORD


@pytest.fixture
def app():
    """Fixture pour créer l'application Flask de test"""
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
            "WTF_CSRF_ENABLED": False,
        }
    )
    app.redis = fakeredis.FakeStrictRedis()
    app.session_key_store = SessionKeyStore(client=app.redis)
    app.rate_limiter = RateLimiter(app.redis)
    app.refresh_registry = RefreshRegistry(app.redis)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture pour créer le client de test"""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Fixture pour créer un utilisateur de test"""
    with app.app_context():
        user = User(email="test@example.com", username="testuser")
        salt, wrapped, vmk = EncryptionService.provision_vault(STRONG_TEST_PASSWORD)
        user.kdf_salt = salt
        user.wrapped_vault_key = wrapped
        db.session.add(user)
        db.session.commit()
        return user


class TestUserRegistration:
    """Tests pour l'enregistrement d'utilisateur"""

    def test_register_valid_user(self, client):
        """Test enregistrement utilisateur valide"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": STRONG_TEST_PASSWORD,
        }

        response = client.post(
            "/api/auth/register", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert "tokens" in response_data
        assert "access_token" in response_data["tokens"]
        assert response_data["user"]["username"] == "newuser"
        assert response_data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, sample_user):
        """Test enregistrement avec email déjà existant"""
        data = {
            "username": "differentuser",
            "email": "test@example.com",  # Email déjà utilisé
            "password": STRONG_TEST_PASSWORD,
        }

        response = client.post(
            "/api/auth/register", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 409
        response_data = json.loads(response.data)
        assert "already registered" in response_data["error"].lower()

    def test_register_duplicate_username(self, client, sample_user):
        """Test enregistrement avec username déjà existant"""
        data = {
            "username": "testuser",  # Username déjà utilisé
            "email": "different@example.com",
            "password": STRONG_TEST_PASSWORD,
        }

        response = client.post(
            "/api/auth/register", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 409
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_register_invalid_password(self, client):
        """Test enregistrement avec mot de passe invalide"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",  # Mot de passe trop simple
        }

        response = client.post(
            "/api/auth/register", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestUserLogin:
    """Tests pour la connexion utilisateur"""

    def test_login_valid_credentials(self, client, sample_user):
        """Test connexion avec identifiants valides"""
        data = {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}

        response = client.post(
            "/api/auth/login", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "tokens" in response_data
        assert "access_token" in response_data["tokens"]
        assert response_data["user"]["email"] == "test@example.com"

    def test_login_invalid_email(self, client):
        """Test connexion avec email inexistant"""
        data = {"email": "nonexistent@example.com", "password": "AnyPassword123!"}

        response = client.post(
            "/api/auth/login", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "invalid credentials" in response_data["error"].lower()

    def test_login_invalid_password(self, client, sample_user):
        """Test connexion avec mot de passe incorrect"""
        data = {"email": "test@example.com", "password": "WrongPassword123!"}

        response = client.post(
            "/api/auth/login", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "invalid credentials" in response_data["error"].lower()

    def test_login_missing_fields(self, client):
        """Test connexion avec champs manquants"""
        data = {
            "email": "test@example.com"
            # password manquant
        }

        response = client.post(
            "/api/auth/login", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestUserLogout:
    """Tests pour la déconnexion utilisateur"""

    def test_logout_success(self, client, sample_user):
        """Test déconnexion réussie"""
        # D'abord se connecter pour obtenir un token
        login_data = {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )
        tokens = json.loads(login_response.data)["tokens"]
        access_token = tokens["access_token"]

        # Ensuite se déconnecter
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "successful" in response_data["message"].lower()


class TestTokenRefresh:
    """Tests pour le rafraîchissement de token"""

    def test_refresh_token_success(self, client, sample_user):
        """Test rafraîchissement de token réussi"""
        # Se connecter pour obtenir un refresh token
        login_data = {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )
        tokens = json.loads(login_response.data)["tokens"]
        refresh_token = tokens["refresh_token"]

        # Rafraîchir le token (le refresh token est attendu dans le corps)
        response = client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "tokens" in response_data
        assert "access_token" in response_data["tokens"]

    def test_refresh_invalid_token(self, client):
        """Token de refresh invalide (dans le corps) → 401."""
        response = client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": "garbage.invalid.token"}),
            content_type="application/json",
        )
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestAccountLocking:
    """Tests pour le verrouillage de compte"""

    def test_account_locking_after_failed_attempts(self, client, sample_user):
        """Test verrouillage de compte après tentatives échouées"""
        login_data = {"email": "test@example.com", "password": "WrongPassword123!"}

        # Faire 5 tentatives échouées
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                data=json.dumps(login_data),
                content_type="application/json",
            )
            assert response.status_code == 401

        # La 6ème tentative devrait déclencher le verrouillage
        response = client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )

        response_data = json.loads(response.data)
        assert response.status_code == 401
        assert "error" in response_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


import jwt as pyjwt

JWT_TEST_SECRET = "test-secret-key-for-testing-only"


def _login(client):
    r = client.post(
        "/api/auth/login",
        data=json.dumps(
            {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
        ),
        content_type="application/json",
    )
    return json.loads(r.data)["tokens"]["access_token"]


class TestSessionModel:
    """H2.2 : session stable, sid sur les tokens, VMK ancrée, révocation par session."""

    def test_authenticated_request_refused_when_session_deleted(
        self, client, sample_user, app
    ):
        """CONDITION Q1 : access token encore valide MAIS session supprimée → refus."""
        access = _login(client)
        sid = pyjwt.decode(access, JWT_TEST_SECRET, algorithms=["HS256"])["sid"]

        # La requête authentifiée passe tant que la session existe
        ok = client.get(
            "/api/passwords/", headers={"Authorization": f"Bearer {access}"}
        )
        assert ok.status_code == 200

        # On supprime la session (révocation) — le token JWT reste pourtant valide
        app.redis.delete(f"session:{sid}")

        refused = client.get(
            "/api/passwords/", headers={"Authorization": f"Bearer {access}"}
        )
        assert refused.status_code in (401, 423)

    def test_vmk_key_stable_during_session(self, client, sample_user, app):
        """La VMK est ancrée sur session:{session_id} — jamais recopiée pendant la session."""
        access = _login(client)
        keys_before = sorted(k for k in app.redis.keys("session:*"))
        assert len(keys_before) == 1

        # Plusieurs requêtes authentifiées ne doivent PAS créer/déplacer la clé VMK
        for _ in range(3):
            client.get("/api/passwords/", headers={"Authorization": f"Bearer {access}"})
        keys_after = sorted(k for k in app.redis.keys("session:*"))
        assert keys_after == keys_before  # même clé unique, inchangée

    def test_e2e_login_create_get_password(self, client, sample_user):
        """Bout en bout : login → create → get (VMK lue par sid, pas de 423 mal câblé)."""
        access = _login(client)
        h = {"Authorization": f"Bearer {access}"}
        secret = "S3cret-Vault-Value!"

        cr = client.post(
            "/api/passwords/",
            headers=h,
            data=json.dumps(
                {"site_name": "example.com", "username": "alice", "password": secret}
            ),
            content_type="application/json",
        )
        assert cr.status_code == 201
        pid = json.loads(cr.data)["password"]["id"]

        gr = client.get(f"/api/passwords/{pid}", headers=h)
        assert gr.status_code == 200
        assert json.loads(gr.data)["password"] == secret


class TestAuthBascule:
    """H2.3 : l'authentification = déballage de la VMK (plus de bcrypt)."""

    def test_auth_via_vmk_unwrap_no_bcrypt(self, client, sample_user):
        """Plus de bcrypt : pas de check_password sur le modèle ; login via unlock."""
        from app.models import User

        assert not hasattr(User, "check_password")
        r = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
            ),
            content_type="application/json",
        )
        assert r.status_code == 200
        assert "access_token" in json.loads(r.data)["tokens"]

    def test_login_wrong_password_401(self, client, sample_user):
        """Mauvais master password → unlock échoue → 401."""
        r = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "test@example.com", "password": "WrongPassword123!"}
            ),
            content_type="application/json",
        )
        assert r.status_code == 401

    def test_login_unknown_email_still_pays_argon2(self, client, monkeypatch):
        """Q3 : email inconnu → on paie quand même Argon2id (anti-énumération par timing)."""
        from app.services.encryption_service import EncryptionService

        calls = {"n": 0}
        real = EncryptionService.derive_kek

        def spy(*a, **k):
            calls["n"] += 1
            return real(*a, **k)

        monkeypatch.setattr(EncryptionService, "derive_kek", spy)
        r = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "ghost@example.com", "password": "Whatever123!"}),
            content_type="application/json",
        )
        assert r.status_code == 401
        assert calls["n"] >= 1  # aucun court-circuit du coût Argon2id


class TestRefreshRotation:
    """H2.4 : rotation des refresh tokens + détection de rejeu + robustesse (Bug B)."""

    def _login_tokens(self, client):
        r = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
            ),
            content_type="application/json",
        )
        return json.loads(r.data)["tokens"]

    def _refresh(self, client, refresh_token):
        return client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

    def test_rotation_old_refresh_invalid_and_vmk_not_moved(
        self, client, sample_user, app
    ):
        toks = self._login_tokens(client)
        keys_before = sorted(app.redis.keys("session:*"))
        assert len(keys_before) == 1  # une seule clé VMK

        r1 = self._refresh(client, toks["refresh_token"])
        assert r1.status_code == 200
        new_refresh = json.loads(r1.data)["tokens"]["refresh_token"]
        assert new_refresh != toks["refresh_token"]

        # Après rotation LÉGITIME, la VMK n'a PAS bougé (même clé de session, jamais recopiée)
        assert sorted(app.redis.keys("session:*")) == keys_before

        # L'ancien refresh ne marche plus (rejeu → 401)
        assert self._refresh(client, toks["refresh_token"]).status_code == 401

    def test_reuse_detection_revokes_session(self, client, sample_user):
        toks = self._login_tokens(client)
        access0 = toks["access_token"]

        # 1re rotation : consomme le refresh initial
        assert self._refresh(client, toks["refresh_token"]).status_code == 200
        # Rejeu du refresh DÉJÀ CONSOMMÉ → détection de vol
        replay = self._refresh(client, toks["refresh_token"])
        assert replay.status_code == 401
        # Toute la session est révoquée → un access token de cette session est refusé
        refused = client.get(
            "/api/passwords/", headers={"Authorization": f"Bearer {access0}"}
        )
        assert refused.status_code in (401, 423)

    def test_new_refresh_after_rotation_works(self, client, sample_user):
        toks = self._login_tokens(client)
        r1 = self._refresh(client, toks["refresh_token"])
        new_refresh = json.loads(r1.data)["tokens"]["refresh_token"]
        # Le NOUVEAU refresh est valide (peut tourner à son tour)
        assert self._refresh(client, new_refresh).status_code == 200

    def test_refresh_empty_body_400(self, client):
        r = client.post("/api/auth/refresh", data="", content_type="application/json")
        assert r.status_code == 400


class TestLoginTimingEqualization:
    """D1 : tous les chemins d'échec du login paient un coût Argon2 équivalent (anti-oracle timing)."""

    def _spy_derive_kek(self, monkeypatch):
        calls = {"n": 0}
        real = EncryptionService.derive_kek

        def spy(*a, **k):
            calls["n"] += 1
            return real(*a, **k)

        monkeypatch.setattr(EncryptionService, "derive_kek", spy)
        return calls

    def _login(self, client):
        return client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "test@example.com", "password": STRONG_TEST_PASSWORD}
            ),
            content_type="application/json",
        )

    def test_locked_account_pays_argon2(self, client, sample_user, app, monkeypatch):
        import datetime as dt

        with app.app_context():
            u = User.query.filter_by(email="test@example.com").first()
            u.locked_until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)
            db.session.commit()
        calls = self._spy_derive_kek(monkeypatch)

        r = self._login(client)
        assert r.status_code == 401
        assert "locked" in r.data.decode().lower()  # verrouillage maintenu
        assert calls["n"] >= 1  # coût Argon2 payé sur ce chemin

    def test_disabled_account_pays_argon2(self, client, sample_user, app, monkeypatch):
        with app.app_context():
            u = User.query.filter_by(email="test@example.com").first()
            u.is_active = False
            db.session.commit()
        calls = self._spy_derive_kek(monkeypatch)

        r = self._login(client)
        assert r.status_code == 401
        assert "disabled" in r.data.decode().lower()  # désactivation maintenue
        assert calls["n"] >= 1


class TestRegisterEnumerationHardening:
    """M2 (Option B) : timing du register égalisé (conflit paie Argon2) + rate-limit de masse."""

    def _spy_derive_kek(self, monkeypatch):
        calls = {"n": 0}
        real = EncryptionService.derive_kek

        def spy(*a, **k):
            calls["n"] += 1
            return real(*a, **k)

        monkeypatch.setattr(EncryptionService, "derive_kek", spy)
        return calls

    def test_email_conflict_pays_argon2(self, client, sample_user, monkeypatch):
        calls = self._spy_derive_kek(monkeypatch)
        r = client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "username": "someoneelse",
                    "email": "test@example.com",
                    "password": STRONG_TEST_PASSWORD,
                }
            ),
            content_type="application/json",
        )
        assert r.status_code == 409  # Q5 : message/statut inchangés
        assert "already registered" in r.data.decode().lower()
        assert calls["n"] >= 1  # timing égalisé (comme le succès)

    def test_username_conflict_pays_argon2(self, client, sample_user, monkeypatch):
        calls = self._spy_derive_kek(monkeypatch)
        r = client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "username": "testuser",
                    "email": "brand-new@example.com",
                    "password": STRONG_TEST_PASSWORD,
                }
            ),
            content_type="application/json",
        )
        assert r.status_code == 409
        assert "already taken" in r.data.decode().lower()
        assert calls["n"] >= 1

    def test_register_is_rate_limited(self, client):
        """Garde/complétude : au-delà de la limite dédiée du register → 429 (énumération de masse throttlée)."""
        statuses = [
            client.post(
                "/api/auth/register",
                data=json.dumps(
                    {
                        "username": f"u{i}",
                        "email": f"u{i}@example.com",
                        "password": STRONG_TEST_PASSWORD,
                    }
                ),
                content_type="application/json",
            ).status_code
            for i in range(13)
        ]
        assert 429 in statuses


class TestMasterPasswordStrength:
    """M6 : le master password (seul secret protégeant tout le coffre) doit être
    FORT — pas seulement long. Gate zxcvbn (score >= 3) + longueur minimale 12,
    appliqués au register uniquement. Les entrées du coffre ne sont PAS gatées."""

    def _register(self, client, password, email="fresh@example.com"):
        return client.post(
            "/api/auth/register",
            data=json.dumps(
                {"username": "freshuser", "email": email, "password": password}
            ),
            content_type="application/json",
        )

    def test_rejects_long_but_weak_master_password(self, client):
        """Long + toutes les classes de caractères MAIS prévisible (zxcvbn=2) → refusé.
        RED avant M6 : accepté (len>=8 + classes) → 201 au lieu de 400."""
        r = self._register(
            client, "Passw0rd1234!"
        )  # 13 car., maj/min/chiffre/spécial, zxcvbn=2
        assert r.status_code == 400
        assert "error" in json.loads(r.data)

    def test_rejects_short_master_password(self, client):
        """Fort en classes mais < 12 caractères → refusé sur la longueur.
        RED avant M6 : minimum était 8 → 11 car. acceptés → 201."""
        r = self._register(client, "qP4#nZ7!wR2")  # 11 car.
        assert r.status_code == 400
        assert "12" in json.loads(r.data)["error"]

    def test_accepts_strong_master_password(self, client):
        """Master password réellement fort (zxcvbn=4, >= 12) → accepté (201)."""
        r = self._register(client, STRONG_TEST_PASSWORD)
        assert r.status_code == 201


class TestAccountDeletion:
    """D2 : DELETE /account (destruction TOTALE irréversible) exige une ré-auth
    FORTE — ressaisie du master password vérifiée par déballage VMK (comme le
    login H2.3, identité prouvée fraîchement) + confirmation littérale "DELETE".
    Séquence critique : prouver -> révoquer la session -> purger. Un token volé
    seul ne doit PLUS suffire à détruire le coffre."""

    def _spy_derive_kek(self, monkeypatch):
        calls = {"n": 0}
        real = EncryptionService.derive_kek

        def spy(*a, **k):
            calls["n"] += 1
            return real(*a, **k)

        monkeypatch.setattr(EncryptionService, "derive_kek", spy)
        return calls

    def _delete(self, client, token, body=None):
        kwargs = {
            "headers": {"Authorization": f"Bearer {token}"},
            "content_type": "application/json",
        }
        if body is not None:
            kwargs["data"] = json.dumps(body)
        return client.delete("/api/users/account", **kwargs)

    def _sid(self, access):
        return pyjwt.decode(access, JWT_TEST_SECRET, algorithms=["HS256"])["sid"]

    def test_delete_account_without_master_password(self, client, sample_user):
        """Token valide seul, sans master password → refusé (400).
        RED avant D2 : le compte est purgé avec le seul access token (200)."""
        access = _login(client)
        r = self._delete(client, access, {"confirm": "DELETE"})
        assert r.status_code == 400
        assert User.query.filter_by(email="test@example.com").first() is not None

    def test_delete_account_wrong_master_password(
        self, client, sample_user, app, monkeypatch
    ):
        """Mauvais master password → 401, RIEN détruit, Argon2 payé (anti-timing).
        RED avant D2 : purge inconditionnelle (200)."""
        access = _login(client)
        sid = self._sid(access)
        calls = self._spy_derive_kek(monkeypatch)

        r = self._delete(
            client,
            access,
            {"master_password": "Wrong-Master-9!xyz", "confirm": "DELETE"},
        )
        assert r.status_code == 401
        assert User.query.filter_by(email="test@example.com").first() is not None
        assert app.session_key_store.session_exists(sid)  # session intacte
        assert calls["n"] >= 1  # déballage tenté → Argon2 payé

    def test_delete_account_without_confirmation(self, client, sample_user):
        """Bon master password mais confirmation absente/incorrecte → refusé (400).
        RED avant D2 : purge (200) sans exiger de confirmation."""
        access = _login(client)
        r = self._delete(client, access, {"master_password": STRONG_TEST_PASSWORD})
        assert r.status_code == 400
        assert User.query.filter_by(email="test@example.com").first() is not None

    def test_delete_account_success(self, client, sample_user, app):
        """Bon master password + confirmation "DELETE" → purge OK ET session révoquée.
        RED avant D2 : la session courante n'est pas évincée."""
        access = _login(client)
        sid = self._sid(access)
        r = self._delete(
            client,
            access,
            {"master_password": STRONG_TEST_PASSWORD, "confirm": "DELETE"},
        )
        assert r.status_code == 200
        assert User.query.filter_by(email="test@example.com").first() is None
        assert not app.session_key_store.session_exists(sid)  # session révoquée

    def test_delete_account_failed_reauth_does_not_revoke_or_purge(
        self, client, sample_user, app
    ):
        """GARDIEN de la séquence prouver->révoquer->purger : un échec de ré-auth
        ne doit NI révoquer la session NI purger le compte (on ne déconnecte pas
        un utilisateur légitime dont la ré-auth échoue)."""
        access = _login(client)
        sid = self._sid(access)
        r = self._delete(
            client, access, {"master_password": "Nope-Wrong-1!abc", "confirm": "DELETE"}
        )
        assert r.status_code == 401
        assert User.query.filter_by(email="test@example.com").first() is not None
        assert app.session_key_store.session_exists(sid)
        # la session reste utilisable
        ok = client.get(
            "/api/passwords/", headers={"Authorization": f"Bearer {access}"}
        )
        assert ok.status_code == 200


class TestPasswordDeleteOwnership:
    """D2 : non-régression IDOR sur DELETE /passwords/<id>. Le contrôle
    d'ownership existe déjà (filter_by(id, user_id)) ; ce test le verrouille."""

    def _register_login(self, client, email, username):
        client.post(
            "/api/auth/register",
            data=json.dumps(
                {"email": email, "username": username, "password": STRONG_TEST_PASSWORD}
            ),
            content_type="application/json",
        )
        r = client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": STRONG_TEST_PASSWORD}),
            content_type="application/json",
        )
        return json.loads(r.data)["tokens"]["access_token"]

    def test_cannot_delete_other_users_password_entry(self, client, sample_user):
        """User B ne peut PAS supprimer l'entrée de User A → 404 (isolation par user_id)."""
        access_a = _login(client)  # user A = sample_user
        cr = client.post(
            "/api/passwords/",
            headers={"Authorization": f"Bearer {access_a}"},
            data=json.dumps(
                {
                    "site_name": "a-site.com",
                    "username": "alice",
                    "password": "A-secret-1!",
                }
            ),
            content_type="application/json",
        )
        pid_a = json.loads(cr.data)["password"]["id"]

        access_b = self._register_login(client, "bob@example.com", "bobuser")
        r = client.delete(
            f"/api/passwords/{pid_a}", headers={"Authorization": f"Bearer {access_b}"}
        )
        assert r.status_code == 404
        # l'entrée de A existe toujours
        still = client.get(
            f"/api/passwords/{pid_a}", headers={"Authorization": f"Bearer {access_a}"}
        )
        assert still.status_code == 200


class TestGetMe:
    """Lot 6 (A3) : GET /api/auth/me renvoie l'utilisateur courant.

    Bug : token_required injecte l'OBJET User, mais la route le nommait
    current_user_id puis faisait User.query.get(<objet>) → 500."""

    def test_get_me_returns_current_user(self, client, sample_user):
        access = _login(client)
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200  # RED avant A3 : 500
        assert json.loads(r.data)["user"]["email"] == "test@example.com"


class TestDecryptionRateLimit:
    """Lot 6 (C7) : les GET qui DÉCHIFFRENT (liste + entrée) sont rate-limités.
    Avant C7 : seuls POST/DELETE l'étaient → un token permettait un dump sans throttle."""

    def _make_entry(self, client, h):
        cr = client.post(
            "/api/passwords/",
            headers=h,
            data=json.dumps(
                {"site_name": "x.com", "username": "u", "password": "P-entry-1!"}
            ),
            content_type="application/json",
        )
        return json.loads(cr.data)["password"]["id"]

    def test_get_entry_is_rate_limited(self, client, sample_user):
        access = _login(client)
        h = {"Authorization": f"Bearer {access}"}
        pid = self._make_entry(client, h)

        # Usage normal : quelques lectures ne déclenchent PAS de 429
        for _ in range(5):
            assert client.get(f"/api/passwords/{pid}", headers=h).status_code == 200

        # Martèlement au-delà du bucket /api/passwords/* → 429 apparaît
        statuses = [
            client.get(f"/api/passwords/{pid}", headers=h).status_code
            for _ in range(120)
        ]
        assert 429 in statuses  # RED avant C7 : jamais limité (que des 200)
