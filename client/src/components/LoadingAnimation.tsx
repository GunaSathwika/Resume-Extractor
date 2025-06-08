import React from 'react';

interface LoadingAnimationProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ 
  className = '', 
  size = 'md' 
}) => {
  const sizes = {
    sm: 'h-24 w-24',
    md: 'h-32 w-32',
    lg: 'h-48 w-48'
  };

  return (
    <div className={`flex justify-center items-center ${className}`}>
      <div className={`animate-spin rounded-full ${sizes[size]} border-b-2 border-indigo-500`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-indigo-500">Loading...</span>
        </div>
      </div>
    </div>
  );
};

export default LoadingAnimation;
