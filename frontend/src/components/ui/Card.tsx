import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  actions,
  padding = 'md',
  hover = false,
  className = ''
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const hoverClass = hover ? 'hover:shadow-md transition-shadow duration-200' : '';

  return (
    <div
      className={`
        bg-white rounded-lg shadow border border-gray-200
        ${hoverClass}
        ${className}
      `}
    >
      {(title || subtitle || actions) && (
        <div className={`border-b border-gray-200 ${paddingStyles[padding]} pb-4`}>
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-medium text-gray-900">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">
                  {subtitle}
                </p>
              )}
            </div>
            {actions && (
              <div className="flex items-center space-x-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}

      <div className={`${paddingStyles[padding]} ${title || subtitle || actions ? 'pt-4' : ''}`}>
        {children}
      </div>
    </div>
  );
};