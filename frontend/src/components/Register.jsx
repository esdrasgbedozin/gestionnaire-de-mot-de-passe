import React, { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  UserPlusIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const Register = () => {
  const { register, loading, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    feedback: '',
    checks: {
      length: false,
      uppercase: false,
      lowercase: false,
      number: false,
      special: false,
    }
  });

  // Rediriger si déjà connecté
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const validateEmail = (email) => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  const checkPasswordStrength = (password) => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const score = Object.values(checks).filter(Boolean).length;
    let feedback = '';

    if (score === 0) feedback = '';
    else if (score <= 2) feedback = 'Weak';
    else if (score <= 3) feedback = 'Medium';
    else if (score <= 4) feedback = 'Strong';
    else feedback = 'Very Strong';

    return { score, feedback, checks };
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Nettoyer l'erreur du champ modifié
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }

    // Vérifier la force du mot de passe
    if (name === 'password') {
      setPasswordStrength(checkPasswordStrength(value));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validation email
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Validation mot de passe
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (passwordStrength.score < 4) {
      newErrors.password = 'Password does not meet security requirements';
    }

    // Validation confirmation mot de passe
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Password confirmation is required';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Validation conditions d'utilisation
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const result = await register(
        formData.email, 
        formData.password, 
        formData.confirmPassword
      );

      if (result.success) {
        toast.success('Account created successfully! Welcome!');
        // La redirection sera automatique via le context
      } else {
        toast.error(result.error || 'Registration failed');
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    }
  };

  const getPasswordStrengthColor = () => {
    switch (passwordStrength.score) {
      case 0:
      case 1: return 'bg-red-500';
      case 2: return 'bg-yellow-500';
      case 3: return 'bg-blue-500';
      case 4:
      case 5: return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  const getPasswordStrengthWidth = () => {
    return `${(passwordStrength.score / 5) * 100}%`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center">
            <UserPlusIcon className="h-6 w-6 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Join us and secure your passwords
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleInputChange}
              className={`appearance-none relative block w-full px-3 py-3 border ${
                errors.email ? 'border-red-300' : 'border-gray-300'
              } placeholder-gray-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
              placeholder="Enter your email"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email}</p>
            )}
          </div>

          {/* Mot de passe */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={formData.password}
                onChange={handleInputChange}
                className={`appearance-none relative block w-full px-3 py-3 pr-10 border ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                placeholder="Enter your password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>

            {/* Indicateur de force du mot de passe */}
            {formData.password && (
              <div className="mt-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-600">Password strength:</span>
                  <span className={`text-xs font-medium ${
                    passwordStrength.score <= 2 ? 'text-red-600' :
                    passwordStrength.score <= 3 ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {passwordStrength.feedback}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                    style={{ width: getPasswordStrengthWidth() }}
                  ></div>
                </div>

                {/* Critères de sécurité */}
                <div className="mt-2 space-y-1">
                  {[
                    { key: 'length', text: 'At least 8 characters' },
                    { key: 'uppercase', text: 'One uppercase letter' },
                    { key: 'lowercase', text: 'One lowercase letter' },
                    { key: 'number', text: 'One number' },
                    { key: 'special', text: 'One special character' },
                  ].map(({ key, text }) => (
                    <div key={key} className="flex items-center text-xs">
                      {passwordStrength.checks[key] ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                      ) : (
                        <XCircleIcon className="h-4 w-4 text-gray-300 mr-1" />
                      )}
                      <span className={passwordStrength.checks[key] ? 'text-green-600' : 'text-gray-500'}>
                        {text}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password}</p>
            )}
          </div>

          {/* Confirmation mot de passe */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Confirm password
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className={`appearance-none relative block w-full px-3 py-3 pr-10 border ${
                  errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                placeholder="Confirm your password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
            )}
          </div>

          {/* Conditions d'utilisation */}
          <div>
            <div className="flex items-start">
              <input
                id="acceptTerms"
                name="acceptTerms"
                type="checkbox"
                checked={formData.acceptTerms}
                onChange={handleInputChange}
                className="mt-0.5 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="acceptTerms" className="ml-2 block text-sm text-gray-700">
                I accept the{' '}
                <Link to="/terms" className="text-blue-600 hover:text-blue-500 underline">
                  Terms and Conditions
                </Link>{' '}
                and{' '}
                <Link to="/privacy" className="text-blue-600 hover:text-blue-500 underline">
                  Privacy Policy
                </Link>
              </label>
            </div>
            {errors.acceptTerms && (
              <p className="mt-1 text-sm text-red-600">{errors.acceptTerms}</p>
            )}
          </div>

          {/* Bouton d'inscription */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating account...
                </div>
              ) : (
                <div className="flex items-center">
                  <ShieldCheckIcon className="h-4 w-4 mr-2" />
                  Create account
                </div>
              )}
            </button>
          </div>

          {/* Lien vers connexion */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
              >
                Sign in here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
