import React, { useState } from 'react';
import {
  EyeIcon,
  EyeSlashIcon,
  DocumentDuplicateIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon,
  UserIcon,
  KeyIcon,
  CalendarIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const PasswordCard = ({ password, viewMode = 'grid', onEdit, onDelete }) => {
  const [showPassword, setShowPassword] = useState(false);

  // Fonction pour copier dans le presse-papiers
  const copyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${field} copié dans le presse-papiers`);
    } catch (error) {
      console.error('Erreur lors de la copie:', error);
      toast.error('Impossible de copier');
    }
  };

  // Fonction pour évaluer la force du mot de passe
  const getPasswordStrength = (password) => {
    if (!password) return { level: 0, text: 'Faible', color: 'red' };
    
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 2) return { level: 1, text: 'Faible', color: 'red' };
    if (score <= 4) return { level: 2, text: 'Moyen', color: 'yellow' };
    return { level: 3, text: 'Fort', color: 'green' };
  };

  // Fonction pour obtenir l'icône de la catégorie
  const getCategoryIcon = (category) => {
    const icons = {
      social: '📱',
      work: '💼',
      personal: '👤',
      banking: '🏦',
      shopping: '🛒',
      default: '🔐'
    };
    return icons[category] || icons.default;
  };

  // Formater la date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const strength = getPasswordStrength(password.password);

  if (viewMode === 'list') {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1">
            {/* Icône et informations principales */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl">
                {getCategoryIcon(password.category)}
              </div>
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                  {password.site_name}
                </h3>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  strength.color === 'green' ? 'bg-green-100 text-green-800' :
                  strength.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {strength.text}
                </span>
              </div>
              
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center">
                  <UserIcon className="h-4 w-4 mr-1" />
                  {password.username}
                </div>
                <div className="flex items-center">
                  <GlobeAltIcon className="h-4 w-4 mr-1" />
                  {password.site_url || 'Aucune URL'}
                </div>
                <div className="flex items-center">
                  <CalendarIcon className="h-4 w-4 mr-1" />
                  {formatDate(password.created_at)}
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => copyToClipboard(password.username, 'Nom d\'utilisateur')}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Copier le nom d'utilisateur"
            >
              <UserIcon className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => copyToClipboard(password.password, 'Mot de passe')}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Copier le mot de passe"
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => setShowPassword(!showPassword)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              title={showPassword ? 'Masquer' : 'Afficher'}
            >
              {showPassword ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
            </button>
            
            <button
              onClick={() => onEdit(password)}
              className="p-2 text-indigo-400 hover:text-indigo-600 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900"
              title="Modifier"
            >
              <PencilIcon className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => onDelete(password.id)}
              className="p-2 text-red-400 hover:text-red-600 rounded-md hover:bg-red-50 dark:hover:bg-red-900"
              title="Supprimer"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Mot de passe affiché */}
        {showPassword && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <KeyIcon className="h-4 w-4 text-gray-400" />
              <span className="font-mono text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {password.password}
              </span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Vue en grille (card)
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-all duration-200 group">
      {/* En-tête de la carte */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl">
            {getCategoryIcon(password.category)}
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate max-w-40">
              {password.site_name}
            </h3>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                strength.color === 'green' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                strength.color === 'yellow' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
                {strength.text}
              </span>
              {password.category && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                  <TagIcon className="h-3 w-3 mr-1" />
                  {password.category}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Menu d'actions */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
          <button
            onClick={() => onEdit(password)}
            className="p-2 text-indigo-400 hover:text-indigo-600 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900"
            title="Modifier"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => onDelete(password.id)}
            className="p-2 text-red-400 hover:text-red-600 rounded-md hover:bg-red-50 dark:hover:bg-red-900"
            title="Supprimer"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Informations */}
      <div className="space-y-3">
        {/* Nom d'utilisateur */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <UserIcon className="h-4 w-4" />
            <span className="truncate max-w-32">{password.username}</span>
          </div>
          <button
            onClick={() => copyToClipboard(password.username, 'Nom d\'utilisateur')}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
            title="Copier"
          >
            <DocumentDuplicateIcon className="h-4 w-4" />
          </button>
        </div>

        {/* URL du site */}
        {password.site_url && (
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <GlobeAltIcon className="h-4 w-4" />
            <a 
              href={password.site_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="truncate max-w-32 hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              {password.site_url}
            </a>
          </div>
        )}

        {/* Mot de passe */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <KeyIcon className="h-4 w-4 text-gray-400" />
            <span className="font-mono text-sm">
              {showPassword ? password.password : '••••••••'}
            </span>
          </div>
          <div className="flex space-x-1">
            <button
              onClick={() => setShowPassword(!showPassword)}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
              title={showPassword ? 'Masquer' : 'Afficher'}
            >
              {showPassword ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
            </button>
            <button
              onClick={() => copyToClipboard(password.password, 'Mot de passe')}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
              title="Copier"
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Notes (si présentes) */}
        {password.notes && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p className="truncate" title={password.notes}>
              📝 {password.notes}
            </p>
          </div>
        )}
      </div>

      {/* Pied de carte avec date */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-1">
            <CalendarIcon className="h-3 w-3" />
            <span>Créé le {formatDate(password.created_at)}</span>
          </div>
          {password.updated_at !== password.created_at && (
            <span>Modifié le {formatDate(password.updated_at)}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default PasswordCard;