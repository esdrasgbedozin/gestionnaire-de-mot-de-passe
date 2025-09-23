import axios from 'axios';

// Configuration de base
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

// Instance axios spécialisée pour les mots de passe
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

const passwordService = {
  /**
   * Récupérer tous les mots de passe de l'utilisateur
   */
  async getPasswords(page = 1, limit = 50, category = null, search = null) {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (category && category !== 'all') {
        params.append('category', category);
      }

      if (search) {
        params.append('search', search);
      }

      const response = await api.get(`/passwords/?${params.toString()}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch passwords',
      };
    }
  },

  /**
   * Récupérer un mot de passe spécifique (avec déchiffrement)
   */
  async getPassword(passwordId) {
    try {
      const response = await api.get(`/passwords/${passwordId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch password',
      };
    }
  },

  /**
   * Créer un nouveau mot de passe
   */
  async createPassword(passwordData) {
    try {
      const response = await api.post('/passwords/', passwordData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create password',
      };
    }
  },

  /**
   * Mettre à jour un mot de passe existant
   */
  async updatePassword(passwordId, passwordData) {
    try {
      const response = await api.put(`/passwords/${passwordId}`, passwordData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to update password',
      };
    }
  },

  /**
   * Supprimer un mot de passe
   */
  async deletePassword(passwordId) {
    try {
      await api.delete(`/passwords/${passwordId}`);
      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to delete password',
      };
    }
  },

  /**
   * Générer un nouveau mot de passe
   */
  async generatePassword(options = {}) {
    try {
      const response = await api.post('/passwords/generate', options);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to generate password',
      };
    }
  },

  /**
   * Évaluer la force d'un mot de passe
   */
  async evaluatePasswordStrength(password) {
    try {
      const response = await api.post('/passwords/strength', { password });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to evaluate password strength',
      };
    }
  },

  /**
   * Récupérer les catégories disponibles
   */
  async getCategories() {
    try {
      const response = await api.get('/passwords/categories');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch categories',
      };
    }
  },

  /**
   * Récupérer les presets de génération de mots de passe
   */
  async getPresets() {
    try {
      const response = await api.get('/passwords/presets');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch presets',
      };
    }
  },

  /**
   * Marquer/démarquer un mot de passe comme favori
   */
  async toggleFavorite(passwordId, isFavorite) {
    try {
      const response = await api.put(`/passwords/${passwordId}`, {
        is_favorite: !isFavorite,
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to toggle favorite',
      };
    }
  },

  /**
   * Rechercher des mots de passe
   */
  async searchPasswords(query, filters = {}) {
    try {
      const params = new URLSearchParams({
        search: query,
      });

      // Ajouter les filtres
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          params.append(key, value.toString());
        }
      });

      const response = await api.get(`/passwords/?${params.toString()}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to search passwords',
      };
    }
  },

  /**
   * Export all passwords with decrypted passwords for backup
   */
  async exportPasswords() {
    try {
      // First get the list of all passwords (without decrypted passwords)
      const listResult = await this.getPasswords(1, 1000); // Get large number to ensure all passwords
      if (!listResult.success) {
        return listResult;
      }

      const passwords = listResult.data.passwords || [];
      const decryptedPasswords = [];

      // Get each password individually to get decrypted version
      for (const pwd of passwords) {
        const passwordResult = await this.getPassword(pwd.id);
        if (passwordResult.success) {
          decryptedPasswords.push(passwordResult.data);
        } else {
          // If we can't decrypt one password, include it without the password field
          decryptedPasswords.push({
            ...pwd,
            password: '[DECRYPTION_FAILED]'
          });
        }
      }

      return {
        success: true,
        data: {
          passwords: decryptedPasswords,
          total: decryptedPasswords.length
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Failed to export passwords',
      };
    }
  },
};

export default passwordService;