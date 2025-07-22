import React from 'react';

type ProgressVariant = 'default' | 'success' | 'warning' | 'error';
type ProgressSize = 'sm' | 'md' | 'lg';

interface ProgressProps {
  value: number;
  max?: number;
  variant?: ProgressVariant;
  size?: ProgressSize;
  showLabel?: boolean;
  label?: string;
  className?: string;
  animated?: boolean;
  striped?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  variant = 'default',
  size = 'md',
  showLabel = false,
  label,
  className = '',
  animated = false,
  striped = false,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  // バリアントごとのスタイル
  const variantStyles = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    error: 'bg-red-600',
  };

  // サイズごとのスタイル
  const sizeStyles = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const containerClasses = `
    w-full bg-gray-200 rounded-full overflow-hidden
    ${sizeStyles[size]}
    ${className}
  `;

  const barClasses = `
    h-full transition-all duration-500 ease-out rounded-full
    ${variantStyles[variant]}
    ${animated ? 'progress-bar-animated' : ''}
    ${striped ? 'progress-bar-striped' : ''}
  `;

  return (
    <div className="w-full">
      {/* ラベル */}
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-sm font-medium text-gray-700">
              {label}
            </span>
          )}
          {showLabel && (
            <span className="text-sm text-gray-500">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      
      {/* プログレスバー */}
      <div className={containerClasses}>
        <div 
          className={barClasses}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      
      <style jsx>{`
        .progress-bar-striped {
          background-image: linear-gradient(
            45deg,
            rgba(255, 255, 255, 0.15) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, 0.15) 50%,
            rgba(255, 255, 255, 0.15) 75%,
            transparent 75%,
            transparent
          );
          background-size: 1rem 1rem;
        }
        
        .progress-bar-animated {
          animation: progress-bar-stripes 1s linear infinite;
        }
        
        @keyframes progress-bar-stripes {
          0% {
            background-position-x: 1rem;
          }
          100% {
            background-position-x: 0;
          }
        }
      `}</style>
    </div>
  );
};