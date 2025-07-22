import React from 'react';

type BadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
  onClick?: () => void;
  closable?: boolean;
  onClose?: () => void;
  dot?: boolean;
  count?: number;
  showZero?: boolean;
  overflowCount?: number;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  onClick,
  closable = false,
  onClose,
  dot = false,
  count,
  showZero = false,
  overflowCount = 99,
  style,
}) => {
  // Handle count display
  const getDisplayCount = () => {
    if (dot) return '';
    if (count === undefined) return children;
    if (count === 0 && !showZero) return children;
    if (count > overflowCount) return `${overflowCount}+`;
    return count;
  };

  const displayCount = getDisplayCount();
  const hasCount = count !== undefined && (count > 0 || showZero);

  // Base classes
  const baseClasses = `
    inline-flex items-center font-medium rounded-full transition-colors duration-200
    ${onClick ? 'cursor-pointer hover:opacity-80' : ''}
  `;

  // Variant styles
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800 border border-gray-200',
    primary: 'bg-blue-100 text-blue-800 border border-blue-200',
    secondary: 'bg-gray-100 text-gray-600 border border-gray-200',
    success: 'bg-green-100 text-green-800 border border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    error: 'bg-red-100 text-red-800 border border-red-200',
    info: 'bg-blue-100 text-blue-800 border border-blue-200',
  };

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  // Count badge styles
  const countBadgeVariants = {
    default: 'bg-red-500 text-white',
    primary: 'bg-blue-500 text-white',
    secondary: 'bg-gray-500 text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-yellow-500 text-white',
    error: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white',
  };

  const badgeClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${className}
  `;

  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClose?.();
  };

  // If this is a count badge or dot badge
  if (hasCount || dot) {
    return (
      <span className="relative inline-flex">
        {children}
        <span className={`
          absolute -top-1 -right-1 flex items-center justify-center
          ${dot 
            ? 'w-2 h-2 rounded-full' 
            : 'min-w-[18px] h-[18px] rounded-full text-xs font-medium px-1'
          }
          ${countBadgeVariants[variant]}
          ${count === 0 && !showZero ? 'hidden' : ''}
        `}>
          {!dot && displayCount}
        </span>
      </span>
    );
  }

  // Regular badge
  return (
    <span
      className={badgeClasses}
      onClick={onClick}
      style={style}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {children}
      
      {closable && (
        <button
          type="button"
          className="ml-1.5 -mr-0.5 flex-shrink-0 text-current opacity-70 hover:opacity-100 focus:outline-none"
          onClick={handleClose}
          aria-label="バッジを削除"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  );
};