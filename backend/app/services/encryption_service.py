"""
Service de chiffrement AES pour les mots de passe
"""

import base64
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets


class EncryptionService:
    """Service de chiffrement/déchiffrement AES-256-GCM"""
    
    # Paramètres de sécurité
    KEY_LENGTH = 32  # 256 bits
    IV_LENGTH = 16   # 128 bits
    SALT_LENGTH = 32 # 256 bits
    TAG_LENGTH = 16  # 128 bits
    PBKDF2_ITERATIONS = 100000  # Nombre d'itérations PBKDF2
    
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
    
    @staticmethod
    def generate_user_key(user_id: str, user_email: str) -> str:
        """
        Générer une clé utilisateur unique basée sur son ID et email
        Cette clé servira pour chiffrer/déchiffrer ses mots de passe
        """
        # Utiliser l'email comme base, qui est unique et stable
        combined = f"{user_id}:{user_email}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    @staticmethod
    def test_encryption():
        """Test rapide du service de chiffrement"""
        test_password = "MonMotDePasseSecretTest123!"
        user_key = "test_user_key_123"
        
        try:
            # Test chiffrement
            encrypted = EncryptionService.encrypt_password(test_password, user_key)
            print(f"✅ Chiffrement réussi: {encrypted[:50]}...")
            
            # Test déchiffrement
            decrypted = EncryptionService.decrypt_password(encrypted, user_key)
            print(f"✅ Déchiffrement réussi: {decrypted}")
            
            # Vérification
            assert test_password == decrypted, "Erreur: le mot de passe déchiffré ne correspond pas"
            print("✅ Test de chiffrement/déchiffrement réussi!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            return False


if __name__ == "__main__":
    # Test du service
    EncryptionService.test_encryption()