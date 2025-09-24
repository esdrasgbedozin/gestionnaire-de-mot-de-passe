import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  KeyIcon, 
  CogIcon, 
  UserIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  BellIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import passwordService from '../services/passwordService';
import { calculatePasswordStats, formatRelativeDate, getRecentPasswords } from '../utils/passwordStats';
import ThemeToggle from './ThemeToggle';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isAnimating, setIsAnimating] = useState(false);
  const [passwords, setPasswords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [recentActivity, setRecentActivity] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    weak: 0,
    medium: 0,
    strong: 0,
    categories: 0,
    favorites: 0,
    recentlyAdded: 0,
  });

  useEffect(() => {
    setIsAnimating(true);
    
    // Charger les mots de passe
    loadPasswords();
  }, []);

  const loadPasswords = async () => {
    try {
      setLoading(true);
      console.log('📱 Dashboard: Starting to load passwords...');
      const response = await passwordService.getPasswords();
      console.log('📱 Dashboard: Response from passwordService:', response);
      
      if (response.success && response.data) {
        const passwordList = response.data.passwords || [];
        console.log('📱 Dashboard: Raw passwords from backend:', passwordList.slice(0, 2)); // Log first 2 passwords
        
        setPasswords(passwordList);
        
        // Calculer les statistiques
        const stats = calculatePasswordStats(passwordList);
        setStats(stats);
        console.log('📱 Dashboard: Calculated stats:', stats);
        
        // Récentes activités
        const recent = getRecentPasswords(passwordList, 7); // Last 7 days
        console.log('📱 Dashboard: Recent passwords for activities:', recent.slice(0, 2)); // Log recent
        
        const recentActivities = recent.map(pwd => {
          const wasUpdated = pwd.updated_at && pwd.updated_at !== pwd.created_at;
          const dateToUse = wasUpdated ? pwd.updated_at : pwd.created_at;
          console.log('📱 Dashboard: Processing password date:', { 
            site: pwd.site_name, 
            created_at: pwd.created_at, 
            updated_at: pwd.updated_at,
            dateToUse: dateToUse,
            wasUpdated: wasUpdated
          });
          
          return {
            id: pwd.id,
            type: wasUpdated ? 'updated' : 'created',
            siteName: pwd.site_name,
            date: dateToUse,
            relativeDate: formatRelativeDate(dateToUse)
          };
        }).slice(0, 5); // Afficher seulement les 5 plus récents

        setRecentActivity(recentActivities);
        console.log('📱 Dashboard: Set recent activities:', recentActivities);
      } else {
        console.error('📱 Dashboard: Error loading passwords:', response.error);
        toast.error(response.error || 'Error loading passwords');
      }
    } catch (error) {
      console.error('📱 Dashboard: Exception loading passwords:', error);
      toast.error('Error loading passwords');
    } finally {
      console.log('📱 Dashboard: Finished loading passwords, setting loading to false');
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('👋 Logged out successfully!');
    } catch (error) {
      toast.error('Error during logout');
    }
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      // Naviguer vers le vault avec le terme de recherche
      navigate('/vault', { state: { searchTerm: searchTerm.trim() } });
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // Configuration des cartes de statistiques avec données réelles
  const statsCards = [
    { 
      name: 'Total Passwords', 
      value: loading ? '...' : stats.total.toString(), 
      icon: KeyIcon, 
      color: 'text-pink-600', 
      bg: 'bg-pink-100' 
    },
    { 
      name: 'Weak Passwords', 
      value: loading ? '...' : stats.weak.toString(), 
      icon: ShieldCheckIcon, 
      color: 'text-red-600', 
      bg: 'bg-red-100' 
    },
    { 
      name: 'Categories', 
      value: loading ? '...' : stats.categories.toString(), 
      icon: HomeIcon, 
      color: 'text-green-600', 
      bg: 'bg-green-100' 
    },
    { 
      name: 'Recently Added', 
      value: loading ? '...' : stats.recentlyAdded.toString(), 
      icon: UserIcon, 
      color: 'text-rose-600', 
      bg: 'bg-rose-100' 
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300">
        <div className="flex items-center justify-center h-16 bg-gradient-to-r from-pink-500 to-rose-600">
          <ShieldCheckIcon className="h-8 w-8 text-white" />
          <span className="ml-2 text-xl font-bold text-white">PassGuard</span>
        </div>
        
        <nav className="mt-8">
          <div className="px-4 space-y-2">
            {[
              { name: 'Dashboard', icon: HomeIcon, path: '/dashboard' },
              { name: 'Passwords', icon: KeyIcon, path: '/vault' },
              { name: 'Settings', icon: CogIcon, path: '/settings' },
            ].map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.path)}
                className={`w-full group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  location.pathname === item.path
                    ? 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <item.icon className={`mr-3 h-5 w-5 ${
                  location.pathname === item.path ? 'text-pink-600' : 'text-gray-400 group-hover:text-gray-600'
                }`} />
                {item.name}
              </button>
            ))}
          </div>
        </nav>
        
        {/* User Section */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UserIcon className="h-8 w-8 text-gray-400" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user?.email}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="ml-3 p-2 text-gray-400 hover:text-red-500 transition-colors"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-400">Secure your digital life, {user?.username || user?.email?.split('@')[0]} ! 🔐</p>
              </div>
              
              <div className="flex items-center space-x-4">
                <ThemeToggle />
                
                <button className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-white transition-colors">
                  <BellIcon className="h-5 w-5" />
                </button>
                
                <div className="flex items-center space-x-2">
                  <form onSubmit={handleSearch} className="relative">
                    <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={searchTerm}
                      onChange={handleSearchChange}
                      placeholder="Search passwords..."
                      className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    />
                  </form>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className={`p-6 transition-all duration-700 ${isAnimating ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statsCards.map((stat, index) => (
              <div 
                key={stat.name} 
                className={`bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200 transform hover:scale-105 animate-fadeInUp`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-center">
                  <div className={`p-3 rounded-full ${stat.bg} dark:bg-opacity-20`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button 
                onClick={() => handleNavigation('/vault')}
                className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl hover:border-pink-500 hover:bg-pink-50 dark:hover:bg-pink-900/20 transition-all duration-200 group"
              >
                <PlusIcon className="h-8 w-8 text-gray-400 group-hover:text-pink-500" />
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900 dark:text-white">Add Password</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Store a new password securely</p>
                </div>
              </button>
              
              <button 
                onClick={() => handleNavigation('/security-check')}
                className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 transition-all duration-200 group"
              >
                <ShieldCheckIcon className="h-8 w-8 text-gray-400 group-hover:text-green-500" />
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900 dark:text-white">Security Check</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Analyze password strength</p>
                </div>
              </button>
              
              <button 
                onClick={() => handleNavigation('/settings')}
                className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl hover:border-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all duration-200 group"
              >
                <CogIcon className="h-8 w-8 text-gray-400 group-hover:text-rose-500" />
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900 dark:text-white">Settings</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Customize your experience</p>
                </div>
              </button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
            <div className="space-y-4">
              {loading ? (
                <div className="animate-pulse space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                      <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                      <div className="ml-4 flex-1">
                        <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : recentActivity.length > 0 ? (
                recentActivity.map(activity => (
                  <div key={activity.id} className="flex items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                    <div className="flex-shrink-0">
                      <div className={`w-2 h-2 rounded-full ${
                        activity.type === 'created' ? 'bg-green-500' : 'bg-blue-500'
                      }`}></div>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Password {activity.type === 'created' ? 'created' : 'updated'} for {activity.siteName}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.relativeDate}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">
                    No recent activity
                  </p>
                  <button
                    onClick={() => handleNavigation('/vault')}
                    className="mt-2 text-indigo-600 dark:text-indigo-400 text-sm hover:underline"
                  >
                    Add your first password
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;