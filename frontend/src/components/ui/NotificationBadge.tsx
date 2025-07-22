import React from 'react';

interface NotificationBadgeProps {
  count: number;
  maxCount?: number;
  variant?: 'primary' | 'danger' | 'warning' | 'success';
  size?: 'sm' | 'md' | 'lg';
  showZero?: boolean;
  children?: React.ReactNode;
}

export const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  count,
  maxCount = 99,
  variant = 'danger',
  size = 'md',
  showZero = false,
  children
}) => {
  const shouldShow = count > 0 || showZero;
  const displayCount = count > maxCount ? `${maxCount}+` : count.toString();

  const variantClasses = {
    primary: 'bg-blue-500 text-white',
    danger: 'bg-red-500 text-white',
    warning: 'bg-yellow-500 text-white',
    success: 'bg-green-500 text-white'
  };

  const sizeClasses = {
    sm: 'h-4 min-w-4 text-xs px-1',
    md: 'h-5 min-w-5 text-sm px-1.5',
    lg: 'h-6 min-w-6 text-base px-2'
  };

  if (!shouldShow && !children) {
    return null;
  }

  if (children) {
    return (
      <div className="relative inline-block">
        {children}
        {shouldShow && (
          <span
            className={`absolute -top-1 -right-1 inline-flex items-center justify-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]}`}
          >
            {displayCount}
          </span>
        )}
      </div>
    );
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]}`}
    >
      {displayCount}
    </span>
  );
};

export default NotificationBadge;