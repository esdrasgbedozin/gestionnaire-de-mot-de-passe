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
