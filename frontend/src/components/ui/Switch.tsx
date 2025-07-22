import React from 'react';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'h-5 w-9',
    md: 'h-6 w-11',
    lg: 'h-7 w-14'
  };

  const thumbSizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6'
  };

  const translateClasses = {
    sm: checked ? 'translate-x-4' : 'translate-x-0',
    md: checked ? 'translate-x-5' : 'translate-x-0',
    lg: checked ? 'translate-x-7' : 'translate-x-0'
  };

  return (
    <div className="flex items-center">
      <button
        type="button"
        className={`
          relative inline-flex flex-shrink-0 border-2 border-transparent rounded-full
          cursor-pointer transition-colors ease-in-out duration-200
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          ${sizeClasses[size]}
          ${checked ? 'bg-blue-600' : 'bg-gray-200'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
      >
        <span
          className={`
            pointer-events-none inline-block rounded-full bg-white shadow transform ring-0
            transition ease-in-out duration-200
            ${thumbSizeClasses[size]}
            ${translateClasses[size]}
          `}
        />
      </button>
      
      {(label || description) && (
        <div className="ml-3">
          {label && (
            <div className={`text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-900'}`}>
              {label}
            </div>
          )}
          {description && (
            <div className={`text-sm ${disabled ? 'text-gray-300' : 'text-gray-500'}`}>
              {description}
            </div>
          )}
        </div>
      )}
    </div>
  );
};