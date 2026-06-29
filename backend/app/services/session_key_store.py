"""
Session key store (Lot 3 / C1) — détention de la VMK pendant une session.

La VMK (Vault Master Key) est dérivée UNE seule fois au login (déverrouillage
de la VMK enveloppée via la KEK Argon2id), puis conservée ici, indexée par la
session (jti du token). Les requêtes suivantes la relisent depuis Redis — il n'y
a JAMAIS de re-dérivation Argon2id par requête.

Garanties :
- TTL = durée de vie du token → la VMK expire automatiquement.
- Éviction explicite au logout.
- Si la VMK est absente (expiration, logout, Redis vidé/redémarré) →
  VaultLockedError, que l'application traduit en réponse 423 « coffre verrouillé »
  (jamais un 500).

Persistance disque : Redis est configuré SANS RDB ni AOF (cf. docker-compose,
`--save "" --appendonly no`) → la VMK ne touche jamais le disque ; elle ne vit
qu'en mémoire le temps du TTL. C'est le compromis « zero-knowledge at rest ».

Sérialisation : la VMK (bytes) est encodée en base64 pour le transport Redis.
"""

import base64
import os

import redis

_KEY_PREFIX = "vault:vmk:"


class VaultLockedError(Exception):
    """Levée quand la VMK n'est pas/plus disponible pour la session courante."""


class SessionKeyStore:
    """Stocke la VMK d'une session dans Redis (en mémoire, TTL court)."""

    def __init__(self, client=None):
        # client injectable (fakeredis en test) ; sinon connexion réelle via REDIS_URL
        self._client = client or redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )

    @staticmethod
    def _key(session_id: str) -> str:
        return _KEY_PREFIX + session_id

    def store_vmk(self, session_id: str, vmk: bytes, ttl_seconds: int) -> None:
        """Stocker la VMK pour la session, avec expiration = TTL du token."""
        if not session_id:
            raise ValueError("session_id requis")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds doit être positif")
        self._client.setex(self._key(session_id), ttl_seconds, base64.b64encode(vmk))

    def get_vmk(self, session_id: str):
        """Relire la VMK depuis Redis (aucune dérivation Argon2id). None si absente."""
        raw = self._client.get(self._key(session_id))
        return base64.b64decode(raw) if raw else None

    def get_required_vmk(self, session_id: str) -> bytes:
        """Comme get_vmk mais lève VaultLockedError si absente (→ 423, pas 500)."""
        vmk = self.get_vmk(session_id)
        if vmk is None:
            raise VaultLockedError(
                "Coffre verrouillé : reconnectez-vous pour le déverrouiller."
            )
        return vmk

    def evict(self, session_id: str) -> None:
        """Supprimer la VMK (logout). Le serveur redevient incapable de déchiffrer."""
        self._client.delete(self._key(session_id))
