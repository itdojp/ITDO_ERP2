import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  hoverable?: boolean;
  bordered?: boolean;
  size?: 'small' | 'default' | 'large';
  loading?: boolean;
  cover?: React.ReactNode;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  actions,
  hoverable = false,
  bordered = true,
  size = 'default',
  loading = false,
  cover,
  onClick,
}) => {
  const baseClasses = `
    bg-white rounded-lg shadow-sm transition-all duration-200
    ${bordered ? 'border border-gray-200' : ''}
    ${hoverable ? 'hover:shadow-md cursor-pointer' : ''}
    ${onClick ? 'cursor-pointer' : ''}
  `;

  const sizeClasses = {
    small: 'p-3',
    default: 'p-4',
    large: 'p-6',
  };

  const cardClasses = `${baseClasses} ${sizeClasses[size]} ${className}`;

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  if (loading) {
    return (
      <div className={cardClasses}>
        <div className="animate-pulse">
          {(title || subtitle) && (
            <div className="mb-4">
              {title && <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>}
              {subtitle && <div className="h-4 bg-gray-200 rounded w-1/2"></div>}
            </div>
          )}
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cardClasses} onClick={handleClick}>
      {cover && <div className="mb-4 -mx-4 -mt-4">{cover}</div>}
      
      {(title || subtitle || actions) && (
        <div className={`flex items-start justify-between ${children ? 'mb-4' : ''}`}>
          <div className="flex-1 min-w-0">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
              {actions}
            </div>
          )}
        </div>
      )}
      
      {children && <div>{children}</div>}
    </div>
  );
};