import axios from 'axios';

// Configuration de base
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

// Instance axios pour les utilisateurs
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token automatiquement
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs d'authentification
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expiré, rediriger vers login
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const userService = {
  /**
   * Récupérer le profil de l'utilisateur connecté
   */
  async getProfile() {
    try {
      const response = await api.get('/users/profile');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch profile',
      };
    }
  },

  /**
   * Mettre à jour le profil utilisateur
   */
  async updateProfile(profileData) {
    try {
      const response = await api.put('/users/profile', profileData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to update profile',
      };
    }
  },

  /**
   * Supprimer le compte utilisateur
   */
  async deleteAccount() {
    try {
      await api.delete('/users/account');
      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to delete account',
      };
    }
  },

  /**
   * Changer le mot de passe utilisateur
   */
  async changePassword(currentPassword, newPassword) {
    try {
      const response = await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to change password',
      };
    }
  },

  /**
   * Obtenir les statistiques de l'utilisateur
   */
  async getStats() {
    try {
      // Pour l'instant, calculer les stats côté client
      // Dans une future version, ceci pourrait être un endpoint dédié
      const passwordService = (await import('./passwordService')).default;
      const passwordResult = await passwordService.getPasswords();
      
      if (passwordResult.success) {
        const passwords = passwordResult.data.passwords || [];
        
        // Calculer les statistiques
        const stats = {
          totalPasswords: passwords.length,
          weakPasswords: passwords.filter(p => p.password_strength <= 2).length,
          categories: [...new Set(passwords.map(p => p.category).filter(c => c))].length,
          favoritePasswords: passwords.filter(p => p.is_favorite).length,
          recentlyUpdated: passwords.filter(p => {
            const updatedDate = new Date(p.updated_at);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return updatedDate > weekAgo;
          }).length,
        };

        return {
          success: true,
          data: stats,
        };
      } else {
        throw new Error('Failed to fetch passwords for stats');
      }
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Failed to calculate stats',
      };
    }
  },
};

export default userService;