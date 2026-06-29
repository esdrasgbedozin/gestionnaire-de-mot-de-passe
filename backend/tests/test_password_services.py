"""
Tests des services Password Manager
"""

import sys
import os
import pytest

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.encryption_service import EncryptionService
from app.services.password_generator import PasswordGenerator


class TestEncryptionService:
    """Tests du service de chiffrement"""
    
    def test_encrypt_decrypt_password(self):
        """Test basique chiffrement/déchiffrement"""
        plaintext = "MonMotDePasseSecret123!"
        user_key = "test_user_key_123"
        
        # Chiffrement
        encrypted = EncryptionService.encrypt_password(plaintext, user_key)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        # Déchiffrement
        decrypted = EncryptionService.decrypt_password(encrypted, user_key)
        assert decrypted == plaintext
    
    def test_different_keys_produce_different_results(self):
        """Vérifier que des clés différentes produisent des résultats différents"""
        plaintext = "SamePassword123"
        key1 = "user_key_1"
        key2 = "user_key_2"
        
        encrypted1 = EncryptionService.encrypt_password(plaintext, key1)
        encrypted2 = EncryptionService.encrypt_password(plaintext, key2)
        
        assert encrypted1 != encrypted2
    
    def test_same_password_different_encryptions(self):
        """Vérifier que le même mot de passe produit des chiffrements différents (IV différents)"""
        plaintext = "SamePassword123"
        user_key = "same_key"
        
        encrypted1 = EncryptionService.encrypt_password(plaintext, user_key)
        encrypted2 = EncryptionService.encrypt_password(plaintext, user_key)
        
        # Doivent être différents à cause des IV aléatoires
        assert encrypted1 != encrypted2
        
        # Mais doivent se déchiffrer vers le même texte
        decrypted1 = EncryptionService.decrypt_password(encrypted1, user_key)
        decrypted2 = EncryptionService.decrypt_password(encrypted2, user_key)
        
        assert decrypted1 == decrypted2 == plaintext
    
    def test_invalid_key_fails(self):
        """Vérifier qu'une mauvaise clé échoue"""
        plaintext = "TestPassword123"
        correct_key = "correct_key"
        wrong_key = "wrong_key"
        
        encrypted = EncryptionService.encrypt_password(plaintext, correct_key)
        
        try:
            EncryptionService.decrypt_password(encrypted, wrong_key)
            assert False, "Devrait lever une exception avec une mauvaise clé"
        except ValueError:
            pass  # Attendu


class TestPasswordGenerator:
    """Tests du générateur de mots de passe"""
    
    def test_generate_default_password(self):
        """Test génération avec paramètres par défaut"""
        result = PasswordGenerator.generate()
        
        assert 'password' in result
        assert 'strength' in result
        assert 'entropy' in result
        assert 'feedback' in result
        
        password = result['password']
        assert len(password) == 16  # Longueur par défaut
        assert result['strength'] >= 1
        assert result['entropy'] > 0
    
    def test_generate_with_specific_length(self):
        """Test génération avec longueur spécifique"""
        for length in [8, 12, 20, 24]:
            result = PasswordGenerator.generate(length=length)
            assert len(result['password']) == length
    
    def test_generate_digits_only(self):
        """Test génération avec seulement des chiffres"""
        result = PasswordGenerator.generate(
            length=10,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=True,
            include_special=False
        )
        
        password = result['password']
        assert password.isdigit()
    
    @pytest.mark.xfail(reason="Évaluation de force trop laxiste (renvoie 1 pour un mot de passe moyen) — à corriger au Lot 5 (M6)")
    def test_password_strength_evaluation(self):
        """Test évaluation de force des mots de passe"""
        test_cases = [
            ("123456", 1),  # Très faible
            ("Password123", 3),  # Moyen
            ("Tr0ub4dor&3", 4),  # Fort
            ("X#9$mP2!vR8@nQ5z", 5),  # Très fort
        ]
        
        for password, expected_min_strength in test_cases:
            result = PasswordGenerator.evaluate_strength(password)
            assert result['strength'] >= expected_min_strength
    
    def test_generate_passphrase(self):
        """Test génération de passphrase"""
        result = PasswordGenerator.generate_passphrase()
        
        assert 'password' in result
        assert 'type' in result
        assert result['type'] == 'passphrase'
        assert 'word_count' in result
        
        # Devrait contenir des séparateurs
        assert '-' in result['password']
    
    def test_presets(self):
        """Test des presets de génération"""
        presets = PasswordGenerator.get_presets()
        
        assert 'weak' in presets
        assert 'strong' in presets
        assert 'maximum' in presets
        
        # Tester un preset
        weak_result = PasswordGenerator.generate(**presets['weak'])
        assert len(weak_result['password']) == 8
    
    def test_validate_parameters(self):
        """Test validation des paramètres"""
        # Longueur trop courte
        try:
            PasswordGenerator.generate(length=2)
            assert False, "Devrait lever une exception pour longueur trop courte"
        except ValueError:
            pass
        
        # Longueur trop longue
        try:
            PasswordGenerator.generate(length=200)
            assert False, "Devrait lever une exception pour longueur trop longue"
        except ValueError:
            pass
        
        # Aucun type de caractère sélectionné
        try:
            PasswordGenerator.generate(
                include_uppercase=False,
                include_lowercase=False,
                include_digits=False,
                include_special=False
            )
            assert False, "Devrait lever une exception si aucun type de caractère"
        except ValueError:
            pass


if __name__ == "__main__":
    # Tests rapides
    print("🧪 Tests des services Password Manager")
    
    # Test chiffrement
    print("\n🔐 Test service de chiffrement...")
    try:
        test_enc = TestEncryptionService()
        test_enc.test_encrypt_decrypt_password()
        test_enc.test_different_keys_produce_different_results()
        test_enc.test_same_password_different_encryptions()
        print("✅ Service de chiffrement : OK")
    except Exception as e:
        print(f"❌ Service de chiffrement : {e}")
    
    # Test générateur
    print("\n🎲 Test générateur de mots de passe...")
    try:
        test_gen = TestPasswordGenerator()
        test_gen.test_generate_default_password()
        test_gen.test_generate_with_specific_length()
        test_gen.test_password_strength_evaluation()
        test_gen.test_generate_passphrase()
        print("✅ Générateur de mots de passe : OK")
    except Exception as e:
        print(f"❌ Générateur de mots de passe : {e}")
    
    print("\n🎉 Tests terminés !")