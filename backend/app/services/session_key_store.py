"""
Session key store (Lot 3/C1 + Lot 4/H2.2) — la session détient la VMK.

Modèle :
- Clé Redis `session:{session_id}` → détient la VMK de la session.
- La VMK est ANCRÉE sur cette clé : elle n'est JAMAIS recopiée/déplacée
  (la rotation des refresh tokens ne déplace pas la VMK — cf. H2.4).
- TTL : inactivité glissante (ré-armée à chaque requête via `touch`) bornée par
  un plafond absolu. La valeur encode `base64(vmk)|deadline_absolu_epoch`.
- Existence de la clé = session active. Sa suppression (logout / lockout / rejeu)
  révoque la session : la VMK disparaît et toute requête authentifiée est refusée.

Persistance disque : Redis est configuré SANS RDB ni AOF (cf. docker-compose) →
la VMK ne touche jamais le disque. Sérialisation : VMK en base64.
"""

import base64
import time

from app.services.redis_client import make_redis_client

_SESSION_PREFIX = "session:"


class VaultLockedError(Exception):
    """Levée quand la session/VMK n'est pas/plus disponible (→ 423)."""


class SessionKeyStore:
    """Détient la VMK d'une session dans Redis (en mémoire, TTL glissant + plafond)."""

    def __init__(self, client=None):
        self._client = client or make_redis_client()

    @staticmethod
    def _key(session_id: str) -> str:
        return _SESSION_PREFIX + session_id

    def store_session(
        self, session_id: str, vmk: bytes, idle_ttl: int, absolute_ttl: int
    ) -> None:
        """Créer la session : ancre la VMK, fixe le plafond absolu, arme le TTL d'inactivité."""
        if not session_id:
            raise ValueError("session_id requis")
        if idle_ttl <= 0 or absolute_ttl <= 0:
            raise ValueError("ttl doit être positif")
        deadline = int(time.time()) + absolute_ttl
        value = base64.b64encode(vmk).decode("utf-8") + "|" + str(deadline)
        self._client.setex(self._key(session_id), min(idle_ttl, absolute_ttl), value)

    def _get_raw(self, session_id: str):
        """Retourne (vmk_b64, deadline) ou None. Supprime la clé si le plafond absolu est dépassé."""
        raw = self._client.get(self._key(session_id))
        if not raw:
            return None
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
        vmk_b64, _, deadline_s = text.partition("|")
        deadline = int(deadline_s)
        if time.time() > deadline:
            self._client.delete(self._key(session_id))  # plafond absolu atteint
            return None
        return vmk_b64, deadline

    def session_exists(self, session_id: str) -> bool:
        """Vraie ssi la session est encore active (clé présente et plafond non dépassé)."""
        if not session_id:
            return False
        return self._get_raw(session_id) is not None

    def touch(self, session_id: str, idle_ttl: int) -> bool:
        """Ré-arme le TTL d'inactivité, borné par le plafond absolu. False si session morte."""
        raw = self._get_raw(session_id)
        if raw is None:
            return False
        _, deadline = raw
        remaining = deadline - int(time.time())
        if remaining <= 0:
            self._client.delete(self._key(session_id))
            return False
        self._client.expire(self._key(session_id), min(idle_ttl, remaining))
        return True

    def get_vmk(self, session_id: str):
        """Relire la VMK (aucune dérivation Argon2id). None si session absente/expirée."""
        raw = self._get_raw(session_id)
        return base64.b64decode(raw[0]) if raw else None

    def get_required_vmk(self, session_id: str) -> bytes:
        """Comme get_vmk mais lève VaultLockedError si absente (→ 423, pas 500)."""
        vmk = self.get_vmk(session_id)
        if vmk is None:
            raise VaultLockedError(
                "Coffre verrouillé : reconnectez-vous pour le déverrouiller."
            )
        return vmk

    def evict(self, session_id: str) -> None:
        """Révoquer la session : supprime la clé → VMK évincée, requêtes refusées."""
        if session_id:
            self._client.delete(self._key(session_id))
