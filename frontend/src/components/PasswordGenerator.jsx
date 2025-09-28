import React, { useState, useCallback } from 'react';
import {
  XMarkIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  CheckIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const PasswordGenerator = ({ onClose, onUsePassword }) => {
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [options, setOptions] = useState({
    length: 16,
    includeUppercase: true,
    includeLowercase: true,
    includeNumbers: true,
    includeSymbols: true,
    excludeSimilar: true,
    excludeAmbiguous: false
  });
  const [passwordStrength, setPasswordStrength] = useState({ level: 0, text: 'Aucun', color: 'gray' });

  // Générer le mot de passe initial au montage du composant
  React.useEffect(() => {
    generatePassword();
  }, []);

  // Calculer la force du mot de passe
  const calculatePasswordStrength = useCallback((password) => {
    if (!password) return { level: 0, text: 'Aucun', color: 'gray' };
    
    let score = 0;
    let feedback = [];

    // Longueur
    if (password.length >= 8) score++;
    if (password.length >= 12) score += 2;
    if (password.length >= 16) score++;
    
    // Types de caractères
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score += 2;

    // Entropie (variété)
    const uniqueChars = new Set(password).size;
    if (uniqueChars / password.length > 0.7) score++;

    // Patterns courants (pénalités)
    if (/(.)\1{2,}/.test(password)) score--; // Répétitions
    if (/123|abc|qwerty/i.test(password)) score--; // Séquences

    const maxScore = 10;
    const percentage = Math.max(0, Math.min(100, (score / maxScore) * 100));

    if (percentage < 30) return { level: 1, text: 'Très faible', color: 'red', percentage };
    if (percentage < 50) return { level: 2, text: 'Faible', color: 'orange', percentage };
    if (percentage < 70) return { level: 3, text: 'Moyen', color: 'yellow', percentage };
    if (percentage < 85) return { level: 4, text: 'Fort', color: 'green', percentage };
    return { level: 5, text: 'Très fort', color: 'emerald', percentage };
  }, []);

  const generatePassword = useCallback(() => {
    let charset = '';
    
    if (options.includeLowercase) charset += 'abcdefghijklmnopqrstuvwxyz';
    if (options.includeUppercase) charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (options.includeNumbers) charset += '0123456789';
    if (options.includeSymbols) charset += '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    if (options.excludeSimilar) {
      charset = charset.replace(/[il1Lo0O]/g, '');
    }
    
    if (options.excludeAmbiguous) {
      charset = charset.replace(/[{}[\]()\/\\'"~,;.<>]/g, '');
    }

    if (charset === '') {
      toast.error('Please select at least one character type');
      return;
    }

    // Générer le mot de passe
    const array = new Uint8Array(options.length);
    crypto.getRandomValues(array);
    
    let result = '';
    for (let i = 0; i < options.length; i++) {
      result += charset[array[i] % charset.length];
    }

    // S'assurer qu'au moins un caractère de chaque type sélectionné est présent
    if (options.includeUppercase && !/[A-Z]/.test(result)) {
      const upperChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      const randomIndex = Math.floor(Math.random() * result.length);
      result = result.substring(0, randomIndex) + upperChars[Math.floor(Math.random() * upperChars.length)] + result.substring(randomIndex + 1);
    }
    
    if (options.includeLowercase && !/[a-z]/.test(result)) {
      const lowerChars = 'abcdefghijklmnopqrstuvwxyz';
      const randomIndex = Math.floor(Math.random() * result.length);
      result = result.substring(0, randomIndex) + lowerChars[Math.floor(Math.random() * lowerChars.length)] + result.substring(randomIndex + 1);
    }
    
    if (options.includeNumbers && !/[0-9]/.test(result)) {
      const numberChars = '0123456789';
      const randomIndex = Math.floor(Math.random() * result.length);
      result = result.substring(0, randomIndex) + numberChars[Math.floor(Math.random() * numberChars.length)] + result.substring(randomIndex + 1);
    }
    
    if (options.includeSymbols && !/[^A-Za-z0-9]/.test(result)) {
      const symbolChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      const randomIndex = Math.floor(Math.random() * result.length);
      result = result.substring(0, randomIndex) + symbolChars[Math.floor(Math.random() * symbolChars.length)] + result.substring(randomIndex + 1);
    }

    setGeneratedPassword(result);
    setPasswordStrength(calculatePasswordStrength(result));
  }, [options, calculatePasswordStrength]);

  // Régénérer quand les options changent
  React.useEffect(() => {
    if (generatedPassword) {
      generatePassword();
    }
  }, [options, generatePassword]);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generatedPassword);
      toast.success('Password copied to clipboard');
    } catch (error) {
      console.error('Erreur lors de la copie:', error);
      toast.error('Failed to copy password to clipboard');
    }
  };

  const handleOptionChange = (option, value) => {
    setOptions(prev => ({
      ...prev,
      [option]: value
    }));
  };

  const presets = [
    { name: 'Basique', length: 12, includeUppercase: true, includeLowercase: true, includeNumbers: true, includeSymbols: false },
    { name: 'Sécurisé', length: 16, includeUppercase: true, includeLowercase: true, includeNumbers: true, includeSymbols: true },
    { name: 'Ultra sécurisé', length: 24, includeUppercase: true, includeLowercase: true, includeNumbers: true, includeSymbols: true },
    { name: 'PIN', length: 6, includeUppercase: false, includeLowercase: false, includeNumbers: true, includeSymbols: false }
  ];

  const applyPreset = (preset) => {
    setOptions({
      ...options,
      ...preset,
      excludeSimilar: options.excludeSimilar,
      excludeAmbiguous: options.excludeAmbiguous
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* En-tête */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <AdjustmentsHorizontalIcon className="h-6 w-6 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Générateur de mots de passe
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Mot de passe généré */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password generated
            </label>
            <div className="relative">
              <input
                type="text"
                value={generatedPassword}
                readOnly
                className="w-full px-4 py-3 pr-24 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-3">
                <button
                  onClick={copyToClipboard}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                  title="Copier"
                >
                  <DocumentDuplicateIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={generatePassword}
                  className="p-2 text-indigo-400 hover:text-indigo-600 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900"
                  title="Générer nouveau"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Indicateur de force */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-600 dark:text-gray-400">Force du mot de passe:</span>
                <span className={`font-medium ${
                  passwordStrength.color === 'emerald' ? 'text-emerald-600' :
                  passwordStrength.color === 'green' ? 'text-green-600' :
                  passwordStrength.color === 'yellow' ? 'text-yellow-600' :
                  passwordStrength.color === 'orange' ? 'text-orange-600' :
                  passwordStrength.color === 'red' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {passwordStrength.text} ({Math.round(passwordStrength.percentage || 0)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${
                    passwordStrength.color === 'emerald' ? 'bg-emerald-500' :
                    passwordStrength.color === 'green' ? 'bg-green-500' :
                    passwordStrength.color === 'yellow' ? 'bg-yellow-500' :
                    passwordStrength.color === 'orange' ? 'bg-orange-500' :
                    passwordStrength.color === 'red' ? 'bg-red-500' :
                    'bg-gray-500'
                  }`}
                  style={{ width: `${passwordStrength.percentage || 0}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Presets rapides */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Modèles prédéfinis
            </label>
            <div className="grid grid-cols-2 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => applyPreset(preset)}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-indigo-500"
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Longueur */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Longueur: {options.length} caractères
            </label>
            <input
              type="range"
              min="6"
              max="64"
              value={options.length}
              onChange={(e) => handleOptionChange('length', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>6</span>
              <span>16</span>
              <span>32</span>
              <span>64</span>
            </div>
          </div>

          {/* Options de caractères */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Types de caractères
            </label>
            <div className="space-y-3">
              {[
                { key: 'includeUppercase', label: 'Majuscules (A-Z)', example: 'ABCDEFG...' },
                { key: 'includeLowercase', label: 'Minuscules (a-z)', example: 'abcdefg...' },
                { key: 'includeNumbers', label: 'Chiffres (0-9)', example: '0123456...' },
                { key: 'includeSymbols', label: 'Symboles (!@#...)', example: '!@#$%^&...' }
              ].map((option) => (
                <div key={option.key} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      id={option.key}
                      checked={options[option.key]}
                      onChange={(e) => handleOptionChange(option.key, e.target.checked)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                    />
                    <div>
                      <label htmlFor={option.key} className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {option.label}
                      </label>
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {option.example}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Options avancées */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Options avancées
            </label>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label htmlFor="excludeSimilar" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Exclure les caractères similaires
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Éviter i, l, 1, L, o, 0, O
                  </p>
                </div>
                <input
                  type="checkbox"
                  id="excludeSimilar"
                  checked={options.excludeSimilar}
                  onChange={(e) => handleOptionChange('excludeSimilar', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label htmlFor="excludeAmbiguous" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Exclure les caractères ambigus
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Éviter {`{ } [ ] ( ) / \\ ' " ~ , ; . < >`}
                  </p>
                </div>
                <input
                  type="checkbox"
                  id="excludeAmbiguous"
                  checked={options.excludeAmbiguous}
                  onChange={(e) => handleOptionChange('excludeAmbiguous', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                />
              </div>
            </div>
          </div>

          {/* Boutons d'action */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-gray-500"
            >
              Fermer
            </button>
            {onUsePassword && (
              <button
                onClick={() => onUsePassword(generatedPassword)}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 flex items-center"
              >
                <CheckIcon className="h-4 w-4 mr-2" />
                Utiliser ce mot de passe
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasswordGenerator;