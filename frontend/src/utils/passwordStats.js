/**
 * Password statistics utilities.
 */

import { evaluateStrength } from "./passwordStrength";

/**
 * Evaluate a password's strength via the single app-wide engine (zxcvbn).
 * Kept returning { score, level, text } for existing callers (e.g. getWeakPasswords).
 */
export const evaluatePasswordStrength = (password) => {
  const s = evaluateStrength(password);
  const level =
    s.score < 0
      ? "none"
      : s.score <= 1
        ? "weak"
        : s.score === 2
          ? "medium"
          : s.score === 3
            ? "strong"
            : "very-strong";
  return { score: s.score, level, text: s.label };
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

  passwords.forEach((pwd) => {
    // Évaluer la force basée sur le score du backend (1-5)
    // 1-2 = weak, 3 = medium, 4-5 = strong
    const strength_score = pwd.password_strength || 1;
    if (strength_score <= 2) {
      stats.weak++;
    } else if (strength_score === 3) {
      stats.medium++;
    } else {
      stats.strong++;
    }

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
    const siteKey = pwd.site_name?.toLowerCase() || "unknown";
    siteCounts[siteKey] = (siteCounts[siteKey] || 0) + 1;
  });

  // Calculer les doublons
  stats.duplicates = Object.values(siteCounts).filter(
    (count) => count > 1,
  ).length;

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

  passwords.forEach((pwd) => {
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
    .map((pwd) => ({
      ...pwd,
      strength: evaluatePasswordStrength(pwd.password),
    }))
    .filter((pwd) => pwd.strength.level === "weak")
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
    .filter((pwd) => {
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
  if (!dateString) return "Never";

  const date = new Date(dateString);
  const now = new Date();

  // Vérifier si la date est valide
  if (isNaN(date.getTime())) {
    return "Invalid date";
  }

  // Reset les heures pour comparer seulement les dates (à minuit local)
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const compareDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );

  const diffInMs = today.getTime() - compareDate.getTime();
  const diffInDays = Math.round(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInDays === 0) return "Today";
  if (diffInDays === 1) return "Yesterday";
  if (diffInDays === -1) return "Tomorrow"; // Au cas où
  if (diffInDays > 1 && diffInDays < 7) return `${diffInDays} days ago`;
  if (diffInDays >= 7 && diffInDays < 30)
    return `${Math.floor(diffInDays / 7)} week${Math.floor(diffInDays / 7) > 1 ? "s" : ""} ago`;
  if (diffInDays >= 30 && diffInDays < 365)
    return `${Math.floor(diffInDays / 30)} month${Math.floor(diffInDays / 30) > 1 ? "s" : ""} ago`;
  if (diffInDays >= 365)
    return `${Math.floor(diffInDays / 365)} year${Math.floor(diffInDays / 365) > 1 ? "s" : ""} ago`;

  // Pour les dates futures
  if (diffInDays < 0) return "Future date";

  return `${diffInDays} days ago`;
};
