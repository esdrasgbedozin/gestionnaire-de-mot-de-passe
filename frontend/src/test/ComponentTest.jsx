import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import { Toaster } from 'react-hot-toast';
import PasswordCard from '../components/PasswordCard';
import PasswordGenerator from '../components/PasswordGenerator';
import Vault from '../pages/Vault';

// Données de test
const testPassword = {
  id: 1,
  title: 'Facebook',
  website: 'https://facebook.com',
  username: 'user@email.com',
  password: 'SecurePass123!',
  category: 'social',
  notes: 'Mon compte principal Facebook',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// Composant de test pour PasswordCard
export const TestPasswordCard = () => {
  const handleEdit = (password) => {
    console.log('Edit password:', password);
  };

  const handleDelete = (password) => {
    console.log('Delete password:', password);
  };

  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Test PasswordCard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <PasswordCard 
          password={testPassword}
          viewMode="grid"
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
      
      <h2 className="text-xl font-bold mt-8 mb-4">Mode Liste</h2>
      <div className="space-y-2">
        <PasswordCard 
          password={testPassword}
          viewMode="list"
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
};

// Composant de test pour PasswordGenerator
export const TestPasswordGenerator = () => {
  const handleGenerate = (password) => {
    console.log('Generated password:', password);
  };

  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Test PasswordGenerator</h1>
      <div className="max-w-md mx-auto">
        <PasswordGenerator onGenerate={handleGenerate} />
      </div>
    </div>
  );
};

// Wrapper pour les tests avec les providers nécessaires
export const TestWrapper = ({ children }) => {
  return (
    <Router>
      <AuthProvider>
        {children}
        <Toaster position="top-right" />
      </AuthProvider>
    </Router>
  );
};

// Test de rendu de base
export const BasicRenderTest = () => {
  try {
    return (
      <TestWrapper>
        <div className="p-4">
          <h1 className="text-2xl font-bold text-green-600">✅ Composants chargés avec succès !</h1>
          <div className="mt-4 space-y-2">
            <p>✅ PasswordCard importé</p>
            <p>✅ PasswordGenerator importé</p>
            <p>✅ Vault importé</p>
            <p>✅ AuthContext importé</p>
            <p>✅ React Hot Toast importé</p>
          </div>
        </div>
      </TestWrapper>
    );
  } catch (error) {
    return (
      <div className="p-4">
        <h1 className="text-2xl font-bold text-red-600">❌ Erreur de chargement</h1>
        <p className="mt-2 text-red-500">{error.message}</p>
      </div>
    );
  }
};