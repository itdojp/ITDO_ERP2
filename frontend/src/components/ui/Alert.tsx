import React, { useState, useEffect } from 'react';

interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode | boolean;
  closable?: boolean;
  onClose?: () => void;
  className?: string;
  titleClassName?: string;
  contentClassName?: string;
  iconClassName?: string;
  closeButtonClassName?: string;
  bordered?: boolean;
  rounded?: boolean;
  autoClose?: boolean;
  autoCloseDelay?: number;
  role?: 'alert' | 'alertdialog' | 'status';
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  size = 'md',
  title,
  children,
  icon = true,
  closable = false,
  onClose,
  className = '',
  titleClassName = '',
  contentClassName = '',
  iconClassName = '',
  closeButtonClassName = '',
  bordered = false,
  rounded = true,
  autoClose = false,
  autoCloseDelay = 5000,
  role = 'alert'
}) => {
  const [isVisible, setIsVisible] = useState(true);

  const getVariantClasses = () => {
    const variantMap = {
      info: 'bg-blue-50 text-blue-800 border-blue-200',
      success: 'bg-green-50 text-green-800 border-green-200',
      warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
      error: 'bg-red-50 text-red-800 border-red-200'
    };
    return variantMap[variant];
  };

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'p-3 text-sm',
      md: 'p-4 text-sm',
      lg: 'p-6 text-base'
    };
    return sizeMap[size];
  };

  const getDefaultIcon = () => {
    const iconMap = {
      info: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      ),
      success: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
      warning: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      ),
      error: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    };
    return iconMap[variant];
  };

  const handleClose = () => {
    setIsVisible(false);
    onClose?.();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape' && closable) {
      handleClose();
    }
  };

  useEffect(() => {
    if (autoClose && autoCloseDelay > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseDelay]);

  if (!isVisible) {
    return null;
  }

  const renderIcon = () => {
    if (icon === false) return null;
    if (React.isValidElement(icon)) return icon;
    if (icon === true) return getDefaultIcon();
    return null;
  };

  return (
    <div
      className={`
        flex items-start gap-3 relative
        ${getVariantClasses()}
        ${getSizeClasses()}
        ${bordered ? 'border' : ''}
        ${rounded ? 'rounded-md' : ''}
        ${className}
      `}
      role={role}
      onKeyDown={handleKeyDown}
      tabIndex={closable ? 0 : -1}
    >
      {renderIcon() && (
        <div className={`flex-shrink-0 ${iconClassName}`}>
          {renderIcon()}
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className={`font-medium mb-1 ${titleClassName}`}>
            {title}
          </h4>
        )}
        
        <div className={`${contentClassName}`}>
          {children}
        </div>
      </div>

      {closable && (
        <button
          onClick={handleClose}
          className={`
            flex-shrink-0 ml-2 p-1 rounded-md transition-colors duration-200
            hover:bg-black hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-offset-2
            ${variant === 'info' ? 'focus:ring-blue-500' : ''}
            ${variant === 'success' ? 'focus:ring-green-500' : ''}
            ${variant === 'warning' ? 'focus:ring-yellow-500' : ''}
            ${variant === 'error' ? 'focus:ring-red-500' : ''}
            ${closeButtonClassName}
          `}
          aria-label="Close alert"
          type="button"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default Alert;