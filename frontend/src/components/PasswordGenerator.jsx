import React, { useState, useCallback } from "react";
import {
  XMarkIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  CheckIcon,
  AdjustmentsHorizontalIcon,
} from "@heroicons/react/24/outline";
import { toast } from "react-hot-toast";
import { evaluateStrength } from "../utils/passwordStrength";
import Button from "./ui/Button";

// Entier aléatoire CSPRNG dans [0, max[ — jamais Math.random() pour du matériel
// de mot de passe (y compris la garantie "au moins un char par classe").
const secureIndex = (max) => {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0] % max;
};

const PasswordGenerator = ({ onClose, onUsePassword }) => {
  const [generatedPassword, setGeneratedPassword] = useState("");
  const [options, setOptions] = useState({
    length: 16,
    includeUppercase: true,
    includeLowercase: true,
    includeNumbers: true,
    includeSymbols: true,
    excludeSimilar: true,
    excludeAmbiguous: false,
  });
  const [passwordStrength, setPasswordStrength] = useState({
    level: 0,
    text: "None",
    color: "gray",
  });

  // Générer le mot de passe initial au montage du composant
  React.useEffect(() => {
    generatePassword();
  }, []);

  // Force via le moteur UNIQUE (zxcvbn) — même mesure et même vocabulaire partout.
  const calculatePasswordStrength = useCallback((password) => {
    const s = evaluateStrength(password);
    return { text: s.label, color: s.color, percentage: s.percent };
  }, []);

  const generatePassword = useCallback(() => {
    let charset = "";

    if (options.includeLowercase) charset += "abcdefghijklmnopqrstuvwxyz";
    if (options.includeUppercase) charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    if (options.includeNumbers) charset += "0123456789";
    if (options.includeSymbols) charset += "!@#$%^&*()_+-=[]{}|;:,.<>?";

    if (options.excludeSimilar) {
      charset = charset.replace(/[il1Lo0O]/g, "");
    }

    if (options.excludeAmbiguous) {
      charset = charset.replace(/[{}[\]()\/\\'"~,;.<>]/g, "");
    }

    if (charset === "") {
      toast.error("Please select at least one character type");
      return;
    }

    // Génération robuste : 1 caractère requis par classe sélectionnée (garantit
    // la couverture), on complète depuis l'ensemble complet, puis on mélange
    // (Fisher-Yates). Tout via secureIndex → pas de biais Uint8, et la garantie
    // de classe ne peut plus être écrasée par un insert ultérieur.
    const requiredPools = [];
    if (options.includeLowercase)
      requiredPools.push("abcdefghijklmnopqrstuvwxyz");
    if (options.includeUppercase)
      requiredPools.push("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
    if (options.includeNumbers) requiredPools.push("0123456789");
    if (options.includeSymbols)
      requiredPools.push("!@#$%^&*()_+-=[]{}|;:,.<>?");
    // Appliquer les mêmes exclusions que `charset` à chaque pool.
    const pools = requiredPools
      .map((p) =>
        Array.from(p)
          .filter((c) => charset.includes(c))
          .join(""),
      )
      .filter((p) => p.length > 0);

    const chars = [];
    for (const pool of pools) {
      if (chars.length >= options.length) break; // longueur < nb de classes
      chars.push(pool[secureIndex(pool.length)]);
    }
    while (chars.length < options.length) {
      chars.push(charset[secureIndex(charset.length)]);
    }
    // Mélange Fisher-Yates (CSPRNG) : les chars requis ne restent pas en tête.
    for (let i = chars.length - 1; i > 0; i--) {
      const j = secureIndex(i + 1);
      [chars[i], chars[j]] = [chars[j], chars[i]];
    }
    const result = chars.join("");

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
      toast.success("Password copied to clipboard");
    } catch (error) {
      console.error("Erreur lors de la copie:", error);
      toast.error("Failed to copy password to clipboard");
    }
  };

  const handleOptionChange = (option, value) => {
    setOptions((prev) => ({
      ...prev,
      [option]: value,
    }));
  };

  const presets = [
    {
      name: "Basic",
      length: 12,
      includeUppercase: true,
      includeLowercase: true,
      includeNumbers: true,
      includeSymbols: false,
    },
    {
      name: "Secure",
      length: 16,
      includeUppercase: true,
      includeLowercase: true,
      includeNumbers: true,
      includeSymbols: true,
    },
    {
      name: "Ultra secure",
      length: 24,
      includeUppercase: true,
      includeLowercase: true,
      includeNumbers: true,
      includeSymbols: true,
    },
    {
      name: "PIN",
      length: 6,
      includeUppercase: false,
      includeLowercase: false,
      includeNumbers: true,
      includeSymbols: false,
    },
  ];

  const applyPreset = (preset) => {
    setOptions({
      ...options,
      ...preset,
      excludeSimilar: options.excludeSimilar,
      excludeAmbiguous: options.excludeAmbiguous,
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
              Password generator
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
                  aria-label="Copy generated password"
                  title="Copy"
                >
                  <DocumentDuplicateIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={generatePassword}
                  className="p-2 text-indigo-400 hover:text-indigo-600 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900"
                  aria-label="Generate a new password"
                  title="Generate new"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Indicateur de force */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-600 dark:text-gray-400">
                  Password strength:
                </span>
                <span
                  className={`font-medium ${
                    passwordStrength.color === "green"
                      ? "text-green-600"
                      : passwordStrength.color === "yellow"
                        ? "text-yellow-700 dark:text-yellow-500"
                        : passwordStrength.color === "red"
                          ? "text-red-600"
                          : "text-gray-600"
                  }`}
                >
                  {passwordStrength.text} (
                  {Math.round(passwordStrength.percentage || 0)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${
                    passwordStrength.color === "green"
                      ? "bg-green-500"
                      : passwordStrength.color === "yellow"
                        ? "bg-yellow-500"
                        : passwordStrength.color === "red"
                          ? "bg-red-500"
                          : "bg-gray-500"
                  }`}
                  style={{ width: `${passwordStrength.percentage || 0}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Presets rapides */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Presets
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
              Length: {options.length} characters
            </label>
            <input
              type="range"
              min="6"
              max="64"
              value={options.length}
              onChange={(e) =>
                handleOptionChange("length", parseInt(e.target.value))
              }
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
              Character types
            </label>
            <div className="space-y-3">
              {[
                {
                  key: "includeUppercase",
                  label: "Uppercase (A-Z)",
                  example: "ABCDEFG...",
                },
                {
                  key: "includeLowercase",
                  label: "Lowercase (a-z)",
                  example: "abcdefg...",
                },
                {
                  key: "includeNumbers",
                  label: "Numbers (0-9)",
                  example: "0123456...",
                },
                {
                  key: "includeSymbols",
                  label: "Symbols (!@#...)",
                  example: "!@#$%^&...",
                },
              ].map((option) => (
                <div
                  key={option.key}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      id={option.key}
                      checked={options[option.key]}
                      onChange={(e) =>
                        handleOptionChange(option.key, e.target.checked)
                      }
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                    />
                    <div>
                      <label
                        htmlFor={option.key}
                        className="text-sm font-medium text-gray-700 dark:text-gray-300"
                      >
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

          {/* Advanced options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Advanced options
            </label>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label
                    htmlFor="excludeSimilar"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Exclude similar characters
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Avoid i, l, 1, L, o, 0, O
                  </p>
                </div>
                <input
                  type="checkbox"
                  id="excludeSimilar"
                  checked={options.excludeSimilar}
                  onChange={(e) =>
                    handleOptionChange("excludeSimilar", e.target.checked)
                  }
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label
                    htmlFor="excludeAmbiguous"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Exclude ambiguous characters
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Avoid {`{ } [ ] ( ) / \\ ' " ~ , ; . < >`}
                  </p>
                </div>
                <input
                  type="checkbox"
                  id="excludeAmbiguous"
                  checked={options.excludeAmbiguous}
                  onChange={(e) =>
                    handleOptionChange("excludeAmbiguous", e.target.checked)
                  }
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                />
              </div>
            </div>
          </div>

          {/* Boutons d'action */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
            {onUsePassword && (
              <Button onClick={() => onUsePassword(generatedPassword)}>
                <CheckIcon className="h-4 w-4" />
                Use this password
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasswordGenerator;
