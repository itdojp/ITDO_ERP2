import React from 'react';

interface ProgressBarProps {
  value: number;
  max?: number;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showValue?: boolean;
  label?: string;
  striped?: boolean;
  animated?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  variant = 'primary',
  size = 'md',
  showLabel = false,
  showValue = false,
  label,
  striped = false,
  animated = false,
  className = ''
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const variantClasses = {
    primary: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    danger: 'bg-red-600',
    info: 'bg-cyan-600'
  };

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6'
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  const getStatusVariant = (percentage: number) => {
    if (percentage >= 100) return 'success';
    if (percentage >= 75) return 'info';
    if (percentage >= 50) return 'warning';
    if (percentage >= 25) return 'primary';
    return 'danger';
  };

  const dynamicVariant = variant === 'primary' ? getStatusVariant(percentage) : variant;

  return (
    <div className={`w-full ${className}`}>
      {/* Label */}
      {(showLabel || label) && (
        <div className={`flex justify-between items-center mb-1 ${textSizeClasses[size]}`}>
          <span className="text-gray-700">{label || 'Progress'}</span>
          {showValue && (
            <span className="text-gray-600 font-medium">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}

      {/* Progress Bar Container */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`
            ${sizeClasses[size]} transition-all duration-300 ease-out rounded-full
            ${variantClasses[dynamicVariant]}
            ${striped ? 'bg-striped' : ''}
            ${animated ? 'animate-pulse' : ''}
          `}
          style={{ 
            width: `${percentage}%`,
            backgroundImage: striped ? `linear-gradient(
              45deg,
              rgba(255, 255, 255, 0.2) 25%,
              transparent 25%,
              transparent 50%,
              rgba(255, 255, 255, 0.2) 50%,
              rgba(255, 255, 255, 0.2) 75%,
              transparent 75%,
              transparent
            )` : undefined,
            backgroundSize: striped ? '1rem 1rem' : undefined,
            animation: striped && animated ? 'progress-bar-stripes 1s linear infinite' : undefined
          }}
        />
      </div>

      {/* Value display inside bar for larger sizes */}
      {size === 'lg' && showValue && (
        <div className="relative">
          <div
            className="absolute inset-0 flex items-center justify-center text-white text-sm font-medium"
            style={{ width: `${percentage}%` }}
          >
            {percentage >= 15 && `${Math.round(percentage)}%`}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes progress-bar-stripes {
          0% {
            background-position: 1rem 0;
          }
          100% {
            background-position: 0 0;
          }
        }
      `}</style>
    </div>
  );
};

export default ProgressBar;