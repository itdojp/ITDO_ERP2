import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  shape?: 'rounded' | 'pill' | 'square';
  outline?: boolean;
  dot?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  removable?: boolean;
  onRemove?: () => void;
  className?: string;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
  animated?: boolean;
  pulse?: boolean;
  count?: number;
  maxCount?: number;
  showZero?: boolean;
  bordered?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  shape = 'rounded',
  outline = false,
  dot = false,
  icon,
  iconPosition = 'left',
  removable = false,
  onRemove,
  className = '',
  onClick,
  href,
  disabled = false,
  animated = false,
  pulse = false,
  count,
  maxCount = 99,
  showZero = false,
  bordered = false
}) => {
  const getVariantClasses = () => {
    const baseClasses = outline ? 'border-2 bg-transparent' : '';
    
    const variantMap = {
      default: outline 
        ? `${baseClasses} border-gray-300 text-gray-700 hover:bg-gray-50`
        : 'bg-gray-100 text-gray-800 hover:bg-gray-200',
      secondary: outline
        ? `${baseClasses} border-gray-600 text-gray-600 hover:bg-gray-50`
        : 'bg-gray-600 text-white hover:bg-gray-700',
      success: outline
        ? `${baseClasses} border-green-500 text-green-600 hover:bg-green-50`
        : 'bg-green-500 text-white hover:bg-green-600',
      warning: outline
        ? `${baseClasses} border-yellow-500 text-yellow-600 hover:bg-yellow-50`
        : 'bg-yellow-500 text-white hover:bg-yellow-600',
      error: outline
        ? `${baseClasses} border-red-500 text-red-600 hover:bg-red-50`
        : 'bg-red-500 text-white hover:bg-red-600',
      info: outline
        ? `${baseClasses} border-blue-500 text-blue-600 hover:bg-blue-50`
        : 'bg-blue-500 text-white hover:bg-blue-600'
    };
    return variantMap[variant];
  };

  const getSizeClasses = () => {
    if (dot) {
      const dotSizeMap = {
        sm: 'w-2 h-2',
        md: 'w-3 h-3',
        lg: 'w-4 h-4'
      };
      return dotSizeMap[size];
    }

    const sizeMap = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base'
    };
    return sizeMap[size];
  };

  const getShapeClasses = () => {
    if (dot) return 'rounded-full';
    
    const shapeMap = {
      rounded: 'rounded-md',
      pill: 'rounded-full',
      square: 'rounded-none'
    };
    return shapeMap[shape];
  };

  const getDisplayContent = () => {
    if (count !== undefined) {
      if (count === 0 && !showZero) return null;
      return count > maxCount ? `${maxCount}+` : count.toString();
    }
    return children;
  };

  const handleRemove = (event: React.MouseEvent) => {
    event.stopPropagation();
    onRemove?.();
  };

  const handleClick = (event: React.MouseEvent) => {
    if (disabled) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled) return;
    
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick?.(event as any);
    }
  };

  const isClickable = !!(onClick || href);
  const Element = href && !disabled ? 'a' : isClickable ? 'button' : 'span';

  const badgeClasses = `
    inline-flex items-center justify-center gap-1 font-medium transition-colors duration-200
    ${getVariantClasses()}
    ${getSizeClasses()}
    ${getShapeClasses()}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    ${isClickable && !disabled ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500' : ''}
    ${animated ? 'transition-all duration-300 ease-in-out' : ''}
    ${pulse ? 'animate-pulse' : ''}
    ${bordered ? 'border' : ''}
    ${className}
  `;

  const elementProps: any = {
    className: badgeClasses,
    onClick: handleClick,
    onKeyDown: handleKeyDown
  };

  if (Element === 'a') {
    elementProps.href = href;
    elementProps.role = 'link';
  } else if (isClickable) {
    elementProps.type = 'button';
    elementProps.role = 'button';
    elementProps.tabIndex = disabled ? -1 : 0;
  }

  if (disabled) {
    elementProps['aria-disabled'] = 'true';
  }

  const displayContent = getDisplayContent();
  if (displayContent === null && !dot) {
    return null;
  }

  if (dot) {
    return (
      <span
        className={`
          ${badgeClasses}
          ${pulse ? 'animate-ping' : ''}
        `}
        aria-label={typeof children === 'string' ? children : 'Badge indicator'}
      />
    );
  }

  const renderIcon = (position: 'left' | 'right') => {
    if (!icon || iconPosition !== position) return null;
    return <span className="flex-shrink-0">{icon}</span>;
  };

  const renderRemoveButton = () => {
    if (!removable) return null;
    
    return (
      <button
        onClick={handleRemove}
        className="ml-1 flex-shrink-0 rounded-full p-0.5 hover:bg-black hover:bg-opacity-20 focus:outline-none focus:bg-black focus:bg-opacity-20 transition-colors duration-200"
        aria-label="Remove badge"
        type="button"
        tabIndex={0}
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    );
  };

  return (
    <Element {...elementProps}>
      {renderIcon('left')}
      <span className="truncate">{displayContent}</span>
      {renderIcon('right')}
      {renderRemoveButton()}
    </Element>
  );
};

export default Badge;