import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ArrowLeftIcon,
  EyeIcon,
  EyeSlashIcon,
  ClockIcon,
  KeyIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import passwordService from '../services/passwordService';
import { evaluatePasswordStrength, getWeakPasswords, formatRelativeDate } from '../utils/passwordStats';

const SecurityCheck = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [passwords, setPasswords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [securityReport, setSecurityReport] = useState(null);
  const [showPasswords, setShowPasswords] = useState({});

  useEffect(() => {
    loadPasswordsAndAnalyze();
  }, []);

  const loadPasswordsAndAnalyze = async () => {
    try {
      setLoading(true);
      const result = await passwordService.getPasswords();
      
      if (result.success) {
        const passwordList = result.data.passwords || [];
        setPasswords(passwordList);
        
        // Récupérer les mots de passe déchiffrés pour l'analyse
        const decryptedPasswords = [];
        for (const pwd of passwordList) {
          try {
            const decryptedResult = await passwordService.getPassword(pwd.id);
            if (decryptedResult.success) {
              decryptedPasswords.push({
                ...pwd,
                password: decryptedResult.data.password
              });
            } else {
              // Si le déchiffrement échoue, ignorer ce mot de passe dans l'analyse
              console.warn(`Impossible de déchiffrer le mot de passe ${pwd.id}`);
            }
          } catch (error) {
            console.warn(`Erreur lors du déchiffrement du mot de passe ${pwd.id}:`, error);
          }
        }
        
        await performSecurityAnalysis(decryptedPasswords);
      } else {
        toast.error('Erreur lors du chargement des mots de passe');
      }
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      toast.error('Erreur lors du chargement des mots de passe');
    } finally {
      setLoading(false);
    }
  };

  const performSecurityAnalysis = async (passwordList) => {
    try {
      setAnalyzing(true);
      
      // Analyse des mots de passe
      const analysis = {
        total: passwordList.length,
        weak: 0,
        medium: 0,
        strong: 0,
        duplicates: [],
        oldPasswords: [],
        commonPasswords: [],
        recommendations: []
      };

      const passwordCounts = {};
      const commonPatterns = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome'];

      passwordList.forEach(pwd => {
        const strength = evaluatePasswordStrength(pwd.password);
        
        // Compter par force
        if (strength.level === 'weak') analysis.weak++;
        else if (strength.level === 'medium') analysis.medium++;
        else analysis.strong++;

        // Détecter les doublons
        if (pwd.password) {
          const lowerPassword = pwd.password.toLowerCase();
          if (passwordCounts[lowerPassword]) {
            passwordCounts[lowerPassword].push(pwd);
          } else {
            passwordCounts[lowerPassword] = [pwd];
          }

          // Détecter les mots de passe courants
          if (commonPatterns.some(pattern => lowerPassword.includes(pattern))) {
            analysis.commonPasswords.push(pwd);
          }
        }

        // Détecter les mots de passe anciens (plus de 90 jours)
        if (pwd.updated_at || pwd.created_at) {
          const lastUpdate = new Date(pwd.updated_at || pwd.created_at);
          const ninetyDaysAgo = new Date();
          ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
          
          if (lastUpdate < ninetyDaysAgo) {
            analysis.oldPasswords.push({
              ...pwd,
              daysOld: Math.floor((new Date() - lastUpdate) / (1000 * 60 * 60 * 24))
            });
          }
        }
      });

      // Identifier les doublons
      analysis.duplicates = Object.values(passwordCounts)
        .filter(group => group.length > 1)
        .flat();

      // Générer des recommandations
      if (analysis.weak > 0) {
        analysis.recommendations.push({
          type: 'warning',
          title: 'Mots de passe faibles détectés',
          description: `${analysis.weak} mot(s) de passe ont une force insuffisante. Renforcez-les en ajoutant des caractères spéciaux, des chiffres et en augmentant leur longueur.`
        });
      }

      if (analysis.duplicates.length > 0) {
        analysis.recommendations.push({
          type: 'error',
          title: 'Mots de passe dupliqués',
          description: `${analysis.duplicates.length} mot(s) de passe sont utilisés plusieurs fois. Utilisez un mot de passe unique pour chaque site.`
        });
      }

      if (analysis.oldPasswords.length > 0) {
        analysis.recommendations.push({
          type: 'warning',
          title: 'Mots de passe anciens',
          description: `${analysis.oldPasswords.length} mot(s) de passe n'ont pas été changés depuis plus de 90 jours. Pensez à les renouveler régulièrement.`
        });
      }

      if (analysis.commonPasswords.length > 0) {
        analysis.recommendations.push({
          type: 'error',
          title: 'Mots de passe courants détectés',
          description: `${analysis.commonPasswords.length} mot(s) de passe contiennent des motifs courants. Évitez les mots du dictionnaire et les séquences prévisibles.`
        });
      }

      if (analysis.recommendations.length === 0) {
        analysis.recommendations.push({
          type: 'success',
          title: 'Excellente sécurité !',
          description: 'Vos mots de passe respectent toutes les bonnes pratiques de sécurité. Continuez ainsi !'
        });
      }

      setSecurityReport(analysis);
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error);
      toast.error('Erreur lors de l\'analyse de sécurité');
    } finally {
      setAnalyzing(false);
    }
  };

  const togglePasswordVisibility = (passwordId) => {
    setShowPasswords(prev => ({
      ...prev,
      [passwordId]: !prev[passwordId]
    }));
  };

  const getSecurityScore = () => {
    if (!securityReport || securityReport.total === 0) return 0;
    
    const strongRatio = securityReport.strong / securityReport.total;
    const weakPenalty = securityReport.weak * 10;
    const duplicatePenalty = securityReport.duplicates.length * 5;
    const oldPasswordPenalty = securityReport.oldPasswords.length * 3;
    
    const baseScore = Math.round(strongRatio * 100);
    const finalScore = Math.max(0, baseScore - weakPenalty - duplicatePenalty - oldPasswordPenalty);
    
    return finalScore;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  if (loading || analyzing) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">
            {loading ? 'Chargement des mots de passe...' : 'Analyse de sécurité en cours...'}
          </p>
        </div>
      </div>
    );
  }

  const securityScore = getSecurityScore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="mr-4 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div className="flex items-center">
              <ShieldCheckIcon className="h-8 w-8 text-indigo-600 mr-3" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Analyse de Sécurité
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Évaluation complète de la sécurité de vos mots de passe
                </p>
              </div>
            </div>
          </div>

          {/* Score de sécurité */}
          {securityReport && (
            <div className={`${getScoreBackground(securityScore)} rounded-2xl p-6 mb-6`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Score de Sécurité</h2>
                  <p className="text-gray-600">Basé sur l'analyse de {securityReport.total} mots de passe</p>
                </div>
                <div className="text-right">
                  <div className={`text-4xl font-bold ${getScoreColor(securityScore)}`}>
                    {securityScore}/100
                  </div>
                  <p className="text-sm text-gray-600">
                    {securityScore >= 80 ? 'Excellent' : 
                     securityScore >= 60 ? 'Correct' : 'À améliorer'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recommandations */}
        {securityReport?.recommendations && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Recommandations
            </h2>
            <div className="space-y-4">
              {securityReport.recommendations.map((rec, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-l-4 ${
                    rec.type === 'error' ? 'bg-red-50 border-red-400 dark:bg-red-900/20' :
                    rec.type === 'warning' ? 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20' :
                    'bg-green-50 border-green-400 dark:bg-green-900/20'
                  }`}
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      {rec.type === 'error' ? (
                        <XCircleIcon className="h-5 w-5 text-red-600" />
                      ) : rec.type === 'warning' ? (
                        <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                      ) : (
                        <CheckCircleIcon className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        {rec.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {rec.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Statistiques détaillées */}
        {securityReport && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
              <div className="flex items-center">
                <KeyIcon className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {securityReport.total}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
              <div className="flex items-center">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Forts</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {securityReport.strong}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Moyens</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {securityReport.medium}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
              <div className="flex items-center">
                <XCircleIcon className="h-8 w-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Faibles</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {securityReport.weak}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Détails des problèmes */}
        {securityReport && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Mots de passe faibles */}
            {securityReport.weak > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
                  Mots de passe faibles ({securityReport.weak})
                </h3>
                <div className="space-y-3">
                  {getWeakPasswords(passwords, 5).map(pwd => (
                    <div key={pwd.id} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {pwd.site_name}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {pwd.username}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => togglePasswordVisibility(pwd.id)}
                          className="p-1 text-gray-400 hover:text-gray-600"
                        >
                          {showPasswords[pwd.id] ? (
                            <EyeSlashIcon className="h-4 w-4" />
                          ) : (
                            <EyeIcon className="h-4 w-4" />
                          )}
                        </button>
                        <span className="text-sm font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                          {showPasswords[pwd.id] ? pwd.password : '••••••••'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mots de passe anciens */}
            {securityReport.oldPasswords.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <ClockIcon className="h-5 w-5 text-yellow-600 mr-2" />
                  Mots de passe anciens ({securityReport.oldPasswords.length})
                </h3>
                <div className="space-y-3">
                  {securityReport.oldPasswords.slice(0, 5).map(pwd => (
                    <div key={pwd.id} className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {pwd.site_name}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Dernière modification: {formatRelativeDate(pwd.updated_at || pwd.created_at)}
                        </p>
                      </div>
                      <span className="text-sm font-medium text-yellow-600">
                        {pwd.daysOld} jours
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Bouton d'action */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={loadPasswordsAndAnalyze}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center"
          >
            <ShieldCheckIcon className="h-5 w-5 mr-2" />
            Relancer l'analyse
          </button>
        </div>
      </div>
    </div>
  );
};

export default SecurityCheck;