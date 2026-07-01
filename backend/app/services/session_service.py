"""
Registre des refresh tokens (Lot 4 / H2.4) — rotation + détection de rejeu.

Modèle : une clé Redis `valid_refresh:{jti}` existe SSI ce jti est le refresh
actuellement valide de sa session (sa valeur = session_id, TTL = durée de vie du
refresh). À la rotation, on **renomme** atomiquement la clé de l'ancien jti vers
le nouveau : l'ancien devient invalide et le nouveau valide en une seule
opération (RENAME) — pas de fenêtre où les deux sont valides, ni aucun des deux.

Détection de rejeu : présenter un refresh dont le jti n'a plus de clé (déjà
consommé par une rotation) = signal de vol → l'appelant révoque toute la session
(suppression de `session:{sid}` → VMK évincée + famille morte).
"""

from redis import exceptions as redis_exceptions

from app.services.redis_client import make_redis_client

_VALID_REFRESH_PREFIX = "valid_refresh:"


class RefreshRegistry:
    """Suivi du refresh token valide par session, avec rotation atomique."""

    def __init__(self, client=None):
        self._client = client or make_redis_client()

    @staticmethod
    def _key(jti: str) -> str:
        return _VALID_REFRESH_PREFIX + jti

    def register(self, jti: str, session_id: str, ttl_seconds: int) -> None:
        """Enregistrer un jti de refresh comme valide pour la session."""
        self._client.setex(self._key(jti), ttl_seconds, session_id)

    def rotate(self, old_jti: str, new_jti: str) -> bool:
        """Consommer old_jti et publier new_jti ATOMIQUEMENT (RENAME).

        Retourne True si old_jti était valide (rotation faite), False sinon
        (jti déjà consommé / inexistant → rejeu à traiter par l'appelant).
        Le new_jti hérite du TTL restant → borné par le plafond de session.
        """
        try:
            self._client.rename(self._key(old_jti), self._key(new_jti))
            return True
        except redis_exceptions.ResponseError:
            # "no such key" : old_jti n'est plus le refresh valide → rejeu
            return False

    def revoke(self, jti: str) -> None:
        """Invalider un jti de refresh (best-effort)."""
        self._client.delete(self._key(jti))
