import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { 
  MagnifyingGlassIcon, 
  BellIcon, 
  SunIcon,
  MoonIcon,
  ChevronLeftIcon,
  ChevronRightIcon 
} from '@heroicons/react/24/outline';

interface HeaderProps {
  className?: string;
}

const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();

  return (
    <header className={`bg-gray-50 dark:bg-gray-900/50 backdrop-blur-sm shadow-sm ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <span className="text-xl font-bold text-gray-900 dark:text-white">Resume Extractor</span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
              </div>
              <input
                type="text"
                name="search"
                id="search"
                className="block w-full pl-10 pr-3 py-2 border border-muted-foreground/50 rounded-md leading-5 bg-background placeholder-muted-foreground focus:outline-none focus:placeholder-muted-foreground focus:ring-1 focus:ring-primary focus:border-primary sm:text-sm"
                placeholder="Search resumes..."
              />
            </div>

            <button 
              onClick={() => navigate('/resumes')}
              className="p-2 rounded-full text-muted-foreground hover:text-primary"
              title="View Resumes"
            >
              <ChevronLeftIcon className="h-6 w-6" />
            </button>

            <button 
              onClick={() => navigate('/upload')}
              className="p-2 rounded-full text-muted-foreground hover:text-primary"
              title="Upload Resume"
            >
              <ChevronRightIcon className="h-6 w-6" />
            </button>

            <button 
              onClick={toggleTheme}
              className="p-2 rounded-full text-muted-foreground hover:text-primary"
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDarkMode ? (
                <SunIcon className="h-6 w-6" />
              ) : (
                <MoonIcon className="h-6 w-6" />
              )}
            </button>

            <button 
              className="p-2 rounded-full text-muted-foreground hover:text-primary"
              title="Notifications"
            >
              <BellIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
