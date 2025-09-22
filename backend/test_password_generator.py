#!/usr/bin/env python3
"""
Test du générateur de mots de passe
"""

from app.services.password_generator import PasswordGenerator

def test_password_generator():
    print('🎲 Test du générateur de mots de passe...')
    
    # Test 1: Génération par défaut
    result = PasswordGenerator.generate()
    print(f'✓ Mot de passe par défaut: {result["password"]} (force: {result["strength"]}/5)')
    print(f'✓ Entropie: {result["entropy"]:.1f} bits')
    
    # Test 2: Génération avec paramètres personnalisés
    custom_result = PasswordGenerator.generate(
        length=20,
        include_uppercase=True,
        include_lowercase=True,
        include_digits=True,
        include_special=True
    )
    print(f'✓ Mot de passe 20 chars: {custom_result["password"]} (force: {custom_result["strength"]}/5)')
    
    # Test 3: Test des presets
    presets = PasswordGenerator.get_presets()
    print(f'✓ Presets disponibles: {list(presets.keys())}')
    
    weak_result = PasswordGenerator.generate(**presets['weak'])
    print(f'✓ Preset weak: {weak_result["password"]} (force: {weak_result["strength"]}/5)')
    
    strong_result = PasswordGenerator.generate(**presets['strong'])
    print(f'✓ Preset strong: {strong_result["password"]} (force: {strong_result["strength"]}/5)')
    
    # Test 4: Génération de passphrase
    passphrase_result = PasswordGenerator.generate_passphrase(word_count=4)
    print(f'✓ Passphrase: {passphrase_result["password"]} (mots: {passphrase_result["word_count"]})')
    
    # Test 5: Évaluation de force
    test_passwords = [
        '123456',
        'Password123',
        'Tr0ub4dor&3',
        'ComplexP@ssw0rd!'
    ]
    
    print('✓ Test évaluation de force:')
    for pwd in test_passwords:
        strength = PasswordGenerator.evaluate_strength(pwd)
        print(f'   "{pwd}" -> Force: {strength["strength"]}/5')
    
    print('🎉 Générateur de mots de passe validé!')

if __name__ == '__main__':
    test_password_generator()