"""
Tests de la refonte cryptographique zero-knowledge (Lot 3 / C1).

Incrément (a) — schéma : les colonnes kdf_salt et wrapped_vault_key existent
sur le modèle User (non-nullable) et persistent en base.
"""

import pytest
from app_entry import create_app, db
from app.models import User
import fakeredis
from app.services.session_key_store import SessionKeyStore
from rate_limiter import RateLimiter


@pytest.fixture
def app():
    app = create_app("testing")
    app.redis = fakeredis.FakeStrictRedis()
    app.session_key_store = SessionKeyStore(client=app.redis)
    app.rate_limiter = RateLimiter(app.redis)
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
        store.store_session('sess-1', vmk, 60, 60)
        assert store.get_vmk('sess-1') == vmk

    def test_ttl_is_applied(self):
        store = _store()
        store.store_session('sess-ttl', E.generate_vmk(), 60, 60)
        ttl = store._client.ttl('session:sess-ttl')
        assert 0 < ttl <= 60

    def test_evict_removes_vmk(self):
        """Logout → VMK évincée → serveur incapable de déchiffrer."""
        store = _store()
        store.store_session('sess-2', E.generate_vmk(), 60, 60)
        store.evict('sess-2')
        assert store.get_vmk('sess-2') is None

    def test_absent_raises_vault_locked(self):
        store = _store()
        with pytest.raises(VaultLockedError):
            store.get_required_vmk('does-not-exist')

    def test_expiry_then_locked(self):
        """Expiration TTL (simulée) → VMK absente → VaultLockedError (→ 423, pas 500)."""
        store = _store()
        store.store_session('sess-exp', E.generate_vmk(), 1, 1)
        store._client.delete('session:sess-exp')  # équivalent à l'expiration du TTL
        with pytest.raises(VaultLockedError):
            store.get_required_vmk('sess-exp')

    def test_multi_worker_shared(self):
        """Une VMK écrite par un worker est lisible par un autre (même Redis)."""
        server = fakeredis.FakeServer()
        worker_a = _store(server)
        worker_b = _store(server)
        vmk = E.generate_vmk()
        worker_a.store_session('shared', vmk, 60, 60)
        assert worker_b.get_vmk('shared') == vmk

    def test_no_argon2_re_derivation_on_retrieval(self, monkeypatch):
        """PREUVE : la récupération de la VMK ne re-dérive JAMAIS la KEK (Argon2id)."""
        store = _store()
        vmk = E.generate_vmk()
        store.store_session('perf', vmk, 60, 60)

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


import hashlib
import secrets as _secrets
from app.models import Password


class TestC1Proofs:
    """Les 4 preuves obligatoires que C1 (zero-knowledge at rest) est corrigée."""

    MP = 'Master-Correct-Horse-9!'
    SECRET = 'my-vault-entry-s3cret-value'

    def _provision_user_with_entry(self, app):
        """État réaliste : un User provisionné + une entrée chiffrée, persistés en base."""
        with app.app_context():
            salt, wrapped, vmk = E.provision_vault(self.MP)
            user = User(email='proof@example.com', password=self.MP, username='proof')
            user.kdf_salt = salt
            user.wrapped_vault_key = wrapped
            db.session.add(user)
            db.session.commit()
            ciphertext = E.encrypt_entry(self.SECRET, vmk)
            entry = Password(
                user_id=user.id, site_name='example.com',
                username='alice', encrypted_password=ciphertext,
            )
            db.session.add(entry)
            db.session.commit()
            return user.id, entry.id

    def test_a_decrypt_with_correct_master_password(self, app):
        """(a) Avec le bon master password : entrée relue en clair."""
        uid, eid = self._provision_user_with_entry(app)
        with app.app_context():
            user = User.query.get(uid)
            entry = Password.query.get(eid)
            vmk = E.unlock_vault(user.kdf_salt, user.wrapped_vault_key, self.MP)
            assert E.decrypt_entry(entry.encrypted_password, vmk) == self.SECRET

    def test_b_db_dump_cannot_decrypt_without_master_password(self, app):
        """(b) PREUVE REINE : tout le contenu de la base ne déchiffre RIEN sans le master password."""
        uid, eid = self._provision_user_with_entry(app)
        with app.app_context():
            user = User.query.get(uid)
            entry = Password.query.get(eid)
            # Le « dump » : exactement ce qui est stocké en base + données publiques
            kdf_salt = user.kdf_salt
            wrapped_vmk = user.wrapped_vault_key
            ciphertext = entry.encrypted_password
            user_id, email = str(user.id), user.email

            # (1) Sans master password → pas de KEK → impossible de désenvelopper la VMK
            with pytest.raises(ValueError):
                E.unwrap_vmk(wrapped_vmk, _secrets.token_bytes(32))

            # (2) L'ANCIENNE attaque SHA256(user_id:email) (données publiques) ne redonne PLUS la clé
            legacy_key = hashlib.sha256(f"{user_id}:{email}".encode()).digest()
            with pytest.raises(ValueError):
                E.decrypt_entry(ciphertext, legacy_key)
            with pytest.raises(ValueError):
                E.unwrap_vmk(wrapped_vmk, legacy_key)

            # (3) Le ciphertext ne contient pas le clair
            assert self.SECRET not in ciphertext
            assert self.SECRET.encode() not in base64.b64decode(ciphertext)

            # (4) MAIS avec le master password, tout se déverrouille (contrôle positif)
            vmk = E.unlock_vault(kdf_salt, wrapped_vmk, self.MP)
            assert E.decrypt_entry(ciphertext, vmk) == self.SECRET

    def test_c_email_change_keeps_decryptable(self, app):
        """(c) Changement d'email → entrées toujours déchiffrables (email hors dérivation)."""
        uid, eid = self._provision_user_with_entry(app)
        with app.app_context():
            user = User.query.get(uid)
            user.email = 'brand-new-email@example.com'
            db.session.commit()

            user = User.query.get(uid)
            entry = Password.query.get(eid)
            vmk = E.unlock_vault(user.kdf_salt, user.wrapped_vault_key, self.MP)
            assert E.decrypt_entry(entry.encrypted_password, vmk) == self.SECRET

    def test_d_master_password_change_no_reencryption(self, app):
        """(d) Changement de master password → entrées NON re-chiffrées (seule la VMK l'est)."""
        uid, eid = self._provision_user_with_entry(app)
        new_mp = 'A-Totally-New-Master-Pw-42!'
        with app.app_context():
            user = User.query.get(uid)
            entry = Password.query.get(eid)
            ct_before = entry.encrypted_password

            # Déverrouiller avec l'ancien MP, puis re-wrap UNIQUEMENT la VMK
            vmk = E.unlock_vault(user.kdf_salt, user.wrapped_vault_key, self.MP)
            new_salt, new_wrapped = E.rewrap_vault(vmk, new_mp)
            user.kdf_salt = new_salt
            user.wrapped_vault_key = new_wrapped
            db.session.commit()

            entry = Password.query.get(eid)
            # (1) l'entrée n'a PAS été re-chiffrée
            assert entry.encrypted_password == ct_before
            # (2) déchiffrable avec le NOUVEAU master password
            user = User.query.get(uid)
            vmk2 = E.unlock_vault(user.kdf_salt, user.wrapped_vault_key, new_mp)
            assert E.decrypt_entry(entry.encrypted_password, vmk2) == self.SECRET
            # (3) l'ANCIEN master password ne déverrouille plus
            with pytest.raises(ValueError):
                E.unlock_vault(user.kdf_salt, user.wrapped_vault_key, self.MP)


class TestSharedRedis:
    """H2.0 : un client Redis unique partagé par l'app et ses services."""

    def test_session_store_uses_shared_app_redis(self, app):
        """Le session key store doit pointer sur le client Redis partagé app.redis."""
        assert app.redis is app.session_key_store._client
