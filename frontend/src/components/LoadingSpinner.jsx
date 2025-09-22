import React from 'react';

const LoadingSpinner = ({ size = 'medium', color = 'indigo' }) => {
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-12 h-12',
    large: 'w-16 h-16',
  };

  const colorClasses = {
    indigo: 'border-indigo-500',
    blue: 'border-blue-500',
    green: 'border-green-500',
    red: 'border-red-500',
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-20 backdrop-blur-sm z-50">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div
            className={`${sizeClasses[size]} border-4 ${colorClasses[color]} border-t-transparent rounded-full animate-spin`}
          ></div>
          <p className="text-gray-600 dark:text-gray-300 font-medium animate-pulse">
            Loading...
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;