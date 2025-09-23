/**
 * Utilitaires pour calculer les statistiques des mots de passe
 */

/**
 * Évaluer la force d'un mot de passe
 * @param {string} password - Le mot de passe à évaluer
 * @returns {Object} - Score et niveau de force
 */
export const evaluatePasswordStrength = (password) => {
  if (!password) return { score: 0, level: 'none', text: 'Aucun' };
  
  let score = 0;
  
  // Critères de base
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;
  
  // Critères de complexité
  if (/[a-z]/.test(password)) score++; // Minuscules
  if (/[A-Z]/.test(password)) score++; // Majuscules
  if (/[0-9]/.test(password)) score++; // Chiffres
  if (/[^A-Za-z0-9]/.test(password)) score++; // Caractères spéciaux
  
  // Pénalités
  if (/(.)\1{2,}/.test(password)) score--; // Répétitions
  if (/123|abc|qwerty|password/i.test(password)) score--; // Séquences communes
  
  // Déterminer le niveau
  if (score <= 2) return { score, level: 'weak', text: 'Faible' };
  if (score <= 4) return { score, level: 'medium', text: 'Moyen' };
  if (score <= 6) return { score, level: 'strong', text: 'Fort' };
  return { score, level: 'very-strong', text: 'Très fort' };
};

/**
 * Calculer les statistiques globales des mots de passe
 * @param {Array} passwords - Liste des mots de passe
 * @returns {Object} - Statistiques calculées
 */
export const calculatePasswordStats = (passwords) => {
  if (!Array.isArray(passwords) || passwords.length === 0) {
    return {
      total: 0,
      weak: 0,
      medium: 0,
      strong: 0,
      categories: 0,
      favorites: 0,
      recentlyAdded: 0,
      duplicates: 0,
      expiringSoon: 0,
    };
  }

  const stats = {
    total: passwords.length,
    weak: 0,
    medium: 0,
    strong: 0,
    categories: new Set(),
    favorites: 0,
    recentlyAdded: 0,
    duplicates: 0,
    expiringSoon: 0,
  };

  // Compter les mots de passe par site pour détecter les doublons
  const siteCounts = {};

  passwords.forEach(pwd => {
    // Évaluer la force
    const strength = evaluatePasswordStrength(pwd.password);
    if (strength.level === 'weak') stats.weak++;
    else if (strength.level === 'medium') stats.medium++;
    else stats.strong++;

    // Catégories
    if (pwd.category) {
      stats.categories.add(pwd.category);
    }

    // Favoris
    if (pwd.is_favorite) {
      stats.favorites++;
    }

    // Récemment ajoutés (derniers 7 jours)
    if (pwd.created_at) {
      const createdDate = new Date(pwd.created_at);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      
      if (createdDate > weekAgo) {
        stats.recentlyAdded++;
      }
    }

    // Compter les doublons par site
    const siteKey = pwd.site_name?.toLowerCase() || 'unknown';
    siteCounts[siteKey] = (siteCounts[siteKey] || 0) + 1;
  });

  // Calculer les doublons
  stats.duplicates = Object.values(siteCounts).filter(count => count > 1).length;

  // Convertir categories Set en nombre
  stats.categories = stats.categories.size;

  return stats;
};

/**
 * Obtenir les catégories les plus utilisées
 * @param {Array} passwords - Liste des mots de passe
 * @returns {Array} - Catégories triées par utilisation
 */
export const getTopCategories = (passwords) => {
  if (!Array.isArray(passwords)) return [];

  const categoryCounts = {};
  
  passwords.forEach(pwd => {
    if (pwd.category) {
      categoryCounts[pwd.category] = (categoryCounts[pwd.category] || 0) + 1;
    }
  });

  return Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([category, count]) => ({ category, count }));
};

/**
 * Obtenir les mots de passe les plus faibles
 * @param {Array} passwords - Liste des mots de passe
 * @param {number} limit - Nombre maximum de résultats
 * @returns {Array} - Mots de passe faibles triés
 */
export const getWeakPasswords = (passwords, limit = 10) => {
  if (!Array.isArray(passwords)) return [];

  return passwords
    .map(pwd => ({
      ...pwd,
      strength: evaluatePasswordStrength(pwd.password)
    }))
    .filter(pwd => pwd.strength.level === 'weak')
    .sort((a, b) => a.strength.score - b.strength.score)
    .slice(0, limit);
};

/**
 * Obtenir les mots de passe récemment modifiés
 * @param {Array} passwords - Liste des mots de passe
 * @param {number} days - Nombre de jours à considérer
 * @returns {Array} - Mots de passe récents
 */
export const getRecentPasswords = (passwords, days = 30) => {
  if (!Array.isArray(passwords)) return [];

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  return passwords
    .filter(pwd => {
      const updatedDate = new Date(pwd.updated_at || pwd.created_at);
      return updatedDate > cutoffDate;
    })
    .sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at);
      const dateB = new Date(b.updated_at || b.created_at);
      return dateB - dateA;
    });
};

/**
 * Format a relative date (ex: "2 days ago")
 * @param {string|Date} dateString - Date to format
 * @returns {string} - Formatted date
 */
export const formatRelativeDate = (dateString) => {
  if (!dateString) return 'Never';

  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now - date;
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInDays === 0) return 'Today';
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 7) return `${diffInDays} days ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`;
  
  return `${Math.floor(diffInDays / 365)} years ago`;
};