import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  UserIcon,
  CogIcon,
  ShieldCheckIcon,
  KeyIcon,
  TrashIcon,
  ArrowLeftIcon,
  EyeIcon,
  EyeSlashIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import passwordService from '../services/passwordService';
import userService from '../services/userService';
import authService from '../services/authService';
import ThemeToggle from '../components/ThemeToggle';

const Settings = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  
    // Profile settings
  const [profileData, setProfileData] = useState({
    email: '',
    username: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [editingProfile, setEditingProfile] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // Export/Import data
  const [exportLoading, setExportLoading] = useState(false);
  
  // Statistics
  const [userStats, setUserStats] = useState({
    totalPasswords: 0,
    accountAge: 0,
    lastLogin: null,
    strongPasswords: 0
  });

  useEffect(() => {
    // Vérifier le thème actuel
    const savedTheme = localStorage.getItem('theme');
    setDarkMode(savedTheme === 'dark');
    
    // Initialiser les données du profil
    if (user) {
      setProfileData(prev => ({
        ...prev,
        email: user.email || '',
        username: user.username || ''
      }));
    }
    
    // Charger les statistiques utilisateur
    loadUserStats();
  }, [user]);

  const loadUserStats = async () => {
    try {
      const result = await passwordService.getPasswords();

      if (result.success) {
        const passwords = result.data.passwords || [];
        setUserStats(prev => ({
          ...prev,
          totalPasswords: passwords.length,
          strongPasswords: passwords.filter(p => 
            p.password_strength && p.password_strength >= 4 // Backend scores 4-5 are strong
          ).length
        }));
      }
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
    
    toast.success(`Thème ${newDarkMode ? 'sombre' : 'clair'} activé`);
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    
    if (profileData.newPassword !== profileData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      let updateData = {
        email: profileData.email,
        username: profileData.username
      };      if (profileData.newPassword) {
        updateData.currentPassword = profileData.currentPassword;
        updateData.newPassword = profileData.newPassword;
      }

      const result = await userService.updateProfile(updateData);
      
      if (result.success) {
        toast.success('Profile updated successfully');
        setEditingProfile(false);
        setProfileData(prev => ({
          ...prev,
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }));
        
        // Mettre à jour l'utilisateur dans le contexte si nécessaire
        if (updateUser) {
          updateUser(result.data);
        }
      } else {
        toast.error(result.error || 'Error updating profile');
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error updating profile');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setExportLoading(true);
    try {
      console.log('🔍 Starting export...');
      const result = await passwordService.exportPasswords();
      console.log('🔍 Export result:', result);
      
      if (result.success) {
        const passwords = result.data.passwords || [];
        console.log('🔍 Passwords received:', passwords);
        
        const exportData = {
          exportDate: new Date().toISOString(),
          userEmail: user?.email,
          passwords: passwords.map(pwd => ({
            site_name: pwd.site_name,
            username: pwd.username,
            password: pwd.password, // Include decrypted password
            site_url: pwd.site_url,
            category: pwd.category,
            notes: pwd.notes,
            created_at: pwd.created_at,
            updated_at: pwd.updated_at
          }))
        };
        
        console.log('🔍 Final export data:', exportData);

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
          type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `password-manager-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success('Data exported successfully');
      } else {
        toast.error('Error exporting data');
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Error exporting data');
    } finally {
      setExportLoading(false);
    }
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'preferences', name: 'Preferences', icon: CogIcon },
    { id: 'data', name: 'Data', icon: KeyIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="mr-4 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage your account and preferences
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <div className="lg:w-1/4">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <tab.icon className="mr-3 h-5 w-5" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:w-3/4">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Profile Information
                  </h2>
                  <button
                    onClick={() => setEditingProfile(!editingProfile)}
                    className="flex items-center px-3 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    {editingProfile ? (
                      <XMarkIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <PencilIcon className="h-4 w-4 mr-1" />
                    )}
                    {editingProfile ? 'Cancel' : 'Edit'}
                  </button>
                </div>

                {editingProfile ? (
                  <form onSubmit={handleProfileUpdate} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Username (optional)
                      </label>
                      <input
                        type="text"
                        value={profileData.username}
                        onChange={(e) => setProfileData(prev => ({ ...prev, username: e.target.value }))}
                        placeholder="Enter your username"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div className="border-t pt-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Change Password (optional)
                      </h3>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Current Password
                          </label>
                          <div className="relative">
                            <input
                              type={showPasswords.current ? 'text' : 'password'}
                              value={profileData.currentPassword}
                              onChange={(e) => setProfileData(prev => ({ ...prev, currentPassword: e.target.value }))}
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility('current')}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showPasswords.current ? (
                                <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                              ) : (
                                <EyeIcon className="h-4 w-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            New Password
                          </label>
                          <div className="relative">
                            <input
                              type={showPasswords.new ? 'text' : 'password'}
                              value={profileData.newPassword}
                              onChange={(e) => setProfileData(prev => ({ ...prev, newPassword: e.target.value }))}
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility('new')}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showPasswords.new ? (
                                <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                              ) : (
                                <EyeIcon className="h-4 w-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Confirm New Password
                          </label>
                          <div className="relative">
                            <input
                              type={showPasswords.confirm ? 'text' : 'password'}
                              value={profileData.confirmPassword}
                              onChange={(e) => setProfileData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility('confirm')}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showPasswords.confirm ? (
                                <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                              ) : (
                                <EyeIcon className="h-4 w-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setEditingProfile(false)}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center"
                      >
                        {loading ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        ) : (
                          <CheckIcon className="h-4 w-4 mr-2" />
                        )}
                        Save
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email
                      </label>
                      <p className="text-gray-900 dark:text-white">{user?.email}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Username
                      </label>
                      <p className="text-gray-900 dark:text-white">
                        {user?.username || <span className="text-gray-500 italic">No username set</span>}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Member since
                      </label>
                      <p className="text-gray-900 dark:text-white">
                        {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US') : 'Unknown date'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Security Settings
                </h2>

                <div className="space-y-6">
                  {/* Statistiques de sécurité */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                      <div className="flex items-center">
                        <KeyIcon className="h-8 w-8 text-blue-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600 dark:text-gray-400">Total Passwords</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {userStats.totalPasswords}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                      <div className="flex items-center">
                        <ShieldCheckIcon className="h-8 w-8 text-green-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600 dark:text-gray-400">Strong Passwords</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {userStats.strongPasswords}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action de sécurité */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                      Security Analysis
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Analyze the security of all your passwords and get personalized recommendations.
                    </p>
                    <button
                      onClick={() => navigate('/security-check')}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
                    >
                      <ShieldCheckIcon className="h-4 w-4 mr-2" />
                      Launch Security Check
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Preferences
                </h2>

                <div className="space-y-6">
                  {/* Thème */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Dark Theme
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Use dark theme to reduce eye strain
                      </p>
                    </div>
                    <button
                      onClick={toggleDarkMode}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        darkMode ? 'bg-indigo-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                          darkMode ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Data Tab */}
            {activeTab === 'data' && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Data Management
                </h2>

                <div className="space-y-6">
                  {/* Export */}
                  <div className="border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Export your data
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Download a copy of your data for your personal records.
                    </p>
                    <button
                      onClick={handleExportData}
                      disabled={exportLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                    >
                      {exportLoading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      ) : (
                        <KeyIcon className="h-4 w-4 mr-2" />
                      )}
                      Export my data
                    </button>
                  </div>

                  {/* Development Tools */}
                  <div className="border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      🔧 Development Tools
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Clear browser cache and localStorage for testing. This will log you out and redirect to login.
                    </p>
                    <button
                      onClick={() => {
                        if (window.confirm('⚠️ This will clear all cached data and log you out. Are you sure?')) {
                          authService.clearAllData();
                        }
                      }}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center"
                    >
                      <TrashIcon className="h-4 w-4 mr-2" />
                      Clear Cache & Logout
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;