import React, { createContext, useContext, useState, useEffect } from 'react';

// Créer le contexte du thème
const ThemeContext = createContext();

// Hook personnalisé pour utiliser le contexte du thème
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Provider du contexte du thème
export const ThemeProvider = ({ children }) => {
  // Récupérer le thème depuis localStorage ou utiliser 'light' par défaut
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme || 'light';
  });

  // Basculer entre les thèmes
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  // Sauvegarder le thème dans localStorage et appliquer la classe CSS
  useEffect(() => {
    localStorage.setItem('theme', theme);
    // Appliquer la classe 'dark' sur le documentElement pour TailwindCSS
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.body.className = 'dark-theme';
    } else {
      document.documentElement.classList.remove('dark');
      document.body.className = 'light-theme';
    }
  }, [theme]);

  const value = {
    theme,
    toggleTheme,
    isDark: theme === 'dark'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};