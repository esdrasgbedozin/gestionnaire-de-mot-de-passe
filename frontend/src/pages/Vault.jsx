import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  FunnelIcon,
  KeyIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
  DocumentDuplicateIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import PasswordCard from '../components/PasswordCard';
import PasswordForm from '../components/PasswordForm';
import PasswordGenerator from '../components/PasswordGenerator';

const Vault = () => {
  const { user } = useAuth();
  const [passwords, setPasswords] = useState([]);
  const [filteredPasswords, setFilteredPasswords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);
  const [editingPassword, setEditingPassword] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' ou 'list'

  // Catégories disponibles
  const categories = [
    { id: 'all', name: 'Tous', icon: KeyIcon, count: passwords.length },
    { id: 'social', name: 'Réseaux sociaux', icon: ShieldCheckIcon, count: 0 },
    { id: 'work', name: 'Travail', icon: ShieldCheckIcon, count: 0 },
    { id: 'personal', name: 'Personnel', icon: ShieldCheckIcon, count: 0 },
    { id: 'banking', name: 'Banque', icon: ShieldCheckIcon, count: 0 },
    { id: 'shopping', name: 'Shopping', icon: ShieldCheckIcon, count: 0 },
  ];

  // Charger les mots de passe au montage du composant
  useEffect(() => {
    fetchPasswords();
  }, []);

  // Filtrer les mots de passe quand la recherche ou la catégorie change
  useEffect(() => {
    filterPasswords();
  }, [passwords, searchTerm, selectedCategory]);

  const fetchPasswords = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/passwords', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPasswords(data.passwords || []);
      } else {
        throw new Error('Erreur lors du chargement des mots de passe');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Impossible de charger les mots de passe');
    } finally {
      setLoading(false);
    }
  };

  const filterPasswords = () => {
    let filtered = passwords;

    // Filtrer par recherche
    if (searchTerm) {
      filtered = filtered.filter(password => 
        password.site_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        password.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (password.notes && password.notes.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filtrer par catégorie
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(password => password.category === selectedCategory);
    }

    setFilteredPasswords(filtered);
  };

  const handleAddPassword = () => {
    setEditingPassword(null);
    setShowAddForm(true);
  };

  const handleEditPassword = (password) => {
    setEditingPassword(password);
    setShowAddForm(true);
  };

  const handleDeletePassword = async (passwordId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce mot de passe ?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/passwords/${passwordId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        toast.success('Mot de passe supprimé avec succès');
        fetchPasswords(); // Recharger la liste
      } else {
        throw new Error('Erreur lors de la suppression');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Impossible de supprimer le mot de passe');
    }
  };

  const handlePasswordSaved = () => {
    setShowAddForm(false);
    setEditingPassword(null);
    fetchPasswords(); // Recharger la liste
    toast.success(editingPassword ? 'Mot de passe modifié' : 'Mot de passe ajouté');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Chargement de votre coffre-fort...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* En-tête */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Coffre-fort de {user?.username}
                </h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {passwords.length} mot(s) de passe stocké(s) en sécurité
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowGenerator(true)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  <ShieldCheckIcon className="h-4 w-4 mr-2" />
                  Générateur
                </button>
                <button
                  onClick={handleAddPassword}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Ajouter un mot de passe
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar avec catégories */}
          <div className="w-64 flex-shrink-0">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Catégories</h3>
                <nav className="space-y-1">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors ${
                        selectedCategory === category.id
                          ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <category.icon className="h-4 w-4 mr-2" />
                        {category.name}
                      </div>
                      <span className="text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-full px-2 py-1">
                        {category.count}
                      </span>
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>

          {/* Contenu principal */}
          <div className="flex-1">
            {/* Barre de recherche et filtres */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
              <div className="p-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1 relative">
                    <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Rechercher dans vos mots de passe..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`p-2 rounded-md ${viewMode === 'grid' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={`p-2 rounded-md ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Liste des mots de passe */}
            {filteredPasswords.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
                <KeyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {passwords.length === 0 ? 'Aucun mot de passe' : 'Aucun résultat'}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  {passwords.length === 0 
                    ? 'Commencez par ajouter votre premier mot de passe'
                    : 'Essayez de modifier vos critères de recherche'
                  }
                </p>
                {passwords.length === 0 && (
                  <button
                    onClick={handleAddPassword}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Ajouter un mot de passe
                  </button>
                )}
              </div>
            ) : (
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
                {filteredPasswords.map((password) => (
                  <PasswordCard
                    key={password.id}
                    password={password}
                    viewMode={viewMode}
                    onEdit={handleEditPassword}
                    onDelete={handleDeletePassword}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modales */}
      {showAddForm && (
        <PasswordForm
          password={editingPassword}
          onSave={handlePasswordSaved}
          onCancel={() => {
            setShowAddForm(false);
            setEditingPassword(null);
          }}
        />
      )}

      {showGenerator && (
        <PasswordGenerator
          onClose={() => setShowGenerator(false)}
        />
      )}
    </div>
  );
};

export default Vault;