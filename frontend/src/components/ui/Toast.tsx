import React, { useEffect, useState } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  onRemove: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onRemove
}) => {
  const [isVisible, setIsVisible] = useState(true);

  const typeStyles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: '✅',
      iconBg: 'bg-green-100',
      textColor: 'text-green-800'
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: '❌',
      iconBg: 'bg-red-100',
      textColor: 'text-red-800'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: '⚠️',
      iconBg: 'bg-yellow-100',
      textColor: 'text-yellow-800'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'ℹ️',
      iconBg: 'bg-blue-100',
      textColor: 'text-blue-800'
    }
  };

  const styles = typeStyles[type];

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onRemove(id), 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onRemove]);

  return (
    <div
      className={`
        max-w-sm w-full ${styles.bg} ${styles.border} border rounded-lg shadow-lg p-4
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
    >
      <div className="flex items-start">
        <div className={`flex-shrink-0 w-8 h-8 ${styles.iconBg} rounded-full flex items-center justify-center`}>
          <span>{styles.icon}</span>
        </div>
        <div className="ml-3 flex-1">
          <p className={`text-sm font-medium ${styles.textColor}`}>
            {title}
          </p>
          {message && (
            <p className={`mt-1 text-sm ${styles.textColor} opacity-75`}>
              {message}
            </p>
          )}
        </div>
        <div className="ml-4 flex-shrink-0">
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(() => onRemove(id), 300);
            }}
            className={`${styles.textColor} opacity-50 hover:opacity-75`}
          >
            <span>×</span>
          </button>
        </div>
      </div>
    </div>
  );
};