"""
Service de chiffrement AES pour les mots de passe
"""

import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type


class EncryptionService:
    """Service de chiffrement/déchiffrement AES-256-GCM"""
    
    # Paramètres de sécurité
    KEY_LENGTH = 32  # 256 bits
    IV_LENGTH = 16   # 128 bits
    SALT_LENGTH = 32 # 256 bits
    TAG_LENGTH = 16  # 128 bits
    PBKDF2_ITERATIONS = 100000  # Nombre d'itérations PBKDF2

    # --- Zero-knowledge (Lot 3 / C1) ---
    VMK_LENGTH = 32          # Vault Master Key : 256 bits
    GCM_NONCE_LENGTH = 12    # Nonce AES-GCM : 96 bits (recommandation NIST)
    # Paramètres Argon2id (configurables par variables d'environnement)
    ARGON2_MEMORY_KIB = int(os.environ.get('ARGON2_MEMORY_KIB', 196608))  # 192 MiB (benchmark ~160 ms, cible 100-250 ms)
    ARGON2_TIME_COST = int(os.environ.get('ARGON2_TIME_COST', 3))
    ARGON2_PARALLELISM = int(os.environ.get('ARGON2_PARALLELISM', 2))
    ARGON2_KEY_LENGTH = 32   # KEK : 256 bits
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Dériver une clé de chiffrement à partir d'un mot de passe et d'un salt
        en utilisant PBKDF2
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=EncryptionService.KEY_LENGTH,
            salt=salt,
            iterations=EncryptionService.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        
        return kdf.derive(password)

    # ==================================================================
    # Zero-knowledge (Lot 3 / C1) : KEK Argon2id + VMK enveloppee (AES-GCM)
    # Format AES-GCM commun : base64( nonce(12) || ciphertext || tag(16) )
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

    @staticmethod
    def _aesgcm_encrypt(key: bytes, plaintext: bytes) -> str:
        """AES-256-GCM avec nonce frais. Retourne base64(nonce || ciphertext || tag)."""
        nonce = secrets.token_bytes(EncryptionService.GCM_NONCE_LENGTH)
        ct = AESGCM(key).encrypt(nonce, plaintext, None)  # ct = ciphertext || tag
        return base64.b64encode(nonce + ct).decode("utf-8")

    @staticmethod
    def _aesgcm_decrypt(key: bytes, token: str) -> bytes:
        """Inverse de _aesgcm_encrypt. Leve ValueError si le tag GCM est invalide."""
        raw = base64.b64decode(token.encode("utf-8"))
        nonce = raw[:EncryptionService.GCM_NONCE_LENGTH]
        ct = raw[EncryptionService.GCM_NONCE_LENGTH:]
        try:
            return AESGCM(key).decrypt(nonce, ct, None)
        except Exception:
            # Ne JAMAIS divulguer la cle / le master password dans l'erreur
            raise ValueError("Dechiffrement impossible (cle invalide ou donnees alterees)")

    @staticmethod
    def wrap_vmk(vmk: bytes, kek: bytes) -> str:
        """Envelopper (chiffrer) la VMK avec la KEK."""
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_encrypt(kek, vmk)

    @staticmethod
    def unwrap_vmk(wrapped: str, kek: bytes) -> bytes:
        """Desenvelopper la VMK. Un mauvais master password (mauvaise KEK) leve ValueError
        car le tag GCM rejette : aucune VMK corrompue n'est renvoyee silencieusement."""
        vmk = EncryptionService._aesgcm_decrypt(kek, wrapped)
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK desenveloppee invalide")
        return vmk

    @staticmethod
    def encrypt_entry(plaintext: str, vmk: bytes) -> str:
        """Chiffrer une entree du coffre avec la VMK brute (AES-256-GCM, nonce unique)."""
        if not plaintext:
            raise ValueError("texte vide")
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_encrypt(vmk, plaintext.encode("utf-8"))

    @staticmethod
    def decrypt_entry(token: str, vmk: bytes) -> str:
        """Dechiffrer une entree du coffre avec la VMK."""
        if len(vmk) != EncryptionService.VMK_LENGTH:
            raise ValueError("VMK invalide")
        return EncryptionService._aesgcm_decrypt(vmk, token).decode("utf-8")
    
    @staticmethod
    def encrypt_password(plaintext: str, user_key: str) -> str:
        """
        Chiffrer un mot de passe avec AES-256-GCM
        
        Args:
            plaintext: Le mot de passe en clair
            user_key: La clé utilisateur (généralement dérivée de son mot de passe principal)
            
        Returns:
            String base64 contenant: salt + iv + tag + ciphertext
        """
        if not plaintext or not user_key:
            raise ValueError("Le texte et la clé ne peuvent pas être vides")
        
        # Générer un salt aléatoire pour cette opération
        salt = secrets.token_bytes(EncryptionService.SALT_LENGTH)
        
        # Dériver la clé de chiffrement
        key = EncryptionService.derive_key(user_key, salt)
        
        # Générer un IV aléatoire
        iv = secrets.token_bytes(EncryptionService.IV_LENGTH)
        
        # Chiffrer avec AES-256-GCM
        cipher = Cipher(
            algorithms.AES(key), 
            modes.GCM(iv), 
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Convertir le plaintext en bytes
        plaintext_bytes = plaintext.encode('utf-8')
        
        # Chiffrement
        ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()
        
        # Récupérer le tag d'authentification
        tag = encryptor.tag
        
        # Combiner salt + iv + tag + ciphertext
        encrypted_data = salt + iv + tag + ciphertext
        
        # Encoder en base64 pour stockage
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    @staticmethod
    def decrypt_password(encrypted_data: str, user_key: str) -> str:
        """
        Déchiffrer un mot de passe
        
        Args:
            encrypted_data: String base64 contenant salt + iv + tag + ciphertext
            user_key: La clé utilisateur
            
        Returns:
            Le mot de passe en clair
        """
        if not encrypted_data or not user_key:
            raise ValueError("Les données chiffrées et la clé ne peuvent pas être vides")
        
        try:
            # Décoder depuis base64
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extraire les composants
            salt = data[:EncryptionService.SALT_LENGTH]
            iv = data[EncryptionService.SALT_LENGTH:EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH]
            tag = data[EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH:EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH + EncryptionService.TAG_LENGTH]
            ciphertext = data[EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH + EncryptionService.TAG_LENGTH:]
            
            # Dériver la clé de déchiffrement
            key = EncryptionService.derive_key(user_key, salt)
            
            # Déchiffrer avec AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key), 
                modes.GCM(iv, tag), 
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Déchiffrement
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext_bytes.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Erreur lors du déchiffrement: {str(e)}")

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
