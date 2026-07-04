"""
Tests des services Password Manager
"""

import sys
import os
import pytest

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.password_generator import PasswordGenerator


class TestPasswordGenerator:
    """Tests du générateur de mots de passe"""

    def test_generate_default_password(self):
        """Test génération avec paramètres par défaut"""
        result = PasswordGenerator.generate()

        assert "password" in result
        assert "strength" in result
        assert "entropy" in result
        assert "feedback" in result

        password = result["password"]
        assert len(password) == 16  # Longueur par défaut
        assert result["strength"] >= 1
        assert result["entropy"] > 0

    def test_generate_with_specific_length(self):
        """Test génération avec longueur spécifique"""
        for length in [8, 12, 20, 24]:
            result = PasswordGenerator.generate(length=length)
            assert len(result["password"]) == length

    def test_generate_digits_only(self):
        """Test génération avec seulement des chiffres"""
        result = PasswordGenerator.generate(
            length=10,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=True,
            include_special=False,
        )

        password = result["password"]
        assert password.isdigit()

    def test_password_strength_evaluation(self):
        """Le meter reflète la VRAIE robustesse (zxcvbn 0-4 → échelle 1-5).

        M6 : l'ancienne évaluation était laxiste (majorée par les seules classes
        de caractères). Ici les attentes reflètent la difficulté de DEVINE (zxcvbn),
        pas la simple diversité de caractères.
        """
        # Bornes hautes : un mot de passe faible ne doit PAS être noté fort.
        assert PasswordGenerator.evaluate_strength("123456")["strength"] <= 1
        assert PasswordGenerator.evaluate_strength("Password123")["strength"] <= 2
        # Un vrai aléatoire est au sommet de l'échelle.
        assert PasswordGenerator.evaluate_strength("X#9$mP2!vR8@nQ5z")["strength"] == 5

        # DISCRIMINANT (le cœur de M6) : « a l'air complexe » (13 car., 4 classes)
        # mais prévisible (base type "password" + suffixe). L'ANCIEN scorer, majoré
        # par les classes de caractères, le notait 4 (« fort ») — c'est la laxité.
        # zxcvbn le capture comme devinable → <= 3. La borne <= 3 est ROUGE avec
        # l'ancien scorer (=4) et VERTE avec zxcvbn (=3).
        looks_complex_but_weak = PasswordGenerator.evaluate_strength("Passw0rd1234!")[
            "strength"
        ]
        truly_random = PasswordGenerator.evaluate_strength("X#9$mP2!vR8@nQ5z")[
            "strength"
        ]
        assert looks_complex_but_weak <= 3
        assert looks_complex_but_weak < truly_random

    def test_generate_passphrase(self):
        """Test génération de passphrase"""
        result = PasswordGenerator.generate_passphrase()

        assert "password" in result
        assert "type" in result
        assert result["type"] == "passphrase"
        assert "word_count" in result

        # Devrait contenir des séparateurs
        assert "-" in result["password"]

    def test_presets(self):
        """Test des presets de génération"""
        presets = PasswordGenerator.get_presets()

        assert "weak" in presets
        assert "strong" in presets
        assert "maximum" in presets

        # Tester un preset
        weak_result = PasswordGenerator.generate(**presets["weak"])
        assert len(weak_result["password"]) == 8

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
                include_special=False,
            )
            assert False, "Devrait lever une exception si aucun type de caractère"
        except ValueError:
            pass


if __name__ == "__main__":
    # Tests rapides
    print("🧪 Tests des services Password Manager")

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
