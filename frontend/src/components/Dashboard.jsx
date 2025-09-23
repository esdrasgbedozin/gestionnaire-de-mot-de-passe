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
  BellIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    // Vérifier le thème sauvegardé
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
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

  const stats = [
    { name: 'Total Passwords', value: '12', icon: KeyIcon, color: 'text-blue-600', bg: 'bg-blue-100' },
    { name: 'Weak Passwords', value: '3', icon: ShieldCheckIcon, color: 'text-red-600', bg: 'bg-red-100' },
    { name: 'Categories', value: '5', icon: HomeIcon, color: 'text-green-600', bg: 'bg-green-100' },
    { name: 'Last Backup', value: '2 days', icon: UserIcon, color: 'text-purple-600', bg: 'bg-purple-100' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300">
        <div className="flex items-center justify-center h-16 bg-gradient-to-r from-indigo-500 to-purple-600">
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
                    ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <item.icon className={`mr-3 h-5 w-5 ${
                  location.pathname === item.path ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-600'
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
                <p className="text-gray-600 dark:text-gray-400">Welcome back, {user?.email?.split('@')[0]}!</p>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={toggleDarkMode}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-white transition-colors"
                >
                  {darkMode ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
                </button>
                
                <button className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-white transition-colors">
                  <BellIcon className="h-5 w-5" />
                </button>
                
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search passwords..."
                      className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className={`p-6 transition-all duration-700 ${isAnimating ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
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
                className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all duration-200 group"
              >
                <PlusIcon className="h-8 w-8 text-gray-400 group-hover:text-indigo-500" />
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900 dark:text-white">Add Password</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Store a new password securely</p>
                </div>
              </button>
              
              <button 
                onClick={() => toast.info('Security check feature coming soon!')}
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
                className="flex items-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all duration-200 group"
              >
                <CogIcon className="h-8 w-8 text-gray-400 group-hover:text-purple-500" />
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
              <div className="flex items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Password created for Gmail</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">2 hours ago</p>
                </div>
              </div>
              
              <div className="flex items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Security check completed</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">1 day ago</p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;