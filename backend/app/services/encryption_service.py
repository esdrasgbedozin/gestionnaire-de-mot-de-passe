"""
Service de chiffrement AES pour les mots de passe
"""

import base64
import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type


class EncryptionService:
    """Service de chiffrement/déchiffrement AES-256-GCM"""

    # --- Zero-knowledge (Lot 3 / C1) ---
    VMK_LENGTH = 32  # Vault Master Key : 256 bits
    GCM_NONCE_LENGTH = 12  # Nonce AES-GCM : 96 bits (recommandation NIST)
    # Paramètres Argon2id (configurables par variables d'environnement)
    ARGON2_MEMORY_KIB = int(
        os.environ.get("ARGON2_MEMORY_KIB", 196608)
    )  # 192 MiB (benchmark ~160 ms, cible 100-250 ms)
    ARGON2_TIME_COST = int(os.environ.get("ARGON2_TIME_COST", 3))
    ARGON2_PARALLELISM = int(os.environ.get("ARGON2_PARALLELISM", 2))
    ARGON2_KEY_LENGTH = 32  # KEK : 256 bits

    # Octet de version du format AEAD (B6). v1 préfixe un octet ; v0 (legacy) n'en
    # a pas (son 1er octet est un octet de nonce aléatoire). L'octet n'est qu'un
    # FAST-PATH de routage : le tag GCM reste l'arbitre (fallback v0 si le tag v1
    # échoue), si bien qu'aucune donnée v0 ne devient illisible.
    AEAD_VERSION_V1 = 0x01

    # ==================================================================
    # Zero-knowledge (Lot 3 / C1) : KEK Argon2id + VMK enveloppee (AES-GCM)
    # Format v1 : base64( 0x01 || nonce(12) || ciphertext || tag(16) )
    # Format v0 (legacy) : base64( nonce(12) || ciphertext || tag(16) )
    # ==================================================================

    @staticmethod
    def derive_kek(master_password: str, salt: bytes) -> bytes:
        """Deriver la Key-Encryption-Key depuis le master password via Argon2id.

        La KEK ne sert qu'a envelopper/desenvelopper la VMK ; elle n'est jamais
        stockee. Parametres configurables via les constantes ARGON2_*.
        """
        if not master_password:
            raise ValueError("master_password requis")
        if not salt or len(salt) < 16:
            raise ValueError("sel invalide (>= 16 octets requis)")
        return hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt,
            time_cost=EncryptionService.ARGON2_TIME_COST,
            memory_cost=EncryptionService.ARGON2_MEMORY_KIB,
            parallelism=EncryptionService.ARGON2_PARALLELISM,
            hash_len=EncryptionService.ARGON2_KEY_LENGTH,
            type=Type.ID,
        )

    @staticmethod
    def generate_vmk() -> bytes:
        """Generer une Vault Master Key aleatoire (256 bits)."""
        return secrets.token_bytes(EncryptionService.VMK_LENGTH)

    # Domaine AAD du wrapped_VMK (B6 b). Constante : la KEK isole déjà par
    # utilisateur (Argon2id + sel) ; l'AAD n'ajoute qu'une séparation de domaine.
    _AAD_VMK = b"vmk"

    @staticmethod
    def _aesgcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = None) -> str:
        """AES-256-GCM, nonce frais, format v1 : base64( 0x01 || nonce(12) || ct || tag ).

        B6 (b) : `aad` (associated data) lie le ciphertext à son contexte — le tag
        GCM couvre l'AAD, donc un blob ne peut plus être déplacé vers un autre
        contexte. `aad=None` = pas de binding (blobs de l'incrément (a)).
        """
        nonce = secrets.token_bytes(EncryptionService.GCM_NONCE_LENGTH)
        ct = AESGCM(key).encrypt(nonce, plaintext, aad)  # ct = ciphertext || tag
        blob = bytes([EncryptionService.AEAD_VERSION_V1]) + nonce + ct
        return base64.b64encode(blob).decode("utf-8")

    @staticmethod
    def _aesgcm_decrypt(key: bytes, token: str, aad: bytes = None) -> bytes:
        """Inverse de _aesgcm_encrypt, routage v1/v0 ; le tag GCM est l'ARBITRE.

        - 1er octet == 0x01 → v1 : tente l'AAD attendue, puis `None` (blob (a)-era
          à AAD vide) ; si aucune n'authentifie → peut être un v0 dont le nonce
          commençait par 0x01 → fallback v0.
        - sinon → v0 (AAD toujours None ; un v1 commence toujours par 0x01).
        L'anti-déplacement tient : un blob lié à un contexte X échoue sous tout
        autre contexte ET sous None. Aucune donnée v0/(a) ne devient illisible.
        """
        raw = base64.b64decode(token.encode("utf-8"))
        N = EncryptionService.GCM_NONCE_LENGTH

        if raw and raw[0] == EncryptionService.AEAD_VERSION_V1:
            nonce, ct = raw[1 : 1 + N], raw[1 + N :]
            candidates = [aad] if aad is None else [aad, None]
            for candidate in candidates:
                try:
                    return AESGCM(key).decrypt(nonce, ct, candidate)
                except Exception:
                    pass  # essaie la suivante, puis fallback v0

        try:
            return AESGCM(key).decrypt(raw[:N], raw[N:], None)
        except Exception:
            # Ne JAMAIS divulguer la cle / le master password dans l'erreur
            raise ValueError(
                "Dechiffrement impossible (cle invalide ou donnees alterees)"
            )

    @staticmethod
    def is_legacy_entry(token: str) -> bool:
        """True si le blob n'est PAS au format v1 (donc candidat au backfill v1).
        Détection déterministe par l'octet de version, sans crypto."""
        raw = base64.b64decode(token.encode("utf-8"))
        return not (raw and raw[0] == EncryptionService.AEAD_VERSION_V1)

    @staticmethod
    def wrap_vmk(vmk: bytes, kek: bytes) -> str:
        """Envelopper (chiffrer) la VMK avec la KEK (AAD = domaine b"vmk")."""
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_encrypt(kek, vmk, EncryptionService._AAD_VMK)

    @staticmethod
    def unwrap_vmk(wrapped: str, kek: bytes) -> bytes:
        """Desenvelopper la VMK. Un mauvais master password (mauvaise KEK) leve ValueError
        car le tag GCM rejette : aucune VMK corrompue n'est renvoyee silencieusement.
        AAD b"vmk" attendue ; le legacy (v0/(a) sans domaine) reste géré (fallback None)."""
        vmk = EncryptionService._aesgcm_decrypt(
            kek, wrapped, EncryptionService._AAD_VMK
        )
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK desenveloppee invalide")
        return vmk

    @staticmethod
    def encrypt_entry(plaintext: str, vmk: bytes, aad: bytes = None) -> str:
        """Chiffrer une entree du coffre avec la VMK (AES-256-GCM, nonce unique).

        `aad` = contexte de l'entrée (ex. b"user_id:entry_id") pour lier le
        ciphertext à sa ligne — passé par la route. None = pas de binding.
        """
        if not plaintext:
            raise ValueError("texte vide")
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_encrypt(vmk, plaintext.encode("utf-8"), aad)

    @staticmethod
    def decrypt_entry(token: str, vmk: bytes, aad: bytes = None) -> str:
        """Dechiffrer une entree du coffre avec la VMK. `aad` = contexte attendu
        (reconstruit à l'identique depuis la ligne : b"user_id:entry_id")."""
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_decrypt(vmk, token, aad).decode("utf-8")

    # ==================================================================
    # Choreographie du coffre (Lot 3 / C1)
    # ==================================================================

    @staticmethod
    def provision_vault(master_password: str):
        """Inscription : genere sel + VMK, derive la KEK, enveloppe la VMK.

        Retourne (kdf_salt: bytes(16), wrapped_vmk: str, vmk: bytes(32)).
        La VMK est aleatoire et NE depend PAS de donnees publiques.
        """
        salt = secrets.token_bytes(16)
        vmk = EncryptionService.generate_vmk()
        kek = EncryptionService.derive_kek(master_password, salt)
        wrapped = EncryptionService.wrap_vmk(vmk, kek)
        return salt, wrapped, vmk

    @staticmethod
    def unlock_vault(kdf_salt: bytes, wrapped_vmk: str, master_password: str) -> bytes:
        """Login : derive la KEK depuis le master password et desenveloppe la VMK.

        Leve ValueError si le master password est incorrect (tag GCM invalide).
        """
        kek = EncryptionService.derive_kek(master_password, kdf_salt)
        return EncryptionService.unwrap_vmk(wrapped_vmk, kek)

    @staticmethod
    def rewrap_vault(vmk: bytes, new_master_password: str):
        """Changement de master password : nouveau sel + nouvelle KEK, re-enveloppe
        la MEME VMK. Les entrees du coffre ne sont PAS re-chiffrees.

        Retourne (new_kdf_salt: bytes(16), new_wrapped_vmk: str).
        """
        salt = secrets.token_bytes(16)
        kek = EncryptionService.derive_kek(new_master_password, salt)
        return salt, EncryptionService.wrap_vmk(vmk, kek)

    @staticmethod
    def waste_argon2():
        """Consommer un cout Argon2id equivalent a un login (anti-enumeration timing).

        Appele quand l'email est inconnu : le temps de reponse d'un login echoue
        devient indistinguable entre compte existant et inexistant.
        """
        EncryptionService.derive_kek("timing-equalizer", b"\x00" * 16)
