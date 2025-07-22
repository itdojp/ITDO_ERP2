import React from 'react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
  error?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  description,
  error,
  className = '',
  ...props
}) => {
  const hasError = !!error;

  return (
    <div className="relative flex items-start">
      <div className="flex items-center h-5">
        <input
          type="checkbox"
          className={`
            focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded
            ${hasError ? 'border-red-300' : ''}
            ${className}
          `}
          {...props}
        />
      </div>
      
      {(label || description) && (
        <div className="ml-3 text-sm">
          {label && (
            <label className={`font-medium ${hasError ? 'text-red-900' : 'text-gray-700'}`}>
              {label}
            </label>
          )}
          {description && (
            <p className={`${hasError ? 'text-red-600' : 'text-gray-500'}`}>
              {description}
            </p>
          )}
        </div>
      )}
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};