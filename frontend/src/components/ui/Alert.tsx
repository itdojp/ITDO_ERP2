import React, { useState } from 'react';

type AlertVariant = 'info' | 'success' | 'warning' | 'error';
type AlertSize = 'sm' | 'md' | 'lg';

interface AlertProps {
  variant?: AlertVariant;
  size?: AlertSize;
  title?: string;
  message?: string;
  children?: React.ReactNode;
  closable?: boolean;
  showIcon?: boolean;
  className?: string;
  onClose?: () => void;
  actions?: React.ReactNode;
  banner?: boolean;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  size = 'md',
  title,
  message,
  children,
  closable = false,
  showIcon = true,
  className = '',
  onClose,
  actions,
  banner = false,
}) => {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  // バリアントごとのスタイル設定
  const variantStyles = {
    info: {
      container: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: 'text-blue-400',
      iconPath: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    },
    success: {
      container: 'bg-green-50 border-green-200 text-green-800',
      icon: 'text-green-400',
      iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      icon: 'text-yellow-400',
      iconPath: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    },
    error: {
      container: 'bg-red-50 border-red-200 text-red-800',
      icon: 'text-red-400',
      iconPath: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    },
  };

  // サイズごとのスタイル設定
  const sizeStyles = {
    sm: {
      container: 'p-3 text-sm',
      icon: 'h-4 w-4',
      title: 'text-sm font-medium',
      message: 'text-sm',
    },
    md: {
      container: 'p-4',
      icon: 'h-5 w-5',
      title: 'text-base font-medium',
      message: 'text-sm',
    },
    lg: {
      container: 'p-6 text-base',
      icon: 'h-6 w-6',
      title: 'text-lg font-semibold',
      message: 'text-base',
    },
  };

  const currentVariant = variantStyles[variant];
  const currentSize = sizeStyles[size];

  const containerClasses = `
    border rounded-lg transition-all duration-200
    ${banner ? 'rounded-none border-x-0 border-t-0' : ''}
    ${currentVariant.container}
    ${currentSize.container}
    ${className}
  `;

  const iconClasses = `
    flex-shrink-0
    ${currentVariant.icon}
    ${currentSize.icon}
  `;

  return (
    <div className={containerClasses}>
      <div className="flex">
        {/* アイコン */}
        {showIcon && (
          <div className="flex">
            <svg
              className={iconClasses}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={currentVariant.iconPath}
              />
            </svg>
          </div>
        )}

        {/* コンテンツ */}
        <div className={`flex-1 ${showIcon ? 'ml-3' : ''}`}>
          {title && (
            <h4 className={`${currentSize.title} mb-1`}>
              {title}
            </h4>
          )}
          
          {message && (
            <p className={currentSize.message}>
              {message}
            </p>
          )}
          
          {children && (
            <div className={`${(title || message) ? 'mt-2' : ''}`}>
              {children}
            </div>
          )}
          
          {actions && (
            <div className="mt-3">
              {actions}
            </div>
          )}
        </div>

        {/* 閉じるボタン */}
        {closable && (
          <div className="ml-auto pl-3">
            <button
              type="button"
              className={`
                inline-flex rounded-md p-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
                ${variant === 'info' ? 'text-blue-500 hover:bg-blue-100 focus:ring-blue-600' : ''}
                ${variant === 'success' ? 'text-green-500 hover:bg-green-100 focus:ring-green-600' : ''}
                ${variant === 'warning' ? 'text-yellow-500 hover:bg-yellow-100 focus:ring-yellow-600' : ''}
                ${variant === 'error' ? 'text-red-500 hover:bg-red-100 focus:ring-red-600' : ''}
              `}
              onClick={handleClose}
            >
              <span className="sr-only">閉じる</span>
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};