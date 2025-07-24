import React from 'react';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated' | 'filled';
  size?: 'sm' | 'md' | 'lg';
  rounded?: boolean;
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  bordered?: boolean;
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: (event: React.MouseEvent) => void;
  href?: string;
  className?: string;
  headerClassName?: string;
  bodyClassName?: string;
  footerClassName?: string;
  imageClassName?: string;
  disabled?: boolean;
  loading?: boolean;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  image?: string | React.ReactNode;
  imageAlt?: string;
  imagePosition?: 'top' | 'bottom' | 'left' | 'right';
  actions?: React.ReactNode;
  title?: string;
  subtitle?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  compact?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  size = 'md',
  rounded = true,
  shadow = 'md',
  bordered = false,
  hoverable = false,
  clickable = false,
  onClick,
  href,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  imageClassName = '',
  disabled = false,
  loading = false,
  header,
  footer,
  image,
  imageAlt = '',
  imagePosition = 'top',
  actions,
  title,
  subtitle,
  titleClassName = '',
  subtitleClassName = '',
  compact = false
}) => {
  const getVariantClasses = () => {
    const variantMap = {
      default: 'bg-white',
      outlined: 'bg-white border border-gray-200',
      elevated: 'bg-white',
      filled: 'bg-gray-50'
    };
    return variantMap[variant];
  };

  const getSizeClasses = () => {
    if (compact) return 'p-3';
    
    const sizeMap = {
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8'
    };
    return sizeMap[size];
  };

  const getShadowClasses = () => {
    const shadowMap = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
      xl: 'shadow-xl'
    };
    return shadowMap[shadow];
  };

  const getHoverClasses = () => {
    if (disabled || loading) return '';
    
    if (hoverable || clickable) {
      return 'transition-all duration-200 hover:shadow-lg hover:-translate-y-1';
    }
    return '';
  };

  const getRoundedClasses = () => {
    return rounded ? 'rounded-lg' : '';
  };

  const isInteractive = !!(clickable || onClick || href);
  const Element = href && !disabled ? 'a' : isInteractive ? 'button' : 'div';

  const handleClick = (event: React.MouseEvent) => {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled || loading) return;
    
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick?.(event as any);
    }
  };

  const cardClasses = `
    relative overflow-hidden
    ${getVariantClasses()}
    ${getRoundedClasses()}
    ${getShadowClasses()}
    ${getHoverClasses()}
    ${bordered ? 'border border-gray-200' : ''}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    ${isInteractive && !disabled && !loading ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2' : ''}
    ${loading ? 'animate-pulse cursor-wait' : ''}
    ${className}
  `;

  const elementProps: any = {
    className: cardClasses,
    onClick: handleClick,
    onKeyDown: handleKeyDown
  };

  if (Element === 'a') {
    elementProps.href = href;
    elementProps.role = 'link';
  } else if (isInteractive) {
    elementProps.type = 'button';
    elementProps.role = 'button';
    elementProps.tabIndex = disabled ? -1 : 0;
  }

  if (disabled) {
    elementProps['aria-disabled'] = 'true';
  }

  if (loading) {
    elementProps['aria-busy'] = 'true';
  }

  const renderImage = () => {
    if (!image) return null;

    const imageElement = typeof image === 'string' ? (
      <img 
        src={image} 
        alt={imageAlt}
        className={`w-full h-full object-cover ${imageClassName}`}
      />
    ) : (
      <div className={imageClassName}>{image}</div>
    );

    const imageWrapperClasses = `
      ${imagePosition === 'top' ? 'w-full h-48' : ''}
      ${imagePosition === 'bottom' ? 'w-full h-48' : ''}
      ${imagePosition === 'left' ? 'w-48 h-full flex-shrink-0' : ''}
      ${imagePosition === 'right' ? 'w-48 h-full flex-shrink-0' : ''}
      overflow-hidden
    `;

    return (
      <div className={imageWrapperClasses}>
        {imageElement}
      </div>
    );
  };

  const renderHeader = () => {
    if (!header && !title && !subtitle) return null;

    return (
      <div className={`${compact ? 'mb-2' : 'mb-4'} ${headerClassName}`}>
        {header || (
          <div>
            {title && (
              <h3 className={`text-lg font-semibold text-gray-900 ${titleClassName}`}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p className={`text-sm text-gray-500 mt-1 ${subtitleClassName}`}>
                {subtitle}
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderBody = () => {
    return (
      <div className={`flex-1 ${bodyClassName}`}>
        {children}
      </div>
    );
  };

  const renderFooter = () => {
    if (!footer && !actions) return null;

    return (
      <div className={`${compact ? 'mt-2' : 'mt-4'} ${footerClassName}`}>
        {footer || actions}
      </div>
    );
  };

  const renderLoadingOverlay = () => {
    if (!loading) return null;

    return (
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-500">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
          <span className="text-sm">Loading...</span>
        </div>
      </div>
    );
  };

  const contentClasses = `
    ${getSizeClasses()}
    ${imagePosition === 'left' || imagePosition === 'right' ? 'flex-1' : ''}
  `;

  const isHorizontalImage = imagePosition === 'left' || imagePosition === 'right';

  return (
    <Element {...elementProps}>
      {imagePosition === 'top' && renderImage()}
      
      <div className={isHorizontalImage ? 'flex' : ''}>
        {imagePosition === 'left' && renderImage()}
        
        <div className={contentClasses}>
          {renderHeader()}
          {renderBody()}
          {renderFooter()}
        </div>
        
        {imagePosition === 'right' && renderImage()}
      </div>
      
      {imagePosition === 'bottom' && renderImage()}
      {renderLoadingOverlay()}
    </Element>
  );
};

export default Card;