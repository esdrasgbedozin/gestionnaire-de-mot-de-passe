"""
Service de génération de mots de passe sécurisés
"""

import secrets
import string
import re
from typing import Dict, List, Optional

from zxcvbn import zxcvbn


class PasswordGenerator:
    """Générateur de mots de passe sécurisés"""

    # Sets de caractères
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    SPECIAL_CHARS_SAFE = "!@#$%^&*_+-="  # Caractères spéciaux sans ambiguïté
    AMBIGUOUS_CHARS = "0O1lI"  # Caractères ambigus à éviter

    # Mots de passe courants à éviter (extrait)
    COMMON_PASSWORDS = {
        "password",
        "123456",
        "123456789",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
        "shadow",
        "azerty",
        "motdepasse",
    }

    @staticmethod
    def generate(
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = True,
        safe_special_only: bool = False,
        min_uppercase: int = 1,
        min_lowercase: int = 1,
        min_digits: int = 1,
        min_special: int = 1,
    ) -> Dict[str, any]:
        """
        Générer un mot de passe sécurisé

        Args:
            length: Longueur du mot de passe (min 4, max 128)
            include_uppercase: Inclure majuscules
            include_lowercase: Inclure minuscules
            include_digits: Inclure chiffres
            include_special: Inclure caractères spéciaux
            exclude_ambiguous: Exclure caractères ambigus (0, O, 1, l, I)
            safe_special_only: Utiliser seulement les caractères spéciaux sûrs
            min_uppercase: Nombre minimum de majuscules
            min_lowercase: Nombre minimum de minuscules
            min_digits: Nombre minimum de chiffres
            min_special: Nombre minimum de caractères spéciaux

        Returns:
            Dict avec 'password', 'strength' et 'entropy'
        """
        # Validation des paramètres
        if length < 4:
            raise ValueError("La longueur minimale est de 4 caractères")
        if length > 128:
            raise ValueError("La longueur maximale est de 128 caractères")

        # Construire l'alphabet de caractères
        alphabet = ""
        required_chars = []

        if include_lowercase:
            chars = PasswordGenerator.LOWERCASE
            if exclude_ambiguous:
                chars = "".join(
                    c for c in chars if c not in PasswordGenerator.AMBIGUOUS_CHARS
                )
            alphabet += chars
            if min_lowercase > 0:
                required_chars.extend(
                    secrets.choice(chars) for _ in range(min_lowercase)
                )

        if include_uppercase:
            chars = PasswordGenerator.UPPERCASE
            if exclude_ambiguous:
                chars = "".join(
                    c for c in chars if c not in PasswordGenerator.AMBIGUOUS_CHARS
                )
            alphabet += chars
            if min_uppercase > 0:
                required_chars.extend(
                    secrets.choice(chars) for _ in range(min_uppercase)
                )

        if include_digits:
            chars = PasswordGenerator.DIGITS
            if exclude_ambiguous:
                chars = "".join(
                    c for c in chars if c not in PasswordGenerator.AMBIGUOUS_CHARS
                )
            alphabet += chars
            if min_digits > 0:
                required_chars.extend(secrets.choice(chars) for _ in range(min_digits))

        if include_special:
            chars = (
                PasswordGenerator.SPECIAL_CHARS_SAFE
                if safe_special_only
                else PasswordGenerator.SPECIAL_CHARS
            )
            alphabet += chars
            if min_special > 0:
                required_chars.extend(secrets.choice(chars) for _ in range(min_special))

        if not alphabet:
            raise ValueError("Au moins un type de caractère doit être sélectionné")

        # Vérifier que les exigences minimales ne dépassent pas la longueur
        total_required = len(required_chars)
        if total_required > length:
            raise ValueError(
                f"Les exigences minimales ({total_required}) dépassent la longueur demandée ({length})"
            )

        # Générer le reste du mot de passe
        remaining_length = length - total_required
        random_chars = [secrets.choice(alphabet) for _ in range(remaining_length)]

        # Combiner et mélanger
        all_chars = required_chars + random_chars
        password_list = list(all_chars)
        secrets.SystemRandom().shuffle(password_list)
        password = "".join(password_list)

        # Vérifier qu'il ne s'agit pas d'un mot de passe courant
        if password.lower() in PasswordGenerator.COMMON_PASSWORDS:
            # Régénérer récursivement
            return PasswordGenerator.generate(
                length,
                include_uppercase,
                include_lowercase,
                include_digits,
                include_special,
                exclude_ambiguous,
                safe_special_only,
                min_uppercase,
                min_lowercase,
                min_digits,
                min_special,
            )

        # Calculer la force et l'entropie
        strength_info = PasswordGenerator.evaluate_strength(password)

        return {
            "password": password,
            "strength": strength_info["strength"],
            "entropy": strength_info["entropy"],
            "feedback": strength_info["feedback"],
        }

    @staticmethod
    def evaluate_strength(password: str) -> Dict[str, any]:
        """
        Évaluer la force d'un mot de passe

        Returns:
            Dict avec 'strength' (1-5), 'entropy', et 'feedback'
        """
        if not password:
            return {"strength": 0, "entropy": 0, "feedback": ["Mot de passe vide"]}

        length = len(password)
        feedback = []

        # Calculer l'entropie
        alphabet_size = 0
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[^a-zA-Z0-9]", password))

        if has_lower:
            alphabet_size += 26
        if has_upper:
            alphabet_size += 26
        if has_digit:
            alphabet_size += 10
        if has_special:
            alphabet_size += 32  # Approximation

        import math

        entropy = length * math.log2(alphabet_size) if alphabet_size > 0 else 0

        # Force via zxcvbn (0-4) → échelle 1-5 du contrat. zxcvbn évalue la
        # DIFFICULTÉ DE DEVINE (dictionnaires, motifs, séquences, leetspeak),
        # pas seulement la diversité de caractères : un mot de passe « qui a l'air
        # complexe » mais prévisible est noté honnêtement (M6). L'entropie et les
        # drapeaux has_* restent calculés au-dessus pour l'affichage des consommateurs.
        z = zxcvbn(password)
        strength = z["score"] + 1  # 0..4 → 1..5

        warning = z["feedback"].get("warning")
        if warning:
            feedback.append(warning)
        feedback.extend(z["feedback"].get("suggestions", []))

        return {
            "strength": strength,
            "entropy": round(entropy, 1),
            "feedback": feedback,
            "has_lowercase": has_lower,
            "has_uppercase": has_upper,
            "has_digits": has_digit,
            "has_special": has_special,
            "length": length,
        }

    @staticmethod
    def generate_passphrase(
        word_count: int = 4,
        separator: str = "-",
        include_numbers: bool = True,
        capitalize_words: bool = True,
    ) -> Dict[str, any]:
        """
        Générer une phrase de passe (passphrase) mémorable

        Args:
            word_count: Nombre de mots (3-8)
            separator: Séparateur entre les mots
            include_numbers: Inclure des nombres
            capitalize_words: Mettre les mots en majuscule

        Returns:
            Dict avec la passphrase et ses métriques
        """
        if word_count < 3 or word_count > 8:
            raise ValueError("Le nombre de mots doit être entre 3 et 8")

        # Liste de mots courants mais sécurisés (normalement depuis un dictionnaire)
        words = [
            "ocean",
            "mountain",
            "forest",
            "river",
            "cloud",
            "storm",
            "lightning",
            "thunder",
            "crystal",
            "diamond",
            "golden",
            "silver",
            "bronze",
            "copper",
            "steel",
            "iron",
            "dragon",
            "phoenix",
            "eagle",
            "lion",
            "tiger",
            "wolf",
            "bear",
            "falcon",
            "castle",
            "tower",
            "bridge",
            "garden",
            "rainbow",
            "sunrise",
            "sunset",
            "moonlight",
            "whisper",
            "shadow",
            "mystery",
            "secret",
            "magic",
            "wonder",
            "dream",
            "vision",
            "journey",
            "adventure",
            "quest",
            "treasure",
            "legend",
            "story",
            "tale",
            "myth",
        ]

        # Sélectionner des mots aléatoires
        selected_words = [secrets.choice(words) for _ in range(word_count)]

        if capitalize_words:
            selected_words = [word.capitalize() for word in selected_words]

        # Ajouter des nombres si demandé
        if include_numbers:
            # Remplacer un mot par un nombre, ou l'ajouter
            if secrets.randbelow(2):  # 50% de chance
                selected_words[secrets.randbelow(len(selected_words))] = str(
                    secrets.randbelow(9999) + 1
                )
            else:
                selected_words.append(str(secrets.randbelow(999) + 1))

        passphrase = separator.join(selected_words)

        # Évaluer la force
        strength_info = PasswordGenerator.evaluate_strength(passphrase)

        return {
            "password": passphrase,
            "type": "passphrase",
            "word_count": len(selected_words),
            "strength": strength_info["strength"],
            "entropy": strength_info["entropy"],
            "feedback": strength_info["feedback"],
        }

    @staticmethod
    def get_presets() -> Dict[str, Dict]:
        """Retourner des presets de configuration courants"""
        return {
            "weak": {
                "length": 8,
                "include_uppercase": True,
                "include_lowercase": True,
                "include_digits": True,
                "include_special": False,
            },
            "medium": {
                "length": 12,
                "include_uppercase": True,
                "include_lowercase": True,
                "include_digits": True,
                "include_special": True,
                "safe_special_only": True,
            },
            "strong": {
                "length": 16,
                "include_uppercase": True,
                "include_lowercase": True,
                "include_digits": True,
                "include_special": True,
                "exclude_ambiguous": True,
                "min_special": 2,
            },
            "maximum": {
                "length": 24,
                "include_uppercase": True,
                "include_lowercase": True,
                "include_digits": True,
                "include_special": True,
                "exclude_ambiguous": True,
                "min_uppercase": 2,
                "min_lowercase": 2,
                "min_digits": 2,
                "min_special": 3,
            },
            "pin": {
                "length": 6,
                "include_uppercase": False,
                "include_lowercase": False,
                "include_digits": True,
                "include_special": False,
            },
        }


if __name__ == "__main__":
    # Tests du générateur
    generator = PasswordGenerator()

    print("🔐 Test du générateur de mots de passe\n")

    # Test avec différents presets
    for preset_name, preset_config in generator.get_presets().items():
        result = generator.generate(**preset_config)
        print(
            f"{preset_name.upper():>8}: {result['password']} (Force: {result['strength']}/5, Entropie: {result['entropy']})"
        )

    print(f"\n📝 Passphrase: {generator.generate_passphrase()['password']}")

    # Test d'évaluation
    test_passwords = [
        "123456",
        "Password123!",
        "Tr0ub4dor&3",
        "correct-horse-battery-staple",
    ]
    print("\n📊 Évaluation de mots de passe:")
    for pwd in test_passwords:
        strength = generator.evaluate_strength(pwd)
        print(f"{pwd:>30}: {strength['strength']}/5 (entropie: {strength['entropy']})")
