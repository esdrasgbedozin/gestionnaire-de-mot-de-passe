import axios from 'axios';

// Configuration de base avec le bon port
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

// Instance axios avec configuration de base
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

// Intercepteur pour gérer l'expiration du token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await authService.refreshToken();
          const { tokens } = response.data;
          
          localStorage.setItem('access_token', tokens.access_token);
          localStorage.setItem('refresh_token', tokens.refresh_token);
          
          // Retry la requête originale avec le nouveau token
          originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si le refresh échoue, déconnecter l'utilisateur
        authService.logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

const authService = {
  /**
   * Connexion utilisateur
   */
  async login(email, password) {
    try {
      const response = await api.post('/auth/login', {
        email: email.trim().toLowerCase(),
        password,
      });

      const { tokens, user } = response.data;

      // Stocker les tokens
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));

      return {
        success: true,
        data: {
          tokens,
          user,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Login failed',
      };
    }
  },

  /**
   * Inscription utilisateur
   */
  async register(email, password, confirmPassword) {
    try {
      // Validation côté client
      if (password !== confirmPassword) {
        return {
          success: false,
          error: 'Passwords do not match',
        };
      }

      const response = await api.post('/auth/register', {
        email: email.trim().toLowerCase(),
        password,
      });

      const { tokens, user } = response.data;

      // Stocker les tokens après inscription automatique
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));

      return {
        success: true,
        data: {
          tokens,
          user,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Registration failed',
      };
    }
  },

  /**
   * Déconnexion
   */
  async logout() {
    try {
      // Appeler l'API pour blacklister le token
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Nettoyer le localStorage dans tous les cas
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Rafraîchir le token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return response;
  },

  /**
   * Obtenir l'utilisateur actuel
   */
  async getCurrentUser() {
    try {
      // D'abord essayer de récupérer depuis localStorage
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        
        // Vérifier que le token est toujours valide
        const response = await api.get('/auth/me');
        const freshUser = response.data.user;
        
        // Mettre à jour les données si elles ont changé
        if (JSON.stringify(user) !== JSON.stringify(freshUser)) {
          localStorage.setItem('user', JSON.stringify(freshUser));
          return freshUser;
        }
        
        return user;
      }

      // Si pas de données locales, récupérer depuis l'API
      const response = await api.get('/auth/me');
      const user = response.data.user;
      localStorage.setItem('user', JSON.stringify(user));
      
      return user;
    } catch (error) {
      return null;
    }
  },

  /**
   * Vérifier si l'utilisateur est connecté
   */
  isAuthenticated() {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  },

  /**
   * Obtenir le token d'accès
   */
  getAccessToken() {
    return localStorage.getItem('access_token');
  },

  /**
   * Obtenir les headers d'authentification
   */
  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  },
};

export default authService;