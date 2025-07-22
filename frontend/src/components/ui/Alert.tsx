import React from 'react';

interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  onClose?: () => void;
  actions?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  type,
  title,
  message,
  onClose,
  actions
}) => {
  const typeStyles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: '✅',
      textColor: 'text-green-800'
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: '❌',
      textColor: 'text-red-800'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: '⚠️',
      textColor: 'text-yellow-800'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'ℹ️',
      textColor: 'text-blue-800'
    }
  };

  const styles = typeStyles[type];

  return (
    <div className={`${styles.bg} ${styles.border} border rounded-lg p-4`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <span className="text-lg">{styles.icon}</span>
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={`text-sm font-medium ${styles.textColor}`}>
              {title}
            </h3>
          )}
          <div className={`${title ? 'mt-2' : ''} text-sm ${styles.textColor}`}>
            {message}
          </div>
          {actions && (
            <div className="mt-4">
              {actions}
            </div>
          )}
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                onClick={onClose}
                className={`inline-flex rounded-md p-1.5 ${styles.textColor} hover:bg-opacity-20 focus:outline-none`}
              >
                <span className="text-lg">×</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};