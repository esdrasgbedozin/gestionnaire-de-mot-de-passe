"""
Tests de la refonte cryptographique zero-knowledge (Lot 3 / C1).

Incrément (a) — schéma : les colonnes kdf_salt et wrapped_vault_key existent
sur le modèle User, sont nullables par défaut, et persistent en base.
"""

import pytest
from app_entry import create_app, db
from app.models import User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


class TestSchemaCrypto:
    """Incrément (a) : colonnes du modèle de chiffrement zero-knowledge."""

    def test_user_has_crypto_columns(self):
        """Le modèle User expose kdf_salt et wrapped_vault_key."""
        assert hasattr(User, "kdf_salt")
        assert hasattr(User, "wrapped_vault_key")

    def test_crypto_columns_default_to_none(self, app):
        """Un nouvel utilisateur a des colonnes crypto nulles tant qu'il n'est pas initialisé."""
        with app.app_context():
            user = User(
                email="schema@example.com", password="SchemaPass123!", username="schema"
            )
            db.session.add(user)
            db.session.commit()

            reloaded = User.query.filter_by(email="schema@example.com").first()
            assert reloaded.kdf_salt is None
            assert reloaded.wrapped_vault_key is None

    def test_crypto_columns_persist(self, app):
        """Les colonnes crypto persistent les valeurs écrites (bytes pour le sel, texte pour la VMK enveloppée)."""
        with app.app_context():
            user = User(
                email="persist@example.com",
                password="PersistPass123!",
                username="persist",
            )
            user.kdf_salt = (
                b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
            )
            user.wrapped_vault_key = "base64-wrapped-vmk-placeholder"
            db.session.add(user)
            db.session.commit()

            reloaded = User.query.filter_by(email="persist@example.com").first()
            assert reloaded.kdf_salt == bytes(range(16))
            assert reloaded.wrapped_vault_key == "base64-wrapped-vmk-placeholder"


import base64
from app.services.encryption_service import EncryptionService as E


class TestCryptoPrimitives:
    """Incrément (b) : KEK Argon2id + VMK enveloppée + chiffrement d'entrée."""

    SALT = b'0123456789abcdef'          # 16 octets
    SALT2 = b'fedcba9876543210'         # 16 octets, différent
    MP = 'Correct-Master-Password-42'

    def _nonce(self, token):
        return base64.b64decode(token.encode())[:E.GCM_NONCE_LENGTH]

    def test_kek_deterministic(self):
        """Même (master password, sel) → même KEK."""
        k1 = E.derive_kek(self.MP, self.SALT)
        k2 = E.derive_kek(self.MP, self.SALT)
        assert k1 == k2
        assert len(k1) == E.ARGON2_KEY_LENGTH

    def test_kek_different_salt_different_key(self):
        """Sels différents → KEK différentes."""
        assert E.derive_kek(self.MP, self.SALT) != E.derive_kek(self.MP, self.SALT2)

    def test_wrap_unwrap_roundtrip(self):
        """unwrap_vmk(wrap_vmk(vmk, kek), kek) == vmk."""
        kek = E.derive_kek(self.MP, self.SALT)
        vmk = E.generate_vmk()
        assert E.unwrap_vmk(E.wrap_vmk(vmk, kek), kek) == vmk

    def test_wrong_password_unwrap_fails(self):
        """Mauvais master password → unwrap échoue (tag GCM), aucune VMK silencieuse."""
        kek_good = E.derive_kek(self.MP, self.SALT)
        kek_bad = E.derive_kek('Wrong-Master-Password', self.SALT)
        wrapped = E.wrap_vmk(E.generate_vmk(), kek_good)
        with pytest.raises(ValueError):
            E.unwrap_vmk(wrapped, kek_bad)

    def test_entry_unique_iv_and_roundtrip(self):
        """Deux chiffrements du même clair → ciphertexts différents (IV unique) ; round-trip OK."""
        vmk = E.generate_vmk()
        c1 = E.encrypt_entry('s3cr3t-value', vmk)
        c2 = E.encrypt_entry('s3cr3t-value', vmk)
        assert c1 != c2                                   # IV différent → ciphertext différent
        assert self._nonce(c1) != self._nonce(c2)         # nonces distincts
        assert E.decrypt_entry(c1, vmk) == 's3cr3t-value'
        assert E.decrypt_entry(c2, vmk) == 's3cr3t-value'

    def test_entry_wrong_vmk_fails(self):
        """Déchiffrer une entrée avec une mauvaise VMK échoue proprement."""
        c = E.encrypt_entry('value', E.generate_vmk())
        with pytest.raises(ValueError):
            E.decrypt_entry(c, E.generate_vmk())

    def test_no_nonce_reuse(self):
        """wrap_vmk et encrypt_entry génèrent un nonce frais à chaque appel."""
        kek = E.derive_kek(self.MP, self.SALT)
        vmk = E.generate_vmk()
        wraps = {self._nonce(E.wrap_vmk(vmk, kek)) for _ in range(5)}
        entries = {self._nonce(E.encrypt_entry('x', vmk)) for _ in range(5)}
        assert len(wraps) == 5
        assert len(entries) == 5


import json
import time
import fakeredis
from app.services.session_key_store import SessionKeyStore, VaultLockedError


def _store(server=None):
    return SessionKeyStore(client=fakeredis.FakeStrictRedis(server=server))


class TestSessionKeyStore:
    """Incrément (c) : VMK détenue dans Redis le temps de la session."""

    def test_store_get_roundtrip(self):
        store = _store()
        vmk = E.generate_vmk()
        store.store_vmk('sess-1', vmk, 60)
        assert store.get_vmk('sess-1') == vmk

    def test_ttl_is_applied(self):
        store = _store()
        store.store_vmk('sess-ttl', E.generate_vmk(), 60)
        ttl = store._client.ttl('vault:vmk:sess-ttl')
        assert 0 < ttl <= 60

    def test_evict_removes_vmk(self):
        """Logout → VMK évincée → serveur incapable de déchiffrer."""
        store = _store()
        store.store_vmk('sess-2', E.generate_vmk(), 60)
        store.evict('sess-2')
        assert store.get_vmk('sess-2') is None

    def test_absent_raises_vault_locked(self):
        store = _store()
        with pytest.raises(VaultLockedError):
            store.get_required_vmk('does-not-exist')

    def test_expiry_then_locked(self):
        """Expiration TTL (simulée) → VMK absente → VaultLockedError (→ 423, pas 500)."""
        store = _store()
        store.store_vmk('sess-exp', E.generate_vmk(), 1)
        store._client.delete('vault:vmk:sess-exp')  # équivalent à l'expiration du TTL
        with pytest.raises(VaultLockedError):
            store.get_required_vmk('sess-exp')

    def test_multi_worker_shared(self):
        """Une VMK écrite par un worker est lisible par un autre (même Redis)."""
        server = fakeredis.FakeServer()
        worker_a = _store(server)
        worker_b = _store(server)
        vmk = E.generate_vmk()
        worker_a.store_vmk('shared', vmk, 60)
        assert worker_b.get_vmk('shared') == vmk

    def test_no_argon2_re_derivation_on_retrieval(self, monkeypatch):
        """PREUVE : la récupération de la VMK ne re-dérive JAMAIS la KEK (Argon2id)."""
        store = _store()
        vmk = E.generate_vmk()
        store.store_vmk('perf', vmk, 60)

        calls = {'n': 0}
        real = E.derive_kek

        def spy(*a, **k):
            calls['n'] += 1
            return real(*a, **k)

        monkeypatch.setattr(E, 'derive_kek', spy)
        t0 = time.perf_counter()
        for _ in range(50):
            assert store.get_vmk('perf') == vmk
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert calls['n'] == 0          # aucune dérivation Argon2id sur le chemin de lecture
        assert elapsed_ms < 149         # 50 lectures < le coût d'UNE seule dérivation Argon2id


class TestVaultLockedResponse:
    """La VMK absente produit un 423 « verrouillé », jamais un 500."""

    def test_absent_vmk_returns_423_not_500(self, app):
        store = _store()

        def locked_route():
            store.get_required_vmk('no-session')  # lève VaultLockedError
            return {'ok': True}

        app.add_url_rule('/__vault_locked_test__', 'vault_locked_test', locked_route)
        resp = app.test_client().get('/__vault_locked_test__')
        assert resp.status_code == 423
        assert json.loads(resp.data)['code'] == 'vault_locked'
